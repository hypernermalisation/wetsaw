from distutils.core import setup

setup(name='wetsaw',
      version="1.0.0",
      description='A Mapnik-based XYZ tile rendering tool.',
      author='WeoGeo - Adam Jones',
      author_email='ajones@weogeo.com',
      url='http://github.com/WeoGeo/wetsaw/',
      packages=['processors'],
      py_modules = ['bound', 'import', 'make_baseimage', 'name', 'parser', 'render', 's3push', 'singleimage', 'tilecutter', 'tilecutter', 'tilerenderer', 'tilesettings', 'tools' ],
      scripts = [ 'scripts/render.py' ],
      data_files=[ ('/etc', ['watermark.png']) ]
     )
