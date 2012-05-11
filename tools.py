
try:
    import json
except:
    import simplejson as json
import os
from itertools import islice, chain

def world_poly_with_hole(bounds, world_bounds):
    """
    Generate a polygon for geojson that is set up appropriately to
    cover the world with a hole at the given (w,n,e,s) bounds.
    """
    west, north, east, south = bounds
    wwest, wnorth, weast, wsouth = world_bounds
    return { 'type' : 'Polygon',
             'coordinates' : [
                [ [wwest, wsouth], [weast, wsouth], [weast, wnorth], [wwest, wnorth], [wwest, wsouth] ],
                [ [west, south], [east, south], [east, north], [west, north], [west, south] ]
            ]
             }

def geojson_highlight(bounds, world_bounds):
    """
    Generate appropriate geojson to highlight the given area on a map.
    """
    return { 'type' : 'FeatureCollection',
             'features' : [
            {
                'type': 'Feature',
                'geometry': world_poly_with_hole(bounds)
                }
            ]
             }

def write_geojson_highlight(filename, bounds, world_bounds):
    """
    Generate a geojson highlight at the given location.
    """
    fp = open(filename, 'w')
    js = geojson_highlight(bounds, world_bounds)
    json.dump(js, fp)
    fp.close()

def tile_exists(tile):
    """
    Check if a file already exist for the given tile
    """
    (bound, name) = tile
    return os.path.exists(name)

def all_tiles_exist(tiles):
    """
    Check if files exist to back up all of the given tiles.
    """
    for t in tiles:
        if not tile_exists(t):
            return False
    return True

def filter_existing_tiles(tiles):
    """
    Generate a list of the tiles that have not been created
    """
    l = []
    for t in tiles:
        if not tile_exists(t):
            l.append(t)
    return l

def tilefun_to_meta(f):
    """
    'hoist' the function on tiles into a function on metabounds
    """
    def fn(mbound):
        (bound, size, loc, tiles) = mbound
        return f(tiles)
    return fn
    
def mbound_filter_existing_tiles(mbound):
    """
    Filter the existing tiles from 'mbound', then return a new version
    that only lists nonexistant tiles. Returns None if this results in
    the tile list being empty.
    """
    (b, iw, n, tiles) = mbound
    newt = filter_existing_tiles(tiles)
    if newt is not None:
        return (b, iw, n, newt)
    else:
        return None
        
    
def apply_filter(f, ms):
    """
    Apply the given filter to the list of metabounds. Return any
    processed items that are not None.
    """
    for m in ms:
        res = f(m)
        if res is not None:
            yield res

def groups(l, size):
    """
    Produce a generator that yields lists, each size 'size', from the
    given generator 'l'. If len(l) is not an even multiple of 'size',
    the last list contains anything remaining.

    e.g.
    l = xrange(19)
    for batchiter in batch(l, 3):
        print "Batch: %s" % item
        Batch:  [0, 1, 2]
        Batch:  [3, 4, 5]
        Batch:  [6, 7, 8]
        Batch:  [9, 10, 11]
        Batch:  [12, 13, 14]
        Batch:  [15, 16, 17]
        Batch:  [18]

    """
    i = iter(l)
    while True:
        group = islice(i, size)
        yield chain([group.next()], group)

def metatile_batches(metatiles, size):
    """
    Group the list of metatiles into 'size' batches. Anything designed
    to consume a metatile list will work appropriately on the batches.
    """
    return groups(metatiles, size)

def pool_metatile_batch(pool, fn, metatiles, size):
    """
    Use the pool 'pool' (a multiprocessing.Pool) to execute 'fn' on
    'metatiles' batched into 'size' batches.
    """
    pool.map(fn,metatile_batches(metatiles, size))
