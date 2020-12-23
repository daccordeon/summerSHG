"""
Provides data access to Advantest R9211 servo analyzer
"""
import re
import netgpib
import numpy as np
import struct
import sys
import time


class R9211:
    """
    A class to represent an R9211 servo analyzer
    """

    def __init__(self, ip, gpibAddr=8):
        self.dev = netgpib.netGPIB(ip, gpibAddr, auto=False)

        self.dev.query('active?')
#        self.dev.query('active?')
        self.dev.command('hed0')
        time.sleep(0.1)

    def getdata(self, disp=[1], verbose=False, binary=False):
        """
        Download data from R9211
        """

        if binary:
            # Set the format to 64bit float big-endian
            self.dev.command('fmt2')
            self.dev.command('hed0')
            time.sleep(0.1)
            stride = 8  # 64bit is 8 bytes
        else:
            self.dev.command('fmt0')  # ASCII Mode
            time.sleep(0.1)

        data = []
        hdr = []
        for dispID in disp:
            if verbose:
                print(('Downloading data from display ' + str(dispID)))
            # set the display to read
            self.dev.command('sel' + str(dispID))
            time.sleep(0.1)

            # First, read from X axis
            self.dev.command('selxy1')
            time.sleep(0.1)

            # Get data length
            numPoint = int(self.dev.query('reqdtn')[:-2])

            # Get data

            if binary:
                if verbose:
                    print('Downloading X axis data ')
                    self.dev.debug = 1

                x = self.dev.query('reqdt', stride * numPoint)
            else:
                self.dev.command('hed1')
                time.sleep(0.1)

                if verbose:
                    print('Downloading X axis data ')
                    self.dev.debug = 1

                x = self.dev.query('reqdt', 12 * numPoint + 10)

            self.dev.debug = 0
#            self.dev.query('selxy?');
            self.dev.command('hed0')
            time.sleep(0.1)

            # Next, read from Y axis
            self.dev.command('selxy0')
            time.sleep(0.1)

            # Get data

            if binary:
                if verbose:
                    print('Downloading Y axis data ')
                    self.dev.debug = 1

                y = self.dev.query('reqdt', stride * numPoint)
            else:
                self.dev.command('hed1')
                time.sleep(0.1)
                if verbose:
                    print('Downloading Y axis data ')
                    self.dev.debug = 1

                y = self.dev.query('reqdt', 12 * numPoint + 10)

            self.dev.debug = 0
#            self.dev.query('selxy?');
            self.dev.command('hed0')
            time.sleep(0.1)

            if binary:
                # Unpack the binary data
                x = np.array(struct.unpack('>' + str(numPoint) + 'd', x))
                y = np.array(struct.unpack('>' + str(numPoint) + 'd', y))
                (Chan, xDataType, xUnit, yDataType, yUnit) = (
                    False, False, False, False, False)
            else:
                head = x[0:6]  # Extract the header
                # decode header
                (xDataType, Chan, xUnit) = self.decodeHeader(head)
                # Convert the string data into numpy array
                x = [np.float(a) for a in x[7:-2].split(',')]

                head = y[0:6]  # Extract the header
                # decode header
                (yDataType, Chan, yUnit) = self.decodeHeader(head)
                # Convert the string data into numpy array
                y = [np.float(a) for a in y[7:-2].split(',')]

            data.append((x, y))
            hdr.append({'Chan': Chan, 'xDataType': xDataType, 'xUnit': xUnit,
                        'yDataType': yDataType, 'yUnit': yUnit})

        return (data, hdr)
# {{{

    def getparams(self, disp=[1], verbose=False):
        """
        Download measurement parameters.
        """
        self.dev.command('hed0')
        time.sleep(0.1)

        if verbose:
            print('Reading parameters ', end=' ')
            sys.stdout.flush()

# {{{ Common parameters
        MEAS = {'0': 'Waveform',
                '1': 'Specrum',
                '2': 'Time-Frequency',
                '3': 'FRF',
                '4': 'Servo'}[self.dev.query('MEAS?')[:-2]]

        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        FUNC = {'0': 'Time',
                '1': 'Auto Correlation',
                '2': 'Cross Correlation',
                '3': 'Auto Correlation',
                '4': 'Power Spectrum',
                '5': 'Cross Spectrum',
                '6': 'Complex Spectrum',
                '10': 'FRF'
                }[self.dev.query('FUNC?')[:-2]]

        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        ACTIVE = {'0': 'ChA',
                  '1': 'ChB',
                  '3': 'ChA-ChB'
                  }[self.dev.query('ACTIVE?')[:-2]]

        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        HISTP = self.dev.query('HISTP?')[:-2]

        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        SENSA = {'0': 'MAN',
                 '1': 'AUTO',
                 }[self.dev.query('SENSA?')[:-2]]

        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        SENSB = {'0': 'MAN',
                 '1': 'AUTO',
                 }[self.dev.query('SENSB?')[:-2]]

        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        SENSADV = self.dev.query('SENSADV?')[:-2] + "dBV"

        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        SENSBDV = self.dev.query('SENSBDV?')[:-2] + "dBV"

        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        ACOUPLE = {'0': 'AC',
                   '1': 'DC',
                   }[self.dev.query('ACOUPLE?')[:-2]]

        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        BCOUPLE = {'0': 'AC',
                   '1': 'DC',
                   }[self.dev.query('BCOUPLE?')[:-2]]

        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        FRANGE = self.dev.query('FRANGE?')[:-2] + "Hz"

        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        FILTER = {'0': 'OFF',
                  '1': 'ON',
                  }[self.dev.query('FILTER?')[:-2]]

        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        ZOOM = {'0': 'Zero start',
                '1': 'Zoom On',
                }[self.dev.query('ZOOM?')[:-2]]

        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        LWBAND = self.dev.query('LWBAND?')[:-2] + "Hz"
        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        UPBAND = self.dev.query('UPBAND?')[:-2] + "Hz"
        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        WINDOWA = {'1': 'Rect',
                   '2': 'Hanning',
                   '3': 'Minimum',
                   '4': 'Flat-pass',
                   '5': 'Force',
                   '6': 'Respons'
                   }[self.dev.query('WINDOWA?')[:-2]]
        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        WINDOWB = {'1': 'Rect',
                   '2': 'Hanning',
                   '3': 'Minimum',
                   '4': 'Flat-pass',
                   '5': 'Force',
                   '6': 'Respons'
                   }[self.dev.query('WINDOWB?')[:-2]]
        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        WEIGHT = {'0': 'No-Weight',
                  '1': 'A-WGT',
                  '2': 'B-WGT',
                  '3': 'C-WGT',
                  '4': 'C-MES-WGT'
                  }[self.dev.query('WEIGHT?')[:-2]]
        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        AVGNO = self.dev.query('AVGNO?')[:-2]
        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        AVGLIMIT = self.dev.query('AVGLIMIT?')[:-2]
        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        AVGMODE = {'1': 'Sum',
                   '2': 'Exp',
                   '3': 'Peak',
                   '4': 'Sub'
                   }[self.dev.query('AVGMODE?')[:-2]]
        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        FREQRES = {'0': 'Lin f',
                   '1': 'Log f',
                   '2': '1/3 Oct f',
                   '3': '1/1 Oct f'
                   }[self.dev.query('FREQRES?')[:-2]]
        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

        LINESPAN = self.dev.query('LINESPAN?')[:-2]
        if verbose:
            print('.', end=' ')
            sys.stdout.flush()

# }}}

        cparams = {'Measurement': MEAS, 'Function': FUNC, 'Active channels': ACTIVE,
                   'Histogram points': HISTP, 'ChA sensitivity': SENSADV, 'ChB sensitivity': SENSBDV,
                   'ChA Range': SENSA, 'ChB Range': SENSB, 'ChA Coupling': ACOUPLE, 'ChB Coupling': BCOUPLE,
                   'Freq Range': FRANGE, 'Input Filter': FILTER, 'Zoom': ZOOM, 'Start Frequency': LWBAND,
                   'Stop Frequency': UPBAND, 'ChA Window': WINDOWA, 'ChB Window': WINDOWB,
                   'Weight': WEIGHT, 'Average number': AVGNO, 'Average limit': AVGLIMIT,
                   'Averaging Mode': AVGMODE, 'Frequency Scale': FREQRES, 'Line Span': LINESPAN}

# {{{ Display specific parameters

        dparams = {}

        for i in disp:
            # Select a display
            self.dev.query('sel' + str(i))
            if verbose:
                print('.', end=' ')
                sys.stdout.flush()

            dparams['Disp' + str(i) + ' View defined in'] = {
                '0': 'Normal',
                '1': 'Memory',
                '2': 'Math',
                '3': 'T-F',
                '4': 'Curve fit',
                '5': 'Synsesis'
            }[self.dev.query('VDEFIN?')[:-2]]
            if verbose:
                print('.', end=' ')
                sys.stdout.flush()

            dparams['Disp' + str(i) + ' View type'] = {
                '2': 'Time Series',
                '7': 'Auto Correlation',
                '8': 'Cross Correlation',
                '9': 'Impulse Response',
                '10': 'Step Response',
                '11': 'Cepstrum',
                '12': 'Histogram',
                '14': 'Complex Spectrum',
                '15': 'Power Spectrum',
                '24': 'Cross Spectrum',
                '29': 'Hxy',
                '32': 'Coherence',
                '35': 'T-F Gxx(f) Sum(Gxx(f))',
                '36': 'T-F f-Peak',
                '37': 'T-F Real Imag Phase'
            }[self.dev.query('VTYPE?')[:-2]]
            if verbose:
                print('.', end=' ')
                sys.stdout.flush()

            dparams['Disp' + str(i) + ' Channel'] = {
                '0': 'A',
                '1': 'B',
                '65': 'A&B'
            }[self.dev.query('VCHNL?')[:-2]]
            if verbose:
                print('.', end=' ')
                sys.stdout.flush()

            dparams['Disp' + str(i) + ' View Type'] = {
                '0': 'Instant',
                '1': 'Averaged'
            }[self.dev.query('VDSW?')[:-2]]
            if verbose:
                print('.', end=' ')
                sys.stdout.flush()

            dparams['Disp' + str(i) + ' X coordinate'] = {
                '0': 'Lin',
                '1': 'Log',
                '2': '1/3 Oct',
                '3': '1/1 Oct'
            }[self.dev.query('VXCORD?')[:-2]]
            if verbose:
                print('.', end=' ')
                sys.stdout.flush()

            dparams['Disp' + str(i) + ' X coordinate'] = {
                '0': 'Lin',
                '1': 'Log',
                '2': '1/3 Oct',
                '3': '1/1 Oct'
            }[self.dev.query('VXCORD?')[:-2]]
            if verbose:
                print('.', end=' ')
                sys.stdout.flush()

            dparams['Disp' + str(i) + ' Y coordinate'] = {
                '0': 'Real',
                '1': 'Imag',
                '2': 'Mag',
                '3': 'Mag2',
                '4': 'dBMag',
                '5': 'Phase',
                '6': '-Phase',
                '7': 'Group Delay',
                '8': 'Nyquest/Orbit',
                '9': 'Cole-Cole',
                '11': 'Nichols'
            }[self.dev.query('VYCORD?')[:-2]]
            if verbose:
                print('.', end=' ')
                sys.stdout.flush()

            dparams['Disp' + str(i) + ' T-F data'] = {
                '-1': 'None',
                '0': 'Gxx(f)',
                '1': 'Sum(Gxx(f))',
                '2': 'Real',
                '3': 'Imag',
                '4': 'Phase',
                '5': 'f Peak'
            }[self.dev.query('TFDATA?')[:-2]]
            if verbose:
                print('.', end=' ')
                sys.stdout.flush()

# }}}

        return (cparams, dparams)


# }}}

    def decodeHeader(self, hdr):
        """
        Decode a data header
        """

        dtypes = {'TIM': 'Time series',
                  'ACR': 'Auto correlation',
                  'CCR': 'Cross correlation',
                  'HST': 'Histogram',
                  'SPC': 'Spectrum',
                  'CSP': 'Cross spectrun',
                  'FRF': 'Transfer function',
                  'COH': 'Coherence',
                  'IMR': 'Impulse response',
                  'COP': 'COP',
                  'SNR': 'SNR',
                  'CEP': 'Cepstrum',
                  'OCT': '1/3 Octave',
                  'OCO': '1/1 Octave',
                  'CLK': 'Time',
                  'FRQ': 'Frequency',
                  'AMP': 'Amplitude',
                  'LAG': 'Time lag',
                  'CEF': 'Quefrency'}

        units = {'__': '',
                 '_S': 'sec',
                 'HZ': 'Hz',
                 '_V': 'V',
                 'DG': 'deg',
                 'PC': '%',
                 'DB': 'dB',
                 'DV': 'dBV',
                 'VZ': 'V/rtHz',
                 'DH': 'dBV/rtHz',
                 'EU': 'EU',
                 'DE': 'dBEU'}

        return (dtypes[hdr[0:3]], hdr[3:4], units[hdr[4:6]])

    def saveData(self, dataFile, data):
        # A list to hold the length of each display data
        k = np.array([len(a[0]) for a in data])
        # If all the displays have the same data length (true for most cases)
        if (k == k[0]).prod():
            # Multi column file
            mcol = True

            for i in range(k[0]):
                for j in range(len(k)):  # Loop through displays
                    dataFile.write(
                        np.str(
                            data[j][0][i]) +
                        "," +
                        np.str(
                            data[j][1][i]))
                    if j != (len(k) - 1):
                        dataFile.write(",")
                    else:
                        dataFile.write("\n")
        else:
            # Two column file
            mcol = False
            for j in range(len(k)):  # Loop through displays
                dataFile.write("Disp" + str(disp[j]) + "\n")
                for i in range(k[j]):
                    dataFile.write(
                        np.str(
                            data[j][0][i]) +
                        "," +
                        np.str(
                            data[j][1][i]) +
                        "\n")

        return mcol

    def saveParam(self, paramFile, cparams, dparams, hdr, mcol, disp):
        # Write to the parameter file
        paramFile.write("------------------------------------------\n")
        paramFile.write(
            "R9211 servo analyzer parameter file" +
            time.ctime() +
            "\n")
        paramFile.write("------------------------------------------\n")
        paramFile.write("\n")
        paramFile.write("Data file format: ")
        if mcol:
            msg =\
                """Multi-colum style
Each row has the following format
Disp1X, Disp1Y, Disp2X, Disp2Y, ...

"""
        else:
            msg =\
                """Two column format
Each row has the following format:
X,Y
Since the data lengths of the displays are different, data from
each display is written one after another.
A line with "Disp1", "Disp2", "Disp3" or "Disp4" appears to separate
each display's data.

"""
        paramFile.write(msg)

        for i in range(len(disp)):
            paramFile.write("Display " + str(disp[i]) + ":\n")
            paramFile.write("Channel: " + hdr[i]['Chan'] + "\n")
            paramFile.write(
                "X axis: " +
                hdr[i]['xDataType'] +
                "[" +
                hdr[i]['xUnit'] +
                "]\n")
            paramFile.write(
                "Y axis: " +
                hdr[i]['yDataType'] +
                "[" +
                hdr[i]['yUnit'] +
                "]\n")
            paramFile.write("\n")

        [paramFile.write(key + ": " + cparams[key] + "\n")
         for key in sorted(cparams.keys())]
        [paramFile.write(key + ": " + dparams[key] + "\n")
         for key in sorted(dparams.keys())]

    def query(self, string, buf=100, sleep=0):
        return self.dev.query(string, buf, sleep)

    def command(self, string, sleep=0):
        self.dev.command(string, sleep)

    def spoll(self):
        return self.dev.spoll()

    def isAveraging(self):
        """Returns True if the device is averaging"""

        s = int(self.dev.spoll())  # Status byte

        # The third bit of the status byte is 1 when averaging is complete
        return not (s & 0b100)

    def waitAvg(self, interval=0.2, timeOut=False):
        """Wait until the averaging completes"""
        startTime = time.time()
        while self.isAveraging():
            time.sleep(interval)
            if timeOut:
                if time.time() - startTime > timeOut:
                    break

    def close(self):
        """
        Close the connection to R9211
        """
        self.dev.close()
