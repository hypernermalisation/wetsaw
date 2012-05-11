#! /bin/bash

if [ $# -lt 1 ]
then
    echo "usage: shapeindexer <folder1> <folder2> ... <folderN>"
else
    find $* -name "*.shp" | sed 's/.shp//g' | \
    while read filename; do
        if [ -e "${filename}.index" ]
	then
	    if [ "${filename}.index" -ot "${filename}.shp" ]
	    then
		echo "shapefile for ${filename} updated"
		rm "${filename}.index"
		shapeindex $filename
	    else
	        echo "index for ${filename} already built"
	    fi
	else
	    shapeindex $filename
	fi
    done
fi