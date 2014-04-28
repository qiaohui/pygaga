import gflags
import logging
import os
import re
import sys
import time

from pygaga.helpers.color_log_format import ColorFormatter
from pygaga.helpers.paperboy_logger import PaperboyHandler
from pygaga.helpers.paperboy_logger import Logger as PaperboyLogger

FLAGS = gflags.FLAGS

#gflags.DEFINE_string('flagfile', '', "Load flags from file name.")

gflags.DEFINE_string('logfile', '', "Log file name.")
gflags.DEFINE_enum('verbose', 'info',
                   ['debug', 'trace', 'info', 'warning', 'error', 'critical'],
                   'Output debug level logs.')
gflags.DEFINE_boolean('stderr', False, 'Output debug level log to stderr')
gflags.DEFINE_boolean('color', False, 'Output colored log to stderr')
gflags.DEFINE_boolean('debug', False, 'Use pdb debug')
gflags.DEFINE_boolean('use_logfile', False, 'Use log file?')

gflags.DEFINE_boolean('use_paperboy', False, 'Use paper boy logger?')
gflags.DEFINE_string('pbhost', 'bi1', "Paper boy server host.")
gflags.DEFINE_integer('pbport', 1415, "Paper boy server port.")
gflags.DEFINE_string('pbcate', 'guangcrawler', "Paper boy category.")
gflags.DEFINE_enum('pbverbose', 'info',
                   ['debug', 'info', 'warning', 'error', 'critical'],
                   'Output debug level logs.')

LOG_LEVELS = {'debug': logging.DEBUG,
              'trace' : logging.DEBUG+5,
              'info': logging.INFO,
              'warning': logging.WARNING,
              'error': logging.ERROR,
              'critical': logging.CRITICAL}

def get_paperboy_logger():
    return PaperboyLogger(FLAGS.pbhost, FLAGS.pbport, FLAGS.pbcate)

def config_logger(loggers):
    date_format = '%m%d %H:%M:%S'
    format = "%(levelname)1.1s%(asctime)s %(process)d [%(filename)s:%(lineno)d] %(message)s"
    formatter = logging.Formatter(format, datefmt = date_format)
    colorformat = "$COLOR%(levelname)1.1s%(asctime)s %(process)d [%(filename)s:%(lineno)d] %(message)s$RESET"
    colorformatter = ColorFormatter(colorformat, datefmt = date_format)

    # Always log to file
    timestr = time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time()))
    if FLAGS.logfile:
        logfile = os.path.join('timedlog', FLAGS.logfile)
    else:
        logfile = os.path.join('timedlog',
                               '.'.join([os.path.basename(sys.argv[0]),
                                         'log', timestr, str(os.getpid())]))
    try:
        os.mkdir(os.path.dirname(logfile))
    except:
        pass

    default_level = logging.WARNING
    if FLAGS.verbose:
        default_level = LOG_LEVELS[FLAGS.verbose]

    for logger in loggers:
        logger.setLevel(default_level)

    if FLAGS.use_logfile:
        filehandler = logging.FileHandler(logfile, "w")
        filehandler.setLevel(default_level)
        filehandler.setFormatter(formatter)
        for logger in loggers:
            logger.addHandler(filehandler)

    sym_logfile = os.path.join('timedlog','.'.join([os.path.basename(sys.argv[0]), 'log']))
    try:
        os.remove(sym_logfile)
    except:
        pass

    try:
        os.symlink(os.path.abspath(logfile), sym_logfile)
    except:
        pass

    # Log to stderr, default level WARNING
    console = logging.StreamHandler()
    console_level = logging.WARNING
    if FLAGS.stderr:
        console_level = default_level
    console.setLevel(console_level)
    if FLAGS.color:
        console.setFormatter(colorformatter)
    else:
        console.setFormatter(formatter)
    for logger in loggers:
        logger.addHandler(console)

    if FLAGS.use_paperboy:
        paperboy_client = PaperboyHandler(FLAGS.pbhost, FLAGS.pbport, FLAGS.pbcate)
        paperboy_client.setLevel(LOG_LEVELS[FLAGS.pbverbose])
        for logger in loggers:
            logger.addHandler(paperboy_client)

class LoggerClass(logging.Logger):
    exclude_pattern = re.compile("DefaultNameShouldNotMatch")

    def __init__(self, name):
        logging.Logger.__init__(self, name)
        if not LoggerClass.exclude_pattern.match(name):
            config_logger([self,])

def log_init(prev_logger_name=['',], exclude_logger_name_pattern=""):
    try:
        argv = FLAGS(sys.argv)[1:]  # parse flags
    except gflags.FlagsError, e:
        print '%s\\nUsage: %s ARGS\\n%s' % (e, sys.argv[0], FLAGS)
        sys.exit(1)

    #if FLAGS.flagfile:
    #    FLAGS("exe_holder %s" % open(FLAGS.flagfile, "r").read())

    if exclude_logger_name_pattern:
        LoggerClass.exclude_pattern = re.compile(exclude_logger_name_pattern)
    logging.setLoggerClass(LoggerClass)

    loggers = []
    if type(prev_logger_name) in (tuple, list):
        for name in prev_logger_name:
            loggers.append(logging.getLogger(name))
    else:
        loggers.append(logging.getLogger(prev_logger_name))
    config_logger(loggers)

    if FLAGS.debug:
        #FLAGS.lock = False
        import pdb
        pdb.set_trace()

    return argv

if __name__ == "__main__":
    log_init("main")
    logger = logging.getLogger("main")
    logger.info("info")
    logger.debug("debug")
    logger.error("error")
    logger.warn("warn")

