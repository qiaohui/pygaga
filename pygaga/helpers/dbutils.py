import gflags
import MySQLdb
from sqlalchemy import create_engine

FLAGS = gflags.FLAGS

gflags.DEFINE_boolean('echosql', False, "is echo sql?")

gflags.DEFINE_string('dbuser', "guang", "mysql user")
gflags.DEFINE_string('dbpasswd', "guang", "mysql passwd")
gflags.DEFINE_string('db', "guang", "mysql database")
gflags.DEFINE_string('dbhost', "127.0.0.1", "mysql host")
gflags.DEFINE_integer('dbport', 3306, "mysql port")

gflags.DEFINE_integer('dbtimeout', 3600*4, "db timeout")

gflags.DEFINE_list('dbconnstrs', ["guang:guang@127.0.0.1:3306/gunag?charset=utf8",], "database connstrs")

def get_db_engines(**kwargs):
    dbconnstrs = kwargs.get('dbconnstrs') if kwargs.has_key('dbconnstrs') else FLAGS.dbconnstrs
    dbtimeout = kwargs.get('dbtimeout') if kwargs.has_key('dbtimeout') else FLAGS.dbtimeout
    echosql = kwargs.get('echosql') if kwargs.has_key('echosql') else FLAGS.echosql
    dbs = []
    for dbconnstr in dbconnstrs:
        conn = create_engine('mysql://%s' % dbconnstr, echo=echosql, pool_recycle=dbtimeout)
        dbs.append(conn)
    return dbs

def get_db_engine(**kwargs):
    echosql = kwargs.get('echosql') if kwargs.has_key('echosql') else FLAGS.echosql
    connstr = kwargs.get('connstr')
    if connstr:
        return create_engine(connstr, echo=echosql)
    dbuser = kwargs.get('dbuser') if kwargs.has_key('dbuser') else FLAGS.dbuser
    dbpasswd = kwargs.get('dbpasswd') if kwargs.has_key('dbpasswd') else FLAGS.dbpasswd
    dbhost = kwargs.get('dbhost') if kwargs.has_key('dbhost') else FLAGS.dbhost
    dbport = kwargs.get('dbport') if kwargs.has_key('dbport') else FLAGS.dbport
    dbtimeout = kwargs.get('dbtimeout') if kwargs.has_key('dbtimeout') else FLAGS.dbtimeout
    db = kwargs.get('db') if kwargs.has_key('db') else FLAGS.db
    return create_engine('mysql://%s:%s@%s:%s/%s?charset=utf8' % (dbuser, dbpasswd, dbhost, dbport, db),
        echo=echosql, pool_recycle=dbtimeout)

def get_rawdb_conn(**kwargs):
    echosql = kwargs.get('echosql') if kwargs.has_key('echosql') else FLAGS.echosql
    dbuser = kwargs.get('dbuser') if kwargs.has_key('dbuser') else FLAGS.dbuser
    dbpasswd = kwargs.get('dbpasswd') if kwargs.has_key('dbpasswd') else FLAGS.dbpasswd
    dbhost = kwargs.get('dbhost') if kwargs.has_key('dbhost') else FLAGS.dbhost
    dbport = kwargs.get('dbport') if kwargs.has_key('dbport') else FLAGS.dbport
    #dbtimeout = kwargs.get('dbtimeout') if kwargs.has_key('dbtimeout') else FLAGS.dbtimeout
    db = kwargs.get('db') if kwargs.has_key('db') else FLAGS.db
    return MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpasswd, port=dbport, db=db, charset='utf8')
