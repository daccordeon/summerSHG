# !/usr/bin/env python
# Master SR785 measurement script
# Eric Quintero - 2014
'''
Modifier: Anchal Gupta
Date: 7/24/19
Modified SRMeasure script to make multiple spectrum measurements ensuring
least linewidth at each point.
First spectrum will be taken with specified startFreq and spanFreq.
If the stopFreq (default=102.4kHz) has not reached, next spectrum will be
started at lastlinewidth+laststopFreq and with 2*lastspanFreq.
This will be continued until stopFreq is reached.

'''
# Standard library imports
import os
import sys
import time
import argparse

# Neccesary external libraries
import yaml
import numpy as np
import matplotlib.pyplot as plt

# Custom libaries
import SR785 as inst


def readParams(paramFile):
    # Function to read a measurement parameter file in the YAML format
    with open(paramFile, 'r') as f:
        reader = yaml.load_all(f)
        params = next(reader)
        reader.close()
    return(params)


def specPlot(dataArray, nDisp, params, legLabel, axlist):
    plotTitle = params.get('plotTitle', 'SR785 Spectrum')
    if nDisp == 2:
        axlist[0].plot(dataArray[:, 0], dataArray[:, 1],
                       label=legLabel + " (Ch1)")
        axlist[1].plot(dataArray[:, 0], dataArray[:, 2],
                       label=legLabel + " (Ch2)")
        axlist[0].set_xscale('log')
        axlist[0].set_ylabel('Magnitude (' + params['dataMode'] + ')')
        axlist[0].set_yscale('log')
        axlist[1].set_xscale('log')
        axlist[1].set_xlabel('Freq. (Hz)')
        axlist[1].set_yscale('log')
        axlist[1].set_ylabel('Magnitude (' + params['dataMode'] + ')')
        axlist[0].set_title(
            plotTitle + ' - ' +
            time.strftime('%b %d %Y - %H:%M:%S', time.localtime()))
        axlist[0].axis('tight')
        axlist[1].axis('tight')
        axlist[0].grid('on', which='both')
        axlist[1].grid('on', which='both')
        axlist[0].legend()
        axlist[0].get_legend().get_frame().set_alpha(.7)
    else:
        axlist.plot(dataArray[:, 0], dataArray[:, 1], label=legLabel)
        axlist.set_xscale('log')
        axlist.set_xlabel('Freq. (Hz)')
        axlist.set_ylabel('Magnitude (' + params['dataMode'] + ')')
        axlist.set_yscale('log')
        axlist.set_title(
            params['plotTitle'] + ' - ' +
            time.strftime('%b %d %Y - %H:%M:%S', time.localtime()))
        axlist.axis('tight')
        axlist.grid('on', which='both')
        axlist.legend()
        axlist.get_legend().get_frame().set_alpha(.7)


def value_suffix_to_multiplier(value):
    '''
    This function reads the suffix letter in given word representing value and
    gives the factor to multiply to come to SI unit.
    Ex: '100m' -> 100*1.0e-3 '5n' -> 5n1.0e-9 etc
    '''
    try:
        return {
            'f': 1.0e-15,
            'p': 1.0e-12,
            'n': 1.0e-9,
            'u': 1.0e-6,
            'm': 1.0e-3,
            'k': 1.0e3,
            'M': 1.0e6,
            'G': 1.0e9,
            'T': 1.0e12
        }[value[-1]] * float(value[0:-1])
    except BaseException:
        try:
            return float(value)
        except BaseException:
            print(('Could not understand the output value ' + value))


def freqStrToFloat(freqstr):
    return value_suffix_to_multiplier(freqstr.split('Hz')[0])


def ftoss(value):
    sgn = np.sign(value)
    if sgn == 0:
        return '0'
    else:
        absv = np.abs(value)
        ex = np.minimum(12, np.maximum(-15, np.floor(np.log10(absv))))
        sv = absv / (10**ex)
        sc = str(int(np.floor(ex / 3)))
        unit = {
            '-5': 'f',
            '-4': 'p',
            '-3': 'n',
            '-2': 'u',
            '-1': 'm',
            '0': '',
            '1': 'k',
            '2': 'M',
            '3': 'G',
            '4': 'T'
        }[sc]
        val = str(sgn * sv * 10**(ex % 3))
        return val + unit


def main(paramFile=None, filename=None, ipAddress=None, gpibAddress=None,
         plotResult=None, plotRefs=None, leglabel=None, stopFreq=102.4e3,
         extraHeader=None):
    try:
        if paramFile is None:
            print('paramFile is required. If you just want to take data')
            print('from the screen, use SRMeasure --getdata')
            sys.exit()
        else:
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
        if params['measType'] == 'TF':
            print('TF measurement is not supported in this script. Use ')
            print('SRmeasure for measuring TF.')
            sys.exit()
        gpibObj = inst.connectGPIB(params['ipAddress'], params['gpibAddress'])

        # Set up output file names

        fileRoot = (params['nameRoot'] + '_' +
                    time.strftime('%d-%m-%Y', time.localtime()) +
                    time.strftime('_%H%M%S', time.localtime()))
        dataFileName = fileRoot + fileExt
        # Craig Cahillane - 20170829.  Expands '~' into home dir
        outDir = os.path.expanduser(params['saveDir'])
        # Check if outDir exists
        if not os.path.exists(outDir):
            os.makedirs(outDir)

        # Creating measurement set
        measSet = []
        firstSet = [params['startFreq'], params['spanFreq']]
        lastspanFreq = freqStrToFloat(params['spanFreq'])
        laststopFreq = freqStrToFloat(params['startFreq']) + lastspanFreq
        measSet += [firstSet]
        while(laststopFreq < stopFreq):
            newStartFreq = ftoss(laststopFreq) + 'Hz'
            newSpanFreq = ftoss(2 * lastspanFreq) + 'Hz'
            measSet += [[newStartFreq, newSpanFreq]]
            lastspanFreq = freqStrToFloat(newSpanFreq)
            laststopFreq = freqStrToFloat(newStartFreq) + lastspanFreq
        # If new measurement is requested, do it!
        print(('Executing measurement specified in ' + paramFile))
        print(('Files will be saved to ' + outDir))
        print(('Measurement data will be written into ' + outDir + dataFileName))
        concFreq = np.zeros(0)
        if params['dualChannel'] == 'Single':
            concData = np.zeros(0)
            nCh = 1
        else:
            concData = np.zeros((0, 2))
            nCh = 2
        lastStopFreq = -1
        for set in measSet:
            params['startFreq'] = set[0]
            params['spanFreq'] = set[1]
            params['timeStamp'] = time.strftime('%b %d %Y - %H:%M:%S',
                                                time.localtime())
            print(('Doing measurement from ' + params['startFreq'] + ' with'
                  ' span ' + params['spanFreq'] + '...'))
            inst.setParameters(gpibObj, params)
            inst.measure(gpibObj, params['measType'])
            # Let the instrument catch up, then download the data
            time.sleep(2)
            (freq, data) = inst.download(gpibObj)
            freqarr = np.transpose(np.array(freq[0], dtype='float'))
            for ind in range(len(freqarr)):
                if freqarr[ind] > lastStopFreq:
                    clipInd = ind
                    break
            freqarr = freqarr[clipInd:]
            lastStopFreq = freqarr[-1]
            if params['dualChannel'] == 'Single':
                dataarr = np.transpose(np.array(data[0],
                                                dtype='float'))[clipInd:]
            else:
                dataarr = np.transpose(np.vstack((
                    np.array(data[0], dtype='float'),
                    np.array(data[1], dtype='float'))))[clipInd:, :]
            concFreq = np.concatenate((concFreq, freqarr))
            concData = np.concatenate((concData, dataarr))
            with open(outDir + dataFileName, 'a') as dataFile:
                # In case extra experiment details are provided
                if extraHeader is not None:
                    dataFile.write('# ' + extraHeader +'\n')
                inst.writeHeader(dataFile, params['timeStamp'])
                dataFile.write(
                    '# Parameter File: ' +
                    params['fileName'] +
                    '\n')
                inst.writeParams(gpibObj, dataFile)
                if params['dualChannel'] == 'Single':
                    inst.writeData(dataFile,
                                   [freq[0][clipInd:]],
                                   [data[0][clipInd:]])
                else:
                    inst.writeData(dataFile,
                                   [freq[0][clipInd:], freq[1][clipInd:]],
                                   [data[0][clipInd:], data[1][clipInd:]])
        print("Done!")
        gpibObj.close()

        if params['plotResult'] is True:
            print('Plotting!')
            if params['dualChannel'] == 'Single':
                dataArray = np.transpose(np.vstack((np.array(concFreq,
                                                             dtype='float'),
                                                    np.array(concData,
                                                             dtype='float'))))
            else:
                dataArray = np.transpose(np.vstack((np.array(concFreq,
                                                             dtype='float'),
                                                    np.array(concData[:, 0],
                                                             dtype='float'),
                                                    np.array(concData[:, 1],
                                                             dtype='float'))))
            # dataArray = np.concatenate((concFreq, concData), axis=1)
            f, axlist = plt.subplots(nrows=nCh, ncols=1, sharex=True)

            # Plot references if desired
            if params['plotRefs'] is True:
                # Get list of files with the same nameRoot
                refFiles = [rf for rf in os.listdir(params['refDir'])
                            if (params['nameRoot'] in rf and '.txt' in rf and
                                rf != dataFileName)]
                print(('Found ' + str(len(refFiles)) + ' references;'
                      ' plotting...'))

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
                                    legendLine = ''.join(
                                        line.split(
                                            'Timestamp:')[1:])
                                    foundLine = True
                        if foundLine is False:
                            legendLine = filename

                    specPlot(refArray, nCh, params,
                             legendLine, axlist)

            if leglabel is None:
                leglabel = params['timeStamp']
            specPlot(dataArray, nCh, params, leglabel,
                     axlist)

            f.set_size_inches(17, 11)
            if params['saveFig'] is True:
                f.savefig(outDir + fileRoot + '.pdf', format='pdf')
            try:
                plt.show()
            except BaseException:
                print('Failed to show plot! X11 problem?')
        return outDir + dataFileName
    # if user presses Control-C, handle exit gracefully
    except KeyboardInterrupt:
        try:
            print('')
            print('Control-C detected.  Handling exit...')
            print('Resetting analyzer.  This takes 12 seconds.')
            inst.reset(gpibObj)
            print('Closing gpibObj')
            gpibObj.close()
        except NameError:
            print('Variable gpibObj not defined.  Analyzer not reset.')


if __name__ == "__main__":

    # Set location of template files, should live with the script
    scriptPath = os.path.dirname(os.path.realpath(__file__))
    SPtemplateFile = scriptPath + '/SPSR785template.yml'
    TFtemplateFile = scriptPath + '/TFSR785template.yml'

    class helpfulParser(argparse.ArgumentParser):
        def error(self, message):
            sys.stderr.write('Error: %s\n' % message)
            self.print_help()
            sys.exit(2)

    parser = helpfulParser(
        description="This script runs multiple spectrum measurements from"
                    "startFreq to stopFreq(default 102.4kHz) with different"
                    "spans starting from spanFreq")
    group = parser.add_mutually_exclusive_group()

    group.add_argument('paramFile', nargs='?',
                       help='The parameter file for the measurement.',
                       default=None)

    parser.add_argument('-i', '--ipaddress', help='IP address or hostname. '
                        'Overrides parameter file.', default=None)

    parser.add_argument('-a', '--gpibaddress', help='GPIB address, typically'
                        '10. Overrides parameter file.', default=10)

    parser.add_argument('--stopFreq', help='Stop Frequency of spectrum'
                        'Default 102.4kHz.', type=float, default=102.4e3)

    parser.add_argument('-f', '--filename', help='Stem of output filename.'
                        'Overrides parameter file.', default=None)

    parser.add_argument('-l', '--leglabel', help='Legend label for measured'
                        'trace. Overrides parameter file.', default=None)

    group.add_argument('--template', help='Copy template parameter files to'
                       ' current dir; no measurement is made.',
                       action='store_true')

    group.add_argument('--reset', help='Resets an SR785, IP and GPIB address'
                       ' are required.', action='store_true')

    parser.add_argument('--plot', help='Plot result of measurement. Overrides'
                        ' parameter file.', action='store_true', default=None)

    parser.add_argument('--plotRefs', help='Plot reference traces. Overrides'
                        ' parameter file. Reads files that have the same'
                        ' filename stem as references.', action='store_true',
                        default=None)
    args = parser.parse_args()

    if args.paramFile is not None:
        main(args.paramFile, args.filename, args.ipaddress, args.gpibaddress,
             args.plot, args.plotRefs, args.leglabel, args.stopFreq,
             extraHeader=args.extraHeader)

    elif args.template:
        import shutil
        print(('Copying ' + SPtemplateFile + ' to ' + os.getcwd()))
        shutil.copyfile(SPtemplateFile, os.getcwd() + '/SPSR785template.yml')
        print(('Copying ' + TFtemplateFile + ' to ' + os.getcwd()))
        shutil.copyfile(TFtemplateFile, os.getcwd() + '/TFSR785template.yml')
        print('Done!')

    elif args.ipaddress is None or args.gpibaddress is None:
        parser.error('Must specify IP and GPIB addresses!\n')

    elif args.reset:
        gpibObj = inst.connectGPIB(args.ipaddress, args.gpibaddress)
        inst.reset(gpibObj)
        gpibObj.close()
