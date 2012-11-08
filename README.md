Wetsaw
======

Wetsaw is a library and command line application for rendering geographic tiles in the XYZ tile format. It is written in Python and builds on the [Mapnik](http://mapnik.org/) rendering library.

Features
========

* **Batched tile rendering**: Multiple tiles are automatically rendered together in Mapnik for efficiency, then the tiles themselves are cut from the larger image
* **Efficiently renders large tilesets**: The library internally generates tile information as it is needed for rendering, allowing it to render millions of tiles in a consistent, small amount of memory
* **Extent highlighting**: (Optional) Generate a GeoJSON file that contains a world polygon with a hole matching the extent rendered
* **Preserve old tiles**: (Optional) Tile rendering can be run to fill in gaps rather than starting from scratch
* **Watermarking**: (Optional) Overlay a transparent png on all tiles. This image has a slight random offset within the tile to hinder automatic removal
* **Status updates**: (Optional) Communicate current rendering progress through a predefined file
* **S3 file upload**: (Optional) Publish the resulting tiles directly to Amazon S3
* **WeoGeo preview data support**: (Optional) Generate all of the preview data needed to upload to WeoGeo's servers

Requirements
============

* Python (tested on 2.6.1+, not yet tested on 3.0)
* Mapnik (0.7.1 or 2.X)
* PIL (test on 1.1.7)
* boto (for s3 file upload)