
from mapnik import load_map, Coord, Envelope, Image, Map, render
import os

# Be sure to add a key point to your class to this hash after writing
# it. Thanks Python for lacking anything resembling forward
# declarations and making this so hacky...
registered = {}

def supported(name):
    global registered
    return registered.get(name) is not None

def retrieve(name):
    global registered
    return registered[name]

def render_panels(mapnik_file, image_size, output_list):
    """
    Render multiple panel images from the same map. Each one needs to be 'image_size' in pixel width/height.
    """
    r = Renderer(mapnik_file, image_size)
    for (bound, filename) in output_list:
        r.render(bound, filename)

class MapnikRenderer:
    """
    An optionally-caching tile renderer.
    """
    def __init__(self, mapnik_file, image_width, image_height = None, cache=True):
        self.mapnik_file = mapnik_file
        self.image_width = image_width
        if image_height is not None:
            self.image_height = image_height
        else:
            self.image_height = image_width
        self.cache = cache
        self._map = None
        self._image = None

    def cached_map(self):
        """
        If caching is enabled, ensure that only one map object is
        generated, otherwise generate a fresh one.
        """
        if self._map is not None:
            return self._map
        m = Map(self.image_width, self.image_height)
        load_map(m, self.mapnik_file)
        if self.cache:
            self._map = m
        return m

    def cached_image(self):
        """
        If caching is enabled, ensure that only one image object is
        generated, otherwise generate a fresh one.
        """
        if self._image is not None:
            return self._image
        i = Image(self.image_width, self.image_height)
        if self.cache:
            self._image = i
        return i

    def new_image_size(self, width, height=None):
        if height is None:
            height = width
        if self.image_width == width and self.image_height == height and self._image is not None:
            return self._image
        else:
            self.image_width  = width
            self.image_height = height
            self._image = None
            return self.cached_image()
        
        
    def render(self, bounds, filename):
        """
        Render the given bounds out to an image at 'filename'.
        """
        map = self.cached_map()
        image = self.cached_image()
        map.zoom_to_box(to_envelope(bounds))
        render(map, image)
        image.save(filename)
        return map.envelope()

# register to make available
registered['mapnik'] = MapnikRenderer


def to_envelope(bounds):
    """
    Translate a bounds object into an equivalent mapnik.Envelope.
    """
    return Envelope(Coord(bounds.west, bounds.north), Coord(bounds.east, bounds.south))


