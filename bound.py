
import math

class Bound:
	west = 0;
	east = 0;
	north = 0;
	south = 0;

	@staticmethod
	def from_tuple(t):
		"""
		Re-contrust the bounds from the given (west, north,
		east, south) tuple.

		Bound.from_tuple(b.tuple()) <=> b
		"""
		b = Bound(west  = t[0],
			  north = t[1],
			  east  = t[2],
			  south = t[3])
		return b

        @staticmethod
        def geographic_max_extent():
                return Bound(north  = 90.0,
                             south  = -90.0,
                             east   = 180.0,
                             west   = -180.0)

        @staticmethod
        def spherical_mercator_max_extent():
                return Bound(north  = 20037508.34,
                             south  = -20037508.34,
                             east   = 20037508.34,
                             west   = -20037508.34)


	def __init__(self, **kwargs):
		self.west = kwargs.get('west', 0)
		self.east = kwargs.get('east', 0)
		self.north = kwargs.get('north', 0)
		self.south = kwargs.get('south', 0)

	def spans_dateline(self, spherical_mercator):
		"""
		Geo only: Does this boundary span the dateline?
		"""
                extent = Bound.spherical_mercator_max_extent() if spherical_mercator else Bound.geographic_max_extent()
		return self.west < extent.west or self.east > extent.east or self.west > self.east

	def slice_at_dateline(self, spherical_mercator):
		"""
		Return a tuple of bound objects that do not wrap the dateline.

		If this bound arleady does not wrap the dateline,
		return a tuple containing a single copy of this bound
		object and the value None.
		
		Does not handle the case where both east and west wrap
		the dateline.
		"""
                extent = Bound.spherical_mercator_max_extent() if spherical_mercator else Bound.geographic_max_extent()

		if not self.spans_dateline(spherical_mercator):
			return (self.copy(), None)

		left  = self.copy()
		right = self.copy()
		# west wraps dateline
		if self.west < extent.west:
			left.east = extent.east
			left.west = self.west % extent.east

			right.west = extent.west
			right.east = self.east

		# east wraps dateline
		elif self.east > extent.east:
			left.west = extent.west
			left.east = self.east % extent.west

			right.west = self.west
			right.east = extent.east

		# request wraps dateline through in-range values
		# (example: request for all of Asia) force into one of
		# the above cases and re-submit
		else:
			b = self.copy()
			b.west -= extent.lon_span()
			assert(b.west < b.east and b.west < extent.west)
			return b.slice_at_dateline()

		return (left, right)

	def tuple(self):
		"Return the values of this instance as the tuple (west,north,east,south)"
		return (self.west, self.north, self.east, self.south)

	def int(self):
		b = Bound(west  = int(self.west),
			  north = int(self.north),
			  east  = int(self.east),
			  south = int(self.south))
		return b
		
        def lat_span(self):
                if self.y_up():
                        return self.north - self.south
                else:
                        return self.south - self.north

        def lon_span(self):
                return self.east - self.west

	def y_up(self):
		return (self.north - self.south) > 0

	def flip_y(self):
		"""
		Return a copy of this bound where:
		north=south, south=north.
		"""
		b = Bound(west  = self.west,
			  north = self.south,
			  east  = self.east,
			  south = self.north)
		return b

	def copy(self):
		b = Bound(west  = self.west,
			  north = self.north,
			  east  = self.east,
			  south = self.south)
		return b

        def aspect_ratio(self):
		"""
		Compute the ratio of width:height for these bounds.
		"""
		w = abs(self.east - self.west)
		h = abs(self.north - self.south)
		return w / h

	def tiles_for(self, width):
		"Return a list of (west,north,east,south) for tiles of width 'width' across this bound, assumes pixels and y points up."
		return ((w,n,w+width,n+width) for w in xrange(self.west, self.east, width) for n in xrange(self.north, self.south, width))

	def sub(self, other):
		"Return new bounds in terms of the vector at (other.top, other.left)"
		b = Bound(west  = self.west - other.west,
			  north = self.north - other.north,
			  east  = self.east - other.west,
			  south = self.south - other.north)
		return b

	
	def constrain(self, other):
		"Return the subset of bounds in self that are also within the bounds of other, assumes pixels and y points down"
		b = self.copy()
		if self.north < other.north:
			b.north = other.north
		if self.east > other.east:
			b.east = other.east
		if self.west < other.west:
			b.west = other.west
		if self.south > other.south:
			b.south = other.south
		return b
	
	def __repr__(self):
		return "Bound(north=%s, east= %s, west=%s, south=%s)" % (self.north, self.east, self.west, self.south)
	
	def overlap(self, other, do_other=True):
		"""
		Check if the given bounds overlap/intersect. 
		"""
		if not self.y_up():
			slf = self.flip_y()
		else:
			slf = self

		if not other.y_up():
			oth = other.flip_y()
		else:
			oth = other

		def between(a,b,c):
			return a < b and b < c
		
                #check north-west point
		if( oth.south <= slf.north and slf.north <= oth.north):
			if( oth.west <=  slf.west and  slf.west <=  oth.east):
				return True

	        #check north-east point
		if( oth.south <=  slf.north and  slf.north <=  oth.north):
			if( oth.west <=  slf.east and  slf.east <=  oth.east):
				return True

                #check south-west point
		if(  oth.south <=  slf.south and  slf.south <=  oth.north):
			if(  oth.west <=  slf.west and  slf.west <=  oth.east):
				return True

                #check south-east point
		if(  oth.south <=  slf.south and  slf.south <=  oth.north):
			if( oth.west <=  slf.east and  slf.east <=  oth.east):
				return True

		# need the 'do_other' check to catch the case where
		# 'self' entirely contains 'other'
		if do_other:
			return other.overlap(self,False)
		else:
			return False

		
		
