#! /usr/bin/env python
"""dlR9211.py [-f filename] [-d devicename] [-i ip_address] [-a gpib_address]

 This script will get data from ADVANTEST R9211 servo analyzer through network and save the data into a data file.
 The name of the data file can be specified by '-f' option. If '-f myfile' is specified,
 myfile.dat is the name of the data file. Also myfile.par will be created.
 The format of myfile.dat should be explained in myfile.par along with various measurement
 parameters.
 Yoichi Aso  Dec 2 2009"""

import optparse
import R9211

# Usage text
usage = """usage: %prog [options]

This command will retrieve data from an R9211 servo analyzer.
The downloaded data will be saved to FILENAME.dat and the measurement parameters will be saved to FILENAME.par.
Optionally, you can plot the downloaded data by specifying --plot option.
You need matplotlib and numpy modules to plot the data.
"""

# Parse options
parser = optparse.OptionParser(usage=usage)
parser.add_option("-f", "--file", dest="filename",
                  help="Output file name without an extension", default="data")
parser.add_option("-a", "--address",
                  dest="gpibAddress", type="int", default=8,
                  help="GPIB device address")
parser.add_option("-i", "--ip",
                  dest="ipAddress", default="133.11.4.82",
                  help="IP address/Host name")
parser.add_option("-d", "--display",
                  dest="disp", default="1",
                  help="Specify display numbers you want to download data from. Comma separated list of numbers, like '-d 1,2'. ")
parser.add_option("--plot",
                  dest="plotData", default=False,
                  action="store_true",
                  help="Plot the downloaded data.")
parser.add_option("--xlin",
                  dest="xlog", default=None,
                  action="store_false",
                  help="Plot with linear x axis")
parser.add_option("--ylin",
                  dest="ylog", default=None,
                  action="store_false",
                  help="Plot with linear y axis")
parser.add_option("--xlog",
                  dest="xlog", default=None,
                  action="store_true",
                  help="Plot with logarithmic x axis")
parser.add_option("--ylog",
                  dest="ylog", default=None,
                  action="store_true",
                  help="Plot with logarithmic y axis")


(options, args) = parser.parse_args()

# Convert disp to a numerical list
disp = eval("[" + options.disp + "]")

# Generate file names
dataFileName = options.filename + '.dat'
paramFileName = options.filename + '.par'

print(('Data will be written into ' + dataFileName))
print(('Parameters will be written into ' + paramFileName + '\n'))

# # Open socket

print(('Connecting to ' + str(options.ipAddress)))
# Create an instance of R9211
dev = R9211.R9211(options.ipAddress, options.gpibAddress)
print('done.')


# Download data
(data, hdr) = dev.getdata(disp, verbose=True)
# Download params
(cparams, dparams) = dev.getparams(disp, verbose=True)

# open files
dataFile = open(dataFileName, 'w')
paramFile = open(paramFileName, 'w')


# Write to the data file
mcol = dev.saveData(dataFile, data)
# Write to the parameter file
dev.saveParam(paramFile, cparams, dparams, hdr, mcol, disp)

# Close files, device
dataFile.close()
paramFile.close()
dev.close()

if options.plotData:
    import matplotlib.pyplot as plt

    fig = []
    ax = []
    for i in range(len(data)):  # Loop through displays
        fig.append(plt.figure())
        ax.append(fig[i].add_subplot(1, 1, 1))
        ax[i].plot(data[i][0], data[i][1])
        ax[i].set_xlabel(hdr[i]['xDataType'] +
                         "[" + hdr[i]['xUnit'] + "]", size=16)

        if hdr[i]['yUnit'][-4:] == 'rtHz':
            ax[i].set_ylabel(
                hdr[i]['yDataType'] + r"[$\mathsf{" + hdr[i]['yUnit'][:-4] + r"\sqrt{Hz}}$]", size=16)
        else:
            ax[i].set_ylabel(
                hdr[i]['yDataType'] + "[" + hdr[i]['yUnit'] + "]", size=16)

        ax[i].set_title("Display " + str(disp[i]) + ": Ch" +
                        hdr[i]['Chan'] + " " + cparams['Function'])
        ax[i].grid(True)

        # Default scaling
        xlog = False
        ylog = False

        # Spectrum and Cross spectrum
        if (hdr[i]['yDataType'] == 'Spectrum') or (
                hdr[i]['yDataType'] == 'Cross spectrum'):
            xlog = True  # Default scale for frequency is log
            if (hdr[i]['yUnit'][0:2] == 'dB') or (hdr[i]['yUnit'] == ''):
                ylog = False
            else:
                ylog = True

        # Transfer function
        if hdr[i]['yDataType'] == 'Transfer function':
            xlog = True
            if (hdr[i]['yUnit'][0:2] == 'dB') or (hdr[i]['yUnit'] == 'deg'):
                ylog = False
            else:
                ylog = True

        # Coherence
        if hdr[i]['yDataType'] == 'Coherence':
            xlog = True
            ylog = False

        # Time series
        if hdr[i]['yDataType'] == 'Time series':
            xlog = False
            ylog = False

        # Override the default scalings with the option specified ones
        if options.xlog is not None:
            xlog = options.xlog
        if options.ylog is not None:
            ylog = options.ylog

        if xlog:
            ax[i].set_xscale('log')
            ax[i].grid(True, which='minor', color=(0.6, 0.6, 0.7))
        if ylog:
            ax[i].set_yscale('log')
            ax[i].grid(True, which='minor', color=(0.6, 0.6, 0.7))

    plt.show()

    input('Press enter to quit:')
