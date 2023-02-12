#include "Arduino.h"
#include "Spouts.h"
#include "Experiment.h"
#include "LickDetection.h"

// –--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--
// This version includes:
// run MS_task_V2_5
// serial communication with USB
// control two stepper motors to move the sputes
// reads water-spout touches using capacitive sensing.
// includes 2 optogenetic triggers at PINs 24 & 25
// Audio stimulus
// –--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--–--

#define FirmwareVersion "0001" // This doesnt many anything here I would say, just copied from TouchShaker
#define moduleName "MS_task_V2_5" // Name of module for manual override UI and state machine assembler

////////////////////////////////////////////////////
// LickDetection ///////////////////////////////////
////////////////////////////////////////////////////
const byte photodiode_pin_R = A4;
const byte photodiode_pin_L = A5;


// Init Photodiode
Photodiode photodiode_R(photodiode_pin_R);
Photodiode photodiode_L(photodiode_pin_L);

////////////////////////////////////////////////////
// LickDetection ///////////////////////////////////
////////////////////////////////////////////////////
// Inputs for lick sensors
#define SPOUTSENSOR_L 1 // touch line for left spout
#define SPOUTSENSOR_R 0 // touch line for right spout

// PINs to send thresholded LickData to PC
#define LICK_OUTPUT_LEFT_PIN 22
#define LICK_OUTPUT_RIGHT_PIN 23

// Init LickDetection
LickDetection lick(SPOUTSENSOR_L, SPOUTSENSOR_R, LICK_OUTPUT_LEFT_PIN, LICK_OUTPUT_RIGHT_PIN);

////////////////////////////////////////////////////
// Spouts //////////////////////////////////////////
////////////////////////////////////////////////////
// Pins for stepper - spouts
#define PIN_SPOUTOUT_R 12 // Pulldown Line for reset after every trial
#define PIN_SPOUTOUT_L 11 // Pulldown Line for reset after every trial
#define PIN_SPOUTSTEP_R 16
#define PIN_SPOUTDIR_R 17
#define PIN_SPOUTSTEP_L 14
#define PIN_SPOUTDIR_L 15

// Init Spouts
Spouts spouts(PIN_SPOUTDIR_L, PIN_SPOUTDIR_R, PIN_SPOUTSTEP_L, PIN_SPOUTSTEP_R, PIN_SPOUTOUT_L, PIN_SPOUTOUT_R);

////////////////////////////////////////////////////
// Experiment //////////////////////////////////////
////////////////////////////////////////////////////
// TTL Outputs
#define PIN_CAMERATRIG 21 // stimulus trigger that can be switched by serial command 'MAKE_STIMTRIGGER'
#define PIN_TASKFEEDBACK 20 // trial-start trigger that can be switched by serial command 'MAKE_TRIALTRIGGER'

// PINs to control Setup
#define PIN_AUDITORY_L 3 // Auditory trigger
#define PIN_AUDITORY_R 4 // Auditory trigger

// PINs to control Setup
#define PIN_AIRPUFF_L 5 // Airpuff valve
#define PIN_AIRPUFF_R 6 // Airpuff valve
#define PIN_VALVE_L 7 // Water valve
#define PIN_VALVE_R 8 // Water valve

// variables that define the next trials
int n_Distractors_Left = 3;
int n_Distractors_Right = 6;

bool cues_left[6];
bool cues_right[6];

bool target_Left = false;
bool auto_reward = false;
bool both_spouts = false;
bool reward_both_sides = false;
bool enable_reward = true;
unsigned long response_delay = 500;
unsigned long ValveDuration_L = 7300;
unsigned long ValveDuration_R = 7400;

bool auditory_left = false;
bool auditory_right = false;

// Init Experiment
Experiment experiment(PIN_VALVE_L, PIN_VALVE_R, PIN_AIRPUFF_L, PIN_AIRPUFF_R, PIN_AUDITORY_L, PIN_AUDITORY_R, PIN_CAMERATRIG, PIN_TASKFEEDBACK, &spouts, &lick, &photodiode_L, &photodiode_R);

////////////////////////////////////////////////////
// USB Serial Communication ////////////////////////
////////////////////////////////////////////////////
// Byte codes for serial communication
// inputs
#define START_TRIAL 70 // identifier to start trial, provides limit for wheel motion and servo movement
#define ADJUST_SPOUTES 71 // identifier to change spout positions
#define ADJUST_SPOUTSPEED 73 // identifier to change spout servo speed
#define ADJUST_TOUCHLEVEL 75 // identifier to re-adjust threshold for touch sensors. Will sample over 1 second of data to infer mean/std of measurements.
//#define MAKE_STIMTRIGGER 77 // identifier to produce a stimulus trigger
//#define MAKE_TRIALTRIGGER 78 // identifier to produce a trial onset trigger
//#define INCREASE_SPOUTTHRESH_L 80 // identifier to increase touch threshold for the left spout
//#define DECREASE_SPOUTTHRESH_L 81 // identifier to decrease touch threshold for the left spout
//#define INCREASE_SPOUTTHRESH_R 82 // identifier to increase touch threshold for the right spout
//#define DECREASE_SPOUTTHRESH_R 83 // identifier to decrease touch threshold for the right spout
#define TOUCH_THRESHOLD_LEFT_UP 111
#define TOUCH_THRESHOLD_LEFT_DOWN 112
#define TOUCH_THRESHOLD_RIGHT_UP 113
#define TOUCH_THRESHOLD_RIGHT_DOWN 114


// outputs
//#define LEFT_SPOUT_TOUCH 1 // byte to indicate left spout is being touched
//#define RIGHT_SPOUT_TOUCH 2 // byte to indicate right spout is being touched
//#define LEFT_SPOUT_RELEASE 3 // byte to indicate left spout was released
//#define RIGHT_SPOUT_RELEASE 4 // byte to indicate left spout was released
#define GOT_BYTE 14 // positive handshake for bpod commands
#define DID_ABORT 15 // negative handshake for bpod commands

// other serial commands during the trial
#define SPOUTS_IN 101 // serial command to move the spouts in
#define LEFT_SPOUT_OUT 102 // serial command to move the left spout out
#define RIGHT_SPOUT_OUT 103 // serial command to move the right spout out

#define FLUSH_VALVE_LEFT 104 // flush valves outside of the experiment using this command
#define FLUSH_VALVE_RIGHT 105 // flush valves outside of the experiment using this command
#define OPEN_VALVE_LEFT 106 // Overwrite to just open the Valve to run water through the system, e.g.: to get bubbles out of the tubes or something
#define OPEN_VALVE_RIGHT 107 // Overwrite to just open the Valve to run water through the system, e.g.: to get bubbles out of the tubes or something
#define CLOSE_VALVE_LEFT 108 // Overwrite to close the valve if they have been opend
#define CLOSE_VALVE_RIGHT 109 // Overwrite to close the valve if they have been opend
#define CALIBRATE_PHOTODIODE 110 // recalibrate photodiode at the start of every trial. Do this at the inter-trial gray-screen!

#define MODULE_INFO 255  // returns module information

// Serial COM variables
unsigned long serialClocker = millis();
int FSMheader = 0;
bool midRead = false;
bool read_msg_length = false;
float temp[50]; // temporary variable for general purposes

//unsigned long _test_clock = millis();
//int _test_cnt = 0;

//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
void setup() {
  pinMode(PIN_AUDITORY_L, OUTPUT);
  pinMode(PIN_AUDITORY_R, OUTPUT);

  Serial.begin(9600);
  Serial2.begin(115200);
}

void loop() {
  ReadSerialCommunication();
  experiment.Update();
} // end of void loop

void ReadSerialCommunication() {
  // Serial Communication over USB
  // Main purpose is to start a new trial
  if (Serial.available() > 0) {
    if (!midRead) {
      FSMheader = Serial.read();
      midRead = 1; // flag for current reading of serial information
      serialClocker = millis(); // counter to make sure that all serial information arrives within a reasonable time frame (currently 100ms)
      read_msg_length = false;
    }
    
    if (FSMheader == START_TRIAL) {
      if (!read_msg_length) {
        if (Serial.available() >= 36) {
          for (int i = 0; i < 36; i++) { // get number of characters for each variable (6 in total)
            temp[i] = Serial.read(); // number of characters for current variable
          }
          read_msg_length = true;
        }
      }

      if (read_msg_length) {
        if (Serial.available() >= (temp[0]+temp[1]+temp[2]+temp[3]+temp[4]+temp[5]+temp[6]+temp[7]+temp[8]+temp[9]+temp[10]+temp[11]+temp[12]+temp[13]+temp[14]+temp[15]+temp[16]+temp[17]+temp[18]+temp[19]+temp[20]+temp[21]+temp[22]+temp[23]+temp[24]+temp[25]+temp[26]+temp[27]+temp[28]+temp[29]+temp[30]+temp[31]+temp[32]+temp[33]+temp[34]+temp[35])) { // if enough bytes are sent for all variables to be read
          // read all variables for current trial
          spouts.lServoIn = readSerialChar(temp[0]); // left spout inner position
          spouts.rServoIn = readSerialChar(temp[1]); // right spout inner position
          spouts.lServoOut = readSerialChar(temp[2]); // left spout outer position
          spouts.rServoOut = readSerialChar(temp[3]); // right spout outer position

          // Trial data
          target_Left = readSerialChar(temp[4]) > 0; // 0: target stimulus left; >0: left
          auto_reward = readSerialChar(temp[5]) > 0;
          both_spouts = readSerialChar(temp[6]) > 0;
          reward_both_sides = readSerialChar(temp[7]) > 0;
          enable_reward = readSerialChar(temp[8]) > 0;
          ValveDuration_L = readSerialChar(temp[9]);
          ValveDuration_R = readSerialChar(temp[10]);

          // experiment.OG1_active = readSerialChar(temp[11]) > 0;
          // experiment.OG1_active = readSerialChar(temp[11]) > 0;

          int auditory_side = int(readSerialChar(temp[11]));
          auditory_left = auditory_side == 2;
          auditory_right = auditory_side == 1;

          experiment.use_left_photodiode = readSerialChar(temp[12]) > 0;
          experiment.spouts_enabled = readSerialChar(temp[13]) > 0;
          experiment.use_response_based_trial_delay = readSerialChar(temp[14]) > 0;

          experiment.OG_trial_L = long(readSerialChar(temp[15]));  // TODO: make this an acutal serial input
          experiment.OG_trial_R = long(readSerialChar(temp[16]));  // TODO: make this an acutal serial input
//          experiment.OG_trial_L = readSerialChar(temp[15]) > 0;  // TODO: make this an acutal serial input
//          experiment.OG_trial_R = readSerialChar(temp[16]) > 0;  // TODO: make this an acutal serial input
//          // experiment.OG_trial_L = 0;
//          // experiment.OG_trial_R = 0;

          experiment.lDistractorNr = int(readSerialChar(temp[17]));
          experiment.rDistractorNr = int(readSerialChar(temp[18]));
          for (int i = 0; i < 6; i++) {
            experiment.lStimulusTimes[i] = (unsigned int) readSerialChar(temp[19 + i]);
          }
          for (int i = 0; i < 6; i++) {
            experiment.rStimulusTimes[i] = (unsigned int) readSerialChar(temp[25 + i]);
          }
          for (int i = 0; i < 5; i++) {
            experiment.taskPhases[i] = readSerialChar(temp[31 + i]);
          }

          // Start next trials
          experiment.ConfigureNextTrial(auditory_left, auditory_right, target_Left, auto_reward, both_spouts, reward_both_sides, enable_reward, response_delay, ValveDuration_L, ValveDuration_R);
          Serial.write(GOT_BYTE); midRead = 0;
          
          //flush the Serial to be ready for new data
          while (Serial.available() > 0) {
            Serial.read();
          }
        }
        
        else if ((millis() - serialClocker) >= 100) {
          Serial.write(DID_ABORT); midRead = 0; 
          while (Serial.available() > 0) {
            Serial.read();
          }
        }
      }
    }
    
    else if (FSMheader == ADJUST_SPOUTES) {
      if (Serial.available() > 1) {
        int lenght_lServoAdjust = Serial.read();
        int lenght_rServoAdjust = Serial.read();
        
        float lServoAdjust = readSerialChar(lenght_lServoAdjust); // requested handle position
        float rServoAdjust = readSerialChar(lenght_rServoAdjust); // requested handle position
        spouts.command_AdjustSpouts(lServoAdjust, rServoAdjust);

        Serial.print("Test: ");
        Serial.print(lServoAdjust);
        Serial.print(", ");
        Serial.println(rServoAdjust);
        Serial.write(GOT_BYTE); midRead = 0;
      } else if ((millis() - serialClocker) >= 100) {
        Serial.write(DID_ABORT); midRead = 0;
      }
    }
    else if (FSMheader == ADJUST_SPOUTSPEED) {
      if (Serial.available() > 0) {
        spouts.command_AdjustSpoutSpeed(readSerialChar(Serial.read())); // Input: Duration of spout movement from outer to inner position in ms.
        Serial.write(GOT_BYTE); midRead = 0;
      } else if ((millis() - serialClocker) >= 100) {
        spouts.command_AdjustSpoutSpeed(35); // Input: Duration of spout movement from outer to inner position in ms.
        Serial.write(DID_ABORT); midRead = 0;
      }
    }
    
    else if (FSMheader == ADJUST_TOUCHLEVEL) { // check mean and std for all touch lines to adjust thresholds
      if (Serial.available() > 0) {
        lick.command_AdjustTouchLevel(readSerialChar(Serial.read()));
        Serial.write(GOT_BYTE); midRead = 0;
      }
      
      else if ((millis() - serialClocker) >= 100) {
        Serial.write(DID_ABORT); midRead = 0;
      }
    }

    else if (FSMheader == SPOUTS_IN) { // move spouts in
      spouts.command_SpoutsIn();
      Serial.write(GOT_BYTE); midRead = 0;
    }
    else if (FSMheader == LEFT_SPOUT_OUT) { // move left spout out
      spouts.command_LeftSpoutOut();
      Serial.write(GOT_BYTE); midRead = 0;
    }
    else if (FSMheader == RIGHT_SPOUT_OUT) { // move right spout out
      spouts.command_RightSpoutOut();
      Serial.write(GOT_BYTE); midRead = 0;
    }
    
    else if (FSMheader == OPEN_VALVE_LEFT) { // move right spout out
      digitalWriteFast(experiment.Valve_L._PIN, HIGH);
      // experiment.Valve_L.sendTrigger();
      Serial.write(GOT_BYTE); midRead = 0;
    }
    else if (FSMheader == OPEN_VALVE_RIGHT) { // move right spout out
      digitalWriteFast(experiment.Valve_R._PIN, HIGH);
      // experiment.Valve_R.sendTrigger();
      Serial.write(GOT_BYTE); midRead = 0;
    }
    else if (FSMheader == CLOSE_VALVE_LEFT) { // move right spout out
      digitalWriteFast(experiment.Valve_L._PIN, LOW);
      Serial.write(GOT_BYTE); midRead = 0;
    }
    else if (FSMheader == CLOSE_VALVE_RIGHT) { // move right spout out
      digitalWriteFast(experiment.Valve_R._PIN, LOW);
      Serial.write(GOT_BYTE); midRead = 0;
    }
    else if (FSMheader == FLUSH_VALVE_LEFT) { // move right spout out
      experiment.Valve_L.change_duration(readSerialChar(Serial.read()));
      experiment.Valve_L.sendTrigger();
      Serial.write(GOT_BYTE); midRead = 0;
    }
    else if (FSMheader == FLUSH_VALVE_RIGHT) { // move right spout out
      experiment.Valve_R.change_duration(readSerialChar(Serial.read()));
      experiment.Valve_R.sendTrigger();
      Serial.write(GOT_BYTE); midRead = 0;
    }
    else if (FSMheader == CALIBRATE_PHOTODIODE) { // check mean and std for photodiode to adjust threshold
      photodiode_L.recalibrate();
      photodiode_R.recalibrate();
      Serial.write(GOT_BYTE); midRead = 0;
    }
    else if (FSMheader == TOUCH_THRESHOLD_LEFT_UP) { // check mean and std for photodiode to adjust threshold
      lick.touchThresholdValues[0] += 10;
      Serial.write(GOT_BYTE); midRead = 0;
    }
    else if (FSMheader == TOUCH_THRESHOLD_LEFT_DOWN) { // check mean and std for photodiode to adjust threshold
      lick.touchThresholdValues[0] -= 10;
      Serial.write(GOT_BYTE); midRead = 0;
    }
    else if (FSMheader == TOUCH_THRESHOLD_RIGHT_UP) { // check mean and std for photodiode to adjust threshold
      lick.touchThresholdValues[1] += 10;
      Serial.write(GOT_BYTE); midRead = 0;
    }
    else if (FSMheader == TOUCH_THRESHOLD_RIGHT_DOWN) { // check mean and std for photodiode to adjust threshold
      lick.touchThresholdValues[1] -= 10;
      Serial.write(GOT_BYTE); midRead = 0;
    }
    else if (FSMheader == MODULE_INFO) { // return module information to bpod
      returnModuleInfo();
      midRead = 0;
    }
    else if (FSMheader == GOT_BYTE){
      // The Serial COM waiting for confirmation inside Experiment makes Issues.
      // This is not elegant, but I'm assuming now that any GOT_BYTE received here is in response to the Stimulus/Response signals send inside Experiment
      experiment.NextTrialSerialObject.waiting_for_confirmation = false;
      experiment.VisualStimulusSerialObject.waiting_for_confirmation = false;
      experiment.ResponseLeftSerialObject.waiting_for_confirmation = false;
      experiment.ResponseRightSerialObject.waiting_for_confirmation = false;
      experiment.ResponseMissedSerialObject.waiting_for_confirmation = false;
      midRead = 0;
    }
    else {
      //flush the Serial to be ready for new data
      while (Serial.available() > 0) {
        Serial.read();
      }

      //send abort to request resend
      Serial.write(DID_ABORT); midRead = 0;
    }
  }

  if (midRead && ((millis() - serialClocker) >= 100)) {
      //flush the Serial to be ready for new data
      while (Serial.available() > 0) {
        Serial.read();
      }

      //send abort to request resend
      Serial.write(DID_ABORT); midRead = 0;
  }
}

float readSerialChar(byte currentRead){
  float currentVar = 0;
  byte cBytes[currentRead-1]; // current byte
  int preDot = currentRead; // indicates how many characters there are before a dot
  int cnt = 0; // character counter

  if (currentRead == 1){
    currentVar = Serial.read() -'0'; 
  }

  else {
    for (int i = 0; i < currentRead; i++) {
      cBytes[i] = Serial.read(); // go through all characters and check for dot or non-numeric characters
      if (cBytes[i] == '.') {cBytes[i] = '0'; preDot = i;}
      if (cBytes[i] < '0') {cBytes[i] = '0';}
      if (cBytes[i] > '9') {cBytes[i] = '9';}
    }
  
    // go through all characters to create new number
    if (currentRead > 1) {
      for (int i = preDot-1; i >= 1; i--) {
        currentVar = currentVar + ((cBytes[cnt]-'0') * pow(10,i));
        cnt++;
      }
    }
    currentVar = currentVar + (cBytes[cnt] -'0'); 
    cnt++;
  
    // add numbers after the dot
    if (preDot != currentRead){
      for (int i = 0; i < (currentRead-preDot); i++) {
        currentVar = currentVar + ((cBytes[cnt]-'0') / pow(10,i));
        cnt++;
      }
    }
  }
  return currentVar;
}

void returnModuleInfo() {
  Serial.write(65); // Acknowledge
  Serial.write(FirmwareVersion); // 4-byte firmware version
  Serial.write(sizeof(moduleName)-1); // Length of module name
  Serial.print(moduleName); // Module name
  Serial.write(0); // 1 if more info follows, 0 if not
}
