#include "Arduino.h"
#include "Experiment.h"
#include "TimedDigitalPulse.h"
#include "Spouts.h"
#include "LickDetection.h"
#include "SerialSend.h"
#include "Photodiode.h"


Experiment::Experiment(int PIN_VALVE_L, int PIN_VALVE_R, int PIN_AIRPUFF_L, int PIN_AIRPUFF_R, int PIN_AUDITORY_L, int PIN_AUDITORY_R, 
                       int PIN_CAMERA_TRIGGER, int PIN_TASKFEEDBACK, 
                       Spouts* spouts, LickDetection* lick, Photodiode* photodiode_L, Photodiode* photodiode_R) :
                       PIN_TASKFEEDBACK(PIN_TASKFEEDBACK) {
  // PINs
  pinMode(PIN_TASKFEEDBACK, OUTPUT);
  pinMode(PIN_OG_L, OUTPUT);
  pinMode(PIN_OG_R, OUTPUT);

  digitalWriteFast(PIN_TASKFEEDBACK, 0);
  digitalWriteFast(PIN_OG_L, 0);
  digitalWriteFast(PIN_OG_R, 0);

  // Initialize the TimedDigitalPulse Objects
  CameraTrigger.configure(PIN_CAMERA_TRIGGER, 500000);
  Airpuff_L.configure(PIN_AIRPUFF_L, AirpuffDuration);
  Airpuff_R.configure(PIN_AIRPUFF_R, AirpuffDuration);
  Valve_L.configure(PIN_VALVE_L, ValveDuration_L);
  Valve_R.configure(PIN_VALVE_R, ValveDuration_R);
  Audio_L.configure(PIN_AUDITORY_L, AudioDuration);
  Audio_R.configure(PIN_AUDITORY_R, AudioDuration);

  // SerialSend Objects
  NextTrialSerialObject.configure(NextTrialByte);
  VisualStimulusSerialObject.configure(VisualStimulusByte);
  ResponseLeftSerialObject.configure(ResponseLeftByte);
  ResponseRightSerialObject.configure(ResponseRightByte);
  ResponseMissedSerialObject.configure(ResponseMissedByte);

  // Class Handles
  spouts_ptr = spouts;
  lick_ptr = lick;
  photodiode_L_ptr = photodiode_L;
  photodiode_R_ptr = photodiode_R;
}

void Experiment::ConfigureNextTrial(bool auditory_left, bool auditory_right, bool target_Left, bool auto_reward, bool both_spouts, bool reward_both_sides, bool enable_reward, unsigned long response_delay, unsigned long valve_duration_left, unsigned long valve_duration_right) {
  stimulusTargetLeft = target_Left; // 0: target stimulus right; >0: left
  autoRewardTrial = auto_reward;
  both_spouts_trial = both_spouts;
  reward_both_sides_trial = reward_both_sides;
  enable_reward_trial = enable_reward;
  // response_delay_trials = response_delay;
  ValveDuration_L = valve_duration_left;
  ValveDuration_R = valve_duration_right;
  
  // now update stim-onset times to be used during this trial
  update_StimulusTimes(auditory_left, auditory_right);

  Valve_L.change_duration(ValveDuration_L);
  Valve_R.change_duration(ValveDuration_R);

  // Reset Trial variables
  lCurrentAirpuffID = 0;
  rCurrentAirpuffID = 0;

  lCurrentAudioID = 0;
  rCurrentAudioID = 0;

  if (OG_trial_L < 3) {
    pre_stimulus_OG_onset = 500;
  } else {
    pre_stimulus_OG_onset = -2900;  // 100ms ramp up before stim end, to be at max when the delay starts
  }
  
  nextTrialConfigured = true;

  // Reset Serial Objects just in case there was a miscommunication
  NextTrialSerialObject.waiting_for_confirmation = false;
  VisualStimulusSerialObject.waiting_for_confirmation = false;
  ResponseLeftSerialObject.waiting_for_confirmation = false;
  ResponseRightSerialObject.waiting_for_confirmation = false;
  ResponseMissedSerialObject.waiting_for_confirmation = false;
}

void Experiment::StartNextTrial() {
  NextTrialSerialObject.send(); // Send NextTrialByte to PC so the PC closes last trials h5-file and starts writing new data to new h5-file
  
  // Move Spouts to Out Position to be ready for the next trial
  if (spouts_enabled) {
    spouts_ptr->command_LeftSpoutOut();
    spouts_ptr->command_RightSpoutOut();
  }
  
  // variables to set after the last trial is over (might interfere in ConfigureNextTrial())
  answerRegistered = false;
  current_trial_state = 0;
  nextTrialConfigured = false;
  flip_detected = false;

  // Time critical functions immediatly before the trial start:
  CameraTrigger.sendTrigger();
  TrialClock = millis(); // This is the reference for the trial phases
}

void Experiment::update_StimulusTimes(bool auditory_l, bool auditory_r) {
  lDistractorNrAuditory = 0;
  if (auditory_l) {
    lStimulusTimesAuditory[0] = 0.;
    lStimulusTimesAuditory[1] = 500.;
    lDistractorNrAuditory = 2;
  }

  rDistractorNrAuditory = 0;
  if (auditory_r) {
    rStimulusTimesAuditory[0] = 0.;
    rStimulusTimesAuditory[1] = 500.;
    rDistractorNrAuditory = 2;
  }
}

void Experiment::Update() {
  ///////////////////////////////////////////////////
  // 1. Determine current Trial state              //
  // Handle State transitions                      //
  ///////////////////////////////////////////////////
  current_time = millis() - TrialClock;
  if (current_trial_state == 0) {
    // BASELINE PHASE
    if (current_time >= taskPhases[0]) {
      // first iteration in STIMULUS PHASE

      // Send Byte signalling PC for Visual-Stimulus on the Monitor 
      VisualStimulusSerialObject.send();

      // // send VisualStimulusBYTE!
      // digitalWriteFast(PIN_TASKFEEDBACK, HIGH);

      current_trial_state = 1;
    }
  } else if (current_trial_state == 1) {
    // STIMULUS PHASE
    if (current_time >= taskPhases[1]) {
      // first iteration in DELAY PHASE
      digitalWriteFast(PIN_TASKFEEDBACK, LOW);

      current_trial_state = 2;
    }
  } else if (current_trial_state == 2) {
    // DELAY PHASE
    if (current_time >= taskPhases[2]) {
      // first iteration in REWARD Window

      // reset the LickDetection
      lick_ptr->reset_response_counter();

      // Move Spouts In
      if (spouts_enabled) {
        if (!both_spouts_trial) {
          if (stimulusTargetLeft) {
            spouts_ptr->rServoIn = spouts_ptr->rServoOut;
          } else{
            spouts_ptr->lServoIn = spouts_ptr->lServoOut;
          }
        }
        spouts_ptr->command_SpoutsIn();
      }
      
      digitalWriteFast(PIN_TASKFEEDBACK, HIGH);

      current_trial_state = 3;
    }
  } else if (current_trial_state == 3) {
    // REWARD PHASE

    // Handle Auto-reward
    if (autoRewardTrial && (!answerRegistered)) {
      if (current_time >= taskPhases[2] + auto_reward_delay) {
        if (stimulusTargetLeft) {
          Valve_L.sendTrigger();
          if (spouts_enabled) {
            spouts_ptr->command_RightSpoutOut();
          }
          // ResponseLeftSerialObject.send();
          ResponseMissedSerialObject.send();
          answerRegistered = true;
          NextTrialPunishmentDelay = 0;
        } else {
          Valve_R.sendTrigger();
          if (spouts_enabled) {
            spouts_ptr->command_LeftSpoutOut();
          }
          // ResponseRightSerialObject.send();
          ResponseMissedSerialObject.send();
          answerRegistered = true;
          NextTrialPunishmentDelay = 0;
        }
      }
    }

    if (current_time >= taskPhases[3]) {
      // end of REWARD PHASE, now ITI
      if (OG_current_state_L) {
        // If te OG Line is on, then switch it off now to start the down ramp of Analoge-Ramp
        OG_current_state_L = 0;
        OG_trial_L = 0;  // I remove this flag now so that the start of the OG ramp doesnt start a new ramp
        digitalWriteFast(PIN_OG_L, 0);
      }
      if (OG_current_state_R) {
        // If te OG Line is on, then switch it off now to start the down ramp of Analoge-Ramp
        OG_current_state_R = 0;
        OG_trial_R = 0;  // I remove this flag now so that the start of the OG ramp doesnt start a new ramp
        digitalWriteFast(PIN_OG_R, 0);
      }
      
      // Recalibrate Spouts for the next trial
      spouts_ptr->command_AdjustSpouts(0, 0);

      // Send Feedback if CORRECT, ERROR or MISSED Trial !
      digitalWriteFast(PIN_TASKFEEDBACK, LOW);

      // check for Missed Trial
      if (!answerRegistered) {
        ResponseMissedSerialObject.send();
        if (use_response_based_trial_delay) {
          NextTrialPunishmentDelay = 1000;
        } else {
          NextTrialPunishmentDelay = 0;
        }
      }

      current_trial_state = 4;
    }
  }

  ///////////////////////////////////////////////////
  // Read LickDetection                            //
  ///////////////////////////////////////////////////
  // TOUCH SENSORS                                 //
  // 1. reads sensors                              //
  // 2. handles recalibration if requested         //
  // 3. thresholds SensorData and returns event    //
  ///////////////////////////////////////////////////
  lick_ptr->ReadTouchSensors();

  ///////////////////////////////////////////////////
  // Read Photodiode                               //
  ///////////////////////////////////////////////////
  // Photodiode                                    //
  // 1. reads analoge input                        //
  // 2. handles calibration                        //
  // 3. thresholds input and returns flip_detected //
  ///////////////////////////////////////////////////
  if (photodiode_L_ptr->calibration) {
    photodiode_L_ptr->update();
  }
  if (photodiode_R_ptr->calibration) {
    photodiode_R_ptr->update();
  }

//  if (current_time < taskPhases[3]) {
//    // Handle variable OG-onset
//    if (OG_trial_L > 0) {
//      if (!OG_current_state_L) {
//        // check this if there is supposed to be an optogenetic trigger this trial and it has not been activated yet
//        if (long(current_time) >= long(taskPhases[0]) - pre_stimulus_OG_onset) {
//          // Its time to activate the OG Line now, to trigger the OG-Teensy to generate an according Analoge-Ramp
//          OG_current_state_L = 1;
//          digitalWriteFast(PIN_OG_L, 1);
//        }
//      }
//    }
//    if (OG_trial_R > 0) {
//      if (!OG_current_state_R) {
//        // check this if there is supposed to be an optogenetic trigger this trial and it has not been activated yet
//        if (long(current_time) >= long(taskPhases[0]) - pre_stimulus_OG_onset) {
//          // Its time to activate the OG Line now, to trigger the OG-Teensy to generate an according Analoge-Ramp
//          OG_current_state_R = 1;
//          digitalWriteFast(PIN_OG_R, 1);
//        }
//      }
//    }
//  }

  ///////////////////////////////////////////////////
  // 2. Handle Trial Behavior                      //
  // 2.1. Generate Airpuffs,                       //
  // 2.2. Check Licks                              //
  // 2.3. Open Valves                              //
  ///////////////////////////////////////////////////
  if (current_trial_state == 0) {
    ////////////////////
    // BASELINE PHASE //
        // Handle variable OG-onset
    if ((OG_trial_L == 1) || (OG_trial_L == 2)) {
      if (!OG_current_state_L) {
        // check this if there is supposed to be an optogenetic trigger this trial and it has not been activated yet
        if (current_time >= taskPhases[0] - 500) {
          // Its time to activate the OG Line now, to trigger the OG-Teensy to generate an according Analoge-Ramp
          OG_current_state_L = 1;
          digitalWriteFast(PIN_OG_L, 1);
        }
      }
    }
    if ((OG_trial_R == 1) || (OG_trial_R == 2)) {
      if (!OG_current_state_R) {
        // check this if there is supposed to be an optogenetic trigger this trial and it has not been activated yet
        if (current_time >= taskPhases[0] - 500) {
          // Its time to activate the OG Line now, to trigger the OG-Teensy to generate an according Analoge-Ramp
          OG_current_state_R = 1;
          digitalWriteFast(PIN_OG_R, 1);
        }
      }
    }
  } else if (current_trial_state == 1) {
    ////////////////////
    // STIMULUS PHASE //
    if (!flip_detected) {
      if (use_left_photodiode) {
        flip_detected = photodiode_L_ptr->update();
      } else{
        flip_detected = photodiode_R_ptr->update();
      }

      // flip_detected = photodiode_ptr->update();
      if (current_time - taskPhases[0] > 100) {
        // This is a 100ms timeout, if not detected use a max delay of 100ms
        flip_detected = true; 
      }
      
      // flip_detected = true;
      if (flip_detected) {
        digitalWriteFast(PIN_TASKFEEDBACK, HIGH);

        TrialClock = millis() - taskPhases[0];
        current_time = taskPhases[0];
      }
    }

    if (flip_detected) {
      if (OG_trial_L == 2) {
        if (current_time >= taskPhases[1] - 500) {  // -500 for the OG down ramp
          if (OG_current_state_L) {
            // If te OG Line is on, then switch it off now to start the down ramp of Analoge-Ramp
            OG_current_state_L = 0;
            OG_trial_L = 0;  // I remove this flag now so that the start of the OG ramp doesnt start a new ramp
            digitalWriteFast(PIN_OG_L, 0);
          }
        }
      }
      if (OG_trial_R == 2) {
        if (current_time >= taskPhases[1] - 500) {  // -500 for the OG down ramp
          if (OG_current_state_R) {
            // If te OG Line is on, then switch it off now to start the down ramp of Analoge-Ramp
            OG_current_state_R = 0;
            OG_trial_R = 0;  // I remove this flag now so that the start of the OG ramp doesnt start a new ramp
            digitalWriteFast(PIN_OG_R, 0);
          }
        }
      }

      if (OG_trial_L == 3) {
        if (!OG_current_state_L) {
          // check this if there is supposed to be an optogenetic trigger this trial and it has not been activated yet
          if (current_time >= taskPhases[0] + 2900) {  // changed this from 2900 to 2500, cause we increased the up-ramp from 100 to 500ms. 2022-02-15 (Emma's Mice)  // changed this back to 2900 on 2022-06-22 as well as the up-ramp back to 100ms for Maria's mice.
            // Its time to activate the OG Line now, to trigger the OG-Teensy to generate an according Analoge-Ramp
            OG_current_state_L = 1;
            digitalWriteFast(PIN_OG_L, 1);
          }
        }
      }
      if (OG_trial_R == 3) {
        if (!OG_current_state_R) {
          // check this if there is supposed to be an optogenetic trigger this trial and it has not been activated yet
          if (current_time >= taskPhases[0] + 2900) {  // changed this from 2900 to 2500, cause we increased the up-ramp from 100 to 500ms. 2022-02-15 (Emma's Mice)  // changed this back to 2900 on 2022-06-22 as well as the up-ramp back to 100ms for Maria's mice.
            // Its time to activate the OG Line now, to trigger the OG-Teensy to generate an according Analoge-Ramp
            OG_current_state_R = 1;
            digitalWriteFast(PIN_OG_R, 1);
          }
        }
      }
    
      // Handle AIRPUFFS Left
      if (lCurrentAirpuffID < lDistractorNr) {
        // the next Airpuff is supposed to be presented
        if (!Airpuff_L.state) {
          // check if its time to start the next airpuff
          if (current_time - taskPhases[0] >= lStimulusTimes[lCurrentAirpuffID]) {
            // next airpuff is due
            Airpuff_L.sendTrigger();
            lCurrentAirpuffID += 1;
          }
        }
      }

      // Handle AIRPUFFS Right
      if (rCurrentAirpuffID < rDistractorNr) {
        // the next Airpuff is supposed to be presented
        if (!Airpuff_R.state) {
          // check if its time to start the next airpuff
          if (current_time - taskPhases[0] >= rStimulusTimes[rCurrentAirpuffID]) {
            // next airpuff is due
            Airpuff_R.sendTrigger();
            rCurrentAirpuffID += 1;
          }
        }
      }

      // Handle AUDIO Left
      if (lCurrentAudioID < lDistractorNrAuditory) {
        // the next Audio is supposed to be presented
        if (!Audio_L.state) {
          // check if its time to start the next Audio
          if (current_time - taskPhases[0] >= lStimulusTimesAuditory[lCurrentAudioID]) {
            // next Audio is due
            Audio_L.sendTrigger();
            lCurrentAudioID += 1;
          }
        }
      }
      

      // Handle AUDIO Left
      if (rCurrentAudioID < rDistractorNrAuditory) {
        // the next Audio is supposed to be presented
        if (!Audio_R.state) {
          // check if its time to start the next Audio
          if (current_time - taskPhases[0] >= rStimulusTimesAuditory[rCurrentAudioID]) {
            // next Audio is due
            Audio_R.sendTrigger();
            rCurrentAudioID += 1;
          }
        }
      }
    }
  } else if (current_trial_state == 2) {
    /////////////////
    // DELAY PHASE //
  } else if (current_trial_state == 3) {
    //////////////////
    // REWARD PHASE //
    if (!answerRegistered) {
      // if (!autoRewardTrial) {
      if (lick_ptr->spoutTouch_L) {
        if (autoRewardTrial) {
          // autoreward-trial, but the mouse licked before the reward was give.
          if (stimulusTargetLeft || reward_both_sides_trial) {
            // the mouse responded correctly -> just treat this as a regulat trial now.
            autoRewardTrial = 0;
            // this enables the if case below, a reward is dispents and the other spouts moves out.
          }
        }
        if (!autoRewardTrial) {
          if (spouts_enabled) {
            spouts_ptr->command_RightSpoutOut();
          }
          ResponseLeftSerialObject.send();
          answerRegistered = true;
  
          if (stimulusTargetLeft || reward_both_sides_trial) {
            if (enable_reward_trial) {
              Valve_L.sendTrigger();
            }
            NextTrialPunishmentDelay = 0;
          } else {
            if (spouts_enabled) {
              spouts_ptr->command_LeftSpoutOut();
            }
  
            // NextTrialPunishmentDelay = 2000;
            if (use_response_based_trial_delay) {
              NextTrialPunishmentDelay = 2000;
            } else {
              NextTrialPunishmentDelay = 0;
            }
          }
        }
      } else if (lick_ptr->spoutTouch_R) {
        if (autoRewardTrial) {
          // autoreward-trial, but the mouse licked before the reward was give.
          if (!stimulusTargetLeft || reward_both_sides_trial) {
            // the mouse responded correctly -> just treat this as a regulat trial now.
            autoRewardTrial = 0;
            // this enables the if case below, a reward is dispents and the other spouts moves out.
          }
        }
        if (!autoRewardTrial) {
          if (spouts_enabled) {
            spouts_ptr->command_LeftSpoutOut();
          }
          ResponseRightSerialObject.send();
          answerRegistered = true;
          
          if (!stimulusTargetLeft || reward_both_sides_trial) {
            if (enable_reward_trial) {
              Valve_R.sendTrigger();
            }
            NextTrialPunishmentDelay = 0;
          } else {
            if (spouts_enabled) {
              spouts_ptr->command_RightSpoutOut();
            }
            // NextTrialPunishmentDelay = 2000;
            if (use_response_based_trial_delay) {
              NextTrialPunishmentDelay = 2000;
            } else {
              NextTrialPunishmentDelay = 0;
            }
          }
        }
      }
    }
  } else {
    if (current_time >= taskPhases[4] + NextTrialPunishmentDelay) {
      if (nextTrialConfigured) {
        // Only start new trial if configured by PC
        StartNextTrial();
      }
    }
  }

  // Update to switch Lines off again, independent of Trial State
  Airpuff_L.update();
  Airpuff_R.update();
  Audio_L.update();
  Audio_R.update();
  Valve_L.update();
  Valve_R.update();
  CameraTrigger.update();

  //// Check for confirmation or resend if timeout
  NextTrialSerialObject.update();
  VisualStimulusSerialObject.update();
  ResponseLeftSerialObject.update();
  ResponseRightSerialObject.update();
  ResponseMissedSerialObject.update();

  // Update Spout Positions
  spouts_ptr->SpoutMovements();
}
