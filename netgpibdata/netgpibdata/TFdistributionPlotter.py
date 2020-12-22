#!/usr/bin/env python
from __future__ import division

import logging as log
import subprocess
import os
import time
import argparse
import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
mpl.rcParams.update({'text.usetex': True,
                     'lines.linewidth': 2,
                     'font.size': 16,
                     'figure.figsize': (16, 8),
                     'xtick.labelsize': 16,
                     'ytick.labelsize': 16,
                     'axes.grid': True,
                     'grid.color': 'xkcd:cement',
                     'grid.alpha': 0.3,
                     'lines.markersize': 12,
                     'legend.borderpad': 0.2,
                     'legend.fancybox': True,
                     'legend.fontsize': 13,
                     'legend.framealpha': 0.7,
                     'legend.handletextpad': 0.1,
                     'legend.labelspacing': 0.2,
                     'legend.loc': 'best',
                     'savefig.dpi': 100,
                     'pdf.compression': 9})

# TO BE CHECKED - DO NOT USE
'''
def std2coh(N, sigma, mag):
	den = (2*N*(sigma**2)/(mag**2)) + 1
	coh2 = 1/den
	return np.sqrt(coh2)
'''

# Nice colors (https://xkcd.com/color/rgb/)
tcolor = '#d62728'      # color of each sweep
mcolor = '#1f3b4d'    # color of the median
uncolor = '#1bfc06'  # color of uncertainty bars

alpha1 = 0.05   # sweeps transparency
alpha2 = 0.6   # means
alpha3 = 0.2   # uncertainties

################################
################################
loglog = True  # Set if we would like a loglog plot
semilogx = False
magdB = True

MergePlots = False
isCsv = False  # Set if reading in .csv files

yConv = 1  # Optional scaling of Magnitude y-axis

xAxisLabel = 'Frequency [Hz]'
yAxisLabel = 'Magnitude'
y2AxisLabel = r'Relative Mag [\%]'
y3AxisLabel = 'Phase [deg]'  # Set y2 axis label
y4AxisLabel = 'Relative Phase [deg]'

plotTitle = 'TF Measurement'
plotLeftTitle = r'TF Measurements $\pm$ Uncertainty'
plotRightTitle = r'Relative Meas $\pm$ Uncertainty'
#plotSaveName = 'PLL_OLGTFs'
################################

parser = argparse.ArgumentParser(description='Usage: python TFdistributionPlotter.py ./path/to/data/folderDescription/TF*.txt   This takes three columns of data, frequency, magnitude and phase, from many .txt files and plots them together.  It also finds the standard deviation and plots it as well.  Puts plots in ./path/to/plots/folderDescription/TF.txt. Can handle many TFs, will put in the folder of the last data file included')
parser.add_argument('files', type=argparse.FileType('r'), nargs='+')
parser.add_argument('--yConv', type=float, nargs=1,
                    help='If defined, becomes the factor by which the magnitude Y-axis is scaled.')
parser.add_argument('--xlabel', type=str, nargs=1,
                    help='If defined, becomes the xlabel of the plot')
parser.add_argument('--ylabel', type=str, nargs=1,
                    help='If defined, becomes the ylabel of the 1st plot')
parser.add_argument('--y2label', type=str, nargs=1,
                    help='If defined, becomes the ylabel of the 2nd plot')
parser.add_argument('--y3label', type=str, nargs=1,
                    help='If defined, becomes the ylabel of the 3nd plot')
parser.add_argument('--y4label', type=str, nargs=1,
                    help='If defined, becomes the ylabel of the 4nd plot')
parser.add_argument('--title', type=str, nargs=1,
                    help='If defined, becomes the subtitle of the plot')
parser.add_argument('--lefttitle', type=str, nargs=1,
                    help='If defined, becomes the title of the 1st plot')
parser.add_argument('--righttitle', type=str, nargs=1,
                    help='If defined, becomes the title of the 2nd plot')
parser.add_argument('--yAxisLimitPercent', '-yP', type=float, nargs=1,
                    help='If defined, becomes the y axis limit of the 2st plot')
parser.add_argument('--yAxisLimitDegrees', '-yD', type=float, nargs=1,
                    help='If defined, becomes the y axis limit of the 4th plot')
parser.add_argument('--notar', action='store_true', default=False,
                    help='If not set, creates a tar of the data, plots, and this script.')
parser.add_argument('--log', type=str, default='WARNING',
                    help='Set the log level to INFO, DEBUG, WARNING')

args = parser.parse_args()

if args.yConv is not None:
    yConv = args.yConv[0]
if args.xlabel is not None:
    xAxisLabel = args.xlabel[0]
if args.ylabel is not None:
    yAxisLabel = args.ylabel[0]
if args.y2label is not None:
    y2AxisLabel = args.y2label[0]
if args.title is not None:
    plotTitle = args.title[0]
if args.lefttitle is not None:
    plotLeftTitle = args.lefttitle[0]
if args.righttitle is not None:
    plotRightTitle = args.righttitle[0]

# set log level based on input arguments
loglevel = args.log
numlevel = getattr(log, loglevel.upper())
log.basicConfig(level=numlevel)

log.debug('xlabel  =  ' + xAxisLabel)
log.debug('ylabel  =  ' + yAxisLabel)
log.debug('y2label = ' + y2AxisLabel)
log.debug('title   =  ' + plotTitle)
log.debug('TF magnitude values will be scaled by ' + str(yConv))

labels = np.array([])
for ii, tempFile in enumerate(vars(args)['files']):
    if ii == 0:
        labels = np.append(labels, 'TF Sweep')
    else:
        labels = np.append(labels, '')

log.debug(str(tempFile.name))

curDateLabel = time.strftime("%b-%d-%Y")
curDate = time.strftime("%Y%m%d_%H%M%S")

pathToData = os.path.dirname(os.path.relpath(tempFile.name)) + '/'
# plotSaveName is always the same as the last .txt file
plotSaveName = os.path.basename(tempFile.name).replace('.txt', '')
#plotSaveName = plotSaveName
log.debug("plotSaveName is " + plotSaveName)

# Check if equivalent /plots/ directory exists where the /data/ folder is
pathToPlots = pathToData.replace('data/', 'plots/')
log.info('Data is in ' + pathToData)
log.info('Plots will be in ' + pathToPlots)
if not os.path.exists(pathToPlots):
    os.makedirs(pathToPlots)

plotDict = {}
txtsWithNans = 0
for ii, arg in enumerate(args.files):
    if isCsv == False:
        tempTxt = np.loadtxt(arg)
    else:
        tempTxt = np.loadtxt(arg, delimiter=',')
    if np.sum(np.isnan(tempTxt)) > 0:  # if there are nans don't record anything
        print
        print 'There are nans in ', arg.name
        print 'Not including in plots'
        args.files = np.delete(args.files, ii)
        txtsWithNans += 1
        continue
    else:
        idx = ii - txtsWithNans
        plotDict[idx] = tempTxt

# Find the distribution, assuming all frequency vectors are the same
measNum = len(plotDict)
freq = plotDict[0][:, 0]
freqLen = len(freq)

plotLeftTitle = str(measNum) + ' ' + plotLeftTitle

# convert TF into real and imag parts for simple unc prop
# a + ib = z * exp(i * phi)
compTF = np.zeros([measNum, freqLen], dtype=complex)
real = np.zeros([measNum, freqLen])
imag = np.zeros([measNum, freqLen])
dz_da = np.zeros(freqLen)
dz_db = np.zeros(freqLen)
dphi_da = np.zeros(freqLen)
dphi_db = np.zeros(freqLen)
realMean = np.zeros(freqLen)
imagMean = np.zeros(freqLen)
compMean = np.zeros([freqLen], dtype=complex)

# convert from dB/deg into complex numbers
for ii in plotDict.keys():
    if magdB:
        mag = 10**(plotDict[ii][:, 1] / 20) * yConv
    else:
        mag = plotDict[ii][:, 1] * yConv
    phase = plotDict[ii][:, 2]  # This value is in degrees
    phase *= np.pi / 180        # convert to radians
    compTF[ii, :] = mag * np.exp(1j * phase)
    real[ii, :] = np.real(compTF[ii, :])
    imag[ii, :] = np.imag(compTF[ii, :])

# why is this called mean when its actually median ???
for ii in np.arange(freqLen):
    realMean[ii] = np.median(real[:, ii])
    imagMean[ii] = np.median(imag[:, ii])
    compMean[ii] = realMean[ii] + 1j * imagMean[ii]

    # Set up derivatives to change back to magnitude and phase basis for
    # plotting
    dz_da[ii] = realMean[ii] / np.sqrt(realMean[ii]**2 + imagMean[ii]**2)
    dz_db[ii] = imagMean[ii] / np.sqrt(realMean[ii]**2 + imagMean[ii]**2)
    dphi_da[ii] = -1 * imagMean[ii] / (realMean[ii]**2 + imagMean[ii]**2)
    dphi_db[ii] = realMean[ii] / (realMean[ii]**2 + imagMean[ii]**2)

covMatrix = np.zeros([freqLen, 2, 2])
basisMatrix = np.zeros([freqLen, 2, 2])
covMatrixMagPhase = np.zeros([freqLen, 2, 2])
#eigvals = np.zeros(freqLen, 2)
#eigvecs = np.zeros(freqLen, 2, 2)

# Define the basis matrix,
# make the covariance matrix in real and imaginary basis,
# and change to magnitude and phase
basisMatrix[:, 0, 0] = dz_da
basisMatrix[:, 0, 1] = dz_db
basisMatrix[:, 1, 0] = dphi_da
basisMatrix[:, 1, 1] = dphi_db
magUnc = np.zeros(freqLen)
phaseUnc = np.zeros(freqLen)
for ii in np.arange(freqLen):
    covMatrix[ii, :, :] = np.cov(np.array([real[:, ii], imag[:, ii]]))

    curBasisMatrix = basisMatrix[ii, :, :]
    curBasisMatrixTranspose = np.transpose(curBasisMatrix)
    covMatrixMagPhase[ii, :, :] = curBasisMatrix.dot(
        covMatrix[ii, :, :].dot(curBasisMatrixTranspose))

    magUnc[ii] = np.sqrt(covMatrixMagPhase[ii, 0, 0])
    phaseUnc[ii] = np.sqrt(covMatrixMagPhase[ii, 1, 1])

#  eigvals, eigvecs = np.linalg.eig(covMatrix[ii,:,:])
#  eigvecs[ii,:] = np.sqrt(eigvecs[ii,:])

# Make da plot
h = plt.figure()
f1 = h.add_subplot(221)
f2 = h.add_subplot(222)
f3 = h.add_subplot(223)
f4 = h.add_subplot(224)
max1Range = -np.inf
min1Range = np.inf
max2Range = -np.inf
min2Range = np.inf
max3Range = -np.inf
min3Range = np.inf
max4Range = -np.inf
min4Range = np.inf

maxDomain = -np.inf
minDomain = np.inf


for key in plotDict.keys():
    tempFreq = plotDict[key][:, 0]
    if magdB:
        tempSpec = 10**(plotDict[key][:, 1] / 20) * yConv
    else:
        tempSpec = plotDict[key][:, 1] * yConv
    tempPhas = plotDict[key][:, 2]

    tempRel = tempSpec * np.exp(1j * tempPhas) / compMean
    tempRelS = np.abs(tempRel)
    tempRelP = np.angle(tempRel)

    if loglog == True:
        f1.loglog(tempFreq, tempSpec,
                  color=tcolor, label=labels[key],
                  alpha=alpha1, rasterized=True)
    elif semilogx == True:
        f1.semilogx(tempFreq, tempSpec,
                    color=tcolor, label=labels[key],
                    alpha=alpha1, rasterized=True)
    else:
        f1.plot(tempFreq, tempSpec,
                color=tcolor, label=labels[key],
                alpha=alpha1, rasterized=True)

    f3.semilogx(tempFreq, 180 / np.pi * tempPhas,
                color=tcolor, alpha=alpha1, rasterized=True)

    f2.semilogx(tempFreq, 100 * (tempRelS - 1.0),
                color=tcolor, alpha=alpha1, rasterized=True)
    f4.semilogx(tempFreq, 180 / np.pi * tempRelP,
                color=tcolor, alpha=alpha1, rasterized=True)

    if max(tempSpec) > max1Range:
        max1Range = max(tempSpec)
    if min(tempSpec) < min1Range:
        min1Range = min(tempSpec)

    if max(100.0 * (tempRelS - 1.0)) > max2Range:
        max2Range = max(100.0 * (tempRelS - 1.0))
    if min(100.0 * (tempRelS - 1.0)) < min2Range:
        min2Range = min(100.0 * (tempRelS - 1.0))

    if max(180 / np.pi * tempPhas) > max3Range:
        max3Range = max(180 / np.pi * tempPhas)
    if min(180 / np.pi * tempPhas) < min3Range:
        min3Range = min(180 / np.pi * tempPhas)

    if max(180 / np.pi * tempRelP) > max4Range:
        max4Range = max(180 / np.pi * tempRelP)
    if min(180 / np.pi * tempRelP) < min4Range:
        min4Range = min(180 / np.pi * tempRelP)

    if max(tempFreq) > maxDomain:
        maxDomain = max(tempFreq)
    if min(tempFreq) < minDomain:
        minDomain = min(tempFreq)


if loglog == True:
    f1.loglog(tempFreq, np.abs(compMean),
              color=mcolor, label='Median', alpha=alpha2, rasterized=True)
    f1.loglog(tempFreq, np.abs(compMean) + magUnc,
              ls='--', color=uncolor, rasterized=True,
              label='$\pm 1 \sigma$ Unc', alpha=alpha3)
    f1.loglog(tempFreq, np.abs(compMean) - magUnc, rasterized=True,
              ls='--', color=uncolor, alpha=alpha3)
elif semilogx == True:
    f1.semilogx(tempFreq, np.abs(compMean),
                color=mcolor, label='Median', alpha=alpha2, rasterized=True)
    f1.semilogx(tempFreq, np.abs(compMean) + magUnc,
                ls='--', color=uncolor, rasterized=True,
                label='$\pm 1 \sigma$ Unc', alpha=alpha3)
    f1.semilogx(tempFreq, np.abs(compMean) - magUnc, rasterized=True,
                ls='--', color=uncolor, alpha=alpha3)
else:
    f1.plot(tempFreq, np.abs(compMean),
            color=mcolor, label='Median', alpha=alpha2, rasterized=True)
    f1.plot(tempFreq, np.abs(compMean) + magUnc, rasterized=True,
            ls='--', color=uncolor,
            label='$\pm 1 \sigma$ Unc', alpha=alpha3)
    f1.plot(tempFreq, np.abs(compMean) - magUnc,
            ls='--', color=uncolor, alpha=alpha3, rasterized=True)

f3.semilogx(tempFreq, 180 / np.pi * np.angle(compMean),
            color=mcolor, alpha=alpha2, rasterized=True)
f3.semilogx(tempFreq, 180 / np.pi * (np.angle(compMean) + phaseUnc),
            ls='--', color=uncolor, label=r'$\pm 1 \sigma$ Unc',
            alpha=alpha3, rasterized=True)
f3.semilogx(tempFreq, 180 / np.pi * (np.angle(compMean) - phaseUnc),
            ls='--', color=uncolor, alpha=alpha3, rasterized=True)

# f2.semilogx(tempFreq, np.zeros(freqLen),
#                  color=mcolor, label='Median', alpha = alpha2)
f2.semilogx(tempFreq, 100 * magUnc / np.abs(compMean),
            ls='--', color=uncolor,
            label='$\pm 1 \sigma$ Unc', alpha=alpha3, rasterized=True)
f2.semilogx(tempFreq, 100 * -magUnc / np.abs(compMean),
            ls='--', color=uncolor, alpha=alpha3, rasterized=True)

# f4.semilogx(tempFreq, np.zeros(freqLen),
#      color=mcolor, alpha = alpha2)
f4.semilogx(tempFreq, 180 / np.pi * phaseUnc,
            ls='--', label=r'$\pm 1 \sigma$ Unc', color=uncolor,
            alpha=alpha3, rasterized=True)
f4.semilogx(tempFreq, -180 / np.pi * phaseUnc,
            ls='--', color=uncolor, alpha=alpha3, rasterized=True)


# Plot settings and titles
f1.legend()
f2.legend()
f3.legend()
f4.legend()

if args.yAxisLimitPercent is not None:
    min2Range = -args.yAxisLimitPercent[0]
    max2Range = args.yAxisLimitPercent[0]
if args.yAxisLimitDegrees is not None:
    min4Range = -args.yAxisLimitDegrees[0]
    max4Range = args.yAxisLimitDegrees[0]

f1.set_xlim([minDomain, maxDomain])
f2.set_xlim([minDomain, maxDomain])
f3.set_xlim([minDomain, maxDomain])
f4.set_xlim([minDomain, maxDomain])

f1.set_ylim([min1Range, max1Range])
f2.set_ylim([min2Range, max2Range])
f3.set_ylim([min3Range, max3Range])
f4.set_ylim([min4Range, max4Range])

f3.set_yticks(range(-180, 182, 45))
f1.grid(which='minor')
f1.set_axisbelow(True)
f2.grid(which='minor')
f2.set_axisbelow(True)
f3.grid(which='minor')
f3.set_axisbelow(True)
f4.grid(which='minor')
f4.set_axisbelow(True)

f1.set_ylabel(yAxisLabel)
f2.set_ylabel(y2AxisLabel)
f3.set_ylabel(y3AxisLabel)
f4.set_ylabel(y4AxisLabel)

f3.set_xlabel(xAxisLabel)
f4.set_xlabel(xAxisLabel)

f1.set_title(plotLeftTitle)
f2.set_title(plotRightTitle)

h.suptitle(plotTitle)

h.subplots_adjust(wspace=0.25)

plt.savefig(pathToPlots + plotSaveName + '_FourSquare.pdf',
            bbox_inches='tight', pad_inches=0.2)

# Make da plot
h = plt.figure()
f1 = h.add_subplot(211)
f3 = h.add_subplot(212)

max1Range = -np.inf
min1Range = np.inf
max2Range = -np.inf
min2Range = np.inf
max3Range = -np.inf
min3Range = np.inf
max4Range = -np.inf
min4Range = np.inf

maxDomain = -np.inf
minDomain = np.inf


for key in plotDict:
    tempFreq = plotDict[key][:, 0]
    if magdB:
        tempSpec = 10**(plotDict[key][:, 1] / 20) * yConv
    else:
        tempSpec = plotDict[key][:, 1] * yConv
    tempPhas = np.pi / 180 * plotDict[key][:, 2]

    if loglog == True:
        f1.loglog(tempFreq, tempSpec,
                  color=tcolor,
                  label=labels[key], alpha=alpha1)
    elif semilogx == True:
        f1.semilogx(tempFreq, tempSpec,
                    color=tcolor,
                    label=labels[key], alpha=alpha1)
    else:
        f1.plot(tempFreq, tempSpec,
                color=tcolor,
                label=labels[key], alpha=alpha1)

    f3.semilogx(tempFreq, 180 / np.pi * tempPhas,
                color=tcolor, alpha=alpha1)

    if max(tempSpec) > max1Range:
        max1Range = max(tempSpec)
    if min(tempSpec) < min1Range:
        min1Range = min(tempSpec)

    if max(180 / np.pi * tempPhas) > max3Range:
        max3Range = max(180 / np.pi * tempPhas)
    if min(180 / np.pi * tempPhas) < min3Range:
        min3Range = min(180 / np.pi * tempPhas)

    if max(tempFreq) > maxDomain:
        maxDomain = max(tempFreq)
    if min(tempFreq) < minDomain:
        minDomain = min(tempFreq)


if loglog == True:
    f1.loglog(tempFreq, np.abs(compMean),
              color=mcolor, label='Mean',
              alpha=alpha1)
    f1.loglog(tempFreq, np.abs(compMean) + magUnc,
              ls='--', color=uncolor,
              label='$\pm 1 \sigma$ Unc', alpha=alpha2)
    f1.loglog(tempFreq, np.abs(compMean) - magUnc,
              ls='--', color=uncolor,
              alpha=alpha3)
elif semilogx == True:
    f1.semilogx(tempFreq, np.abs(compMean),
                color=mcolor, label='Mean', alpha=alpha2)
    f1.semilogx(tempFreq, np.abs(compMean) + magUnc,
                ls='--', color=uncolor,
                label=r'$\pm 1 \sigma$ Unc',
                alpha=alpha3)
    f1.semilogx(tempFreq, np.abs(compMean) - magUnc,
                ls='--', color=uncolor, alpha=alpha3)
else:
    f1.plot(tempFreq, np.abs(compMean),
            color=mcolor, label='Mean', alpha=alpha2)
    f1.plot(tempFreq, np.abs(compMean) + magUnc,
            ls='--', color=uncolor,
            label='$\pm 1 \sigma$ Unc', alpha=alpha3)
    f1.plot(tempFreq, np.abs(compMean) - magUnc,
            ls='--', color=uncolor, alpha=alpha3)

f3.semilogx(tempFreq, 180 / np.pi * np.angle(compMean),
            color=mcolor, alpha=alpha2)
f3.semilogx(tempFreq, 180 / np.pi * (np.angle(compMean) + phaseUnc),
            ls='--', color=uncolor, label='$\pm 1 \sigma$ Unc', alpha=alpha3)
f3.semilogx(tempFreq, 180 / np.pi * (np.angle(compMean) - phaseUnc),
            ls='--', color=uncolor, alpha=alpha3)


# Plot settings and titles
f1.set_xlim([minDomain, maxDomain])
f3.set_xlim([minDomain, maxDomain])

f1.set_ylim([min1Range, max1Range])
f3.set_ylim([min3Range, max3Range])

f3.set_yticks([-180, -90, 0, 90, 180])
f1.grid(which='minor', alpha=0.4, linestyle='--')
f1.set_axisbelow(True)
f3.grid(which='minor', alpha=0.4, linestyle='--')
f3.set_axisbelow(True)

f1.set_ylabel(yAxisLabel)
f3.set_ylabel(y3AxisLabel)

f3.set_xlabel(xAxisLabel)


f1.set_title(plotTitle + curDateLabel)
h.subplots_adjust(wspace=0.25)
plt.savefig(pathToPlots + plotSaveName + '_JustBode.pdf',
            bbox_inches='tight', pad_inches=0.2)

# Merge PDFs into one page (OMG, please use PyPDF2)
if MergePlots:
    command = 'gs -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -sOutputFile=' + pathToPlots + plotSaveName + \
        '.pdf' + ' ' + pathToPlots + plotSaveName + '_FourSquare.pdf ' + \
        pathToPlots + plotSaveName + '_JustBode.pdf'
    print(' ')
    log.debug('Running $', command)
    print
    try:
        os.system(command)
    except BaseException:
        print "WARNING: problem running GhostScript"

# Make tar automatically if --tar is set
if not args.notar:
    tarCommand = 'tar -cvzf ' + plotSaveName + '.tgz '
    for ff in args.files:
        tarCommand = tarCommand + ff.name + ' '
    #tarCommand = tarCommand + pathToPlots + plotSaveName +'_Merged.pdf '
    tarCommand = tarCommand + __file__

    print
    log.debug('Running ' + tarCommand)
    print
    try:
        FNULL = open(os.devnull, 'w')
        subprocess.call(tarCommand,
                        shell=True, stdout=FNULL, stderr=subprocess.STDOUT)
        log.info("TAR file successfully created.")
    except BaseException:
        log.warning("TAR: some tar syntax issues.")
