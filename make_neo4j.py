#import setup.populate_neo4j as pop
import setup.populate_database as pop
import setup.neo4j_utils as n4j


# Be sure to clear out any previous database before you begin:
# sudo rm -r /var/lib/neo4j/data/databases/graph.db


pop.populate_database(
        corpus_path='data/s2-corpus',
        csv_path='data/csv',
        prefix='s2-corpus',
        suffix='.csv',
        start=0,
        end=176,
        compress=False,
        engine='neo4j',
        testing=False,
        cache=True)


#bucket='data-atsume-arxiv'
#source='open-corpus/2019-09-17/s2-corpus-000.gz'
#destination='data/s2-corpus/s2-corpus-000.gz'

#s3 = boto3.client('s3')
#s3.download_file(bucket, source, destination)
