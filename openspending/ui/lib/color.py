import random

from pylons.decorators.cache import beaker_cache

from openspending.mongo import db

DEFAULT_COLOR = "#607890"

@beaker_cache(type='dbm')
def parent_color(obj):
    if 'color' in obj:
        return obj.get('color')
    if 'parent' in obj and obj.get('parent'):
        try:
            parent = db.dereference(obj.get('parent'))
            return parent_color(parent)
        except:
            pass
    return DEFAULT_COLOR

# color range generator:
def hex_to_tuple(val, alpha=False):
    if isinstance(val,basestring):
        val = val[1:]
        if len(val) == 8:
            alpha = True
        try:
            val = int(val,16)
        except Exception:
            val = int(DEFAULT_COLOR[1:], 16)
    if alpha:
        t = ((val>>24)&0xFF,((val>>16)&0xFF),((val>>8)&0xFF),(val&0xFF))
    else:
        t = (((val>>16)&0xFF),((val>>8)&0xFF),(val&0xFF))
    return [int(n) for n in t[:3]]

def tuple_to_hex(tup):
    return "#" + "%02x%02x%02x" % (int(tup[0]), int(tup[1]), int(tup[2]))

def _color_range(color, slices, var=70.0):
    slice_value = lambda n: ((var*2)/slices)*n
    color_part = lambda c, n: max(0, min(255, (c-var)+slice_value(n)))
    cv = hex_to_tuple(color)
    for n in range(slices):
        yield tuple_to_hex((color_part(cv[0], n),
                            color_part(cv[1], n),
                            color_part(cv[2], n)))

@beaker_cache(type='dbm')
def color_range(color, slices, var=70.0):
    colors = list(_color_range(color, slices, var=70.0))
    random.shuffle(colors)
    return colors
