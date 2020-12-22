#! /usr/bin/env python

import sys
import optparse
import netgpib

# Usage text
usage = """usage: %prog [options] CMD

Issue a command or query from a network-connected GPIB device.

example:
%prog -i 192.168.113.105 -d AG4395A -a 10 'POIN?'"""

# Parse options
parser = optparse.OptionParser(usage=usage)
parser.add_option("-a", "--address",
                  dest="gpibAddress", type="int", default=10,
                  help="GPIB device address (default: 10)")
parser.add_option("-i", "--ip",
                  dest="ipAddress", default="gpib01",
                  help="IP address/Host name (default: gpib01)")
parser.add_option("-l", "--log",
                  dest="log", action="store_true",
                  help="Log GPIB commands")

(options, args) = parser.parse_args()

if not args:
    print('Must supply command argument.', file=sys.stderr)
    sys.exit(1)

##################################################

# Create/connect to netGPIB object
#print >>sys.stderr, 'Connecting to %s...' % (options.ipAddress),
gpibObj = netgpib.netGPIB(options.ipAddress,
                          options.gpibAddress,
                          '\004', 0,
                          log=options.log)
#print >>sys.stderr, ' done.'

for cmd_string in args[0].split('\n'):
    if not cmd_string:
        continue

    cmd = cmd_string.split(' ')

    if cmd[0].find('?') > 0:
        print(gpibObj.query(cmd_string).strip())
    elif cmd == 'refresh':
        gpibObj.refresh()
    else:
        gpibObj.command(cmd_string)

gpibObj.close()
