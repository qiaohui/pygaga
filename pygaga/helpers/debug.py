
def debug(f, *args, **kwargs):
    from pdb import Pdb as OldPdb
    try:
        from IPython.core.debugger import Pdb
        kw = dict(color_scheme='Linux')
    except ImportError:
        Pdb = OldPdb
        kw = {}
    pdb = Pdb(**kw)
    return pdb.runcall(f, *args, **kwargs)

def set_trace():
    try:
        __import__('IPython').core.debugger.Pdb(color_scheme='Linux').set_trace()
    except:
        try:
            __import__('IPython').Debugger.Pdb(color_scheme='Linux').set_trace()
        except:
            import pdb; pdb.set_trace()

