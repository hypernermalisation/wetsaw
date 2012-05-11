from __future__ import division 

import tilesettings, tilerenderer, tilecutter

import Image

import itertools

import bound
import math
import os, signal

import logging

from tools import apply_filter, mbound_filter_existing_tiles

# magic numbers and other "constants"
preview_image_size = 256
thumbnail_size     = (64, 64)
kml_max_size       = 1024
kml_filename       = "kml.png"
thumbnail_filename = "thumbnail.png"
baseimage_filename = "baseimage.png"
job_filename       = "job.txt"
tilepack_filename  = "xyz.tar.gz"

def calc_zoom_levels(highest, levels, base, in_xyz=False):
    if in_xyz:
        start = highest + base
        for x in xrange(start, start + levels):
            yield x
    else:
        for x in xrange(base,levels):
            val = int(math.ceil(highest / (2. ** float(x))))
            yield val

def write_bound(file, desc, bound):
    """
    Write the bound (given as a (n,s,e,w) tuple) to the given file with the
    given description.
    """
    file.write("%s:\n" % desc)
    file.write("  north: %s\n" % bound[0])
    file.write("  south: %s\n" % bound[1])
    file.write("  east: %s\n"  % bound[2])
    file.write("  west: %s\n"  % bound[3])
    file.write("\n")

class Renderer:
    def __init__(self, settings, renderer, watermark_file):
        self.settings = tilesettings.retrieve(settings)
        self.renderer = tilerenderer.retrieve(renderer)
        self.cutter   = tilecutter.TileCutter(watermark_file)

    def status(self, opts, msg):
        if opts.website_mode:
            os.system("mkdir -p %s" % opts.base_dir)
            f = open(os.path.join(opts.base_dir, "progress.log"), 'w')
            f.write(msg)
            f.close()
            
        
    def run(self,target, opts):
        global preview_image_size, thumbnail_size, kml_max_size
        global kml_filename,thumbnail_filename, baseimage_filename, job_filename, tilepack_filename


        logging.basicConfig(filename=opts.log_file,level=logging.INFO,format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        domain = bound.Bound(west  = opts.west,
                             south = opts.south,
                             north = opts.north,
                             east  = opts.east)

        try:
            if target.endswith('.rb'):
                targetOut = target[:-3] + ".xml"
                os.system("ruby %s > %s" % (target, targetOut))
                if not os.path.isfile(targetOut):
                    raise "Unable to create mapnik style from stylenik file %s" % target
                else:
                    target = targetOut
            
            if opts.website_mode:
                render_lock = os.path.join(opts.base_dir, "render.pid")
                if os.path.isfile(render_lock):
                    logging.error("Render process already running")
                    self.status(opts,"Render process already running")
                    exit()
                else:
                    def handler(signum, frame):
                        render_lock = os.path.join(opts.base_dir, "render.pid")
                        os.remove(render_lock)
                        exit()

                    signal.signal(signal.SIGHUP, handler)

                    os.system("mkdir -p %s" % opts.base_dir)
                    rf = open(render_lock, 'w')
                    rf.write(str(os.getpid()))
                    rf.close()

            logging.info("Rendering bounds: %s" % domain)

            if opts.do_previews:
                logging.info("generating preview file")
                self.status(opts,"Generating preview images")
                preview_file   = os.path.join(opts.base_dir, baseimage_filename)
                thumbnail_file = os.path.join(opts.base_dir, thumbnail_filename)

                if not os.path.exists(os.path.dirname(preview_file)):
                    try:
                        os.makedirs(os.path.dirname(preview_file))
                    except OSError:
                        pass

                renderer = self.renderer(target, preview_image_size)
                env      = renderer.render(domain, preview_file)
                logging.info("rendered with envelope: %s" % env)
                note_file = os.path.join(opts.base_dir, job_filename)
                note      = open(note_file, 'w')

                write_bound(note, "tile boundary values", (domain.north, domain.south, domain.east, domain.west) )

                write_bound(note, "baseimage extent", (env.maxy, env.miny, env.maxx, env.minx) )
                write_bound(note, "kml extent", (env.maxy, env.miny, env.maxx, env.minx) )

                note.close()
                
                logging.info("preview image generated at: %s" % preview_file)

                im = Image.open(preview_file)
                im.resize( thumbnail_size, Image.ANTIALIAS).save(thumbnail_file)
                logging.info("thumnail generated at: %s" % thumbnail_file)

            if opts.do_kml:
                kml_file = os.path.join(opts.base_dir, kml_filename)

                if not os.path.exists(os.path.dirname(kml_file)):
                    try:
                        os.makedirs(os.path.dirname(kml_file))
                    except OSError:
                        pass

                ar = domain.aspect_ratio()
                width, height = (0, 0)
                if ar < 1.0:
                    width  = int(math.floor(ar * kml_max_size))
                    height = kml_max_size
                else:
                    width  = kml_max_size
                    height = int(math.floor( (1/ar) * kml_max_size))

                logging.info("generating kml with width: %s, height: %s" % (width, height))
                renderer = self.renderer(target, width, height)
                renderer.render(domain, kml_file)
                logging.info("kml generated at: %s" % kml_file)

            settings = self.settings(opts.dpi, opts.meta_size, opts.output_format, opts.spherical_mercator)

            # grab a fresh renderer set for the meta_pixel size
            renderer = self.renderer(target, opts.meta_pixels)

            num = opts.zoom_levels + opts.first_scale
            scales_to_do    = len([x for x in calc_zoom_levels(opts.scale, num, opts.first_scale, in_xyz=True)])
            scales_rendered = 1
            for scale in calc_zoom_levels(opts.scale, num, opts.first_scale, in_xyz=True):
                logging.info("rendering zoom: %s" % scale)
                cut = 0
                lst = None
                estimate = 0
                if domain.spans_dateline(opts.spherical_mercator):
                    left, right = domain.slice_at_dateline(opts.spherical_mercator)
                    estimate = settings.estimate_tiles(left, scale)
                    estimate += settings.estimate_tiles(right, scale)

                    leftl  = settings.settings_for(left, scale, opts.overwrite, opts.base_dir)
                    rightl = settings.settings_for(right, scale, opts.overwrite, opts.base_dir)

                    lst = itertools.chain(leftl, rightl)
                else:
                    estimate = settings.estimate_tiles(domain, scale)
                    lst = settings.settings_for(domain, scale, opts.overwrite, opts.base_dir)

                if not opts.overwrite:
                    lst = apply_filter(mbound_filter_existing_tiles, lst)

                for (metabound, image_width, meta_file, clippings) in lst:
                    self.status(opts, "[%s/%s] zoom %s: tiles: %s/~%s" % (scales_rendered, scales_to_do, scale, cut, estimate))

                    renderer.new_image_size(image_width)
                    renderer.render(metabound, meta_file)
                    cut = cut + self.cutter.cut_tiles(meta_file, opts.overwrite, opts.pixel_bits, opts.output_format, clippings, opts.preserve_metapanels, opts.watermark_file)
                scales_rendered = scales_rendered + 1
                        

                logging.info("finished zoom: %s (%s tiles rendered)" % (scale, cut))
            logging.info("all rendering finished")

            if opts.generate_tilepack is not None:
                import tarfile, zipfile

                # Since our tar archives are coming out with full
                # paths on some systems, change the directory so we
                # can reference these files with relative paths
                cwd_save = os.getcwd()
                os.chdir(opts.base_dir)

                zipname = os.path.join(os.getcwd(), "%s.zip" % opts.generate_tilepack)
                tfname  = os.path.join(os.getcwd(), tilepack_filename)
                logging.info("generating download zip %s" % zipname)

                scales    = [str(s) for s in calc_zoom_levels(opts.scale, num, opts.first_scale, in_xyz = True)]
                # baseimage = os.path.join(opts.base_dir, baseimage_filename)
                # thumbnail = os.path.join(opts.base_dir, thumbnail_filename)
                # kml       = os.path.join(opts.base_dir, kml_filename)
                # note_file = os.path.join(opts.base_dir, job_filename)
                # tilepack  = os.path.join(opts.base_dir, tilepack_filename)

                baseimage = baseimage_filename
                thumbnail = thumbnail_filename
                kml       = kml_filename
                note_file = job_filename
                tilepack  = tilepack_filename
                note      = open(note_file, 'a')

                logging.info("generating tilepack")
                self.status(opts,"generating tilepack")

                tf = tarfile.open(tfname, mode='w:gz')

                note.write("\n")
                note.write("scales: %s\n" % ';'.join(scales))
                note.close()

                for s in scales:
                    sloc = os.path.join('xyz', s)
                    logging.info("adding zoom: %s" % sloc)
                    self.status(opts,"Archiving scale: %s" % sloc)
                    tf.add(sloc, sloc, True)

                tf.close()
                logging.info("tilepack generated")
                self.status(opts,"tilepack generated")

                zf = zipfile.ZipFile(zipname, 'w', zipfile.ZIP_STORED, True)

                logging.info("adding baseimage, thumbnail, kml")
                self.status(opts,"Archiving baseimage, thumbnail, kml")
                zf.write(baseimage, baseimage_filename)
                zf.write(thumbnail, thumbnail_filename)
                zf.write(kml,       kml_filename)
                zf.write(note_file, job_filename)
                zf.write(tilepack,  tilepack_filename)

                zf.close()

                logging.info("download zip generated")
                self.status(opts,"download zip generated")
                os.chdir(cwd_save)

            if opts.s3_upload:
                try:
                    import s3push
                    p = s3push.S3Push(opts)
                    p.run(logging)
                except Exception, e:
                    logging.error("unable to load s3 library (is boto installed?)")
                    logging.exception(e)


            logging.info("job complete")
            self.status(opts,"Job complete")
            if opts.website_mode:
                render_lock = os.path.join(opts.base_dir, "render.pid")
                os.remove(render_lock)
                
                
        except Exception, e:
            self.status(opts,"Error during rendering")
            logging.error("error during processing")
            logging.exception(e)
            logging.shutdown()
            if opts.website_mode:
                render_lock = os.path.join(opts.base_dir, "render.pid")
                if os.path.isfile(render_lock):
                    os.remove(render_lock)


