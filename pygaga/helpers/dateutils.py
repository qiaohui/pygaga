import gflags
import time, datetime
from pygaga.helpers import gflags_ext

FLAGS = gflags.FLAGS

def yesterday():
    return datetime.datetime.now() - datetime.timedelta(1)

def tomorrow():
    return datetime.datetime.now() - datetime.timedelta(1)

gflags_ext.DEFINE_date('start', yesterday(), "start from date, 20120109 or timestamp")
gflags_ext.DEFINE_date('end', datetime.datetime.now(), "end date")
gflags_ext.DEFINE_date('date', datetime.datetime.now(), "date")

def ts2date(ts):
    return datetime.datetime.fromtimestamp(ts)

def date2ts(date):
    return time.mktime(date.timetuple())

def datestr(date):
    return time.strftime('%Y-%m-%d', date.timetuple())

def dateplus(date, plus):
    ts = time.localtime(time.mktime(time.strptime(date, '%Y-%m-%d')) + plus * 86400)
    return time.strftime('%Y-%m-%d', ts)

def eachday(start, end):
    td = end - start
    for d in range(td.days):
        yield start + datetime.timedelta(d)

####### deprecated #################
def date2epoch(ts):
    return time.mktime(time.strptime(ts, '%Y-%m-%d'))

def epoch2date(ts):
    return time.strftime('%Y-%m-%d', datetime.datetime.fromtimestamp(ts).timetuple())

def weekday(date):
    return time.strptime(date, '%Y-%m-%d')[6]

def datediff(a, b):
    """
    >>> datediff('2010-01-01', '2009-12-30')
    2
    >>> datediff('2010-01-01', '2009-12-01')
    31
    """
    return int((date2epoch(a) - date2epoch(b)) / 86400)

def dates(start, end=1):
    """
    >>> dates('2009-12-28', '2010-1-04')
    ['2009-12-28', '2009-12-29', '2009-12-30', '2009-12-31', '2010-01-01', '2010-01-02', '2010-01-03', '2010-01-04']
    >>> dates(0,1) == [time.strftime("%Y-%m-%d",datetime.datetime.now().timetuple())]
    True
    """
    if isinstance(start,unicode):
        start = str(start)
    if isinstance(end,unicode):
        end = str(end)
    if isinstance(start,str):
        start = int(datediff(start,dates(0)[0]))
    if isinstance(end,str):
        end = int(datediff(end,dates(0)[0])+1)
    return [time.strftime('%Y-%m-%d',
                          time.localtime(time.time() + x * 86400))
            for x in range(start, end)]

if __name__ == "__main__":
    import doctest
    doctest.testmod()
