import numpy as np
import os
import time
import argparse

parser = argparse.ArgumentParser(
    description='Usage: python takeManyTFs.py --command <input some command string> --number <input some int>')
parser.add_argument(
    '--command',
    type=str,
    nargs=1,
    help='If defined, becomes the command line run <number> times')
parser.add_argument(
    '--number',
    type=int,
    nargs=1,
    help='If defined, becomes the number of measurements taken')

args = parser.parse_args()

if args.command is not None:
    command = args.command[0]
else:
    command = "./AGmeasure TF_AG_A_over_R.yml"
if args.number is not None:
    number = args.number[0]
else:
    number = 10

print('Command: ', command)
print('Number:  ', number)
print()
startTime = time.time()
for ii in np.arange(number):
    print()
    print('Starting Measurement ', ii)
    print()
    os.system(command)
    print()
    print('Measurement ', ii, ' finished in ', time.time() - startTime, ' seconds')
    print()
    print('---------------------------------------------------------------------')
