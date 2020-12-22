#!/usr/bin/env python
# Master AG4395 measurement script
# Eric Quintero - 2015

# Standard library imports
import os
import sys
import time
import argparse

# Neccesary external libraries
import yaml
import numpy as np
#import matplotlib.pyplot as plt

# Custom libaries
import HP8591E as inst


def readParams(paramFile):
    # Function to read a measurement parameter file in the YAML format
    with open(paramFile, 'r') as f:
        reader = yaml.load_all(f, Loader=yaml.FullLoader)
        params = next(reader)
        reader.close()
    return(params)


def specPlot(dataArray, nDisp, params, legLabel, axlist):
    plotTitle = params.get('plotTitle', 'HP8591E Spectrum')
    plotScales = params.get('plotScales', None)

    if plotScales is None:
        if 'db' in params['dataMode'].lower():
            xScale = 'linear'
            yScale = 'linear'
        else:
            xScale = 'log'
            yScale = 'log'
    else:
        (xScale, yScale) = plotScales.split(',')

    axlist.plot(dataArray[:, 0], dataArray[:, 1], label=legLabel)
    axlist.set_xscale(xScale)
    axlist.set_yscale(yScale)
    axlist.set_xlabel('Freq. (Hz)')
    axlist.set_ylabel('Magnitude (' + params['dataMode'] + ')')
    axlist.set_title(plotTitle + ' - ' +
                     time.strftime('%b %d %Y - %H:%M:%S', time.localtime()))
    axlist.axis('tight')
    axlist.grid('on', which='both')
    axlist.legend()
    axlist.get_legend().get_frame().set_alpha(.7)


def main(paramFile=None, filename=None, ipAddress=None, gpibAddress=None,
         plotResult=None, plotRefs=None):
    if paramFile is None:
        # Set sensible defaults for downloading live data
        noParam = True
        params = {}
        params['nameRoot'] = 'HP8591E'
        params['saveDir'] = os.getcwd() + '/'
        params['plotRefs'] = False
        params['plotResult'] = False
        params['averages'] = 1
    else:
        noParam = False
        print(('Reading parameters from ' + paramFile))
        params = readParams(paramFile)
        params['fileName'] = paramFile

    fileExt = '.txt'
    if filename is not None:
        params['nameRoot'] = filename.split('.')[0]
        if '.' in filename:
            fileExt = ''.join(filename.split('.')[1:])
    if ipAddress is not None:
        params['ipAddress'] = ipAddress
    if gpibAddress is not None:
        params['gpibAddress'] = gpibAddress
    if plotResult is not None:
        params['plotResult'] = plotResult
        params['saveFig'] = True
    if plotRefs is not None:
        params['plotRefs'] = plotRefs
        params['refDir'] = os.getcwd() + '/'

    gpibObj = inst.connectGPIB(params['ipAddress'], params['gpibAddress'])

    # Set up output file names
    params['timeStamp'] = time.strftime(
        '%b %d %Y - %H:%M:%S', time.localtime())
    fileRoot = (params['nameRoot'] + '_' +
                time.strftime('%d-%m-%Y', time.localtime()) +
                time.strftime('_%H%M%S', time.localtime()))
    dataFileName = fileRoot + fileExt

    # Craig Cahillane - 20170829.
    outDir = os.path.expanduser(params['saveDir'])
    # Check if outDir exists
    if not os.path.exists(outDir):
        os.makedirs(outDir)
    # If new measurement is requested, do it!
    if noParam is False:
        print('Executing measurement specified in ' + paramFile)
        inst.setParameters(gpibObj, params)
        inst.measure(gpibObj, params)

    params['measType'] = 'Spectrum'
    params['dataMode'] = (gpibObj.query('AUNITS?')[:-2])

    print('Detected Units: ' + params['dataMode'])

    # Let the instrument catch up, then download the data
    time.sleep(2)
    (freq, data) = inst.download(gpibObj)

    # Done measuring! Just output file writing and plotting below
    print(('Saving files to ' + outDir))
    print(('Measurement data will be written into ' + outDir + dataFileName))

    with open(outDir + dataFileName, 'w') as dataFile:
        inst.writeHeader(dataFile, params['timeStamp'])

        if noParam is False:
            dataFile.write('# Parameter File: '
                           + params['fileName'] + '\n')

        inst.writeParams(gpibObj, dataFile)
        inst.writeData(dataFile, freq, data)

    print("Done!")
    gpibObj.close()

    if params['plotResult'] is True:
        print('Plotting!')
        dataArray = np.transpose(np.vstack((np.array(freq, dtype='float'),
                                            np.array(data, dtype='float'))))

        f, axlist = plt.subplots(nrows=1, ncols=1, sharex=True)

        # Plot references if desired
        if params['plotRefs'] is True:
            # Get list of files with the same nameRoot
            refFiles = [rf for rf in os.listdir(params['refDir'])
                        if (params['nameRoot'] in rf and '.txt' in rf and
                            rf != dataFileName)]
            print('Found ' + str(len(refFiles)) + ' references; plotting...')

            # Plot each reference in order
            refFiles.sort()
            for filename in refFiles:
                refArray = np.loadtxt(params['refDir'] + filename)

                # Find memo or timestamp of Ref for the legend
                with open(params['refDir'] + filename, 'r') as rf:
                    foundLine = False
                    for line in rf:
                        if foundLine is False:
                            if 'Memo:' in line:
                                legendLine = ''.join(line.split('Memo:')[1:])
                                foundLine = True
                            elif 'Timestamp:' in line:
                                legendLine = ''.join(
                                    line.split('Timestamp:')[1:])
                                foundLine = True
                    if foundLine is False:
                        legendLine = filename

                specPlot(refArray, len(data), params, legendLine, axlist)

        specPlot(dataArray, len(data), params, params['legendLine'], axlist)

        f.set_size_inches(11, 8)
        if params['saveFig'] is True:
            f.savefig(outDir + fileRoot + '.pdf', format='pdf')
        try:
            plt.show()
        except BaseException:
            print('Failed to show plot! X11 problem?')


if __name__ == "__main__":

    # Set location of template files, should live with the script
    scriptPath = os.path.dirname(os.path.realpath(__file__))
    SPtemplateFile = scriptPath + '/SPHP8591Etemplate.yml'

    class helpfulParser(argparse.ArgumentParser):
        def error(self, message):
            sys.stderr.write('Error: %s\n' % message)
            self.print_help()
            sys.exit(2)

    parser = helpfulParser()
    group = parser.add_mutually_exclusive_group()

    group.add_argument('paramFile', nargs='?',
                       help='The parameter file for the measurement.',
                       default=None)

    parser.add_argument('-i', '--ipaddress', help='IP address or hostname. '
                        'Overrides parameter file.', default=None)

    parser.add_argument('-a', '--gpibaddress', help='GPIB address, typically'
                        '10. Overrides parameter file.', default=10)

    parser.add_argument('-f', '--filename', help='Stem of output filename.'
                        'Overrides parameter file.', default=None)

    group.add_argument('--template', help='Copy template parameter file to'
                       ' current dir; no measurement is made.',
                       action='store_true')

    group.add_argument('--reset', help='Resets the HP8591E, IP and GPIB address'
                       ' are required.', action='store_true')

    group.add_argument('--getdata', help='Downloads live data from a HP8591E.'
                       ' IP and GPIB address are required.',
                       action='store_true')

    group.add_argument('--peak', help='Zoom span to a peak above 10MHz',
                       action='store_true')

    group.add_argument('--trigger', help='Trigger a single sweep of the '
                       'currently configured measurement. IP and GPIB address '
                       'are required.', action='store_true')

    parser.add_argument('--plot', help='Plot result of measurement. Overrides'
                        ' parameter file.', action='store_true', default=None)

    parser.add_argument('--plotRefs', help='Plot reference traces. Overrides'
                        ' parameter file. Reads files that have the same'
                        ' filename stem as references.', action='store_true',
                        default=None)

    args = parser.parse_args()

    if args.paramFile is not None:
        main(args.paramFile, args.filename, args.ipaddress, args.gpibaddress,
             args.plot, args.plotRefs)

    elif args.template:
        import shutil
        print('Copying ' + SPtemplateFile + ' to ' + os.getcwd())
        shutil.copyfile(SPtemplateFile, os.getcwd() + '/SPHP8591Etemplate.yml')
        print('Done!')

    elif args.ipaddress is None or args.gpibaddress is None:
        parser.error('Must specify IP and GPIB addresses!\n')

    elif args.getdata:
        main(None, args.filename, args.ipaddress, args.gpibaddress,
             args.plot, args.plotRefs)

    elif args.reset:
        gpibObj = inst.connectGPIB(args.ipaddress, args.gpibaddress)
        inst.reset(gpibObj)
        gpibObj.close()

    elif args.trigger:
        gpibObj = inst.connectGPIB(args.ipaddress, args.gpibaddress)
        gpibObj.command('CONTS;SNGLS')
        gpibObj.close()

    elif args.peak:
        gpibObj = inst.connectGPIB(args.ipaddress, args.gpibaddress)
        inst.peakZoom(gpibObj)
        gpibObj.close()
