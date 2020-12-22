import numpy as np
import os
import time
import argparse


def main():
    args = grabInputArgs()

    # takes input array or defaults to set values
    if args.command is not None:
        ymlFileList = args.command[0]
    else:
        ymlFileList = np.array(['SPAG4395Atemplate_5MHzStop.yml',
                                'SPAG4395Atemplate_100kHzStop.yml',
                                'SPAG4395Atemplate_10kHzStop.yml',
                                'SPAG4395Atemplate_1kHzStop.yml'])

    # work out if directory exists, if not make it
    fName = args.filename[0]
    if not os.path.exists(os.path.dirname(args.filename[0])):
        os.makedirs(os.path.dirname(args.filename[0]))
        print(('Folder created at {0}.').format(os.path.dirname(fName)))

    # Construct commands to run based on whether file name base is given
    commands = np.array([])
    for ymlF in ymlFileList:
        if args.filename is not None:
            fName = args.filename[0] + '_' + ymlF.split('_')[-1].split('.')[0]
            commands = np.append(
                commands,
                './AGmeasure {ymlF} -f {FN}'.format(ymlF=ymlF, FN=fName))
        else:
            commands = np.append(
                commands,
                './AGmeasure {ymlF}'.format(ymlF=ymlF))

    print(('{nb} commands to run:\n{cmd}\n'.format(
        nb=len(commands),
        cmd=commands)))
    startTime = time.time()
    for ii, command in enumerate(commands):
        print(('Starting Measurement ', ii))
        print(command)
        os.system(command)
        print('')
        print(('Measurement ', ii, ' finished in ',
              time.time() - startTime, ' seconds\n'))
        print('------------------------------------------------------------\n')


def grabInputArgs():
    parser = argparse.ArgumentParser(
        description='Usage: python takeManySpectraAG.py --command <input some'
                    'command string>')
    parser.add_argument(
        '--command',
        type=str,
        nargs=1,
        help='If defined, becomes the command line executed.  Make sure the'
             'Agilent is hooked up to the PLL control signal.')
    parser.add_argument(
        '-f', '--filename',
        type=str,
        nargs=1,
        help='Provide an optional filename base and path for output files that'
             'overrides the .yml configuration')
    return parser.parse_args()


if __name__ == "__main__":
    main()
