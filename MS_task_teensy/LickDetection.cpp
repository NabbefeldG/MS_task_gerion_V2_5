/*
  Morse.cpp - Library for flashing Morse code.
  Created by David A. Mellis, November 2, 2007.
  Released into the public domain.
*/

#include "Arduino.h"
#include "LickDetection.h"

LickDetection::LickDetection(int SPOUTSENSOR_L, int SPOUTSENSOR_R, int LICK_OUTPUT_LEFT_PIN, int LICK_OUTPUT_RIGHT_PIN) {
  // PINs
  _SPOUTSENSOR_L = SPOUTSENSOR_L; // Spout Left
  _SPOUTSENSOR_R = SPOUTSENSOR_R; // Spout Right

  _LICK_OUTPUT_LEFT_PIN = LICK_OUTPUT_LEFT_PIN; // PIN to send thresholded LickData
  _LICK_OUTPUT_RIGHT_PIN = LICK_OUTPUT_RIGHT_PIN; // PIN to send thresholded LickData

  // Initialize PINs
  pinMode(_LICK_OUTPUT_LEFT_PIN, OUTPUT);
  pinMode(_LICK_OUTPUT_RIGHT_PIN, OUTPUT);

  // Clocks
  adjustClocker = millis(); // timer for re-adjustment of touch lines
  spoutClocker_L = millis(); // timer to measure duration of left lick
  spoutClocker_R = millis(); // timer to measure duration of right lick

  spoutInitialTouchClock_L = millis();
  spoutInitialTouchClock_R = millis();
  usbClocker = millis();

}

void LickDetection::ReadTouchSensors() {
  ////////////////////////////////////////////////////////////////////////////////////////////////////////////
  // Read Data from TouchPins ////////////////////////////////////////////////////////////////////////////////
  ////////////////////////////////////////////////////////////////////////////////////////////////////////////
  touchData[0] = 0.25 * touchRead(_SPOUTSENSOR_L) + 0.75 * touchData[0];
  touchData[1] = 0.25 * touchRead(_SPOUTSENSOR_R) + 0.75 * touchData[1];

  ////////////////////////////////////////////////////////////////////////////////////////////////////////////
  // Recalibrate TouchSensors upon request ///////////////////////////////////////////////////////////////////
  ////////////////////////////////////////////////////////////////////////////////////////////////////////////
  // recompute estimates for mean and standard deviation in each touch line and updates thresholds accordingly
  if (touchAdjust) {
    ++sampleCnt[0];
    for (int i = 0; i < 2; i++) {
      meanTouchVals[i] = meanTouchVals[i] + ((touchData[i] - meanTouchVals[i])/sampleCnt[0]); // update mean
    }
    if ((millis() - adjustClocker) > (touchAdjustDur/2)) { // second part of adjustment: get summed variance
      ++sampleCnt[1];
      for (int i = 0; i < 2; i++) {
        stdTouchVals[i] = stdTouchVals[i] + sq(touchData[i] - meanTouchVals[i]); // update standard deviation (summed variance here)
      }
    }
    if ((millis() - adjustClocker) > touchAdjustDur) {  // done with adjustment
      for (int i = 0; i < 2; i++) {
         stdTouchVals[i] = sqrt(stdTouchVals[i]/sampleCnt[1]) + touchThreshOffset; // compute standard deviation from summed variance
      }
      touchAdjust = false;
    }
    touchThresholdValues[0] = (meanTouchVals[0]+(stdTouchVals[0]*touchThresh));
    touchThresholdValues[1] = (meanTouchVals[1]+(stdTouchVals[1]*touchThresh));
  }

  ////////////////////////////////////////////////////////////////////////////////////////////////////////////
  // check touch lines and create according output ///////////////////////////////////////////////////////////
  ////////////////////////////////////////////////////////////////////////////////////////////////////////////
  if (!touchAdjust) {
    if (touchData[0] > touchThresholdValues[0]) { // signal above 'stdTouchVals' standard deviations indicate lick event. only when spouts dont move.
      digitalWriteFast(_LICK_OUTPUT_LEFT_PIN, HIGH);
      spoutClocker_L = millis(); //update time when spout was last touched
//      if (!spoutTouch_L) {
//        Serial.write(LEFT_SPOUT_TOUCH); // send a byte to bpod if this is an onset event
//      }
      // spoutTouch_L = true;

      if ((!touch_state_L) || (millis() - spoutInitialTouchClock_L > 100)) {
        if (touch_history_ctr < 3) {
          spoutInitialTouchClock_L = millis();
          touch_state_L = true;
          touch_history[touch_history_ctr] = 1;
          touch_history_ctr += 1;
        }
      }
    }
    else {
      digitalWriteFast(_LICK_OUTPUT_LEFT_PIN, LOW);
      if ((millis() - spoutClocker_L) >= sRateLicks) { // check when lever was last touched and set output to low if it happened too long ago.
//        if (spoutTouch_L) {
//          Serial.write(LEFT_SPOUT_RELEASE); // send a byte to bpod if this is an offset event
//        }
        // spoutTouch_L = false;

        if (touch_state_L) {
          touch_state_L = false;
        }
      }
    }

    
    if (touchData[1] > touchThresholdValues[1]) { // signal above 'stdTouchVals' standard deviations indicate lick event. only when spouts dont move.
      digitalWriteFast(_LICK_OUTPUT_RIGHT_PIN, HIGH);
      spoutClocker_R = millis(); //update time when spout was last touched
//      if (!spoutTouch_R) {
//        Serial.write(RIGHT_SPOUT_TOUCH); // send a byte to bpod if this is an onset event
//      }
      // spoutTouch_R = true;

      if ((!touch_state_R) || (millis() - spoutInitialTouchClock_R > 100)) {
        if (touch_history_ctr < 3) {
          spoutInitialTouchClock_R = millis();
          touch_state_R = true;
          touch_history[touch_history_ctr] = 2;
          touch_history_ctr += 1;
        }
      }
    }
    else {
      digitalWriteFast(_LICK_OUTPUT_RIGHT_PIN, LOW);

      if ((millis() - spoutClocker_R) >= sRateLicks) { // check when lever was last touched and set output to low if it happened too long ago.
//        if (spoutTouch_R) {
//          Serial.write(RIGHT_SPOUT_RELEASE); // send a byte to bpod if this is an offset event
//        }
        // spoutTouch_R = false;
        
        if (touch_state_R) {
          touch_state_R = false;
        }
      }
    }

    // now check if the consecutive licks have been acquired
    if (touch_history_ctr > 1) {
      if (touch_history[0] == touch_history[1]) {
        if (touch_history[0] == 1) {
          // left response
          spoutTouch_L = true;
        } else if (touch_history[0] == 2) {
          // right response
          spoutTouch_R = true;
        }
      } else if (touch_history_ctr >= 2) {
        if (touch_history[1] == touch_history[2]) {
          if (touch_history[1] == 1) {
            // left response
            spoutTouch_L = true;
          } else if (touch_history[1] == 2) {
            // right response
            spoutTouch_R = true;
          }
        }
      }
    }
  }
  
  ////////////////////////////////////////////////////////////////////////////////////////////////////////////
  // send some feedback to other serial devices
  ////////////////////////////////////////////////////////////////////////////////////////////////////////////
  
  if ((millis() - usbClocker) >= usbRate){
    usbClocker = millis();
  
    ///////////////////////////////////////////////////
    // send touch data for serial monitor
    for (int i = 0; i < 2; i++) { // send some feedback about touch events
  
      // touchVal = ((touchData[i] / pow(2,16)) * pow(2,8) + (i*20)); // convert value from 16 to 8 bit number
      Serial2.print(touchData[i] + (i*1000)); Serial2.print(",");
    
      // touchVal = (((meanTouchVals[i]+(stdTouchVals[i]*touchThresh))/ pow(2,16)) * pow(2,8) + (i*20)); // convert bound from 16 to 8 bit number
      Serial2.print(touchThresholdValues[i] + (i*1000)); Serial2.print(",");
    }
    Serial2.println();
  }
}

void LickDetection::reset_response_counter() {
  spoutTouch_L = false;
  spoutTouch_R = false;

  touch_state_L = false;
  touch_state_R = false;

  for (int i = 0; i < 3; i++) {
    touch_history[i] = 0;
  }
  touch_history_ctr = 0;
}

void LickDetection::command_AdjustTouchLevel(float new_threshold) {
  touchThresh = new_threshold;
  touchAdjust = true; // flag to adjust touchlevels
  adjustClocker = millis();
  sampleCnt[0] = 0; sampleCnt[1] = 0; // reset counter
  meanTouchVals[0] = 0; meanTouchVals[1] = 0; meanTouchVals[2] = 0; meanTouchVals[3] = 0; // reset mean values
  stdTouchVals[0] = 0; stdTouchVals[1] = 0; stdTouchVals[2] = 0; stdTouchVals[3] = 0; // reset std values
}
