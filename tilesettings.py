from __future__ import division

from bound import Bound
from name import XYZNamingScheme

from math import ceil, floor, log
import math, os

# Be sure to add a key point to your class to this hash after writing
# it.
# TODO: consider getting rid of this in favor of an abstract base
# class that is used to look up inheritors.
registered = {}

def supported(name):
    global registered
    return registered.get(name) is not None

def retrieve(name):
    global registered
    return registered[name]

class XYZTileSettings:
    """
    Generate settings for cutting XYZ tiles from the given bounds.
    """
    def __init__(self, dpi, meta_size, file_type, spherical_mercator, verbose=False):
        self.dpi = dpi
        self.meta_size = meta_size
        self.file_type = file_type
        self.spherical_mercator = spherical_mercator
        self.namer = XYZNamingScheme(file_type)
        self.verbose = verbose

        if self.spherical_mercator:
            self.max_bounds = Bound.spherical_mercator_max_extent()
            pass
        else:
            self.max_bounds = Bound.geographic_max_extent()

    def settings_for(self, domain, scale, overwrite, base_dir):
        """
        Generate all of the settings that the tile renderer and tile
        cutter will need to correctly produce xyz tiles from the
        given domain.
        """
        loc = os.path.join(base_dir, "meta_panels", "foo")
        if not os.path.exists(os.path.dirname(loc)):
            try:
                os.makedirs(os.path.dirname(loc))
            except OSError:
                pass

        self.namer.basedir = base_dir
        return self.meta_tiles(domain, scale, base_dir)

    def calc_bounds(self, domain, scale):
        """
        Calculate the set of xyz tiles to render for the domain,
        expressed as boundary objects in terms of xyz tile numbers.
        """
        denom = self.scale_denominator(scale)
        tiles = Bound(north = self.lat_to_xyz(domain.north, denom),
                      south = self.lat_to_xyz(domain.south, denom),
                      east  = self.lon_to_xyz(domain.east, denom),
                      west  = self.lon_to_xyz(domain.west, denom))

        return tiles
                
    def estimate_tiles(self, domain, scale):
        """
        Estimate the number of tiles that will be generated to satisfy
        the given domain/scale. This does not account for tiles that
        are not rendered due to the overwrite flag.
        """
        tiles = self.calc_bounds(domain, scale)
        return tiles.lon_span() * tiles.lat_span()
        return int(len(lonrange) * len(latrange))
                
    def lat_to_xyz(self, lat, scale_denom):
        """
        From the given latitude, compute the y-index of the
        corresponding xyz tile at scale_denom.
        """
        return int(floor((abs(lat - self.max_bounds.north)) / scale_denom))

    def lon_to_xyz(self, lon, scale_denom):
        """
        From the given longitude, compute the x-index of the
        corresponding xyz tile at scale_denom.
        """
        return int(floor((abs(lon + self.max_bounds.east)) / scale_denom))

    def scale_denominator(self, scale):
        """
        Computer the number of degrees/meters per-tile at the given scale.
        """
        if self.spherical_mercator:
            return self.max_bounds.lat_span() / (2.0 ** (scale - 1))
        else:
            return self.max_bounds.lat_span() / (2.0 ** scale)

    def appropriate_meta_width(self, extent):
        """
        For the area being rendered, decide on an appropriate
        meta-tile size. Result is the tile-width of a meta-tile
        square.
        """
        lat_range = extent.north - extent.south
        lon_range = extent.east - extent.west

        if lat_range <= 1 or lon_range <= 1:
            return 1
        
        smaller_range = min(lat_range, lon_range)

        # logarithm of the smaller range's tile count gives us an
        # extra two tiles to the meta square for each power of ten in
        # total tile count.
        width = 2 * floor(log(smaller_range) / log(10))

        if width > smaller_range:
            return smaller_range

        # Don't let the meta tile get *too* huge
        return min(width, 20)

    def meta_tiles(self, domain, scale, base_dir):
        """
        Create a generator for a list of (meta_extent, meta_pixels,
        meta_filename, [(tile_offset, tile_name)]) tuples. That can be
        used to generate tiles at 'scale' from 'domain'.

        meta_extent - the real-world unit extent to render into the metatile
        meta_pixels - the pixel width/height of the metatile (they're always square)
        meta_filename - the file name to store the metatile in
        tile_offset - the pixel offset of this tile within the meta tile
        tile_name - the file name to store this tile in
        """
        tiles = self.calc_bounds(domain, scale)

        meta_width = self.appropriate_meta_width(tiles)

        meta_bounds = tiles.tiles_for(meta_width)

        north_max = self.max_bounds.north
        west_max  = self.max_bounds.west

        scale_denom = self.scale_denominator(scale)

        for boundaries in meta_bounds:
            bw, bn, be, bs = boundaries
            meta_filename = "%s-%s-%s.%s" % (scale, bw, bn, self.file_type)
            meta_loc = os.path.join(base_dir, "meta_panels", meta_filename)

            extent = Bound(north = north_max - float(bn * scale_denom),
                           south = north_max - float(bs * scale_denom),
                           east  = west_max  + float(be * scale_denom),
                           west  = west_max  + float(bw * scale_denom))

            scale_filename = scale
            if self.spherical_mercator:
                scale_filename = scale - 1
            yield (extent, meta_width * 256, meta_loc, self.inner_tiles(boundaries, scale_filename))
        
    def inner_tiles(self, meta_bounds, scale):
        mw, mn, me, ms = meta_bounds
        meta = Bound(north = mn * 256,
                     south = ms * 256,
                     east  = me * 256,
                     west  = mw * 256)

        for bound in meta.tiles_for(256):
            loc = Bound.from_tuple(bound).sub(meta).int().tuple()

            yield (loc, self.namer.name_for(scale, int(bound[1]/256), int(bound[0]/256)))


# register for plugin use
registered['xyz'] = XYZTileSettings
