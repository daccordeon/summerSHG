#!/usr/bin/env python
"""A quick way to plot data downloaded by netgpibdata.py"""
import optparse
import gpibplot

# Usage text
usage = """usage: %prog [options]
Plot the data downloaded by netgpibdata.py.
Data is read from FILENAME.dat and the associated parameters are read from FILENAME.par.
You can start an ipython session after a plot is generated. This enables one to change annotations/appearance of the plot.
"""
# Parse options
parser = optparse.OptionParser(usage=usage)
parser.add_option("-f", "--file", dest="filename",
                  help="Filename without an extension from which the data and parameters are read.", default="data")
parser.add_option("-i", "--ipython",
                  dest="ipython", default=False,
                  action="store_true",
                  help="Invoke ipython to interactively change the plot")
parser.add_option("--xlin",
                  dest="xlog", default=True,
                  action="store_false",
                  help="Plot with linear x axis")
parser.add_option("--ylin",
                  dest="ylog", default=None,
                  action="store_false",
                  help="Plot with linear y axis")
parser.add_option("--xlog",
                  dest="xlog", default=True,
                  action="store_true",
                  help="Plot with logarithmic x axis")
parser.add_option("--ylog",
                  dest="ylog", default=None,
                  action="store_true",
                  help="Plot with logarithmic y axis")


(opts, args) = parser.parse_args()

ax = gpibplot.plotSR785(opts.filename, xlog=opts.xlog, ylog=opts.ylog)
fig = ax[0].figure

if opts.ipython:
    from IPython.Shell import IPShellEmbed
    ipshell = IPShellEmbed([], banner="""The following objects are exported:
    ax: a list of axes objects.
    fig: figure object.""")
    ipshell()

else:
    input('Press enter to quit:')
