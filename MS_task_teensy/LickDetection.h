/*
  Task.h - Library to run MS_Task_V2_0.
  Created by Gerion Nabbefeld, October 8, 2020.
  Released into the public domain.
*/

#ifndef LickDetection_h
#define LickDetection_h

#include "Arduino.h"

class LickDetection {
  public:
    // constructor
    LickDetection(int SPOUTSENSOR_L, int SPOUTSENSOR_R, int LICK_OUTPUT_LEFT_PIN, int LICK_OUTPUT_RIGHT_PIN);

    // Call function
    void ReadTouchSensors();

    // adjustment functions
    void command_AdjustTouchLevel(float new_threshold);

    // resets the counters for the next trials
    void reset_response_counter();

    // Touch variables
    unsigned int touchAdjustDur = 2000; // time used to re-adjust touch levels if neccessary. This will infer the mean (in the first hald) and standard deviation (in the second half) of the read-noise to infer decent thresholds for touch.
    float touchThresh = 5; // threshold for touch event in standard deviation units.
    int touchThreshOffset = 10; // additional offset for touch threshold.
    bool touchAdjust = true; // flag to determine values to detect touches. Do this on startup.
    float touchData[2] = { 0, 0 }; // current values for the four touch lines (left spout, right spout, left, handle, right handle)
    float meanTouchVals[4] = { 0, 0, 0, 0 }; // mean values for the four touch lines (left spout, right spout, left, handle, right handle)
    float stdTouchVals[4] = { 0, 0, 0, 0 }; // stand deviation values for the four touch lines (left spout, right spout, left, handle, right handle)
    float touchVal = 0; // temporary variable for usb communication
    long int sampleCnt[2] = { 0, 0 }; // counter for samples during touch adjustment
    unsigned int usbRate = 10;
    float touchThresholdValues[2] = {0, 0};
    
    // State Values
    bool spoutTouch_L = false; // flag to indicate that left spout is touched
    bool spoutTouch_R = false; // flag to indicate that right spout is touched
    
  private:
    // PINs
    int _SPOUTSENSOR_L; // Spout Left
    int _SPOUTSENSOR_R; // Spout Right
    int _LICK_OUTPUT_LEFT_PIN; // PIN to send thresholded LickData
    int _LICK_OUTPUT_RIGHT_PIN; // PIN to send thresholded LickData

    //
    unsigned int sRateLicks = 5;  // This is the minimum duration of lick events that are send to bpod.

    // state variables to ensure that 
    bool touch_state_L = false;
    bool touch_state_R = false;
    int touch_history[3] = { 0, 0, 0 };
    int touch_history_ctr = 0;

    // Clocks
    unsigned long spoutClocker_L; // timer to measure duration of left lick
    unsigned long spoutClocker_R; // timer to measure duration of right lick
    unsigned long adjustClocker; // timer for re-adjustment of touch lines
    unsigned long spoutInitialTouchClock_L;
    unsigned long spoutInitialTouchClock_R;
    unsigned long usbClocker;

};

#endif
