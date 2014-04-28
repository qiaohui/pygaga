import gflags
from pygaga.helpers.dbutils import get_db_engine
from pygaga.helpers.logger import log_init

FLAGS = gflags.FLAGS

if __name__ == "__main__":
    #log_init("CrawlLogger", "sqlalchemy.*")
    log_init("CrawlLogger", "sqlalchemy.*")
    db = get_db_engine()
    result = db.execute("select count(id) from item")
    print result.rowcount, list(result)

