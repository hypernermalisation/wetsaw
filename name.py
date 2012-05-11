import os

class XYZNamingScheme:
    file_type = 'png'
    basedir = './'
    def __init__(self, file_type, basedir="./"):
        self.file_type = file_type
        self.basedir = basedir

    def bound_name(self, lonTS, latTS):
        """Generate the name reference for the given bound"""
        return "%s/%s" % (str(lonTS), str(latTS))

    def adjust_file_type(self):
        """Change file extension to fit the file format"""
        if self.file_type == 'jpeg':
            return 'jpg'
        else:
            return self.file_type

    def name_for(self, scale, lonTS, latTS):
        """Return a string for the file name for the given tile within a metatile"""
        return os.path.join(self.dir_for(scale, lonTS, latTS) + "." + str(self.adjust_file_type()))

    def dir_for(self, scale, lonTS, latTS):
        """Return a string for the directory that contains the given metatile bounds"""
        return os.path.join(self.basedir, "xyz", str(scale), self.bound_name(lonTS, latTS))
