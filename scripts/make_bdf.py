#!/usr/bin/env python

import argparse
import functools
import sys
import os
from bdflib.model import Font
from bdflib import writer, xlfd

# NOTE: This script requires the 'bdflib' module (available from PyPI).

def main():
    parser = argparse.ArgumentParser(
        description='Generates a BDF from a file of raw binary font data '
                    'and a character mapping.')
    parser.add_argument('-cw', '--width', type=int, default=12, 
                        help='character width (default: %(default)d)')
    parser.add_argument('-ch', '--height', type=int, default=18, 
                        help='character height (default: %(default)d)')
    parser.add_argument('-cd', '--descent', type=int, default=-2, 
                        help='character descent (default: %(default)d)')
    parser.add_argument('-o', '--output',
                        help='output file (default: stdout)')
    parser.add_argument('-n', '--name',
                        help='font name to use for generated font. '
                             'By default, auto-derived from the name '
                             'of binfile.')
    parser.add_argument('binfile',
                        help='file containing binary font data')
    parser.add_argument('mapfile',
                        help='file containing character map. Each line '
                             'identifies the hex value of the corresponding '
                             'character, optionally followed by whitespace '
                             'and a comment.')
    args = parser.parse_args()

    with open(args.binfile, 'rb') as fp:
        data = fp.read()
    with open(args.mapfile, 'r') as fp:
        mapping = [int(line.strip().split()[0], 16)
                   for line in fp]

    fontname = os.path.splitext(os.path.basename(args.binfile))[0] \
               if args.name is None else args.name

    char_width = args.width
    char_byte_width = (char_width+7)//8
    char_height = args.height
    char_length = char_byte_width * char_height
    char_descent = args.descent
    num_chars = len(data) // char_length
    # number of bits to shift character right to fit into bounding box
    rshift = 8 * char_byte_width - char_width

    font = Font(fontname.encode('utf-8'), char_height, 72, 72)
    for glyph_num in range(num_chars):
        if glyph_num >= len(mapping): break
        glyph_cp = mapping[glyph_num]
        if glyph_cp == 0: continue
        glyph_start = glyph_num*char_length
        rows = []
        for row in range(char_height):
            row_start = glyph_start + char_byte_width * row
            row_value = 0
            for byte in data[row_start:row_start+char_byte_width]:
                row_value = (row_value << 8) | byte
            rows.insert(0, row_value >> rshift)
        if glyph_cp <= 0xFFFF:
            glyph_name = 'uni{0:04x}'.format(glyph_cp)
        else:
            glyph_name = 'U+{0:x}'.format(glyph_cp)
        font.new_glyph_from_data(
            name=glyph_name.encode('utf-8'), codepoint=glyph_cp, data=rows,
            bbX=0, bbY=char_descent, bbW=char_width, bbH=char_height,
            advance=char_width)
    xlfd.fix(font)

    if args.output:
        fp = open(args.output, 'wb')
    else:
        fp = open(sys.stdout.fileno(), 'wb', closefd=False)
    writer.write_bdf(font, fp)
    if not args.output:
        fp.close()

if __name__=="__main__":
    main()
