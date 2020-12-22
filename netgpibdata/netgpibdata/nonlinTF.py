import numpy as np
import netgpib
import argparse
import time
import yaml
from SRmeasure import main as SRmeasure

def main(paramFile, ipMarconi='10.0.1.67', gpibMarconi=17, startCarrier=1e6,
         stopCarrier=100e6, stepCarrier=10e6, carrierLevel=0,filename=None,
         log=False, fstd='Int'):
    try:
        if filename == None:
            with open(paramFile, 'r') as f:
                reader = yaml.load_all(f, Loader=yaml.FullLoader)
                params = reader.next()
                reader.close()
            filename = params['nameRoot']
        gpibObj = netgpib.netGPIB(ip=ipMarconi, gpibAddr=gpibMarconi,
                                  eot='\004',debug=0, log=log)
        gpibObj.command('*CLS')
        gpibObj.command('*RST')
        if fstd.lower()=='int':
            gpibObj.command('FSTD INT')
        elif fstd.lower()=='ext10dir':
            gpibObj.command('FSTD EXT10DIR')
        elif fstd.lower()=='ext1ind':
            gpibObj.command('FSTD EXT1IND')
        elif fstd.lower()=='ext10ind':
            gpibObj.command('FSTD EXT10IND')
        elif fstd.lower()=='int10out':
            gpibObj.command('FSTD INT10OUT')
        else:
            print('Frequency Standard argument is wrong. Doing nothing.')
        gpibObj.command('CFRQ ' + str(startCarrier))
        gpibObj.command('RFLV ' + str(carrierLevel))
        gpibObj.command('RFLV:ON')
        gpibObj.command('MOD:OFF')
        cf = startCarrier
        while(cf<=stopCarrier):
            # Set new carrier frequency
            gpibObj.command('CFRQ ' + str(cf))
            # Stamp Carrier Frequency on File Root
            thisFilename = filename + '_CF_'+str(np.round(cf,0))
            # Measure using SR785
            retVal = SRmeasure(paramFile=paramFile, filename=thisFilename)
            if retVal=='Control-C':
                raise KeyboardInterrupt
            cf = cf + stepCarrier
        gpibObj.command('RFLV:OFF')
        gpibObj.close()
    except KeyboardInterrupt:  # if user presses Control-C, handle exit gracefully
        try:
            print('Control-C detected.  Handling exit...')
            print('Resetting Marconi 2023A.')
            gpibObj.command('*RST')
            print('Closing gpibObj')
            gpibObj.close()
        except NameError:
            print('Variable gpibObj not defined.  Analyzer not reset.')

def grabInputArgs():
    parser = argparse.ArgumentParser(
        description='This script uses a Marconi 2023A and a SR785 to measure'
                    'transfer function from an upconverted RF frequency to '
                    'to audio band. The RF out of Marconi should be connected '
                    'to LO port of a mixer. The IF port should be connected '
                    'to Source Out of SR785. DUT should be connected between '
                    'RF port of Mixer and measurement channel of SR785.\n'
                    'Note: You must set remote operation to GPIB at Util 50\n'
                    'And you can set GPIB address on Marconi 2023A at Util 51')
    parser.add_argument('paramFile', nargs='?',
                        help='The parameter file for the measurement in SR785.'
                             'This must be a transfer function file for this '
                             'measurement to make sense. This is required.',
                        default=None)
    parser.add_argument('-i', '--ipMarconi',
                        help='IP address of Marconi. Default is 10.0.1.67.',
                        default='10.0.1.67')
    parser.add_argument('-a', '--gpibMarconi', type=int, default=17,
                        help='GPIB device address of Marconi.  Default is 17.')
    parser.add_argument('-f', '--filename', help='Stem of output filename.'
                        'Overrides parameter file.', default=None)
    parser.add_argument('--startCarrier', type=float,
                        help='Start carrier Frequency in Hz. Default is 1 MHz',
                        default=1e6)
    parser.add_argument('--stopCarrier', type=float,
                        help='Stop carrier Frequency in Hz. '
                             'Default is 100 MHz',
                        default=100e6)
    parser.add_argument('--stepCarrier', type=float,
                        help='Step carrier Frequency in Hz. Default is 10 MHz',
                        default=10e6)
    parser.add_argument('--carrierLevel', type=float,
                        help='Carrier Level in dBm',
                        default=0)
    parser.add_argument('-l', '--log', action='store_true',
                        help='Flag.  If set, script will log GPIB commands.')
    return parser.parse_args()


if __name__ == "__main__":
    args = grabInputArgs()
    main(args.paramFile, args.ipMarconi, args.gpibMarconi, args.startCarrier,
         args.stopCarrier, args.stepCarrier, args.carrierLevel, args.filename,
         args.log)
