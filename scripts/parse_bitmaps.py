#!/usr/bin/env python2.7

from __future__ import print_function, division
import sys
import struct
import argparse
import io
from PIL import Image, ImageChops, ImageStat

"""Parses bitmap grids from a datasheet image, and converts them to a
binary format suitable for use in a tile editor."""
__author__="Cody 'codeman38' Boisclair"

def main():
    parser = argparse.ArgumentParser(
        description='Parses bitmap grids from a datasheet image, and '
                    'converts them to a binary format suitable for use '
                    'in a tile editor.')
    parser.add_argument('-i', '--invert', action='store_true',
        help='look for white pixels rather than black')
    parser.add_argument('-W', '--width', type=int, default=12,
        help='width, in pixels, of each character cell '
             '(default: %(default)d)')
    parser.add_argument('-H', '--height', type=int, default=18,
        help='height, in pixels, of each character cell '
             '(default: %(default)d)')
    parser.add_argument('-t', '--thresh', type=int, default=192,
        help='mean value threshold for a pixel to be considered active '
             '(default: %(default)d)')
    parser.add_argument('-o', '--out',
        help='output file (default: stdout)')
    parser.add_argument('imgfile', nargs='+',
        help='image(s) from which to read bitmaps')
    args = parser.parse_args()

    if args.out:
        out = io.open(args.out, 'wb')
    else:
        out = io.open(sys.stdout.fileno(), 'wb', closefd=False)
    for imgfile in args.imgfile:
        out.write(parse_image(imgfile, args.width, args.height,
                              args.thresh, args.invert))
    out.close()

def parse_image(imgfile, cwidth, cheight, thresh, invert):
    """Reads the image from the specified image file, parses the character
    bitmaps from it, and returns the binary representation as a byte string.

    Arguments:
    - imgfile: file name of image to parse
    - cwidth: width of character cell, in pixels
    - cheight: height of character cell, in pixels
    - thresh: mean value above which a pixel from the scanned image is
              considered to be active
    - invert: if True, look for white pixels in the image rather than black"""
    im = Image.open(imgfile)
    # downsample to greyscale
    im = im.convert('L')
    # invert so that active pixels are white
    if not invert:
        im = ImageChops.invert(im)

    parts = []
    for (ystart, yend) in get_bounds(im, 1):
        #print(ystart, yend, file=sys.stderr)
        row = im.crop((0, ystart, im.size[0]+1, yend+1))
        x_bounds = get_bounds(row, 0)
        for (xstart, xend) in x_bounds:
            #print('    ', xstart, xend, file=sys.stderr)
            charbit = im.crop((xstart, ystart, xend+1, yend+1))
            for val in parse_char(charbit, cwidth, cheight, thresh):
                parts.append(struct.pack('>H', val))
    return b''.join(parts)


def get_bounds(im, dim, thresh=32):
    """Finds the horizontal or vertical boundary lines between characters
    in a character bitmap sheet and yields them.

    Arguments:
    - im: PIL Image object containing the bitmap sheet
    - dim: 0 to find horizontal bounds, 1 to find vertical bounds
    - thresh: average pixel value above which a row/column will be considered
              a boundary"""
    max_x, max_y = im.size
    max_dim = max_x if dim == 0 else max_y
    last_mean = -1
    cur_bound = [-1, -1]
    for i in range(max_dim):
        if dim == 0:
            sl = im.crop((i, 0, i+1, max_y+1))
        else:
            sl = im.crop((0, i, max_x+1, i+1))
        mean = ImageStat.Stat(sl).mean[0]
        #print(mean)
        if mean > thresh and last_mean <= thresh:
            cur_bound[0] = i
        elif mean <= thresh and last_mean > thresh:
            cur_bound[1] = i-1
            # don't output this as a boundary unless there's more than a
            # single pixel distance
            if cur_bound[1] - cur_bound[0] > 1: 
                yield tuple(cur_bound)
        last_mean = mean

def parse_char(im, cwidth, cheight, thresh):
    """Parse the pixels from a character image, and yield the integer values
    that represent each row's bitmap in binary.

    Arguments:
    - im: PIL Image object containing the character bitmap, as cropped from
          the datasheet image.
    - cwidth: Expected width of the character bitmap, in pixels.
    - cheight: Expected height of the character bitmap, in pixels.
    - thresh: Mean value above which a pixel from the scanned image is
              considered to be active."""
    byte_aligned_bits = ((cwidth+7)//8)*8
    pix_width  = im.size[0] / cwidth
    pix_height = im.size[1] / cheight
    y1, y2 = 0.0, pix_height
    for nrow in range(cheight):
        row_val = 0
        x1, x2 = 0.0, pix_width
        for ncol in range(cwidth):
            # get the portion of the image representing this pixel
            # (rounding to the nearest integer)
            pixel = im.crop((int(x1+0.5), int(y1+0.5),
                             int(x2+0.5), int(y2+0.5)))
            # is its average over the threshold? then set that bit
            # (counting from the left end of the byte-aligned row)
            if ImageStat.Stat(pixel).mean[0] > thresh:
                row_val |= 1<<(byte_aligned_bits-1-ncol)
            x1, x2 = x2, x2+pix_width
        yield row_val
        y1, y2 = y2, y2+pix_height

if __name__=='__main__':
    main()