# This module provides data access to the HP 3563A Control System analyzer
#
# --copied from AG4395A and modified

import re
import sys
import math
import time
import netgpib
import pdb


def getdata(gpibObj, dataFile, paramFile):

    # Put the analyzer on hold
    gpibObj.command("PAUS")
    time.sleep(0.1)

    # Get the number of data points
    numPoints = int(gpibObj.query("FREQ?"))

    # Set the output format to ASCII
    # gpibObj.command("FORM4")

    # Check for the analyzer mode
    # analyzerMode = int(gpibObj.query("NA?"))
    analyzerMode = 0

    if analyzerMode == 1:
        # It is the network analyzer mode
        # In this mode, the data format is real,imag for each frequency point

        # Get the frequency points
        print('Reading frequency points.')
        receivedData = gpibObj.query("OUTPSWPRM?", 1024)

        # Parse data
        # Matching to the second column of dumpedData
        freqList = re.findall(r'[-+.E0-9]+', receivedData, re.M)

        # Get the data
        print('Reading data.')
        receivedData = gpibObj.query("OUTPDATA?", 1024)

        # Break the data into lists
        dataList = re.findall(r'[-+.E0-9]+', receivedData)

        # Output data
        print('Writing the data into a file.')

        j = 0
        for i in range(len(freqList)):
            dataFile.write(freqList[i] + ', ' +
                           dataList[j] + ', ' + dataList[j + 1] + '\n')
            j = j + 2
    else:
        # It is spectrum analyzer mode

        # Check if it is the dual channel mode or not
        #numOfChan = int(gpibObj.query("DUAC?")) +1

        # Get the current channel number
        # ans=int(gpibObj.query("CHAN1?"))
        # if ans ==1:
        #    currentChannel=1
        # else:
        #    currentChannel=2

        # Get the data

        dataList = []
        freqList = []
        # Loop for each channel
        for i in range(1, numOfChan + 1):
             # ch stores the current channel number
            if numOfChan == 1:
                ch = currentChannel
            else:
                ch = i

            # Change the active channel to ch
            gpibObj.command("CHAN" + str(ch))
            time.sleep(1)

            # Get the frequency points
            print(('Reading frequency points for channel ' + str(i)))
            receivedData = gpibObj.query("OUTPSWPRM?", 1024)

            # Break into elements
            freqList = re.findall(r'[-+.E0-9]+', receivedData)

            print(('Reading data from channel ' + str(i)))
            receivedData = gpibObj.query("OUTPDATA?", 1024)

            # Break into elements
            dataList = re.findall(r'[-+.E0-9]+', receivedData)

            # Output data
            print(('Writing channel ' + str(ch) + ' data into a file.'))
            dataFile.write('# Channel ' + str(ch))
            for j in range(len(freqList)):
                dataFile.write(freqList[j] + ', ' + dataList[j])
                dataFile.write('\n')

    # Continue the measurement
    #netSock.send( "CONT\n")


def getparam(gpibObj, filename, dataFile, paramFile):
    # Get measurement parameters

    print('Reading measurement parameters')

    # pdb.set_trace()
    # Check the analyzer mode
    analyzerMode = int(gpibObj.query("NA?"))
    analyzerType = {
        1: 'Network Analyzer',
        0: 'Spectrum Analyzer'}[analyzerMode]

    # Determine labels and units
    Label = []
    Unit = []
    if analyzerMode == 1:  # Network analyzer mode
        Label.append('Real Part')
        Label.append('Imaginary Part')
        Unit.append('')
        Unit.append('')
        numOfChan = 2
    else:  # Spectrum analyzer mode
        numOfChan = int(gpibObj.query("DUAC?")) + 1
        for i in range(numOfChan):
            Label.append('Spectrum')
            Unit.append('W')

    # Get the current channel number
    ans = int(gpibObj.query("CHAN1?"))
    if ans == 1:
        currentChannel = 1
    else:
        currentChannel = 2

    BW = []
    BWAuto = []
    MEAS = []
    for i in range(numOfChan):

        # ch stores the current channel number
        if numOfChan == 1:
            ch = currentChannel
        else:
            ch = i + 1

        # Change the active channel to ch
        print(("Change channel to " + str(ch)))
        gpibObj.command("CHAN" + str(ch))
        time.sleep(1)

    # Get bandwidth information

        buf = gpibObj.query("BW?")
        BW.append(buf[:-1])

        j = int(gpibObj.query("BWAUTO?"))
        BWAuto.append({0: 'Off', 1: 'On'}[j])

    # Measurement Type
        gpibObj.command('CHAN' + str(i + 1))
        buf = gpibObj.query("MEAS?")
        MEAS.append(buf[:-1])

    # Get attenuator information
    AttnR = str(int(gpibObj.query("ATTR?"))) + 'dB'
    AttnA = str(int(gpibObj.query("ATTA?"))) + 'dB'
    AttnB = str(int(gpibObj.query("ATTB?"))) + 'dB'

    # Source power
    buf = gpibObj.query("POWE?")
    SPW = buf[:-1] + 'dBm'

    # Write to the parameter file
    # Header
    paramFile.write('#HP 3563A parameter file\n#This file contains measurement parameters for the data saved in '
                    + filename + '.dat\n')
    # For the ease of getting necessary information for plotting the data, several numbers and strings are put first
    # The format is the number of channels comes first, then the title of the channels and the units follow,
    # one per line.
#     paramFile.write('#The following lines are for a matlab plotting function\n')
#     paramFile.write(str(numOfChan)+'\n')
#     for i in range(numOfChan):
#         paramFile.write(Label[i]+'\n')
#         paramFile.write(Unit[i]+'\n')

    paramFile.write(
        '##################### Measurement Parameters #############################\n')
    paramFile.write('Analyzer Type: ' + analyzerType + '\n')
    for i in range(numOfChan):
        # ch stores the current channel number
        if numOfChan == 1:
            ch = currentChannel
        else:
            ch = i + 1

        paramFile.write('CH' + str(ch) + ' measurement: ' + MEAS[i] + '\n')

    for i in range(numOfChan):
        paramFile.write('CH' + str(ch) + ' bandwidth: ' + BW[i] + '\n')
        paramFile.write(
            'CH' +
            str(ch) +
            ' auto bandwidth: ' +
            BWAuto[i] +
            '\n')

    paramFile.write('R attanuator: ' + AttnR + '\n')
    paramFile.write('A attanuator: ' + AttnA + '\n')
    paramFile.write('B attanuator: ' + AttnB + '\n')

    paramFile.write('Source power: ' + SPW + '\n')
