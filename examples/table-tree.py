import sys

import Numeric
from numarray import *
from numarray import records
from tables import *

class Particle(IsDescription):
    ADCcount    = Int16Col(0)              # signed short integer
    TDCcount    = UInt8Col(0)              # unsigned byte
    grid_i      = IntCol(0)                # integer
    grid_j      = IntCol(0)                # integer
    idnumber    = Int64Col(0)              # signed long long 
    name        = StringCol(16, dflt="")   # 16-character String
    pressure    = Float32Col(0.0, shape=2) # float  (single-precision)
    temperature = FloatCol(0.0)            # double (double-precision)

Particle2 = {
    # The old way to declare columns is still supported, although its
    # use is discouraged
    "ADCcount"    : Col("Int16", 1, 0),    # signed short integer
    "TDCcount"    : Col("UInt8", 1, 0),    # unsigned byte
    "grid_i"      : Col("Int32", 1, 0),    # integer
    "grid_j"      : Col("Int32", 1, 0),    # integer
    "idnumber"    : Col("Int64", 1, 0),    # signed long long 
    "name"        : Col("CharType", 16, ""),  # 16-character String
    "pressure"    : Col("Float32", 2, 0),  # float  (single-precision)
    "temperature" : Col("Float64", 1, 0),  # double (double-precision)
}

# The name of our HDF5 filename
filename = "table-tree.h5"

# A translation map
trMap = {"detector": "for",  # A reserved word
         "table": " 11 ",}   # A non-valid python variable name
    
# Open a file in "w"rite mode
h5file = openFile(filename, mode = "w", trMap=trMap)

# Create a new group under "/" (root)
group = h5file.createGroup("/", 'detector')

# Create one table on it
#table = h5file.createTable(group, 'table', Particle, "Title example")
# You can choose creating a Table from a description dictionary if you wish
table = h5file.createTable(group, 'table', Particle2, "Title example")

# Create a shortcut to the table record object
particle = table.row

# Fill the table with 10 particles
for i in xrange(10):
    # First, assign the values to the Particle record
    particle['name']  = 'Particle: %6d' % (i)
    particle['TDCcount'] = i % 256    
    particle['ADCcount'] = (i * 256) % (1 << 16)
    particle['grid_i'] = i 
    particle['grid_j'] = 10 - i
    particle['pressure'] = [float(i*i), float(i*2)]
    particle['temperature'] = float(i**2)
    particle['idnumber'] = i * (2 ** 34)  # This exceeds integer range
    # This injects the Record values.
    particle.append()

# Flush the buffers for table
table.flush()

# Get actual data from table. We are interested in column pressure.
pressure = [ p['pressure'] for p in table.iterrows() ]
print "Last record ==>", p
print "Column pressure ==>", array(pressure)
print "Total records in table ==> ", len(pressure)
print

# Create a new group to hold new arrays
gcolumns = h5file.createGroup("/", "columns")
print "columns ==>", gcolumns, pressure
# Create a Numeric array with this info under '/columns'
h5file.createArray(gcolumns, 'pressure', Numeric.array(pressure),
                   "Pressure column")
print "gcolumns.pressure type ==> ", gcolumns.pressure.type

# Do the same with TDCcount, but with a numarray object
TDC = [ p['TDCcount'] for p in table.iterrows() ]
print "TDC ==>", TDC
print "TDC shape ==>", array(TDC).shape
h5file.createArray('/columns', 'TDC', array(TDC), "TDCcount column")

# Do the same with name column
names = [ p['name'] for p in table.iterrows() ]
print "names ==>", names
h5file.createArray('/columns', 'name', names, "Name column")
# This works even with homogeneous tuples or lists (!)
print "gcolumns.name shape ==>", gcolumns.name.shape 
print "gcolumns.name type ==> ", gcolumns.name.type

print "Table dump:"
for p in table.iterrows():
    print p

# Save a recarray object under detector
r=records.array("a"*300,'f4,3i4,a5,i2',3)
recarrt = h5file.createTable("/detector", 'recarray', r, "RecArray example")
r2 = r[0:3:2]
# Change the byteorder property
# The next gives an error with numarray 0.6
#r2.togglebyteorder()
r2._byteorder = {"little":"big","big":"little"}[r2._byteorder]
recarrt = h5file.createTable("/detector", 'recarray2', r2,
                             "Non-contiguous recarray")
print recarrt
print

print h5file.root.detector.table.description
# Close the file
h5file.close()

#sys.exit()

# Reopen it in append mode
h5file = openFile(filename, "a", trMap=trMap)

# Ok. let's start browsing the tree from this filename
print "Reading info from filename:", h5file.filename
print

# Firstly, list all the groups on tree
print "Groups in file:"
for group in h5file.walkGroups("/"):
    print group
print

# List all the nodes (Group and Leaf objects) on tree
print "List of all nodes in file:"
print h5file

# And finally, only the Arrays (Array objects)
print "Arrays in file:"
for array in h5file.walkNodes("/", classname="Array"):
    print array
print

# Get group /detector and print some info on it
detector = h5file.getNode("/detector")
print "detector object ==>", detector

# List only leaves on detector
print "Leaves in group", detector, ":"
for leaf in h5file.listNodes("/detector", 'Leaf'):
    print leaf
print

# List only tables on detector
print "Tables in group", detector, ":"
for leaf in h5file.listNodes("/detector", 'Table'):
    print leaf
print

# List only arrays on detector (there should be none!)
print "Arrays in group", detector, ":"
for leaf in h5file.listNodes("/detector", 'Array'):
    print leaf
print

# Get "/detector" Group object
group = h5file.root.detector
print "/detector ==>", group 

# Get the "/detector/table
table = h5file.getNode("/detector/table")
print "/detector/table ==>", table 

# Get metadata from table
print "Object:", table
print "Table name:", table.name
print "Table title:", table.title
print "Rows saved on table: %d" % (table.nrows)

print "Variable names on table with their type:"
for name in table.colnames:
    print "  ", name, ':=', table.coltypes[name] 
print    

# Read arrays in /columns/names and /columns/pressure

# Get the object in "/columns pressure"
pressureObject = h5file.getNode("/columns", "pressure")

# Get some metadata on this object
print "Info on the object:", pressureObject
print "  shape ==>", pressureObject.shape
print "  title ==>", pressureObject.title
print "  type ==> ", pressureObject.type
print "  byteorder ==> ", pressureObject.byteorder

# Read the pressure actual data
pressureArray = pressureObject.read()
print "  data type ==>", type(pressureArray)
print "  data ==>", pressureArray
print

# Get the object in "/columns/names"
nameObject = h5file.root.columns.name

# Get some metadata on this object
print "Info on the object:", nameObject
print "  shape ==>", nameObject.shape
print "  title ==>", nameObject.title
print "  type ==> " % nameObject.type


# Read the 'name' actual data
nameArray = nameObject.read()
print "  data type ==>", type(nameArray)
print "  data ==>", nameArray

# Print the data for both arrays
print "Data on arrays name and pressure:"
for i in range(pressureObject.shape[0]):
    print "".join(nameArray[i]), "-->", pressureArray[i]
print


# Finally, append some new records to table
table = h5file.root.detector.table

# Append 5 new particles to table (yes, tables can be enlarged!)
particle = table.row
for i in xrange(10, 15):
    # First, assign the values to the Particle record
    particle['name']  = 'Particle: %6d' % (i)
    particle['TDCcount'] = i % 256    
    particle['ADCcount'] = (i * 256) % (1 << 16)
    particle['grid_i'] = i 
    particle['grid_j'] = 10 - i
    particle['pressure'] = [float(i*i), float(i*2)]
    particle['temperature'] = float(i**2)
    particle['idnumber'] = i * (2 ** 34)  # This exceeds integer range
    # This injects the Row values.
    particle.append()

# Flush this table
table.flush()

print "Columns name and pressure on expanded table:"
# Print some table columns, for comparison with array data
for p in table:
    print p['name'], '-->', p['pressure']
print

print table.read(field="ADCcount")
print table.read(field="ADCcount", flavor="Numeric")
print table.read(0, 0, 1, "name")
print table.read(0, 0, 1, "name", flavor="List")
print table.read(0, 0, 2, "pressure")
print table.read(0, 0, 2, "pressure", flavor="Tuple")

# Several range selections
print "Extended slice in selection: [0:7:6]"
print table.read(0,7,6)
print "Single record in selection: [1]"
print table.read(1)
print "Last record in selection: [-1]"
print table.read(-1)
print "Two records before the last in selection: [-3:-1]"
print table.read(-3, -1)

# Print a recarray in table form
table = h5file.root.detector.recarray2
print "recarray2:", table
print "  nrows:", table.nrows
print "  byteorder:", table.byteorder
print "  coltypes:", table.coltypes
print "  colnames:", table.colnames

print table.read()
for p in table.iterrows():
    print p['c1'], '-->', p['c2']
print

result = [ rec['c1'] for rec in table if rec.nrow() < 2 ]
print result

# Test the File.renameNode() method
h5file.renameNode(h5file.root.detector.recarray2, "recarray3")
# Delete a Leaf from the HDF5 tree
h5file.removeNode(h5file.root.detector.recarray3)
# Delete the detector group and its leaves recursively
#h5file.removeNode(h5file.root.detector, recursive=1)
# Create a Group and then remove it
h5file.createGroup(h5file.root, "newgroup")
h5file.removeNode(h5file.root, "newgroup")
h5file.renameNode(h5file.root.columns, "newcolumns")

print h5file

# Close this file
h5file.close()

