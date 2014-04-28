
import re
import time
import datetime
from gflags import DEFINE_flag
from gflags import Flag
from gflags import FLAGS
from gflags import ArgumentParser
from pygaga.helpers.magicdate import magicdate

class DateParser(ArgumentParser):
  """Parser of date values."""

  def Convert(self, argument):
    """Converts the argument to a date; raise ValueError on errors."""
    if type(argument) == datetime.datetime:
      return argument
    elif type(argument) == str or type(argument) == unicode:
      argstr = "".join([x for x in argument if x.isdigit()])
      try:
        tmp_date = datetime.datetime.fromtimestamp(int(argstr))
        if tmp_date.year > 1990 and tmp_date.year < 2050:
          return tmp_date
      except:
        pass
      return magicdate(argument)

    raise ValueError('Non-date to date flag', argument)

  def Parse(self, argument):
    val = self.Convert(argument)
    return val

  def Type(self):
    return 'date'

class DateFlag(Flag):
  """Basic date flag.
  """

  def __init__(self, name, default, help, short_name=None, **args):
    p = DateParser()
    Flag.__init__(self, p, None, name, default, help, short_name, 0, **args)
    if not self.help: self.help = "a date value"

def DEFINE_date(name, default, help, flag_values=FLAGS, **args):
  """Registers a date flag.

  This flag will have a value of Date.  None is possible
  if default=None and the user does not specify the flag on the command
  line.
  """
  DEFINE_flag(DateFlag(name, default, help, **args), flag_values)

