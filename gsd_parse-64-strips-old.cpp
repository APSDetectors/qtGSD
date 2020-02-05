/******************************************************
Program acquires events in binary format from the 
GSD-64 detector, and outputs events in a CSV format.

The input binary format is a stripped down version of
the Maia blogd. A single event consists of 4 bytes containing
the pixel address, the pulse height and time value, 
plus another 4 bytes which is an FPGA clock counter 
intended to give the absolute time the event was read out. 

Together with the TDC value, we hope we can reconstruct 
the arrival time of each photon to a few nanoseconds. 
This is all in aid of doing charge reconstruction 
and/or position interpolation based on charge sharing. 

Data Format Diagram:
_________________________________________________________________________________________________
|               byte_0  |               byte_1  |            byte_2     |               byte_3  |
|31|30|29|28|27|26|25|24|23|22|21|20|19|18|17|16|15|14|13|12|11|10|09|08|07|06|05|04|03|02|01|00|
| 0|                  address |                         tdc |                            energy |
_________________________________________________________________________________________________
_________________________________________________________________________________________________
|               byte_0  |               byte_1  |            byte_2     |               byte_3  |
|31|30|29|28|27|26|25|24|23|22|21|20|19|18|17|16|15|14|13|12|11|10|09|08|07|06|05|04|03|02|01|00|
| 0|                                                                           FPGA clock ticks |
_________________________________________________________________________________________________


Author: 	R.Woods
			P.Siddons
			
Updates: 	8/25/2016

*******************************************************/
#include <stdio.h>
#include <string.h>
#include <iostream>
#include <fstream>
#include <istream>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

using namespace std;

/* Globals */
const unsigned int nStrips = 64 ;
const unsigned int nADCBins = 4096 ;	// 12-bit ADC
const unsigned int nTDCBins = 1024 ;	// 10-bit TDC
unsigned int tempZero, tempAddr, tempTime, tempEnergy, tempClock ;
unsigned int mca[nStrips][nADCBins] ;
unsigned int tdc[nStrips][nTDCBins] ;
unsigned long byteCount = 0 ;
unsigned int verbose = 0 ;
ifstream source ;


//--------------------------------------------------------------------------------------------------------------------
/* Get 4-byte Word Function: */
int get4ByteWord()
{
	unsigned char readBytes[4] ;
	unsigned long word ;
	
	/* Read bytes into char array */
	readBytes[0] = source.get() ; 
	readBytes[1] = source.get() ; 
	readBytes[2] = source.get() ; 
	readBytes[3] = source.get() ; 
	
	/* Increase byte counter */
	//byteCount += 4 ;
	//cout << "byteCount = " << byteCount << endl ;
	
	/* Mask and Shift to build 4-byte word */
    return (readBytes[0] << 0) | (readBytes[1] << 8) | (readBytes[2] << 16) | (readBytes[3] << 24) ;
}
//--------------------------------------------------------------------------------------------------------------------
/* Decode MCA Word: */
void decodeMCAWord(int word)
{
	tempZero = (word >> 31) & ((1 << 1) - 1) ;
	tempAddr = (word >> 22) & ((1 << 9) - 1) ;
	tempTime = (word >> 12) & ((1 << 10) - 1) ;
	tempEnergy = (word >> 0) & ((1 << 12) - 1) ;

	/* print out event */
	//cout << "strip = " << tempAddr << "\t" << "time = " << tempTime << "\t" << "energy = " << tempEnergy << endl ;

	/* increment Arrays */
	/* increment the Spectrum Array */
	mca[tempAddr][tempEnergy] += 1 ;
	tdc[tempAddr][tempTime] += 1 ;
}
//--------------------------------------------------------------------------------------------------------------------
/* Decode FPGA Word: */
void decodeFPGAWord(int word)
{
	tempClock = int(word) ;		// Not sure about this cast!!! Float() yields offset value

	/* Print FPGA Clock time */
	//cout << "fpga time = " << tempClock << endl ;
}
//--------------------------------------------------------------------------------------------------------------------


int main(int argc, char *argv[]) 
{
	/* variables */
	unsigned long tempWord ;
	char outputFile1[256] ;
	char outputFile2[256] ;


	/* Check number of arguments provided */
	if (argc != 3)
	{
		cout << "Missing INPUT & OUTPUT filenames - provide as 2nd and 3rd arguements.\n" ;
	}
	else
	{
		/* open stream to user provided raw data file */
		source.open( argv[1], std::ios_base::binary) ;
		if(source.fail())
		{
			cout << "\n...Unable to open provided file. Please check that filename and path exists." << endl ;
			exit(0) ;
		}

		/* Get the file size in bytes */
		struct stat filestatus;
		stat( argv[ 1 ], &filestatus );
		cout << "...Size of raw data file = " << float(filestatus.st_size)/1000000 << " Mbytes" << endl ;


		/* read the raw data file */
		for(int i=0; i<=(filestatus.st_size)/8-8; i++)
		{
			tempWord = get4ByteWord() ;
			decodeMCAWord(tempWord) ;

			tempWord = get4ByteWord() ;
			decodeFPGAWord(tempWord) ;
		
			//cout << "i = " << i << endl ;
		}
		source.close() ;



		/* Print MCA and TDC files */
		strcpy(outputFile1, argv[2]) ;
		strcat(outputFile1, ".mca");
		ofstream output1(outputFile1) ;

		strcpy(outputFile2, argv[2]) ;
		strcat(outputFile2, ".tdc");
		ofstream output2(outputFile2) ;

		cout << "...Writing ouput files: " << outputFile1 << ", " << outputFile2 << endl ;
		output1 << "\t#name: " << argv[1]  << "\n" ;
		output1 << "\t#type: MCA\n" ;
		output1 << "\t#rows: " << nStrips <<"\n" ;
		output1 << "\t#columns: " << nADCBins << "\n" ;

		output2 << "\t#name: " << argv[1]  << endl ;
		output2 << "\t#type: TDC" << endl ;
		output2 << "\t#rows: " << nStrips << endl ;
		output2 << "\t#columns: " << nTDCBins << endl ;
	
		for(int i=0; i<nStrips; i++)
		{
			for(int j=0; j<nADCBins; j++)
			{
				output1 << mca[i][j] << "  " ;
	
				if(j<nTDCBins) output2 << tdc[i][j] << "  " ;
			}
			output1 << endl ;
			output2 << endl ;
		}
		output1.close() ;
		output2.close() ;
		cout << "...Done." << endl ;

	}
	return 0 ;
}








