/*
  Task.h - Library to run MS_Task_V2_4.
  Created by Gerion Nabbefeld, October 8, 2020.
*/

#ifndef Experiment_h
#define Experiment_h

#include "Arduino.h"
#include "TimedDigitalPulse.h"
#include "Spouts.h"
#include "LickDetection.h"
#include "SerialSend.h"
#include "Photodiode.h"


class Experiment {
  uint8_t NextTrialByte = 110; // Send at the actual start of the next trial (before Baseline) to signal closing of last trials h5-file
  uint8_t VisualStimulusByte = 111; // To start the Stimulus
  uint8_t ResponseLeftByte = 112; // Signal that the mouse licked left
  uint8_t ResponseRightByte = 113; // Signal that the mouse licked right
  uint8_t ResponseMissedByte = 114; // missed Trial - No Response

  public:
    // constructor
//    Experiment(int PIN_VALVE_L, int PIN_VALVE_R, int PIN_AIRPUFF_L, int PIN_AIRPUFF_R, 
//               int PIN_CAMERA_TRIGGER, int PIN_TASKFEEDBACK, 
//               Spouts* spouts, LickDetection* lick, Photodiode* photodiode);
    Experiment(int PIN_VALVE_L, int PIN_VALVE_R, int PIN_AIRPUFF_L, int PIN_AIRPUFF_R, int PIN_AUDITORY_L, int PIN_AUDITORY_R, 
               int PIN_CAMERA_TRIGGER, int PIN_TASKFEEDBACK, 
               Spouts* spouts, LickDetection* lick, Photodiode* photodiode_L, Photodiode* photodiode_R);
  
	// Initialize a new Trial
	//void ConfigureNextTrial(bool target_Left, bool auto_reward, bool both_spouts, bool reward_both_sides, bool enable_reward, unsigned long response_delay, unsigned long valve_duration_left, unsigned long valve_duration_right);
  void ConfigureNextTrial(bool audiroty_left, bool audiroty_right, bool target_Left, bool auto_reward, bool both_spouts, bool reward_both_sides, bool enable_reward, unsigned long response_delay, unsigned long valve_duration_left, unsigned long valve_duration_right);
    void StartNextTrial();

	// public void to update spout current Experiment state, call every loop() iteration
	void Update();

    // SerialSend Objects
    SerialSend NextTrialSerialObject;
    SerialSend VisualStimulusSerialObject;
    SerialSend ResponseLeftSerialObject;
    SerialSend ResponseRightSerialObject;
    SerialSend ResponseMissedSerialObject;
    
    // Declare the TimedDigitalPulse Objects
    TimedDigitalPulse Airpuff_L;
    TimedDigitalPulse Airpuff_R;
    TimedDigitalPulse Valve_L;
    TimedDigitalPulse Valve_R;
    TimedDigitalPulse Audio_L;
    TimedDigitalPulse Audio_R;

  int lDistractorNr = 0; // how many cues on the LEFT-side  to present in the next trial
    int rDistractorNr = 0; // how many cues on the RIGHT-side to present in the next trial
    unsigned int lStimulusTimes[6]; // List so start the stim-onset times for the current trial
    unsigned int rStimulusTimes[6]; // List so start the stim-onset times for the current trial

  // [Baseline Duration, Stimulus, Delay, Reward, ITI]
  unsigned long taskPhases[5] = { 2000, 5000, 5500, 7500, 9000 }; // in ms
  bool use_left_photodiode = 0;
  bool spouts_enabled = true;
  bool use_response_based_trial_delay = true;

  // Optogenetic parameters
  long OG_trial_L = 0;
  long OG_trial_R = 0;
  bool OG_current_state_L = 0;
  bool OG_current_state_R = 0;

  // Optogenetic parameters
  long pre_stimulus_OG_onset = 500;  // in ms, if Stimulus onset is 4000ms and pre_stimulus_OG_onset is 500ms, then the trigger is send at 3500ms (500ms before the stimulus)

  private:
  // Internal functions
  void update_StimulusTimes(bool auditory_l, bool auditory_r);
  
    // Class Handles
    Spouts* spouts_ptr;
    LickDetection* lick_ptr;
    Photodiode* photodiode_L_ptr;
    Photodiode* photodiode_R_ptr;

	// PINs
  int PIN_TASKFEEDBACK;
  int PIN_OG_L = 25;
  int PIN_OG_R = 24;

    // Declare the TimedDigitalPulse Objects
    TimedDigitalPulse CameraTrigger;

	// Clocks
    unsigned long current_time = 0;
    unsigned int AirpuffDuration =  20000; // in us
    unsigned int AudioDuration =  500; // in us

    unsigned int ValveDuration_L = 10000; // in us
    unsigned int ValveDuration_R = 10000; // in us

    unsigned int auto_reward_delay = 500; // in ms

    unsigned long NextTrialPunishmentDelay = 0; // correct: 0, missed: 1000, error: 2000 ms
    unsigned long TrialClock; // in millis
    
    // Trial Defining Variables
	bool stimulusTargetLeft = true; // 0: target stimulus left; >0: left

  int lDistractorNrAuditory = 2; // how many cues on the LEFT-side  to present in the next trial
    int rDistractorNrAuditory = 2; // how many cues on the RIGHT-side to present in the next trial
    unsigned int lStimulusTimesAuditory[2]; // List so start the stim-onset times for the current trial
    unsigned int rStimulusTimesAuditory[2]; // List so start the stim-onset times for the current trial
  
    bool reward_both_sides_trial = false; // this is an exeption for the discrimination case, that if its the same number of cues on both sides than there is no real target anymore and I want to reward either response then.
    bool enable_reward_trial = true; // for control trials to determine differences between response and the actual reward
    bool flip_detected = false;

    // State Variables
    bool both_spouts_trial = false;
    bool autoRewardTrial = true;
    int lCurrentAirpuffID = 0;
    int rCurrentAirpuffID = 0;
    int lCurrentAudioID = 0;
    int rCurrentAudioID = 0;

    int current_trial_state = 4; // something higher than len(taskPhases)
    bool answerRegistered = false;

    bool nextTrialConfigured = false;
};

#endif
