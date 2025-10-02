//=============================================================================
// Copyright � 2001 Point Grey Research, Inc. All Rights Reserved.
// 
// This software is the confidential and proprietary information of Point
// Grey Research, Inc. ("Confidential Information").  You shall not
// disclose such Confidential Information and shall use it only in
// accordance with the terms of the license agreement you entered into
// with Point Grey Research, Inc. (PGR).
// 
// PGR MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT THE SUITABILITY OF THE
// SOFTWARE, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
// PURPOSE, OR NON-INFRINGEMENT. PGR SHALL NOT BE LIABLE FOR ANY DAMAGES
// SUFFERED BY LICENSEE AS A RESULT OF USING, MODIFYING OR DISTRIBUTING
// THIS SOFTWARE OR ITS DERIVATIVES.
//
// Digiclops� is a registered Trademark of Point Grey Research Inc.
//=============================================================================
//=============================================================================
// $Id: PGRFlyCaptureTimestampTest.cpp,v 1.3 2006/08/11 21:14:15 mgibbons Exp $
//=============================================================================

//=============================================================================
//
// PGRFlyCaptureTest.cpp
//   - Grabs a few images and saves the last to disk.
//
//=============================================================================

//=============================================================================
// System Includes
//=============================================================================
#include <assert.h>
#include <stdio.h>
#include <sys/timeb.h>
#include <math.h>
#include <windows.h>

//=============================================================================
// Project Includes
//=============================================================================
#include "pgrflycapture.h"


#define NUM_GRABS 50

// returns true if no errors are found, false if an error is found
bool errCheck( FlyCaptureError err, const char* szFunc )
{
   if( err != FLYCAPTURE_OK )
   {
      printf( "%s: %s\n<press return>\n", szFunc, flycaptureErrorToString( err ) );
      getchar();
      return false;
   }

   return true;
}

int diff( unsigned int a, unsigned int b )
{
   if( a > b )
      return a - b;

   return b - a;
}

inline double 
imageTimeStampToSeconds(unsigned int uiRawTimestamp)
{

   int nSecond      = (uiRawTimestamp >> 25) & 0x7F;   // get rid of cycle_* - keep 7 bits
   int nCycleCount  = (uiRawTimestamp >> 12) & 0x1FFF; // get rid of offset
   int nCycleOffset = (uiRawTimestamp >>  0) & 0xFFF;  // get rid of *_count

   return (double)nSecond + (((double)nCycleCount+((double)nCycleOffset/3072.0))/8000.0);
}

int 
main( int /* argc */, char* /* argv[] */ )
{
   FlyCaptureError	error;
   FlyCaptureContext	context1;
   FlyCaptureContext	context2;
   bool			bHiRes1;
   bool			bHiRes2;

   // image returned by flycaptureGrabImage2().
   FlyCaptureImage   image1;
   FlyCaptureImage   image2;

   //
   // Initialize the image structure to sane values
   //
   image1.iCols = 0;
   image1.iRows = 0;
   image2.iCols = 0;
   image2.iRows = 0;

   // enumerate the cameras on the bus
   FlyCaptureInfo arInfo[ 32 ];
   unsigned int	 uiSize;
   error = flycaptureBusEnumerateCameras( arInfo, &uiSize );
   if( !errCheck( error, "flycaptureBusEnumerateCameras()" ) ) return 1;
   
   // create the flycapture contexts.
   error = flycaptureCreateContext( &context1 );
   if( !errCheck( error, "flycaptureCreateContext()" ) ) return 1;
   
   error = flycaptureCreateContext( &context2 );
   if( !errCheck( error, "flycaptureCreateContext()" ) ) return 1;

   // initialize the first camera on the bus.
   error = flycaptureInitialize( context1, 0 );
   if( !errCheck( error, "flycaptureInitialize()" ) ) return 1;

   // initialize the second camera on the bus.
   error = flycaptureInitialize( context2, 1 );
   if( !errCheck( error, "flycaptureInitialize()" ) ) return 1;

   // figure out if they're high or low res
   error = flycaptureCheckVideoMode( context1, FLYCAPTURE_VIDEOMODE_1024x768Y8,
				     FLYCAPTURE_FRAMERATE_15, &bHiRes1 );
   if( !errCheck( error, "flycaptureCheckVideoMode()" ) ) return 1;
   if (bHiRes1 )
   {
      printf("Camera 1 is a high resolution camera.\n");
   }
   else
   {
      printf("Camera 1 is a low resolution camera.\n");
   }

   error = flycaptureCheckVideoMode( context2, FLYCAPTURE_VIDEOMODE_1024x768Y8,
				     FLYCAPTURE_FRAMERATE_15, &bHiRes2 );
   if( !errCheck( error, "flycaptureCheckVideoMode()" ) ) return 1;
   if (bHiRes2 )
   {
      printf("Camera 2 is a high resolution camera.\n");
   }
   else
   {
      printf("Camera 2 is a low resolution camera.\n");
   }


   //
   // start grabbing images in 8-bit greyscale mode with a frame rate of 15
   // fps.
   //
   FlyCaptureVideoMode camera1VideoMode = 
      (bHiRes1 ? FLYCAPTURE_VIDEOMODE_1024x768Y8 : FLYCAPTURE_VIDEOMODE_640x480Y8);
   FlyCaptureVideoMode camera2VideoMode =
      (bHiRes2 ? FLYCAPTURE_VIDEOMODE_1024x768Y8 : FLYCAPTURE_VIDEOMODE_640x480Y8);
   FlyCaptureFrameRate frameRate = 
      ((bHiRes1 || bHiRes2) ? FLYCAPTURE_FRAMERATE_15 : FLYCAPTURE_FRAMERATE_30 );
   double dFrameRate = ((bHiRes1 || bHiRes2) ? 1.0/15.0 : 1.0/30.0 );

   error = flycaptureStart( 
      context1, camera1VideoMode, frameRate );
   if( !errCheck( error, "flycaptureStart()" ) ) return 1;
   
   error = flycaptureStart( 
      context2, camera2VideoMode, frameRate );
   if( !errCheck( error, "flycaptureStart()" ) ) return 1;

   printf("Frame rate %lf fps\n",1.0/dFrameRate );

  


   // not neccessary...
   flycaptureSetColorProcessingMethod( context1, FLYCAPTURE_DISABLE );
   flycaptureSetColorProcessingMethod( context2, FLYCAPTURE_DISABLE );

   // turn on timestamping
   unsigned long ulRegister = 0x12f8;
   unsigned long ulValue;
   error = flycaptureGetCameraRegister( context1, ulRegister, &ulValue );
   if( !errCheck( error, "flycaptureGetCameraRegister()" ) ) return 1;

   //
   // ensure time stamping is present...
   //
   if (!( ulValue & 0x80000000))
   {
      printf("Camera 1 does not support the timestamp feature - upgrade firmware\n");
      return 1;
   }

   error = flycaptureGetCameraRegister( context2, ulRegister, &ulValue );
   if( !errCheck( error, "flycaptureGetCameraRegister()" ) ) return 1;

   //
   // ensure time stamping is present...
   //
   if (!( ulValue & 0x80000000))
   {
      printf("Camera 2 does not support the timestamp feature - upgrade firmware\n");
      return 1;
   }

   error = flycaptureSetCameraRegister( context1, ulRegister, ulValue | 1 );
   if( !errCheck( error, "flycaptureSetCameraRegister()" ) ) return 1;

   error = flycaptureSetCameraRegister( context2, ulRegister, ulValue | 1 );
   if( !errCheck( error, "flycaptureSetCameraRegister()" ) ) return 1;

   // get room for NUM_GRABS timestamps
   unsigned int stamps1[ NUM_GRABS ];
   unsigned int stamps2[ NUM_GRABS ];
   double ardTimeDifferences[ NUM_GRABS ];
   unsigned char* pStamp1 = (unsigned char*)&stamps1;
   unsigned char* pStamp2 = (unsigned char*)&stamps2;

   // grab NUM_GRABS images and save the timestamps
   int i = 0;
   int nTotalGrabs = 0;
   double dTimeDiff = 0;
   while (i < NUM_GRABS )
   {
      
      if( flycaptureGrabImage2( context1, &image1 ) != FLYCAPTURE_OK )
      {
	 printf( "Failed to grab image.\n" );
	 return false;
      }

      if( flycaptureGrabImage2( context2, &image2 ) != FLYCAPTURE_OK )
      {
	 printf( "Failed to grab image.\n" );
	 return false;
      }
      nTotalGrabs++;

      /* strictly little endian... */
      pStamp1[ (i * 4) + 0 ] = image1.pData[3];
      pStamp1[ (i * 4) + 1 ] = image1.pData[2];
      pStamp1[ (i * 4) + 2 ] = image1.pData[1];
      pStamp1[ (i * 4) + 3 ] = image1.pData[0];

      pStamp2[ (i * 4) + 0 ] = image2.pData[3];
      pStamp2[ (i * 4) + 1 ] = image2.pData[2];
      pStamp2[ (i * 4) + 2 ] = image2.pData[1];
      pStamp2[ (i * 4) + 3 ] = image2.pData[0];

      double dTime1 = imageTimeStampToSeconds(stamps1[i]);
      double dTime2 = imageTimeStampToSeconds(stamps2[i]);

      if( fabs(dTime1-dTime2) < dFrameRate/2.0 )
      {
	 ardTimeDifferences[i] = fabs( dTime1 - dTime2);
	 dTimeDiff += ardTimeDifferences[i];
	 i++;
      }
      else
      {
	 Sleep( (unsigned long)(1000.0*dFrameRate));
      }
   }

   FILE* pFile = fopen( "stamps.txt", "w" );
   fprintf(pFile, "sec\tcyc_co\tcyc_off\thex"
      "\t\tsec\tcyc_co\tcyc_off\thex\t\ttime diff (ms)\n");
   for( i = 0; i < NUM_GRABS; i++ )
   {
      unsigned int second_count1;
      unsigned int second_count2;
      unsigned int cycle_count1;
      unsigned int cycle_count2;
      unsigned int cycle_offset1;
      unsigned int cycle_offset2;

      second_count1 = (stamps1[ i ] >> 25) & 0x7F; // get rid of cycle_* - keep 7 bits
      second_count2 = (stamps2[ i ] >> 25) & 0x7F; // get rid of cycle_* - keep 7 bits

      cycle_count1 = (stamps1[ i ] >> 12) & 0x1FFF; // get rid of offset
      cycle_count2 = (stamps2[ i ] >> 12) & 0x1FFF; // get rid of offset

      cycle_offset1 = (stamps1[ i ] >> 0) & 0xFFF; // get rid of *_count
      cycle_offset2 = (stamps2[ i ] >> 0) & 0xFFF; // get rid of *_count

      fprintf( pFile, "%u\t%u\t%u\t%08X\t%u\t%u\t%u\t%08X\t%1.6lf\n",
	       second_count1, cycle_count1, cycle_offset1, stamps1[i],
	       second_count2, cycle_count2, cycle_offset2, stamps2[i],
	       ardTimeDifferences[i]*1000);
   }
   fclose( pFile );


   // destroy the contexts
   error = flycaptureDestroyContext( context1 );
   if( error != FLYCAPTURE_OK )
   {
      printf( "flycaptureDestroyContext: %s\n", flycaptureErrorToString( error ) );
   }

   error = flycaptureDestroyContext( context2 );
   if( error != FLYCAPTURE_OK )
   {
      printf( "flycaptureDestroyContext: %s\n", flycaptureErrorToString( error ) );
   }

   double dAverageTimeDiff = dTimeDiff/NUM_GRABS;
   double dMaxTimeDiff     = dFrameRate/2.0;
   printf( "Total time difference: %5.3lfms\n"
      "Average time difference: %5.3lfms (worst possible is: %5.3lfms)\n"
      "Total grabs required: %d (%d were requested)\n\n"
      "Press enter to exit",
      dTimeDiff*1000, dAverageTimeDiff*1000, 
      dMaxTimeDiff*1000, nTotalGrabs, NUM_GRABS );
   getchar();
   return 0;
}
