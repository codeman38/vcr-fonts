# Unnamed VCR Font

Resurrecting fonts from the datasheets for old OSD chips. Whee!

Directory structure is as follows:

* `sources` - Original source datasheets, together with images extracted
  from them via the `pdfimages` command.

* `scripts` - Scripts for doing the conversion.

* `raw` - Raw 1BPP binary data parsed from the datasheet images using
  `scripts/parse_bitmaps.py` with the default parameters.

* `map` - Character mappings corresponding to the character data in `raw`,
  with one Unicode ID (and optional comment) per line.

* `bdf` - BDFs generated from `raw` and `map` files using
  `scripts/make_bdf.py`.

* `kbits` - Source files in [Bits'n'Picas][bitsnpicas] format, converted by
  loading the BDFs in that app and adding metadata.

[bitsnpicas]: https://github.com/kreativekorp/bitsnpicas/
