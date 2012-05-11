from distutils.core import setup
import os

svnversion=""
svnversion=os.popen(''' svn info | sed -e '/^URL:/!d' -e 's/^.*\/tags\///g' -e 's/\/.*$$//g' -e '/^URL:/d' -e 's/^[A-Z,a-z]*-//g' -e 's/_/\./g' ''',"r").readline()
if svnversion == "":
  svnversion = os.popen(''' svn info | sed -e '/^Revision:/!d' -e 's/.* /svn/g' ''', "r").readline()

if svnversion == "":
  svnversion = "svn"

setup(name='wetsaw',
      version=svnversion.rstrip(),
      description='Tile Renderer',
      author='WeoGeo - Adam Jones',
      author_email='ajones@weogeo.com',
      url='http://godzilla.weogeo.com/svn/wetsaw/',
      packages=['processors'],
      py_modules = ['bound', 'import', 'make_baseimage', 'name', 'parser', 'render', 's3push', 'singleimage', 'tilecutter', 'tilecutter', 'tilerenderer', 'tilesettings', 'tools' ],
      scripts = [ 'scripts/render.py' ],
      data_files=[ ('/etc', ['watermark.png']) ]
     )
