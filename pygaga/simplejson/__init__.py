from .jsobject_decoder import JsJSONDecoder
from simplejson import loads as json_loads

def loads(s, encoding=None, object_hook=None, parse_float=None,
        parse_int=None, parse_constant=None, object_pairs_hook=None,
        use_decimal=False, **kw):
    return json_loads(s, encoding=encoding, cls=JsJSONDecoder,
        object_hook=object_hook, parse_float=parse_float, parse_int=parse_int, parse_constant=parse_constant,
        object_pairs_hook=object_pairs_hook, use_decimal=use_decimal, **kw)

def load(fp, encoding=None, object_hook=None, parse_float=None,
        parse_int=None, parse_constant=None, object_pairs_hook=None,
        use_decimal=False, namedtuple_as_object=True, tuple_as_array=True,
        **kw):
    return loads(fp.read(), encoding=encoding,
        object_hook=object_hook, parse_float=parse_float, parse_int=parse_int, parse_constant=parse_constant,
        object_pairs_hook=object_pairs_hook, use_decimal=use_decimal, **kw)
