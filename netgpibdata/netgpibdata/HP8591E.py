# This module provides data access to Agilent 4395 network analyzer

# Standard Library imports
import time
# Third-party libraries
from numpy import linspace
# Required custom libraries
import netgpib


####################
# GPIB
####################


def connectGPIB(ipAddress, gpibAddress):
    print('Connecting to ' + str(ipAddress) + ':' + str(gpibAddress) + '...', end=' ')
    gpibObj = netgpib.netGPIB(ipAddress, gpibAddress)
    print('Connected.')
    print("Instrument ID: ", end=' ')
    idnString = gpibObj.query("ID?")
    print(idnString.splitlines()[-1])
    return(gpibObj)


####################
# Settings helpers
####################

def reset(gpibObj):
    print('Resetting HP8591E...')
    gpibObj.command('IP')
    gpibObj.command('FA 0MHz')
    gpibObj.command('FB 250MHz')
    gpibObj.command('CONTS')
    gpibObj.command('RB 300kHz')
    print('Done!')


def peakZoom(gpibObj):
    print('Zooming to Min 10kHz Span. Peak must be above 10MHz!')
    gpibObj.command('FA 10MHz')
    gpibObj.command('RB AUTO')
    gpibObj.command('VAVG 5')
    gpibObj.command('VB AUTO')
    gpibObj.command('RQS 4')
    span = float(gpibObj.query('SPAN?')[:-2])
    while span >= 10000.0:

        gpibObj.command('CONTS;SNGLS')
        gpibObj.command('CLS')
        gpibObj.command('CLRAVG')  # Doesn't work?
        gpibObj.command('TS')

        while not int(gpibObj.srq()):
            time.sleep(1)

        gpibObj.command('MKPK HI')
        peakF = gpibObj.query('MKF?')[:-2]
        gpibObj.command('CF ' + peakF)

        if float(peakF) - span / 2.0 < 10e6:
            span = (float(peakF) - float(gpibObj.query('FA?'))) / 2.0
        else:
            span /= 2.0

        gpibObj.command('SPAN ' + str(span))
        span = float(gpibObj.query('SPAN?')[:-2])
        time.sleep(1)

    print('Done!')
    gpibObj.command('VAVG 25')


####################
# Compatibility with old netgpibdata script
####################


def getdata(gpibObj, dataFile, paramFile):
    # For compatibility with old netgpibdata
    timeStamp = time.strftime('%b %d %Y - %H:%M:%S', time.localtime())
    (freq, data) = download(gpibObj)
    writeHeader(dataFile, timeStamp)
    writeData(dataFile, freq, data, delimiter=', ')


def getparam(gpibObj, fileRoot, dataFile, paramFile):
    # For compatibility with old netgpibdata
    timeStamp = time.strftime('%b %d %Y - %H:%M:%S', time.localtime())
    writeHeader(paramFile, timeStamp)
    writeParams(gpibObj, paramFile)


####################
# Fetching data
####################


def download(gpibObj):

    print('Downloading Data...')
    gpibObj.command('TDF P')
    data = [float(val) for val in gpibObj.query('TRA?')[:-2].split(',')]

    freqLo = float(gpibObj.query('FA?'))
    freqHi = float(gpibObj.query('FB?'))
    freqs = list(linspace(freqLo, freqHi, num=len(data)))

    return(freqs, data)


####################
# Output file writing
####################


def writeHeader(dataFile, timeStamp):
    dataFile.write('# HP8591E Measurement - Timestamp: ' + timeStamp + '\n')


def writeData(dataFile, freq, data, delimiter='    '):
    print('Writing measurement data to file...')
    # Write data vectors
    for i in range(len(freq)):
        dataFile.write(str(freq[i]) + delimiter + str(data[i]) + '\n')

####################
# Run measurements
####################


def measure(gpibObj, params):
    print('Triggering measurement!')
    # Clear status bits, only ask for sweep end events
    gpibObj.command('RQS 4')
    gpibObj.command('CONTS;SNGLS')
    gpibObj.command('CLS')
    gpibObj.command('CLRAVG')  # Doesn't work?
    gpibObj.command('TS')

    while not int(gpibObj.srq()):
        time.sleep(1)
    print('Done!')


####################
# Saving and setting measurement parameters
####################


def setParameters(gpibObj, params):
    gpibObj.command('IP')
    gpibObj.command('SNGLS')
    gpibObj.command('AUNITS ' + str(params['dataMode']))
    gpibObj.command('VAVG ' + str(params['averages']))
    gpibObj.command('VB AUTO')
    gpibObj.command('FA ' + params['startFreq'])
    gpibObj.command('FB ' + params['stopFreq'])
    gpibObj.command('RB ' + str(params['resBW']))
    gpibObj.command('AT ' + str(params['attenuation']))

    print('Parameters set!')


def writeParams(gpibObj, paramFile):

    # Get bandwidth information
    bw = str(float(gpibObj.query('RB?')))
    unit = gpibObj.query('AUNITS?')[:-2]
    fStart = str(float(gpibObj.query('FA?')))
    fStop = str(float(gpibObj.query('FB?')))

    # Get attenuator information
    att = str(int(gpibObj.query('AT?'))) + 'dB '

    # Averages
    nAvg = str(int(gpibObj.query('VAVG?')))

    print("Writing to the parameter file.")

    paramFile.write('#---------- Measurement Parameters ------------\n')
    paramFile.write('# Start Frequency (Hz): ' + fStart + '\n')
    paramFile.write('# Stop Frequency (Hz): ' + fStop + '\n')
    paramFile.write('# Measurement Units: ' + unit + '\n')

    paramFile.write('#---------- Analyzer Settings ----------\n')
    paramFile.write('# Number of Averages: ' + nAvg + '\n')
    paramFile.write('# Resolution Bandwidth: ' + bw + '\n')
    paramFile.write('# Input Attenuator: ' + att + '\n')

    paramFile.write('#---------- Measurement Data ----------\n')
    paramFile.write('# [Freq(Hz) Spectrum(' + unit + ')]\n')
