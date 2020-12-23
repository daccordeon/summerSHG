# This module provides data access to Agilent 4395 network analyzer
# Standard Library imports
import re
from numpy import logspace, log10
import time
# Required custom libraries
import netgpib


####################
# GPIB
####################


def connectGPIB(ipAddress, gpibAddress):
    print('Connecting to ' + str(ipAddress) + ':' + str(gpibAddress) + '...')
    gpibObj = netgpib.netGPIB(ipAddress, gpibAddress, tSleep=0.2)
    print('Connected.')
    print("Instrument ID: ")
    idnString = gpibObj.query("*IDN?")
    print(idnString.splitlines()[-1])
    return(gpibObj)


####################
# Settings helpers
####################

def reset(gpibObj):
    # Call reset command, manual states it takes 12 sec to finish
    print('Resetting AG4395A...')
    gpibObj.command("*RST")
    time.sleep(12)
    print('Done!')


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
    # Put the analyzer on hold
    gpibObj.command('HOLD')

    # Set the output format to ASCII
    # TODO: FORM2 binary transfer is many times faster.
    #       Figure out the string decoding (read raw in netgpib?)
    gpibObj.command('FORM4')

    data = []
    freqs = []
    nDisp = int(gpibObj.query('DUAC?')) + 1
    if nDisp == 1:
        chans = [int(gpibObj.query('CHAN2?')) + 1]
    else:
        chans = [1, 2]

    for chan in chans:
        gpibObj.command('CHAN' + str(chan))

        freqString = gpibObj.query('OUTPSWPRM?', 1024)
        chanFreqs = [float(s) for s in re.findall(r'[-+.E0-9]+', freqString)]
        freqs.append(chanFreqs)

        dataString = gpibObj.query('OUTPDTRC?', 1024)
        chanData = [float(s) for s in re.findall(r'[-+.E0-9]+', dataString)]
        # If we're taking TFs, but just downloading real data,
        # discard the null complex parts
        if all(val == 0 for val in chanData[1::2]):
            chanData = chanData[::2]
        data.append(chanData)

    return(freqs, data)


####################
# Output file writing
####################


def writeHeader(dataFile, timeStamp):
    dataFile.write('# AG4395A Measurement - Timestamp: ' + timeStamp + '\n')


def writeData(dataFile, freq, data, delimiter='    '):
    print('Writing measurement data to file...')
    # Write data vectors
    if len(freq) > 1:  # Dual chan

        if freq[0] == freq[1]:  # Shared Freq axis
            for i in range(len(freq[0])):
                dataFile.write(str(freq[0][i]) + delimiter + str(data[0][i])
                               + delimiter + str(data[1][i]) + '\n')

        else:  # Unequal axes! Kind of awkward to output nicely
            print('Unequal Frequency Axes, stacking output')
            for i in range(len(freq[0])):
                dataFile.write(str(freq[0][i])
                               + delimiter + str(data[0][i]) + '\n')
            # Print unit line?
            dataFile.write('# Channel 2 Data\n')
            for i in range(len(freq[1])):
                dataFile.write(str(freq[1][i])
                               + delimiter + str(data[1][i]) + '\n')

    else:  # Single display
        for i in range(len(freq[0])):
            dataFile.write(str(freq[0][i])
                           + delimiter + str(data[0][i]) + '\n')

####################
# Run measurements
####################


def multiMeasure(gpibObj, params):
    # Assuming that measurement has already been set up

    if 'nSegment' not in params or int(params['nSegment']) == 1:
        measure(gpibObj, params)
        (freq, data) = download(gpibObj)

    else:
        nseg = params['nSegment']
        nDisp = int(gpibObj.query('DUAC?')[0]) + 1

        # We're doing a pseudo-log sweep!
        # Need to find segment limits...
        unitDict = {'MHz': 1e6, 'kHz': 1e3, 'Hz': 1.0, 'mHz': 1e-3}
        f1m = re.search('([0-9]+)([A-Za-z]+)', params['startFreq'])
        f2m = re.search('([0-9]+)([A-Za-z]+)', params['stopFreq'])
        f1 = float(f1m.group(1)) * unitDict[f1m.group(2)]
        f2 = float(f2m.group(1)) * unitDict[f2m.group(2)]

        fLims = round(logspace(log10(f1), log10(f2), nseg + 1))

        # Loop over segments and measure
        for ii in range(nseg):
            if nDisp == 2:
                gpibObj.command('CHAN1')
                gpibObj.command('STAR ' + str(fLims[ii]))
                gpibObj.command('STOP ' + str(fLims[ii + 1]))
                gpibObj.command('CHAN2')
            gpibObj.command('STAR ' + str(fLims[ii]))
            gpibObj.command('STOP ' + str(fLims[ii + 1]))
            print('Segment ' + str(ii + 1) + ' of ' + str(nseg) + '...')
            measure(gpibObj, params)
            (fi, di) = download(gpibObj)

            if ii == 0:
                freq = fi
                data = di
            else:
                freq = [prev + new for (prev, new) in zip(freq, fi)]
                data = [prev + new for (prev, new) in zip(data, di)]


def measure(gpibObj, params):
    gpibObj.command("TRGS INT")
    gpibObj.command('CLES')
    gpibObj.command('*SRE 4')
    gpibObj.command('ESNB 1')

    print('Preparing to trigger...')
    nDisp = int(gpibObj.query('DUAC?')[0]) + 1
    nAvg = str(params.get('averages', 1))

    if nDisp == 2:
        gpibObj.command('CHAN1')
        gpibObj.command('AVER ON')
        gpibObj.command('AVERREST')
        gpibObj.command('AVERFACT ' + nAvg)
        gpibObj.command('CHAN2')

    gpibObj.command('AVER ON')
    gpibObj.command('AVERFACT ' + nAvg)
    gpibObj.command('AVERREST')
    print('Taking ' + nAvg + ' averages...')
    gpibObj.command('NUMG ' + nAvg)

    while not int(gpibObj.srq()):
        time.sleep(1)
    print('Done!')


####################
# Saving and setting measurement parameters
####################

def _parseUnit(string):
    # Assumes a series of numbers with a few letters at the end
    # e.g. 30.123kHz
    prefixD = {'n': 1e-9, 'u': 1e-6, 'm': 1e-3, 'k': 1e3, 'M': 1e6, 'G': 1e9}

    unit = ''.join([s for s in string if s.isalpha()])
    val = string[:-len(unit)]

    mult = prefixD.get(unit[0], 1.0)

    return mult * float(val)


def setParameters(gpibObj, params):
    gpibObj.command('PRES')
    time.sleep(5)
    gpibObj.command('TRGS INT')  # get triggering from GPIB
    if params['measType'] == 'Spectrum':
        gpibObj.command('SA')

        # Set up channel inputs
        if params['dualChannel'].lower() == 'dual' and len(
                params['channels']) == 2:
            gpibObj.command('DUAC ON')

        for jj in range(len(params['channels'])):
            gpibObj.command('CHAN' + str(jj + 1))
            gpibObj.command('MEAS ' + params['channels'][jj])
            if params['specType'].lower() == 'noise':
                gpibObj.command('FMT ' + params['specType'][0:5].upper())
            elif params['specType'].lower() != 'spectrum':
                raise ValueError('specType not parsing!')

            # For now, default noise to V^2/Hz and spectrum to dBm
            if params['specType'].lower() == 'noise':
                gpibObj.command('SAUNIT V')
            else:
                gpibObj.command('SAUNIT DBM')
            gpibObj.command('AVERFACT ' + str(params['averages']))
            gpibObj.command('AVER OFF')
            gpibObj.command('STAR ' + params['startFreq'])
            gpibObj.command('STOP ' + params['stopFreq'])
            gpibObj.command('BWAUTO ON')
            gpibObj.command('BWSRAT ' + str(params['bwSpanRatio']))

            if 'attenuation' in params:
                if isinstance(params['attenuation'], str):
                    if params['attenuation'].lower() == 'auto':
                        gpibObj.command('ATTAUTO ON')
                    else:
                        raise ValueError('Attenuation String not parseable!')
                else:
                    gpibObj.command('ATTAUTO OFF')
                    gpibObj.command('ATT' + params['channels'][jj] + ' '
                                    + str(params['attenuation']) + 'DB')
            else:  # Default setitngs
                gpibObj.command('ATTAUTO OFF')
                for chan in ['R', 'A', 'B']:
                    gpibObj.command('ATT' + chan + ' 20DB')

            # If provided separately, override above.
            if 'attenuationR' in params:
                gpibObj.command('ATTAUTO OFF')
                gpibObj.command('ATTR ' + str(params['attenuationR']) + 'DB')
            if 'attenuationA' in params:
                gpibObj.command('ATTAUTO OFF')
                gpibObj.command('ATTA ' + str(params['attenuationA']) + 'DB')
            if 'attenuationB' in params:
                gpibObj.command('ATTAUTO OFF')
                gpibObj.command('ATTB ' + str(params['attenuationB']) + 'DB')

    elif params['measType'] == 'TF':
        gpibObj.command('NA')
        gpibObj.command('DUAC ON')

        if not any([params['inputMode'] == s for s in ('AR', 'BR', 'AB')]):
            raise ValueError('Bad inputMode! Must be "AR", "BR" or "AB"!')

        if 'attenuation' in params:
            if isinstance(params['attenuation'], str):
                if params['attenuation'].lower() == 'auto':
                    gpibObj.command('ATTAUTO ON')
                else:
                    raise ValueError('Attenuation String not parseable!')
            else:
                gpibObj.command('ATTAUTO OFF')
                for chan in params['inputMode']:
                    gpibObj.command('ATT' + chan + ' '
                                    + str(params['attenuation']) + 'DB')
        else:  # Default setitngs
            gpibObj.command('ATTAUTO OFF')
            for chan in ['R', 'A', 'B']:
                gpibObj.command('ATT' + chan + ' 20DB')

        # If provided separately, override above.
        if 'attenuationR' in params:
            gpibObj.command('ATTAUTO OFF')
            gpibObj.command('ATTR ' + str(params['attenuationR']) + 'DB')
        if 'attenuationA' in params:
            gpibObj.command('ATTAUTO OFF')
            gpibObj.command('ATTA ' + str(params['attenuationA']) + 'DB')
        if 'attenuationB' in params:
            gpibObj.command('ATTAUTO OFF')
            gpibObj.command('ATTB ' + str(params['attenuationB']) + 'DB')

        gpibObj.command('SWETAUTO')       # auto sweep time
        if params['sweepType'] == 'Linear':
            gpibObj.command('SWPT LINF')  # sweep lin freq.
        else:
            gpibObj.command('SWPT LOGF')  # sweep log freq.

        IF = params['ifBandwidth']  # Need to convert to int...
        if IF == 'auto':
            gpibObj.command('BWAUTO ON')
        else:
            gpibObj.command('BW ' + str(IF))  # to set the IF bandwidth

        gpibObj.command('POWE ' + str(params['excAmp']))  # units are in dBm

        gpibObj.command('CHAN1')  # choose the active channel
        gpibObj.command('MEAS ' + params['inputMode'])
        if 'mag' in params['dataMode'].lower():
            gpibObj.command('FMT LINM')
        elif 'reim' in params['dataMode'].lower():
            gpibObj.command('FMT REAL')
        else:
            gpibObj.command('FMT LOGM')

        gpibObj.command('CHAN2')
        gpibObj.command('MEAS ' + params['inputMode'])
        if 'reim' in params['dataMode'].lower():
            gpibObj.command('FMT IMAG')
        else:
            gpibObj.command('FMT PHAS')

        gpibObj.command('AVER ON')  # average ON
        gpibObj.command('POIN ' + str(params['numOfPoints']))

        gpibObj.command('STAR ' + params['startFreq'])
        gpibObj.command('STOP ' + params['stopFreq'])

    else:
        raise ValueError('Can only set parameters for measType="Spectrum" or'
                         '"TF".')
    time.sleep(15)
    print('Parameters set!')


def _joinParam(thingList):
    return ', '.join(['{:}'.format(thing) for thing in thingList])


def writeParams(gpibObj, paramFile):
    # Check the analyzer mode
    measType = {1: 'Network Analyzer', 0: 'Spectrum'}[
        int(gpibObj.query('NA?'))]

    nDisp = int(gpibObj.query('DUAC?')) + 1
    if nDisp == 1:
        chans = [int(gpibObj.query('CHAN2?')) + 1]
    else:
        chans = [1, 2]

    bw = []
    bwAuto = []
    meas = []
    fmt = []
    saUnit = []
    fStart = []
    fStop = []
    nPoint = []
    for chan in chans:
        # Change the active channel
        gpibObj.command('CHAN' + str(chan))

        # Get bandwidth information
        bw.append(float(gpibObj.query('BW?')))
        bwAuto.append({0: 'Off', 1: 'On'}[int(gpibObj.query('BWAUTO?'))])

        # What measurement?
        meas.append(gpibObj.query('MEAS?')[:-1])
        fmt.append(gpibObj.query('FMT?')[:-1])
        if measType == 'Spectrum':
            saUnit.append(gpibObj.query('SAUNIT?')[:-1])
            if 'NOISE' in fmt[-1]:
                saUnit[-1] += '/rtHz'
        else:
            excAmp = str(float(gpibObj.query('POWE?'))) + 'dBm'

        fStart.append(float(gpibObj.query('STAR?')))
        fStop.append(float(gpibObj.query('STOP?')))
        nPoint.append(int(gpibObj.query('POIN?')))

    fStart = _joinParam(fStart)
    fStop = _joinParam(fStop)
    bw = _joinParam(bw)
    bwAuto = _joinParam(bwAuto)
    meas = _joinParam(meas)
    fmt = _joinParam(fmt)
    saUnit = _joinParam(saUnit)
    nPoint = _joinParam(nPoint)

    # Get attenuator information
    attR = str(int(gpibObj.query('ATTR?'))) + 'dB '
    attA = str(int(gpibObj.query('ATTA?'))) + 'dB '
    attB = str(int(gpibObj.query('ATTB?'))) + 'dB '

    # Averages
    nAvg = str(int(gpibObj.query('AVERFACT?')))

    print("Writing to the parameter file.")

    paramFile.write('#---------- Measurement Parameters ------------\n')
    paramFile.write('# Start Frequency (Hz): ' + fStart + '\n')
    paramFile.write('# Stop Frequency (Hz): ' + fStop + '\n')
    paramFile.write('# Frequency Points: ' + nPoint + '\n')
    paramFile.write('# Measurement Format: ' + fmt + '\n')
    paramFile.write('# Measuremed Input: ' + meas + '\n')

    paramFile.write('#---------- Analyzer Settings ----------\n')
    paramFile.write('# Number of Averages: ' + nAvg + '\n')
    paramFile.write('# Auto Bandwidth: ' + bwAuto + '\n')
    paramFile.write('# IF Bandwidth: ' + bw + '\n')
    paramFile.write('# Input Attenuators (R,A,B): ' + attR + attA + attB
                    + '\n')
    if measType == 'Spectrum':
        paramFile.write('# Units: ' + saUnit + '\n')
    else:
        paramFile.write('# Excitation amplitude = ' + excAmp + '\n')

    paramFile.write('#---------- Measurement Data ----------\n')
    paramFile.write('# [Freq(Hz) ')

    for chan in chans:
        paramFile.write('Chan ' + str(chan) + ' ')
    paramFile.write(']\n')
