import logging
from pygaga.helpers.logger import log_init
from pygaga.helpers.dateutils import tomorrow

import gflags

FLAGS = gflags.FLAGS

logger = logging.getLogger('TestLogger')

if __name__ == "__main__":
    log_init("TestLogger", "sqlalchemy.*")
    print "%s %s %s" % (FLAGS.start, FLAGS.end, FLAGS.date)
    logger.debug("debug")
    logger.warn("warn")
    logger.info("info")
    logger.error("error")
