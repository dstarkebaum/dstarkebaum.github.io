# Welcome to postgres-vs-neo4j!

## Prepared by David Starkebaum for
## Insight Data Engineering 2019 in Seattle!

The goal of this project is to compare two database engines:
**Postgres (Relational)** and **Neo4 (Graph)**


`setup/populate_database.py` contains the main code,
which will download a specified subset of json files from S3,
send them to `setup/json_to_csv.py` to parse into csv files,
then send those files to either `postgres_util.py`
or `neo4j_utils.py` to be loaded into the database.

From there it may be necessary to call additional functions
to remove duplicates and add indexes as needed.


# Neo4j import:
There are two versions of the script:
- One uses `neo4j-admin import`, which is adapted for large-scale bulk csv imports,
but it only works on an empty database, and all of the csv files are available
locally on disk.
- The other method uses Cypher queries `COPY FROM CSV WITH HEADERS AS row...`
## For `neo4j-admin import`:
You will need to delete (or backup) the current database before repopulating:

`sudo rm -r /var/lib/neo4j/data/databases/graph.db`


## Troubleshooting:
Sometimes you try to start neo4j and it will not work:
`sudo neo4j start`

Start by checking:
`neo4j status`

If neo4j is not running, check the log file:
`sudo nano /var/log/neo4j/neo4j.log`

You may see an error like this:
```
ERROR Failed to start Neo4j: Starting Neo4j failed:
Component 'org.neo4j.server.database.LifecycleManagingDatabase@xxxxxx'
was was successfully initialized, but failed to start.
Please see the attached cause exception
"Store and its lock file has been locked by another process:
/var/lib/neo4j/data/databases/store_lock.
Please ensure no other process is using this database,
and that the directory is writable (required even for read-only access)".
```
In this case, a store lock has been used to prevent racing conditions
(when multiple processes try to read/write from the same location).
You can double-check if another process is running neo4j by using htop:
`sudo apt-get install htop` (if its not already installed):
`sudo htop` --> F5 (to show tree-view) --> F4 (filter) --> type 'neo4j'
You can then kill the top neo4j process with F9:
`usr/bin/java -cp /var/lib/neo4j/plugins: ...`

You can also do this by command line:
(search for neo4j with pgrep, and kill whatever process is there)
`sudo kill $(pgrep -f neo4j)`

Then remove the store_lock
`sudo rm /var/lib/neo4j/data/databases/store_lock`

## Setting up a password:
If you haven't started your server yet, you can pre-configure neo4j
with a default password using neo4j-admin:

`sudo neo4j-admin set-initial-password <password>`

If you have already started your database you can login to it
with cypher-shell, (default user:`neo4j`, default: `neo4j`)
`CALL dbms.security.changePassword("<password>")`



You may also need to modify the neo4j configuration file:
`sudo nano /etc/neo4j/neo4j.conf`

You can find (somewhat) detailed information about each parameter here:
https://neo4j.com/docs/operations-manual/current/reference/configuration-settings/

Use this to estimate appropriate settings:
`neo4j-admin memrec`

Paramaters to look for:
`dbms.security.auth_enabled=false`
- Disables authentication for user access...
Not ideal from a security standpoint, but this may help you just get it working

`#dbms.directories.import=/var/lib/neo4j/import`
- Commenting this out allows you to load csv files from anywhere,
not just from the neo4j/import directory.
`dbms.security.allow_csv_import_from_file_urls=true`
- This allows you to read CSV files from remote URL's (like S3), if you prefer

`dbms.memory.heap.max_size=512m`
`dbms.memory.pagecache.size=10g`
- See https://neo4j.com/docs/operations-manual/current/performance/memory-configuration/
for advice on memory allocation (depends on how much RAM you actually have available)

`dbms.connectors.default_listen_address=0.0.0.0`
- You can choose specific IP addresses to listen to, rather than all internet
But you will need to put something here to enable any access over a network

`dbms.db.timezone=SYSTEM`
- **NOTE**: This setting is not included in the default neo4j.conf file
But it is very helpful to get useful logs that actually record the local time
according to your system clock instead of UTC


Check the results with `cypher-shell`:
`CALL db.indexes();`

Make indexes if needed:
`CREATE CONSTRAINT ON (p:Paper) ASSERT p.id IS UNIQUE;`
`CREATE CONSTRAINT ON (a:Author) ASSERT a.id IS UNIQUE;`

You can also execute commands directly from bash (useful for long-running tasks):
`cypher-shell --non-interactive 'CREATE CONSTRAINT ON (a:Author) ASSERT a.id IS UNIQUE;'`
then press ctrl+z to pause, type `bg` to move to background, then `disown` to release it from your terminal
This can allow you to logout and let the process continue until it is finished

Backup neo4j (community edition):
https://www.postgresql.org/docs/10/backup-file.html
`tar -cf backup.tar /var/lib/neo4j/data/databases/graph.db`
"tar -c" = create archive
"tar -f" = choose filename for the archive (next argument)





## For postgres import
- More to come soon

PGTune - a convenient tool to estimate memory settings for Postgres:
https://pgtune.leopard.in.ua/

Settings files:
`sudo nano /etc/postgresql/10/main/postgresql.conf`
`sudo nano /etc/postgresql/10/main/pg_hba.conf`


psql:
SELECT * FROM pg_available_extensions;
create extension btree_gin;
create extension pg_stat_statements;
create extension pg_trgm;
\dx



`sudo service postgresql restart`

logfile on Ubuntu
`less /var/log/postgresql/postgresql-10-main.log`

Calculate the size of the database:
`sudo du -sh /var/lib/postgresql/10/main`

Making a database backup:
https://www.postgresql.org/docs/10/backup-file.html

First *stop the database*
`sudo service postgresql stop`
Navigate to the directory containing your database:
`cd /var/lib/postgresql/10`
Put the whole database into a tar file:
`sudo tar -cf main_backup.tar main`

Restoring a backup:
Navigate to the directory containing your database:
`cd /var/lib/postgresql/10`
For safety sake you can first just rename your current database:
`sudo mv main main_original`
Then extract your tar file (it should automatically be named "main", and have the correct permissions as before):
`sudo tar -xvf main_backup.tar`
Finally, restart the database
`sudo service postgresql start`


Check indexes:
```
SELECT tablename, indexname, indexdef
FROM pg_indexes WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

## Clearing cache for benchmarking

`sudo service postgresql stop` / `sudo neo4j stop`
`sync && echo 3 | sudo tee /proc/sys/vm/drop_caches`
`sudo service postgresql start` / `sudo neo4j start`


## Increasing EBS Volume size
https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-modify-volume.html

You can increase the volumne through the EC2 Console,
but then you have to tell your linux OS that things have changed.
After increaseing the volume size, check the current partitions:
`lsblk`

You should see something like this:
```
nvme0n1
└─nvme0n1p1
```

You can also check the filesystem with:
`df -Th`

You can extend the partition (even while it is mounted) with:
`sudo growpart /dev/nvme0n1 1`
Note: nvme0n1 is the drive name, and nvme0n1p1 is partition 1 on that drive

Then you extend the file system (usually Ext4) with:
`sudo resize2fs /dev/nvme0n1p1`

Done!

[Data Atsume website](http://www.data-atsu.me)
