#!/APSshare/anaconda/x86_64/bin/python2.7

#____________________________________________________________________
#  qtGSD_GUI.py
#
#  This program imports from a Qt Designer files and adds python code	
#  
#     NOTE: It reqiuires Pete's OCTAVE style Data Arrays, where each ROW contains
#			the data for a single strip or pixel.  It relies on headers
#			to get the number of pixels, and bit depth
#
#  Authors:	Russ Woods
#     Date:	7/8/2015
#			8/27/2016  - converted from MAIA to GSD
#			9/1/2016   - added multiple plots to canvas
#			6/6/2017   - remove Output File choice, added filename copy down, added image options
#			6/9/2017   - fixed comboBox lists, so they are cleared each time data is loaded
#			12/13/2017 - removed calibration and epics stuff
#____________________________________________________________________


import sys
import os
from PyQt4 import QtCore, QtGui
from qtGSD_DESIGN import Ui_MainWindow
#from dialog import Ui_Dialog
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as pyPlot
from subprocess import call
import numpy as np
import linecache  # Not sure that I still need this


# Globals:
numHeaderLines = 4

class MainDialog(QtGui.QMainWindow):
	'''This class modifies the GUI crrated by Qt-Designer'''

	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self, parent)

		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)

		# Prepare 2nd Window
		self.window2 = None

		# Modify Group Box borders
		self.ui.groupBox.setStyleSheet("QGroupBox { border:1px solid 'black';}")
		self.ui.groupBox_2.setStyleSheet("QGroupBox { border:1px solid 'black';}")
		self.ui.groupBox_3.setStyleSheet("QGroupBox { border:1px solid rbg(0,0,0);}")

		# A figure instance to plot on and the Canvas Widget that displays the `figure`
		# NOTE: it takes the `figure` instance as a parameter to __init__
		self.figure1 = pyPlot.figure()
		self.canvas1 = FigureCanvas(self.figure1)
		self.ui.MainVertLayout.addWidget(self.canvas1)

		# Add the Navigation widget toolbar
		# NOTE: it takes the Canvas widget and a parent
		self.navToolbar1 = NavigationToolbar(self.canvas1, self)
		self.addToolBar(self.navToolbar1)

		# Connect the 'Browse' button to 'selectFile()'
		self.ui.browserButton.clicked.connect(self.selectFile)
		self.ui.browserButton.setToolTip('Click Browse for Binary Decoder File')

		# Connect the 'Browse_3' button to 'selectFile()'
		self.ui.browserButton_3.clicked.connect(self.selectFile_3)
		self.ui.browserButton_3.setToolTip('Click to Browse for Input Binary file')

		# Connect the 'Browse_7' button to 'selectFile()'
		self.ui.browserButton_7.clicked.connect(self.selectFile_7)
		self.ui.browserButton_7.setToolTip('Click to Browse for Output file')

		# Connect the 'Run' button to 'parseBinaryFile()'
		self.ui.runButton.clicked.connect(self.parseBinaryFile)
		self.ui.runButton.setToolTip('Click to convert selected binary file')

		# Connect the 'Browse_4' button to 'selectFile()'
		self.ui.browserButton_4.clicked.connect(self.selectFile_4)
		self.ui.browserButton_4.setToolTip('Click to Browse for .dat file')

		# Connect the 'Load' button to 'selectFile()'
		self.ui.loadButton.clicked.connect(self.loadDatFile)
		self.ui.loadButton.setToolTip('Click to Browse for .dat file')

		# Connect the PlotButton to a method
		self.ui.plotButton.clicked.connect(self.plot)
		self.ui.plotButton.setToolTip('Click to plot .mca file')

		# Connect the 'Clear' button to 'clearPlot()'
		self.ui.clearPlotButton.clicked.connect(self.clearPlot)
		self.ui.clearPlotButton.setToolTip('Click to clear canvas')

		# Connect the 'Plot All' button to 'plotAll'
		self.ui.plotRangeButton.clicked.connect(self.plotRange)
		self.ui.plotRangeButton.setToolTip('Click to plot ALL strips')

		# Connect the 'Plot Image' button to 'plotImage()'
		self.ui.plotImageButton.clicked.connect(self.plotImage)
		self.ui.plotImageButton.setToolTip('Click to plot image')

		# Connect the 'Plot Strips' button to 'plotStrips()'
		self.ui.plotStripsButton.clicked.connect(self.plotStrips)
		self.ui.plotStripsButton.setToolTip('Click to plot strips')

	def selectFile(self):
		print 'select a Decoder file!'
		self.fileDialog = QtGui.QFileDialog(self)
		self.ui.filePathEdit_3.setText(self.fileDialog.getOpenFileName())

	def selectFile_3(self):
		print 'select an Input file!'
		self.fileDialog = QtGui.QFileDialog(self)
		self.ui.filePathEdit_5.setText(self.fileDialog.getOpenFileName())
		self.ui.filePathEdit_7.setText(self.ui.filePathEdit_5.text())
		self.ui.filePathEdit_4.setText(self.ui.filePathEdit_5.text() + str('.mca'))

	def selectFile_7(self):
		print 'select a Output file!'
		self.fileDialog = QtGui.QFileDialog(self)
		self.ui.filePathEdit_7.setText(self.fileDialog.getOpenFileName())

	def selectFile_4(self):
		print 'select an Output file!'
		self.fileDialog = QtGui.QFileDialog(self)
		self.ui.filePathEdit_4.setText(self.fileDialog.getOpenFileName())

	def parseBinaryFile(self):
		# Grab the file paths entered in the GUI
		callList = [str(self.ui.filePathEdit_3.text()), str(self.ui.filePathEdit_5.text()), str(self.ui.filePathEdit_7.text())]
		# Execute the GSD Parse Binary script, which creates .mca and .tdc files
		call(callList)

	def loadDatFile(self):
		# Make a Data List
		dataList = []

		# Read from new dataFile
		# (#name:, #type:, #rows:, #columns:,)
		dataFile = open(self.ui.filePathEdit_4.text(), 'r')
		for line in dataFile:
			if '#name:' in line:
				self.dataOrigin = line.split(':')[1]
				print 'dataOrigin = ' + str(self.dataOrigin)

			elif '#type:' in line:
				self.dataType = line.split(':')[1]
				print 'dataType = ' + str(self.dataType)

			elif '#rows:' in line: 
				self.numStrips = int(line.split(':')[1])
				print 'numStrips = ' + str(self.numStrips)

			elif '#columns:' in line: 
				self.numChannels = int(line.split(':')[1])
				print 'numChannels = ' + str(self.numChannels)

			else:
				# Read the data into an (numStrips)x(1) list
				dataList.append(line.split())
		dataFile.close() 

		# Call buildComboBox
		self.buildComboBoxList()

		# Convert dataList to global numpy array
		self.dataArray = np.asarray(dataList, int)
		print self.dataArray

		# Integrate counts on each strip
		self.dataArrayTotalCounts = np.sum(self.dataArray, axis=1)
		print 'Total Number of Events = ' + str(np.sum(self.dataArrayTotalCounts))

		# Populate ComboBox_2 with Color Map choices
		self.buildColorMapComboBox()

	def buildComboBoxList(self):
		print 'building checkBoxes!'

		# Important to always clear the comboBox otherwise the number of entries will duplicate each time a new data file is loaded.
		self.ui.comboBox.clear()
		self.ui.comboBox_R1.clear()
		self.ui.comboBox_R2.clear()

		for i in range(0, self.numStrips):
			self.ui.comboBox.addItem('pixel_' + str(i))
			self.ui.comboBox_R1.addItem('pixel_' + str(i))
			self.ui.comboBox_R2.addItem('pixel_' + str(i))

	def buildColorMapComboBox(self):
		# Add choices for Image Plot colour mapping
		self.ui.comboBox_2.clear()
		self.ui.comboBox_2.addItem('hot')
		self.ui.comboBox_2.addItem('inferno')
		self.ui.comboBox_2.addItem('gray')
		self.ui.comboBox_2.addItem('seismic')
		self.ui.comboBox_2.addItem('prism')
		self.ui.comboBox_2.addItem('plasma')
		self.ui.comboBox_2.addItem('winter')
		self.ui.comboBox_2.addItem('spring')
		self.ui.comboBox_2.addItem('summer')
		self.ui.comboBox_2.addItem('autumn')

	def plot(self):
		print 'plotButton pressed!'

		# Give the file and line number, but skip the header lines:
		# (#name: spect, #type: matrix, #rows: 384, #columns: 4096)
		stripNumber = int(self.ui.comboBox.currentText().split('_')[1])

		# create a sub plot
		self.figure1.add_subplot(111)

		# plot the data
		pyPlot.plot(self.dataArray[stripNumber], '-', label=str(stripNumber))

		# add labels
		pyPlot.title(self.dataType, fontsize=16)
		pyPlot.xlabel('Energy (ADC units)', fontsize=10)
		pyPlot.ylabel('Counts', fontsize=10)

		# add legend
		newLeg = pyPlot.legend(loc=1, frameon=True, fancybox=True, shadow=False, mode='none', title='Pixel' )
		
		# change the colour
		self.figure1.set_facecolor('white')

		# refresh the canvas
		self.canvas1.draw_idle()

	def plotRange(self):
		print 'plot multiple strips!'

		lowStrip = int(self.ui.comboBox_R1.currentText().split('_')[1])
		highStrip = int(self.ui.comboBox_R2.currentText().split('_')[1])

		for pixel in range(lowStrip, highStrip+1):
			tempIndex = self.ui.comboBox.findText('pixel_' + str(pixel))
			self.ui.comboBox.setCurrentIndex(tempIndex)
			self.plot()
			
	def clearPlot(self):
		print 'clear plot!'
		self.figure1.clf()
		self.canvas1.draw()

	def plotImage(self):
		print 'plot all strips with spectrum as a image!'			
		self.figure1.clf()

		# Plot as image, cmap(spectral, hot,), aspect(changes pixel ratio)   
		#pyPlot.imshow(self.dataArray, cmap='hot', interpolation='nearest', aspect=10) # clim=(0, 500))
		if(self.ui.checkBox.isChecked()):
			pyPlot.imshow(np.log10(self.dataArray), cmap=str(self.ui.comboBox_2.currentText()), interpolation='nearest', aspect=10) # clim=(0, 500))
		else:
			pyPlot.imshow(self.dataArray, cmap=str(self.ui.comboBox_2.currentText()), interpolation='nearest', aspect=10) # clim=(0, 500))

		pyPlot.title('Spectrum from each Strip')
		pyPlot.xlabel('Energy (ADC units)')
		pyPlot.ylabel('Strip Address')
		pyPlot.colorbar(spacing='uniform', fraction=0.01, pad=0.01, orientation='vertical')		#TODO: Fix the scale when plotting in log
		self.figure1.set_facecolor('white')
		self.canvas1.draw_idle()

	def plotStrips(self):
		print 'plot all strips with integrated counts'				
		self.figure1.clf()
		#pyPlot.fill(np.arange(0, self.numStrips, 1), self.dataArrayTotalCounts, 'yellow', alpha=0.5)
		pyPlot.bar(np.arange(0, self.numStrips, 1), self.dataArrayTotalCounts, width=1, color='blue', alpha=0.5)
		pyPlot.title('Total Counts per Strip')
		pyPlot.xlabel('Strip Address')
		pyPlot.ylabel('Counts')
		pyPlot.grid(True)
		self.figure1.set_facecolor('white')
		self.canvas1.draw_idle()

#__________________________________________________
# Run the GUI program 
if __name__ == '__main__':
	app = QtGui.QApplication(sys.argv)

	window = MainDialog()
	window.show()

	sys.exit(app.exec_())





