##!/APSshare/anaconda/x86_64/bin/python2.7

import glob
from subprocess import call

# Path to C++ binary file parser (.out)
#parsePath = '/home/beams/RWOODS/Germanium/GSD_Scripts/gsd_parse.out_64'
parsePath = './gsd_parse.out'

# Path to Raw Data Files (.dat)
#rawFileList = glob.glob('r:/1BM_Testing/Data/6bm_gsd64-Dec2016/*.dat')
rawFileList = glob.glob('z:/aa_Detector Development/Ge_Strip_Detector_Siddons/Data/1BMB_2017-1/*.dat')
print rawFileList

# Call c++ parser and provide input and output files
for count, item in enumerate(rawFileList):
	print '...Parsing ' + str(count)
	call([parsePath, item, item.replace('.dat', '')])

print '\nFinished!\n'
