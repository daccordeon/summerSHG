#! /usr/bin/env python
# Yoichi Aso  Sep 22 2008

import re
import sys
import math
import optparse
import netgpib

# Usage text
usage = """usage: %prog [options]

This command will retrieve data from a network connected GPIB device.
The downloaded data will be saved to FILENAME.dat and the measurement parameters will be saved to FILENAME.par.
Optionally, you can plot the downloaded data by specifying --plot option.
You need matplotlib and numpy modules to plot the data.

example:
./%prog -i 192.168.113.105 -d AG4395A -a 10 -f meas01
./%prog -i 192.168.113.108 -d SR785 -a 6 -f meas01
"""

# Parse options
parser = optparse.OptionParser(usage=usage)
parser.add_option("-f", "--file", dest="filename",
                  help="Output file name without an extension", default="data")
parser.add_option("-d", "--device",
                  dest="deviceName", default="SR785",
                  help="A GPIB device name. Default = SR785.")
parser.add_option("-a", "--address",
                  dest="gpibAddress", type="int", default=10,
                  help="GPIB device address")
parser.add_option("-i", "--ip",
                  dest="ipAddress", default="gpib01",
                  help="IP address/Host name")
parser.add_option("--title",
                  dest="title", type="string", default="",
                  help="Title of the measurement. The given string will be written into the parameter file.")
parser.add_option("--memo",
                  dest="memo", type="string", default="",
                  help="Use this option to note miscellaneous things.")

(options, args) = parser.parse_args()

# Deal with an empty title
if options.title == "":
    options.title = options.filename

##################################################

# Load instrument module
try:
    inst = __import__(options.deviceName)
except ImportError:
    print("Unknown source:", options.deviceName, file=sys.stderr)
    sys.exit(1)

# Create/connect netGPIB object
print('Connecting to host %s, GPIB %d...' % (options.ipAddress, options.gpibAddress))
gpibObj = netgpib.netGPIB(options.ipAddress,
                          options.gpibAddress,
                          '\004', 0)
print('done.')

# open files
dataFileName = options.filename + '.dat'
paramFileName = options.filename + '.par'
print('Data will be written into %s.' % dataFileName)
print('Parameters will be written into %s.' % paramFileName)
dataFile = open(dataFileName, 'w')
paramFile = open(paramFileName, 'w')

# Write the title and the memo string into the parameter file
paramFile.write('#Title: ' + options.title + '\n')
paramFile.write('#Memo: ' + options.memo + '\n')

# Get the data
inst.getdata(gpibObj, dataFile, paramFile)
inst.getparam(gpibObj, options.filename, dataFile, paramFile)

# Close open file handles
dataFile.close()
paramFile.close()
gpibObj.close()
