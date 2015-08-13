import math
import psyco
psyco.full()

#plugin information
"""
info = {}
info['name'] = "Vecmath EventScripts python library"
info['version'] = "2.0d"
info['author'] = "GODJonez"
info['url'] = "http://www.eventscripts.com/pages/Vecmath/"
info['description'] = "Provides class and functions for handling vectors for Source"
info['tags'] = ""
"""

class vector(object):
    '''
vecmath.vector(source)
    
    Parameters:
        source - a vectorstring or iterable three-item datatype

    Returns a new vector object
    '''
    def __init__(self, vl, add1=None, add2=None, **kw):
        if add1 and add2:
            try:
                self.vl = [float(vl), float(add1), float(add2)]
            except:
                raise TypeError("Invalid data for vector")
        else:
            try:
                self.vl = [float(x) for x in vl]
            except ValueError:
                self.vl = [float(x) for x in vl.split(",")]
            except TypeError:
                raise TypeError("Invalid data type for vector")
        if kw:
            try:
                compval = 0
                for comp in ('x','y','z'):
                    if comp in kw:
                        self.vl[compval] = float(kw[comp])
                    compval += 1
            except:
                raise TypeError("Invalid data type in override for vector")
        while len(self.vl) < 3:
            self.vl.append(0.0)
    def __repr__(self):
        return "vector(%s)"%str(self.vl)
    def __list__(self):
        '''
x.__list__() <-> list(x)

    Returns a list with the vector components
    [x, y, z]
        '''
        return list(self.vl)
    def getdict(self):
        '''
x.getdict()

    Returns a dict object with the vector components
    {'x': x, 'y': y, 'z': z}
        '''
        return {'x':self.vl[0],'y':self.vl[1],'z':self.vl[2]}
    def __str__(self):
        '''
x.__str__() <-> str(x)

    Returns the vector info as a vectorstring
    "0.000000,0.000000,0.000000"
        '''
        return self.getstr()
    def getstr(self,sep=","):
        '''
x.getstr(sep=",")

    Parameters:
        sep - optional parameter (defaults to ",") to specify string separator
        
    Returns a string representation of the vector with specified separator
    "0.000000,0.000000,0.000000"
        '''
        return str(self.vl[0])+str(sep)+str(self.vl[1])+str(sep)+str(self.vl[2])
    def __len__(self):
        '''
x.__len__() <-> len(x)

    Returns the number of components of the vector, usually 3
        '''
        return len(self.vl)
    def __add__(self, vl2):
        '''
x.__add__(y) <-> x + y

    Returns a new vector with the two vectors summed together
    (x1, y1, z1) + (x2, y2, z2) == (x1+x2, y1+y2, z1+z2)
        '''
        return vector([self[0]+vl2[0], self[1]+vl2[1], self[2]+vl2[2]])
    def __sub__(self, vl2):
        '''
x.__sub__(y) <-> x - y

    Returns a new vector with the two vectors subtracted
    (x1, y1, z1) - (x2, y2, z2) == (x1-x2, y1-y2, z1-z2)
        '''        
        return vector([self[0]-vl2[0], self[1]-vl2[1], self[2]-vl2[2]])
    def __mul__(self, value):
        '''
x.__mul__(y) <-> x * y

    Returns a new vector with the vector multiplied with a scalar
    (x, y, z) * a == (x*a, y*a, z*a)

    Note! You cannot swap the order (a * vector will not work!)
        '''
        return vector([self[0]*value, self[1]*value, self[2]*value])
    def __div__(self, value):
        '''
x.__div__(y) <-> x / y

    Returns a new vector with the vector divided with a scalar
    (x, y, z) / a == (x/a, y/a, z/a)
        '''        
        return vector([self[0]/value, self[1]/value, self[2]/value])
    def __getitem__(self, index):
        '''
y = x.__getitem__(i) <-> y = x[i]

    Returns specified vector component.
    Index can be an integer between 0 and 2 or
    'x', 'y' or 'z'.
        '''
        try:
            return self.vl[int(index)]
        except (ValueError, IndexError):
            try:
                return self.vl[{'x':0,'y':1,'z':2}[str(index)]]
            except KeyError:
                raise IndexError("Index must be 0, 1, 2, 'x', 'y' or 'z'")
    def __setitem__(self, index, value):
        '''
x.__setitem__(i, y) <-> x[i] = y

    Sets a component's value to a new value.
    Index can be an integer between 0 and 2 or
    'x', 'y' or 'z'.
        '''
        try:
            self.vl[int(index)] = float(value)
        except (ValueError, IndexError):
            try:
                self.vl[{'x':0,'y':1,'z':2}[str(index)]] = float(value)
            except KeyError:
                raise IndexError("Index must be 0, 1, 2, 'x', 'y' or 'z'")
    def __eq__(self, vec2):
        '''
x.__eq__(y) <-> x == y

    Returns True if the vectors are identical, False if not.
    Vectors are identical when all of their components are identical.
        '''
        return self.vl == vec2.vl
    def __ne__(self, vec2):
        '''
x.__ne__(y) <-> x != y

    Returns True if the vectors are not identical, False if they are.
    Vectors are not identical when any of the components is different.
        '''
        return not self.__eq__(vec2)
    def __neg__(self):
        '''
x.__neq__() == -x

    Returns opposite vector.
    -(x, y, z) == (-x, -y, -z)
        '''
        return vector([x.__neg__() for x in self.vl])
    
    def copy(self):
        '''
x.copy()

    Returns a new identical vector object.
        '''
        return vector(self.vl)
    
    def ip(self, vec2):
        '''
x.ip(y)

    Parameters:
        y - another vector object

    Calculates the inner product (scalar product, dot product) of the
    two vectors.
    (x1, y1, z1) . (x2, y2, z2) == x1*x2 + y1*y2 + z1*z2
        '''
        return ip(self, vec2)
    def cp(self, vec2):
        '''
x.cp(y)

    Parameters:
        y - another vector object

    Calculates the cross product (outer product) of the
    two vectors.
    (x1, y1, z1) x (x2, y2, z2) == (y1*z2-z1*y2, z1*x2-x1*z2, x1*y2-y1*x2)
        '''
        return cp(self, vec2)
    def angle(self, vec2):
        '''
x.angle(y)

    Parameters:
        y - another vector object

    Calculates the angle between the vectors in radians.
    Paraller vectors return angle 0.
        '''
        return angle(self, vec2)
    def angles(self, vec2):
        '''
x.angles(y)

    Parameters:
        y - another vector object

    Calculates angles of vector projections to all coordinate axis
    perpendicular planes. Returns a list of angles in radians.
        '''
        return angles(self, vec2)
    def length(self):
        '''
x.length()

    Returns the length of the vector.
    |(x, y, z)| == sqrt(x^2 + y^2 + z^2)
        '''
        return length(self)
    def setlength(self, newlength):
        '''
x.setlength(y)

    Parameters:
        y - the new length for the vector

    Returns a new vector that is the vector x modified to be of length y.
        '''
        return setlength(self, newlength)
    def normalize(self):
        '''
x.normalize()

    Returns a new vector that is the vector x with length 1.
        '''
        return normalize(self)

def angle(vec1, vec2):
    # angle between the vectors
    try:
        return math.acos(ip(vec1, vec2)/(length(vec1)*length(vec2)))
    except ZeroDivisionError:
        raise ZeroDivisionError("Cannot calculate angle for zero vector")
def angles(vec1, vec2):
    # list of angles in three planes
    noxip = vec1[1]*vec2[1]+vec1[2]*vec2[2]
    noxl1 = math.sqrt(math.pow(vec1[1],2)+math.pow(vec1[2],2))
    noxl2 = math.sqrt(math.pow(vec2[1],2)+math.pow(vec2[2],2))
    noyip = vec1[0]*vec2[0]+vec1[2]*vec2[2]
    noyl1 = math.sqrt(math.pow(vec1[0],2)+math.pow(vec1[2],2))
    noyl2 = math.sqrt(math.pow(vec2[0],2)+math.pow(vec2[2],2))
    nozip = vec1[1]*vec2[1]+vec1[0]*vec2[0]
    nozl1 = math.sqrt(math.pow(vec1[1],2)+math.pow(vec1[0],2))
    nozl2 = math.sqrt(math.pow(vec2[1],2)+math.pow(vec2[0],2))
    try:
        nox = math.acos(noxip/(noxl1*noxl2))
    except ZeroDivisionError:
        nox = None
    try:
        noy = math.acos(noyip/(noyl1*noyl2))
    except ZeroDivisionError:
        noy = None
    try:
        noz = math.acos(nozip/(nozl1*nozl2))
    except ZeroDivisionError:
        noz = None
    return [nox, noy, noz]
def cp(vec1, vec2):
    # cross product
    x = vec1[1]*vec2[2]-vec1[2]*vec2[1]
    y = vec1[2]*vec2[0]-vec1[0]*vec2[2]
    z = vec1[0]*vec2[1]-vec1[1]*vec2[0]
    return vector((x,y,z))
def ip(vec1, vec2):
    # dot product (inner product, scalar product)
    return vec1[0]*vec2[0]+vec1[1]*vec2[1]+vec1[2]*vec2[2]
def length(vec1):
    # vector length
    return math.sqrt(math.pow(vec1[0],2)+math.pow(vec1[1],2)+math.pow(vec1[2],2))
def normalize(vec1):
    # set length to 1
    return setlength(vec1, 1)
def setlength(vec1, newlength):
    try:
        mod = newlength/length(vec1)
    except ZeroDivisionError:
        raise ZeroDivisionError("Cannot set length of zero vector")
    return vec1 * mod

# some helper functions
def distance(coord1, coord2):
    return length(vector(coord1)-vector(coord2))
def viewangles(coord1, coord2, roll=0.0):
    # note: vector(vector) works also, so you can pass vectors also ;)
    v1 = vector(coord1)
    v2 = vector(coord2)
    height = v2[2]-v1[2]
    xl = v2[0]-v1[0]
    yl = v2[1]-v1[1]
    xylen = math.hypot(xl,yl)
    try:
        pitch = math.degrees(math.atan(height/xylen))
    except ZeroDivisionError:
        pitch = cmp(v2[2],v1[2])*90.0
    try:
        yaw = math.degrees(math.atan(yl/xl))
        if xl < 0:
            yaw += 180.0
        if yaw < 0:
            yaw += 360.0
    except ZeroDivisionError:
        yaw = cmp(v2[1],v1[1])*90.0
    return [pitch, yaw, float(roll)]
def viewvector(va):
    # creates a vector from [pitch, yaw, roll] list
    vangles = vector(va)
    z = math.sin(math.radians(vangles[0]))
    a = math.sqrt(1-z**2)
    x = a*math.cos(math.radians(vangles[1]))
    y = a*math.sin(math.radians(vangles[1]))
    return vector((x,y,z))
def isbetweenRect(what, corner1, corner2):
    minvector = vector((
        min((corner1[0],corner2[0])),
        min((corner1[1],corner2[1])),
        min((corner1[2],corner2[2]))
        ))
    maxvector = vector((
        max((corner1[0],corner2[0])),
        max((corner1[1],corner2[1])),
        max((corner1[2],corner2[2]))
        ))
    for i in (0,1,2):
        if minvector[i] > what[i] or what[i] > maxvector[i]:
            return False
    return True
def isbetweenVect(what, corner1, corner2):
    v = vector(what)
    c1 = vector(corner1)
    c2 = vector(corner2)
    if (v==c1 or v==c2):
        return True
    if c1==c2:
        return False
    return ((v[0]-c1[0])/(v[1]-c1[1])==(c2[0]-c1[0])/(c2[1]-c1[1]) and
            (v[0]-c1[0])/(v[2]-c1[2])==(c2[0]-c1[0])/(c2[2]-c1[2]) and
            (v[2]-c1[2])/(v[1]-c1[1])==(c2[2]-c1[2])/(c2[1]-c1[1]))
