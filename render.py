#!/usr/bin/env python

import tilesettings, tilerenderer, tools, bound

from processors import Renderer

from optparse import OptionParser, OptionGroup

usage = "usage: %prog [options] <style_file.xml>"
parser = OptionParser(usage=usage)

# pipeline selection options
parser.add_option("-T", "--tile-type", dest="tile_type", default="xyz", type="string",
                  help="Type of tiles to generate. options: [xyz], default: xyz")
parser.add_option("-R", "--tile-renderer", dest="tile_renderer", default="mapnik", type="string",
                  help="Renderer to use in producing tiles. options [mapnik], default: mapnik")

# kamap specific options
parser.add_option("-m", "--meta-size", dest="meta_size", default=20, type="int",
                  help="The width of one dimension in a meta-tile. Arg N generates an NxN metatile")

# console output options
parser.add_option("-v", "--verbose", dest="verbose", default=False, action="store_true",
                  help="more detailed output")


# map extent options
map_group = OptionGroup(parser, "Geographic Options")
map_group.add_option("-n", "--north", dest="north", default=None, type="float",
                     help="Northern map extent default: [projection max]")
map_group.add_option("-e", "--east", dest="east", default=None, type="float",
                     help="Eastern map extent default: [projection max]")
map_group.add_option("-s", "--south", dest="south", default=None, type="float",
                     help="Southern map extent default: [projection max]")
map_group.add_option("-w", "--west", dest="west", default=None, type="float",
                     help="Western map extent default: [projection max]")

map_group.add_option("-p", "--projection", dest="projection", default="geo", type="string",
                     help="The projection to be used. Note: source data files must match this projection at this time. options [geo, sm], default: geo")

# zoom level options
map_group.add_option("-c", "--scale", dest="scale", default=0, type="int",
                     help="The scale of the furthest zoomed out zoom level")
map_group.add_option("-l", "--first-scale", dest="first_scale", default=1, type="int",
                     help="The first scale to start rendering at, default: the input to '-c'")
map_group.add_option("-z", "--zoom-levels", dest="zoom_levels", default=5, type="int",
                     help="The number of zoom levels to render default: 5")


parser.add_option_group(map_group)


watermark_group = OptionGroup(parser, "Watermarking")
# watermarking options
watermark_group.add_option("--watermark", dest="watermark", default=False, action="store_true",
                           help="Enable watermarking")
watermark_group.add_option("--watermark_file", dest="watermark_file", default="./watermark.png", type="string",
                           help="The file to use for watermarking. Default is ./watermark.png")

parser.add_option_group(watermark_group)

# file handling options
file_group = OptionGroup(parser, "File Settings")
file_group.add_option("-k", "--keep-existing", dest="overwrite", default=True, action="store_false",
                      help="Keep files that already exist? default: not kept")
file_group.add_option("-f", "--output-format", dest="output_format", default='png', type="string",
                      help="The output file format. Only 'png' and 'jpeg' are allowed default: png")
file_group.add_option("-b", "--base-directory", dest="base_dir", default='./tiles/', type="string",
                      help="The base directory in which to store tiles default: ./tiles/")
file_group.add_option('-g', '--log-file', dest='log_file', default='./render.log', type='string',
                      help="The file to append long information to, default: 'render.log' in the current directory")
file_group.add_option('-i', '--pixel-bits', dest="pixel_bits", default=8, type='int',
                      help="The bits per pixel to use for .png renderings, allowed are '8', '24', and '32'. default: 8")
file_group.add_option("-d", "--do-not-delete-metapanels", dest="preserve_metapanels", default=False, action="store_true",
                      help="Preserve meta panels after finished cutting tiles from them (default: no)")
file_group.add_option("-W", "--website-mode", dest="website_mode", default=False, action="store_true",
                      help="Produce special output designed for control by/interaction wtih a website. default: no")
file_group.add_option('-H', '--add-highlight', dest='highlight', default=None, type='string',
                      help="Generate a json highlight layer for the bounds. Argument is the file location to store the json. Default: do not generate")
parser.add_option_group(file_group)

# s3 upload options
s3_group = OptionGroup(parser, "S3 Upload")
s3_group.add_option("--s3-file", dest="s3_file", default="/data/.s3",
                    help="location of the file containing s3 keys. Only needed when s3-access and s3-secret are not provided directly. Default is /data/.s3")
s3_group.add_option("--s3-access", dest="s3_access", default=None,
                    help="S3 access key. Default is to gather it from the s3 file")
s3_group.add_option("--s3-secret", dest="s3_secret", default=None,
                    help="S3 secret key. Default is to gather it from the s3 file")
s3_group.add_option("--s3-bucket", dest="s3_bucket", default=None,
                    help="Bucket to use when uploading to s3. S3 uploads will not be performed unless this option is set")
s3_group.add_option("--s3-prefix", dest="s3_prefix", default=None,
                    help="prefix added to the tile location. S3 uploads will not be performed unless this option is set")
parser.add_option_group(s3_group)

# kml/preview image/tilepack related options
tilepack_group = OptionGroup(parser, "WeoGeo Tilepack Settings")
tilepack_group.add_option("-P", "--generate-preview-images", dest="do_previews", default=False, action="store_true",
                          help="Generate a 316x316 preview along with the tiles, and resample a 61x61 thumbnail from that. default: do not generate")
tilepack_group.add_option("-K", "--generate-kml-preview", dest="do_kml", default=False, action="store_true",
                          help="Generate a kml preview image from the bounds. These always have one max dimension of 1024, and are always geographic/png. default: do not generate")
tilepack_group.add_option("-Z", "--generate-tilepack", dest="generate_tilepack", default=None, type="string",
                          help="Generate a tilepack (with the given name) from the rendered tiles/preview image/kml. Turns on the -P and -K flags automatically. default: do not generate")
parser.add_option_group(tilepack_group)

if __name__ == '__main__':
    (opts, args) = parser.parse_args()
    if len(args) == 0:
        parser.error("no style file provided")

    opts.output_format = opts.output_format.lower()
    if opts.output_format == 'jpg':
        opts.output_format = 'jpeg'


    if opts.projection != 'geo' and opts.projection != 'sm':
        parser.error("invalid projection: '%s'" % opts.projection)
    opts.spherical_mercator = opts.projection != 'geo'
        
    extent = None
    if opts.spherical_mercator:
        extent = bound.Bound.spherical_mercator_max_extent()
    else:
        extent = bound.Bound.geographic_max_extent()

    if opts.north is None:
        opts.north = extent.north
    if opts.south is None:
        opts.south = extent.south
    if opts.east is None:
        opts.east = extent.east
    if opts.west is None:
        opts.west = extent.west

    if opts.output_format != 'jpeg' and opts.output_format != 'png':
        parser.error("invalid output format: '%s'" % opts.output_format)

    if not (opts.pixel_bits in [8,24,32]):
        parser.error("invalid image depth: '%s'" % opts.pixel_bits)

    # add non-user-accessible configuration settings
    opts.meta_pixels = opts.meta_size * 256
    opts.dpi = 72

    # switch to 0-indexed scale numbers
    opts.first_scale = opts.first_scale - 1

    if opts.highlight is not None:
        bounds = (opts.west, opts.north, opts.east, opts.south)
        write_geojson_highlight(opts.geojson_highlight, bounds)
    
    # switch on kml/preview generation if we're buliding a tilepack
    if opts.generate_tilepack is not None:
        opts.do_previews = True
        opts.do_kml      = True

    # turn on watermarking for the user if they supplied a custom file
    if opts.watermark_file != "./watermark.png":
        opts.watermark = True

    # should we push to s3?
    opts.s3_upload = opts.s3_prefix is not None and opts.s3_bucket is not None
    if opts.s3_upload:
        if opts.s3_access is None or opts.s3_secret is None:
            try:
                f = open(opts.s3_file)
                l = f.readlines()
                if opts.s3_access is None:
                    opts.s3_access = l[0].replace('\n','')
                if opts.s3_secret is None:
                    opts.s3_secret = l[1].replace('\n','')
            except IOError:
                parser.error("Unable to load the s3 file at: %s" % opts.s3_file)

    # fix case on pipeline items before we go further
    opts.tile_type     = opts.tile_type.lower()
    opts.tile_renderer = opts.tile_renderer.lower()

    if not tilesettings.supported(opts.tile_type):
        parser.error("invalid tile type: %s" % opts.tile_type)

    if not tilerenderer.supported(opts.tile_renderer):
        parser.error("invalid tile renderer: %s" % opts.tile_renderer)

    if opts.verbose:
        optnames = [x for x in dir(opts) if x.find('_') != 0]
        print "running with options:"
        for name in optnames:
            attr = getattr(opts, name)
            if type(attr) in [str, bool, float, int]:
                print "    %s: %s" % (name, attr)

    r = Renderer(opts.tile_type, opts.tile_renderer, opts.watermark_file)
    r.run(args[0], opts)
