#!/usr/bin/env python2.7

import psycopg2
import os
import time
#def main(host='localhost',database='ubuntu',user='ubuntu',password='ubuntu'):

'''
Decorator to handle database connections.
'''
def with_connection(f):
    def with_connection_(*args, **kwargs):
        # or use a pool, or a factory function...
        connection = psycopg2.connect('''
                host={h} dbname={db} user={u} password={pw}
                '''.format(
                        h='localhost',
                        db='ubuntu',
                        u='ubuntu',
                        pw='ubuntu')
                )
        try:
            return_value = f(connection, *args, **kwargs)
        except Exception:
            connection.rollback()
            raise
        else:
            connection.commit() # or maybe not
        finally:
            connection.close()

        return return_value

    return with_connection_

@with_connection
def remove_duplicates(connection,table,columns):
    cursor = connection.cursor()
    start=time.perf_counter()
    # build up combined conditions from multiple columns
    conditions = ''.join(
            [' AND a.{c} = b.{c}'.format(c=col) for col in columns]
            )
    cursor.execute('''
            DELETE FROM {t} a USING {t} b
            WHERE a.ctid < b.ctid
            '''.format(t=table) + conditions + ';'
            )
    print(str(time.perf_counter()-start) + " s to remove duplicates " +
            "from {t}({c})".format(t=table,c=','.join(columns))
            )

@with_connection
def create_index(
        connection,
        table,
        columns,
        unique=False,
        primary=False,
        gin=False,
        gin_type='trigram'
        ):
    cursor = connection.cursor()
    start=time.perf_counter()
    uni=''
    gi=''
    if unique:
        #remove_duplicates(table,columns)
        uni='UNIQUE '
    if gin:
        if (gin_type=='trigram' or gin_type=='trgm'):
            gi=' USING GIN({c} gin_trgm_ops)'.format(c=columns[0])
        elif (gin_type=='vector' or gin_type=='tsvector' or gin_type=='vec'):
            gi=' USING GIN(to_tsvector("simple",{c}))'.format(c=columns[0])
        else:
            print("Ignoring invalid gin_type: " + gin_type)
    cols = ', '.join(columns)
    index= 'index_{t}_{c_o}'.format(
            t=table,c_o='_'.join(columns)
            )

    cursor.execute('''
            CREATE {u}INDEX {i} ON {t}({c}){g};
            '''.format(u=uni,t=table,c=cols,i=index,g=gi)
            )

    print(str(time.perf_counter()-start) + " s to create index on " +
            "{t}({c})".format(t=table,c=','.join(columns))
            )
    return index
    #if unique and primary:
    #    set_primary_key(table,index)

@with_connection
def set_primary_key(connection,table,index):
    cursor = connection.cursor()
    start=time.perf_counter()
    cursor.execute('''
    ALTER TABLE {t} ADD PRIMARY KEY USING INDEX {i};
    '''.format(t=table,i=index)
    )
    print(str(time.perf_counter()-start) + " s to set primary key on " +
            "{i}".format(i=index)
            )


def load_csv(file,table,headers,cursor):
    delimiter = '|'
    heads = ','.join(headers)
    cursor.execute("""
            COPY {t}({h}) FROM '{f}' DELIMITER '{d}' CSV HEADER;
            """.format(f=file,d=delimiter,t=table,h=heads)
            )

def main():
    remove_duplicates('authors',['id'])
    index = create_index('authors',['id'],unique=True,primary=True)
    set_primary_key('authors',index)
    #create_index(cur,'papers',['id'],unique=True,primary=True)
    #create_index(cur,'paper_authors',['author_id'])
    #create_index(cur,'paper_authors',['paper_id'])

    #remove_duplicates(cur,'incits',['id','incit_id'])
    #remove_duplicates(cur,'outcits',['id','outcit_id'])

    #create_index(cur,'incits',['id'])
    #create_index(cur,'outcits',['id'])

    #create_index(cur,'authors',['name'],gin=True)
    #create_index(cur,'papers',['title'],gin=True,gin_type='vector')



    #pw = input('enter database password for david: ')
    # options for tables include:
    # dbname=postgres user=postgres
    # dbname=ubuntu user=postgres
    #conn = psycopg2.connect("host=localhost dbname=david user=david password=david")
    #conn = psycopg2.connect("dbname=postgres user=postgres")
    #host=10.0.0.5
    #TODO: Modify this to connect over network from one EC2 instance to another
    #conn = psycopg2.connect("host=localhost dbname=david user=david password=david")

    #create_tables(cursor)
    #papers_header = 'id,title,year,doi'
    #inCit_header = 'id,inCit_id'
    #outCit_header = 'id,outCit_id'
    #authors_header = 'id,name'
    #paper_authors_header = 'paper_id,author_id'
    #author_papers_header = 'author_id,paper_id'
    #load_csv(papers_csv,'papers',['id','title','year','doi'],cursor)
    #load_csv(inCit_csv,'inCits',['id','inCit_id'],cursor)
    #load_csv(outCit_csv,'outCits',['id','outCit_id'],cursor)
    #load_csv(authors_csv,'temp_authors',['id','name'],cursor)
    #load_csv(paper_authors_csv,'paper_authors',['paper_id','author_id'],cursor)

    # TODO: Create index on authors and paper_authors and remove duplicate rows
    # get list of tables and columns in schema
    #'''select table_schema, table_name, column_name
    #from information_schema.columns
    #where table_schema not in ('pg_catalog','information_schema')
    #order by 1,2,3


if __name__ == "__main__":
    main()
