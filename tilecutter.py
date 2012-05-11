
import Image, ImageOps
import os, random

class TileCutter:
    def __init__(self, watermark_file=None):
        self.watermark_file = watermark_file
        self.watermark = None
        if watermark_file is not None:
            self.watermark = Image.open(watermark_file)
            self.watermark_xmid = 128 - (self.watermark.size[0] / 2)
            self.watermark_ymid = 128 - (self.watermark.size[0] / 2)


    def cut_tiles(self, imagefile, overwrite, out_depth, format, clippings, preserve_meta, watermark_file=None):
        """
        Cut tiles from 'imagefile' according to the 'clippings' bounds and file names.
        Expects clippings to have the following format:
        [((left,up,right,down), "filename")]
        e.g. (for XYZ tile system)

        [((0,0,180,180),"zoom/0/0.png"),
            ((180,0,360,180),"zoom/0/1.png"),
            ...])

        The clipping bounds should be in __image local__ coordinates.

        Will not overwrite files, or even bother loading the image, if all
        of the images exist and 'overwrite' is False.
        """

        # check if we should even bother clipping images
        num_cut = 0
        if not overwrite:
            filled = True
            for (b, name) in clippings:
                if not os.path.exists(name):
                    filled = False
                    break
            if filled:
                return num_cut

        Image.preinit()
        image = Image.open(imagefile)

        for (bounds, name) in clippings:
            if overwrite or not os.path.exists(name):
                # ensure the output directory exists
                if not os.path.exists(os.path.dirname(name)):
                    os.makedirs(os.path.dirname(name))
                out = image.crop(bounds)
                # handle watermarking, if requested
                if self.watermark is not None:
                    # offset watermark from the center by a random x/y
                    # within the image.
                    xloc = self.watermark_xmid + random.randint(-10,10)
                    yloc = self.watermark_ymid + random.randint(-10,10)

                    out.paste(self.watermark, (xloc, yloc), self.watermark)

                # handle image depth changes for pngs
                if format == 'png':
                    if out_depth == 8:
                        if out.mode == 'RGBA': # have to drop alpha channel
                            out = out.convert('RGB')
                        out = out.convert('P', colors = 256, palette=Image.ADAPTIVE)
                    elif out_depth == 24:
                        out = out.convert('RGB')
                    else:
                        out = out.convert('RGBA')
                out.save(name)
                num_cut = num_cut + 1

        if not preserve_meta:
            os.remove(imagefile)

        return num_cut
