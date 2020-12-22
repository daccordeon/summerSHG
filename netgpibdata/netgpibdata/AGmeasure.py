#!/usr/bin/env python
# Master AG4395 measurement script
# Eric Quintero - 2015

# Standard library imports
import AG4395A as inst
import matplotlib.pyplot as plt
import os
import sys
import time
import argparse

# Neccesary external libraries
import yaml
import numpy as np


def readParams(paramFile):
    # Function to read a measurement parameter file in the YAML format
    with open(paramFile, 'r') as f:
        reader = yaml.load_all(f, Loader=yaml.FullLoader)
        params = next(reader)
        reader.close()
    return(params)


def specPlot(dataArray, nDisp, params, legLabel, axlist):
    plotTitle = params.get('plotTitle', 'AG4395A Spectrum')
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

    if nDisp == 2:
        axlist[0].plot(dataArray[:, 0],
                       dataArray[:, 1],
                       label=legLabel + " (Ch1)")
        axlist[1].plot(dataArray[:, 0],
                       dataArray[:, 2],
                       label=legLabel + " (Ch2)")
        axlist[0].set_xscale(xScale)
        axlist[0].set_yscale(yScale)
        axlist[0].set_ylabel('Magnitude (' + params['dataMode'] + ')')
        axlist[1].set_xscale(xScale)
        axlist[1].set_yscale(yScale)
        axlist[1].set_xlabel('Freq. (Hz)')
        axlist[1].set_ylabel('Magnitude (' + params['dataMode'] + ')')
        axlist[0].set_title(plotTitle + ' - '
                            + time.strftime('%b %d %Y - %H:%M:%S',
                                            time.localtime()))
        axlist[0].axis('tight')
        axlist[1].axis('tight')
        axlist[0].grid('on', which='both')
        axlist[1].grid('on', which='both')
        axlist[0].legend()
        axlist[0].get_legend().get_frame().set_alpha(.7)
    else:
        axlist.plot(dataArray[:, 0], dataArray[:, 1], label=legLabel)
        axlist.set_xscale(xScale)
        axlist.set_yscale(yScale)
        axlist.set_xlabel('Freq. (Hz)')
        axlist.set_ylabel('Magnitude (' + params['dataMode'] + ')')
        axlist.set_title(plotTitle + ' - '
                         + time.strftime('%b %d %Y - %H:%M:%S',
                                         time.localtime()))
        axlist.axis('tight')
        axlist.grid('on', which='both')
        axlist.legend()
        axlist.get_legend().get_frame().set_alpha(.7)


def tfPlot(dataArray, params, legLabel, axlist):
    plotTitle = params.get('plotTitle', 'AG4395A TF')
    format = params['dataMode']
    if format.lower() == 'reim':
        Carray = dataArray[:, 1] + 1j * dataArray[:, 2]
    elif format.lower() == 'magdeg':
        Carray = dataArray[:, 1] * np.exp(1j * dataArray[:, 2] / 180.0 * np.pi)
    elif format.lower() == 'dbdeg':
        Carray = 10**(dataArray[:, 1] / 20.0) * np.exp(1j * dataArray[:, 2]
                                                       / 180.0 * np.pi)
    else:  # FIXME, what do I do if it doesn't match anything?
        print('Problem detecting units for plot... assuming dB, Degrees')
        Carray = 10**(dataArray[:, 1] / 20.0) * np.exp(1j * dataArray[:, 2]
                                                       / 180.0 * np.pi)

    axlist[0].plot(dataArray[:, 0],
                   20 * np.log10(np.abs(Carray)),
                   label=legLabel)
    axlist[1].plot(dataArray[:, 0],
                   np.angle(Carray, deg=True),
                   label=legLabel)

    axlist[0].set_xscale('log')
    axlist[0].set_ylabel('Magnitude (dB)')
    axlist[0].set_yscale('linear')
    axlist[1].set_xscale('log')
    axlist[1].set_xlabel('Freq. (Hz)')
    axlist[1].set_yscale('linear')
    axlist[1].set_ylabel('Phase (deg)')
    axlist[0].set_title(plotTitle + ' - '
                        + time.strftime('%b %d %Y - %H:%M:%S',
                                        time.localtime()))
    axlist[0].axis('tight')
    axlist[1].axis('tight')
    axlist[1].set_ylim((-180, 180))
    axlist[0].grid('on', which='both')
    axlist[1].grid('on', which='both')
    axlist[1].legend(loc=2)
    axlist[1].get_legend().get_frame().set_alpha(.7)


def main(paramFile=None, filename=None, ipAddress=None, gpibAddress=None,
         plotResult=None, plotRefs=None, leglabel=None, extraHeader=None,
         startFreq=None, stopFreq=None):
    try:
        if paramFile is None:
            # Set sensible defaults for downloading live data
            noParam = True
            params = {}
            params['nameRoot'] = 'AG4395A'
            params['saveDir'] = os.getcwd() + '/'
            params['plotRefs'] = False
            params['plotResult'] = False
            params['averages'] = 1
        else:
            noParam = False
            print('Reading parameters from ' + paramFile)
            params = readParams(paramFile)
            params['fileName'] = paramFile

        fileExt = '.txt'
        if filename is not None:
            params['nameRoot'] = filename.split('.')[0]
            # awade 20171106: added case no saveDir for full path saves from
            # cmd
            if params['saveDir'] == 'NaN':
                params['saveDir'] = os.path.dirname(filename) + '/'
                params['nameRoot'] = os.path.basename(filename).split('.')[0]
                print(params['saveDir'])
                print(params['nameRoot'])
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
        if startFreq is not None:
            params['startFreq'] = startFreq
        if stopFreq is not None:
            params['stopFreq'] = stopFreq

        gpibObj = inst.connectGPIB(params['ipAddress'], params['gpibAddress'])

        # Set up output file names
        params['timeStamp'] = time.strftime('%b %d %Y - %H:%M:%S',
                                            time.localtime())
        fileRoot = (params['nameRoot'] + '_'
                    + time.strftime('%d-%m-%Y', time.localtime())
                    + time.strftime('_%H%M%S', time.localtime()))
        dataFileName = fileRoot + fileExt
        # Craig Cahillane - 20170829.  Below expands '~' into home dir
        outDir = os.path.expanduser(params['saveDir'])
        # Check if outDir exists
        if not os.path.exists(outDir):
            os.makedirs(outDir)

        # If new measurement is requested, do it!
        if noParam is False:
            print('Executing measurement specified in ' + paramFile)
            inst.setParameters(gpibObj, params)
            inst.measure(gpibObj, params)
        else:  # What kind of measurement are we doing?
            params['measType'] = {1: 'TF', 0: 'Spectrum'}[
                int(gpibObj.query('NA?'))]

        nDisp = int(gpibObj.query('DUAC?')) + 1
        if nDisp == 1:
            chans = [int(gpibObj.query('CHAN2?')) + 1]
        else:
            chans = [1, 2]

        meas = []
        fmt = []
        for chan in chans:
            gpibObj.command('CHAN' + str(chan))
            # What measurement?
            meas.append(gpibObj.query('MEAS?')[:-1])
            fmt.append(gpibObj.query('FMT?')[:-1])

        if params['measType'] == 'Spectrum':
            # Doesn't handle channels being in different units...
            params['dataMode'] = (gpibObj.query('SAUNIT?')[:-1])
            if 'NOISE' in fmt:
                params['dataMode'] += '/rtHz'

        elif params['measType'] == 'TF':
            # What if channel 1 and 2 are swapped from the expected placement?
            if fmt == ['LOGM', 'PHAS']:
                params['dataMode'] = 'dbdeg'
            elif fmt == ['LINM', 'PHAS']:
                params['dataMode'] = 'magdeg'
            elif fmt == ['REAL', 'IMAG']:
                params['dataMode'] = 'reim'
            else:
                params['dataMode'] = str(fmt)
                if params['plotResult'] is True:
                    print("No plot routined exists for "
                          "data format, will skip plotting")
                    params['plotResult'] = False

        print('Detected Units: ' + params['dataMode'])

        # Let the instrument catch up, then download the data
        time.sleep(2)
        (freq, data) = inst.download(gpibObj)

        # Done measuring! Just output file writing and plotting below
        print('Saving files to ' + outDir)
        print('Measurement data will be written into ' + outDir + dataFileName)

        with open(outDir + dataFileName, 'w') as dataFile:
            # In case extra experiment details are provided
            if extraHeader is not None:
                dataFile.write('# ' + extraHeader + '\n')
            inst.writeHeader(dataFile, params['timeStamp'])

            if noParam is False:
                dataFile.write('# Parameter File: ' + params['fileName']
                               + '\n')

            inst.writeParams(gpibObj, dataFile)
            inst.writeData(dataFile, freq, data)

        print("Done!")
        gpibObj.close()

        if params['plotResult'] is True:
            print('Plotting!')
            dataArray = np.transpose(np.vstack((np.array(freq[0],
                                                         dtype='float'),
                                                np.array(data,
                                                         dtype='float'))))

            f, axlist = plt.subplots(nrows=len(data), ncols=1, sharex=True)

            # Plot references if desired
            if params['plotRefs'] is True:
                # Get list of files with the same nameRoot
                refFiles = [rf for rf in os.listdir(params['refDir'])
                            if (params['nameRoot'] in rf
                                and '.txt' in rf
                                and rf != dataFileName)]
                # todo: the above line needs tidying up into more obvious form
                print('Found ' + str(len(refFiles))
                      + ' references; plotting...')

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
                                    legendLine = ''.join(
                                        line.split('Memo:')[1:])
                                    foundLine = True
                                elif 'Timestamp:' in line:
                                    legendLine = ''.join(line.split(
                                        'Timestamp:')[1:])
                                    foundLine = True
                        if foundLine is False:
                            legendLine = filename

                    if params['measType'] == 'Spectrum':
                        specPlot(
                            refArray, len(data), params, legendLine, axlist)
                    elif params['measType'] == 'TF':
                        tfPlot(refArray, params, legendLine, axlist)

            if leglabel is None:
                leglabel = params['timeStamp']
            if params['measType'] == 'Spectrum':
                specPlot(dataArray, len(data), params, leglabel, axlist)
            elif params['measType'] == 'TF':
                tfPlot(dataArray, params, leglabel, axlist)

            f.set_size_inches(11, 8)
            if params['saveFig'] is True:
                f.savefig(outDir + fileRoot + '.pdf', format='pdf')
            try:
                plt.show()
            except Exception:
                print('Failed to show plot! X11 problem?')
        return outDir + dataFileName
    except KeyboardInterrupt:
        try:
            print()
            print('Control-C detected.  Handling exit...')
            print('Resetting analyzer.  This takes 12 seconds.')
            inst.reset(gpibObj)
            print('Closing gpibObj')
            gpibObj.close()
        except NameError:
            print('Variable gpibObj not defined.  Analyzer not reset.')
        finally:
            return 'Control-C'


if __name__ == "__main__":

    # Set location of template files, should live with the script
    scriptPath = os.path.dirname(os.path.realpath(__file__))
    SPtemplateFile = scriptPath + '/SPAG4395Atemplate.yml'
    TFtemplateFile = scriptPath + '/TFAG4395Atemplate.yml'

    class helpfulParser(argparse.ArgumentParser):
        def error(self, message):
            sys.stderr.write('Error: {s}\n'.format(s=message))
            self.print_help()
            sys.exit(2)

    parser = helpfulParser()
    group = parser.add_mutually_exclusive_group()

    group.add_argument('paramFile',
                       nargs='?',
                       help='The parameter file for the measurement.',
                       default=None)

    parser.add_argument('-i',
                        '--ipaddress',
                        help='IP address or hostname. Overrides param file.',
                        default=None)

    parser.add_argument('-a',
                        '--gpibaddress',
                        help='GPIB address, typically 10.'
                             'Overrides parameter file.',
                        default=10)

    parser.add_argument('-f',
                        '--filename',
                        help='Stem of output filename.'
                             ' Overrides parameter file.',
                        default=None)

    parser.add_argument('-l',
                        '--leglabel',
                        help='Legend label for measured trace. '
                             'Overrides parameter file.',
                        default=None)

    group.add_argument('--template',
                       help='Copy template parameter files to '
                            'current dir; no measurement is made.',
                       action='store_true')

    group.add_argument('--reset',
                       help='Resets the AG4396, IP and GPIB address '
                            'are required.',
                       action='store_true')

    group.add_argument('--getdata',
                       help='Downloads live data from an AG4395A. '
                       'IP and GPIB address are required.',
                       action='store_true')

    group.add_argument('--trigger',
                       help='Trigger a single sweep of the '
                       'currently configured measurement. IP and GPIB address '
                       'are required.',
                       action='store_true')

    group.add_argument('--monit',
                       help='Live plotting of the active display, '
                       'IP and GPIB address are required.',
                       action='store_true')

    parser.add_argument('--plot',
                        help='Plot result of measurement. Overrides '
                        'parameter file.', action='store_true',
                        default=None)

    parser.add_argument('--plotRefs',
                        help='Plot reference traces. Overrides '
                        'parameter file. Reads files that have the same '
                        'filename stem as references.',
                        action='store_true',
                        default=None)
    parser.add_argument('--extraHeader', type=str,
                        help='Provides option of adding any additional '
                             'experimental detail on top of measurement file. '
                             'Must be a single string.',
                        default=None)
    parser.add_argument('--startFreq',
                        help='Start Frequency of measurement.'
                             'Overrides parameter file.',
                        default=None)
    parser.add_argument('--stopFreq',
                        help='Stop Frequency of measurement.'
                             'Overrides parameter file.',
                        default=None)

    args = parser.parse_args()

    if args.paramFile is not None:
        main(args.paramFile, args.filename, args.ipaddress, args.gpibaddress,
             args.plot, args.plotRefs, args.leglabel, args.extraHeader,
             startFreq=args.startFreq, stopFreq=args.stopFreq)

    elif args.template:
        import shutil
        print('Copying ' + SPtemplateFile + ' to ' + os.getcwd())
        shutil.copyfile(SPtemplateFile, os.getcwd() + '/SPAG4395Atemplate.yml')
        print('Copying ' + TFtemplateFile + ' to ' + os.getcwd())
        shutil.copyfile(TFtemplateFile, os.getcwd() + '/TFAG4395Atemplate.yml')
        print('Done!')

    elif args.ipaddress is None or args.gpibaddress is None:
        parser.error('Must specify IP and GPIB addresses!\n')

    elif args.getdata:
        main(None, args.filename, args.ipaddress, args.gpibaddress,
             args.plot, args.plotRefs, args.leglabel, args.extraHeader,
             startFreq=args.startFreq, stopFreq=args.stopFreq)

    elif args.reset:
        gpibObj = inst.connectGPIB(args.ipaddress, args.gpibaddress)
        inst.reset(gpibObj)
        gpibObj.close()

    elif args.trigger:
        gpibObj = inst.connectGPIB(args.ipaddress, args.gpibaddress)
        gpibObj.command('SING')
        gpibObj.close()
