import sys
import traceback
from log_decoder import decode_click
from log_decoder import decode_click_ex
import tclog

def do_reduce(key, clicks, tracs, hops):
    if len(clicks) == 0:
        return
    if len(clicks) > 1:
        print >>sys.stderr, "WARNING! click_hash should never collide!"
    click = clicks[-1]
    click_obj, click_ex_obj, score, why = click
    media_id = click_obj.display_info.media_id
    print("%d\t%d\t%d" % (media_id, len(tracs), len(hops)))

def get_click(arg_list):
    line = arg_list[0]
    try:
        fields       = line.split(" ")
        machine, click_ex_msg, click_msg, score, why = fields[:5]
        score        = int(score)
        click_ex_obj = decode_click_ex(click_ex_msg)
        click_obj    = decode_click(click_msg)
    except Exception:
        traceback.print_exc()
        return
    return (click_obj, click_ex_obj, score, why)

def get_trac(arg_list):
    line = arg_list[0]
    try:
        return tclog.from_base64(line)
    except Exception:
        traceback.print_exc()
        return

def work(reducer, input=sys.stdin):
    key, clicks, tracs, hops = "", [], [], []
    for line in input:
        row = line[:-1].split("\t")
        if len(row) < 3:
            print >>sys.stderr, "reducer input less than 3 fields.", line
        if key != row[0]:
            if key != "":
                reducer.do(key, clicks, tracs, hops)
            key = row[0]
            clicks = []
            tracs  = []
            hops   = []
        
        if row[1] == "CLICK":
            click = get_click(row[2:])
            if click != None : clicks.append(click)
        elif row[1] == "TRAC":
            trac = get_trac(row[2:])
            if trac != None : tracs.append(trac)
        elif row[1] == "HOP":
            hop = get_click(row[2:])
            if hop != None : hops.append(hop)
        else:
            print >>sys.stderr, "unkown type", row[1]
            
    if key != "":
        reducer.do(key, clicks, tracs, hops)

class TestReducer:
    def __init__(self):
        pass

    def do(self, key, clicks, tracs, hops):
        do_reduce(key, clicks, tracs, hops)


class ReducerList:
    def __init__(self):
        self.reducers = []

    def add_reducer(self, reducer):
        self.reducers.append(reducer)
        return self

    def do(self, key, clicks, tracs, hops):
        for reducer in self.reducers:
            reducer.do(key, clicks, tracs, hops)

    def output(self):
        for reducer in self.reducers:
            reducer.output()

def main():
    work(ReducerList().add_reducer(TestReducer()))

if __name__ == "__main__":
    main()

