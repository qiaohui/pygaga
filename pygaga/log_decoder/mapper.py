import sys
import gflags
from glob import glob
import time
from pygaga.helpers import urlutils, utils
from pygaga.log_decoder import decode_click
from pygaga.log_decoder import decode_click_ex
from pygaga.log_decoder import tclog

FLAGS=gflags.FLAGS
YESTERDAY = time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400))
gflags.DEFINE_string('click_prefix', '/space/log/filtered/click/click-', 'Click log file name prefix')
gflags.DEFINE_string('click_postfix', '_?????', 'click log postfix')
gflags.DEFINE_string('stat_day', YESTERDAY, 'click log postfix')
gflags.DEFINE_string('tc_prefix', '/space/tao.cai/jobs/guang_tc/tmp/tc.uctrac.', 'tc apache log prefix')
gflags.DEFINE_string('tc_postfix', '.adweb*', 'tc apache log postfix')

def click_mapper(flist):
    for fn in flist:
        for line in open(fn, "r"):
            try:
                fields       = line.split(" ")
                machine, click_ex_msg, click_msg, score, why = fields[:5]
                score        = int(score)
                click_ex_obj = decode_click_ex(click_ex_msg)
                click_obj    = decode_click(click_msg)
            except Exception:
                traceback.print_exc()
                continue
            media_id = click_obj.display_info.media_id
            if media_id == 10140:
                referer = click_ex_obj.user_info.referer
                arg_idx = referer.find("?")
                ref_arg = referer
                if arg_idx != -1:
                    ref_arg = referer[arg_idx+1:]
                click_hash = urlutils.get_query_arg(ref_arg, "uctrac_clk_1")
                if "" == click_hash:
                    click_hash = urlutils.get_query_arg(ref_arg,"uctrac_clk")
                if "" != click_hash:
                    print("%s\tHOP\t%s" % (click_hash, line)),
            else:
                print("%016x\tCLICK\t%s" % (click_ex_obj.click_hash, line)),

def trac_mapper(flist):
    for fn in flist:
        for line in open(fn, "r"):
            trac = tclog.parse_apache_log(line)
            if trac and trac.click_hash != "":
                print("%s\tTRAC\t%s" % (trac.click_hash, tclog.to_base64(trac)))

def test_click_mapper():
    click_mapper(sys.argv[1:])

def test_trac_mapper():
    trac_mapper(sys.argv[1:])

def main():
    try:
        argv = FLAGS(sys.argv)
    except gflags.FlagsError, e:
        print '%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS)
        return

    stat_day    = FLAGS.stat_day
    prefix      = FLAGS.click_prefix
    postfix     = FLAGS.click_postfix

    tc_prefix   = FLAGS.tc_prefix
    tc_postfix  = FLAGS.tc_postfix

    click_mapper(glob(prefix + stat_day + postfix))
    trac_mapper(glob(tc_prefix + stat_day + tc_postfix))

if __name__ == "__main__":
    main()
