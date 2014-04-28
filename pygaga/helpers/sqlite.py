from sqlite3 import dbapi2 as sqlite
import re

RE_SQL_CREATE = re.compile('^create\s+table\s+\w+\s*\(([^\)]+)\)$', re.I)

# 'CREATE TABLE data (a,b,c,d)'
def sqlite_schema(conn, table_name):
    sql = 'select sql from sqlite_master where type="table" and tbl_name="%s"' % table_name
    rs = conn.execute(sql).fetchall()
    return RE_SQL_CREATE.findall(rs[0][0])[0].split(',')

def sql_conn(file):
    conn = sqlite.connect(file)
    conn.text_factory = str
    conn.execute('pragma cache_size=100000')
    conn.execute('pragma synchronous=OFF')
    return conn

def sql_columns(conn, tablename):
    return [x.lower() for x in sqlite_schema(conn, tablename)]

def init_sqlite_table(cur, cols, uniqkey, idxlst, tablename = "data"):
    """init table, index, unique key
    Arguments:
    - cur:
    - cols: "f1,f2,f3,f4"  or ["f1", "f2", "f3", "f4"]
    - uniqkey: "f1,f2,f3,f4"  or ["f1", "f2", "f3", "f4"]
    - idxlst: "f1.f2,f3.f4" or ["f1.f2", "f3.f4"]
    """
    if isinstance(cols, str):
        cols = cols.split(",")
    try:
        cur.execute('create table %s (%s)'%(tablename, ','.join(cols)))
    except Exception,e:
        if e.message != 'table %s already exists' % tablename:
            print e.message
            raise e

    if uniqkey:
        if isinstance(uniqkey, str):
            uniqkey = uniqkey.split(",")
        cur.execute('drop index if exists %s.idx ' % (tablename))
        uniq_sql = ('create unique index if not exists '
                    'uniq_idx on %s (%s)'
                    ) % (tablename, ','.join(uniqkey))

        cur.execute(uniq_sql)

    if isinstance(idxlst, str):
        idxlst = [i for i in idxlst.split(",") if i.strip()]
    for idx in idxlst:
        sql = 'create index if not exists idx_%s on %s (%s)' % (idx.replace('.' , '_'),
                                                                tablename,
                                                                ','.join(idx.split('.'))
                                                                )
        cur.execute(sql)

def to_sql_str(v):
    if type(v) == bool:
        return '1' if v else '0'
    elif type(v) == int or type(v) == long or type(v) == float:
        return str(v)
    elif type(v) == str:
        return "'%s'" % v
    elif type(v) == unicode:
        return "'%s'" % v.encode('utf-8')
    else:
        return "'%s'" % str(v)

def generate_insert_sql(cols, data, table_name='data'):
    """
    >>> generate_insert_sql(["a","b","c"], {'a':123,'c':False,'b':'sk'})
    insert into data (a,b,c) values (123,'v',0)
    """
    sql = ""
    fields = []
    values = []
    for c in cols:
        if data.has_key(c):
            fields.append(c)
            values.append(to_sql_str(data[c]))
    return "insert into %s (%s) values (%s)" % (table_name, ",".join(fields), ",".join(values))

def select(cur, sql, params = []):
    if params:
        sql = sql.replace('%s', '?')
    cur.execute(sql, params)
    for d in cur:
        yield d
