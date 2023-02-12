/*
  Morse.cpp - Library for flashing Morse code.
  Created by David A. Mellis, November 2, 2007.
  Released into the public domain.
*/

#include "Arduino.h"
#include "Spouts.h"

Spouts::Spouts(int PIN_SPOUTDIR_L, int PIN_SPOUTDIR_R, int PIN_SPOUTSTEP_L, int PIN_SPOUTSTEP_R, int PIN_SPOUTOUT_L, int PIN_SPOUTOUT_R)
{
  // PINs
  _PIN_SPOUTDIR_L = PIN_SPOUTDIR_L;
  _PIN_SPOUTDIR_R = PIN_SPOUTDIR_R;
  _PIN_SPOUTSTEP_L = PIN_SPOUTSTEP_L;
  _PIN_SPOUTSTEP_R = PIN_SPOUTSTEP_R;
  _PIN_SPOUTOUT_L = PIN_SPOUTOUT_L;
  _PIN_SPOUTOUT_R = PIN_SPOUTOUT_R;

  // Initialize PINs
  pinMode(_PIN_SPOUTDIR_L, OUTPUT);
  pinMode(_PIN_SPOUTDIR_R, OUTPUT);
  pinMode(_PIN_SPOUTSTEP_L, OUTPUT);
  pinMode(_PIN_SPOUTSTEP_R, OUTPUT);
  pinMode(_PIN_SPOUTOUT_L, INPUT_PULLUP);
  pinMode(_PIN_SPOUTOUT_R, INPUT_PULLUP);

  // Clocks
  lSpoutClocker = micros(); // timer to modulate speed of left spout
  rSpoutClocker = micros(); // timer to modulate speed of right spout

  //Recalibrate Spout Position
  command_AdjustSpoutSpeed(35);
  command_AdjustSpouts(0, 0);
}

void Spouts::SpoutMovements() {
  ////////////////////////////////////////////////////////////////////////////////////////
  // Call this function every loop() iteration to update Spouts
  ////////////////////////////////////////////////////////////////////////////////////////

  // Check for ongoing spout movements
  if (spoutMoves) { // check spout motion

    // left spout movements
    if (lSpoutMovesIn || lSpoutMovesOut || lSpoutMovesAdjust) {
      if ((micros() - lSpoutClocker) >= lSpoutInc) { // move left spout motor
        lSpoutClocker = micros();
  
        // find absolute outer limits, this happens when requestion a movement to position zero
        if (findSpoutOut[0]) { // left spout is moving to zero position
          digitalWriteFast(_PIN_SPOUTDIR_L, HIGH); // make sure stepper is moving in the right direction
          delayMicroseconds(10); // short delay to ensure direction has changed
          sendStep(_PIN_SPOUTSTEP_L, stepPulse); // make a step
            if (!digitalReadFast(_PIN_SPOUTOUT_L)) { // check if outer limit has been reached
              findSpoutOut[0] = false;
              lServoCurrent = 0;
            }
        }
  
        // regular movements, relative to zero position
        if (!findSpoutOut[0]) {

          // left spout moves in
          if (lSpoutMovesIn == true) {
            // target hasnt been reached yet
            if (lServoCurrent != lServoIn) {
              lServoCurrent = moveLeftSpout(lServoCurrent, lServoIn, stepPulse); // move left spout
            }
            
            // stop motion when target has been reached  
            if (lServoCurrent == lServoIn) {
              lSpoutMovesIn = false;
            }
          }
    
          // left spout adjustment movement
          else if (lSpoutMovesAdjust == true) {

            // target hasnt been reached yet
            if (lServoCurrent != lServoAdjust) {
              lServoCurrent = moveLeftSpout(lServoCurrent, lServoAdjust, stepPulse); // move left spout
            }
            
            // stop motion when target has been reached
            if (lServoCurrent == lServoAdjust) {
              lSpoutMovesAdjust = false;
            }
          }
    
          // left spout moves out
          else if (lSpoutMovesOut == true) {
            // target hasnt been reached yet
            if (lServoCurrent != lServoOut) {
              lServoCurrent = moveLeftSpout(lServoCurrent, lServoOut, stepPulse); // move left spout
            }
            
            // stop motion when target has been reached
            if (lServoCurrent == lServoOut) {
              lSpoutMovesOut = false;
            }
          }
        }
      }
    }
    
    // right spout movements
    if (rSpoutMovesIn || rSpoutMovesOut || rSpoutMovesAdjust) {
      if ((micros() - rSpoutClocker) >= rSpoutInc) { // move right spout motor
        rSpoutClocker = micros();
  
        // find absolute outer limits, this happens when requestion a movement to position zero
        if (findSpoutOut[1]) { // right spout is moving to zero position
          digitalWriteFast(_PIN_SPOUTDIR_R, LOW); // make sure stepper is moving in the right direction
          delayMicroseconds(10); // short delay to ensure direction has changed
          sendStep(_PIN_SPOUTSTEP_R, stepPulse); // make a step
            if (!digitalReadFast(_PIN_SPOUTOUT_R)) { // check if outer limit has been reached
              findSpoutOut[1] = false;
              rServoCurrent = 0;
            }
        }
  
        // regular movements, relative to zero position
        if (!findSpoutOut[1]) {
           
          // right spout moves in
          if (rSpoutMovesIn == true) {
            // target hasnt been reached yet
            if (rServoCurrent != rServoIn) { 
              rServoCurrent = moveRightSpout(rServoCurrent, rServoIn, stepPulse); // move right spout
            }
            
            // stop motion when target has been reached  
            if (rServoCurrent == rServoIn) { 
              rSpoutMovesIn = false;
            }
          }

          // right spout adjustment movement
          else if (rSpoutMovesAdjust == true) {
            // target hasnt been reached yet
            if (rServoCurrent != rServoAdjust) {
              rServoCurrent = moveRightSpout(rServoCurrent, rServoAdjust, stepPulse); // move right spout
            }
            
            // stop motion when target has been reached
            if (rServoCurrent == rServoAdjust) {
              rSpoutMovesAdjust = false;
            }
          }
    
          // right spout moves out
          else if (rSpoutMovesOut == true) {
            // target hasnt been reached yet
            if (rServoCurrent != rServoOut) {
              rServoCurrent = moveRightSpout(rServoCurrent, rServoOut, stepPulse); // move right spout
            }
            
            // stop motion when target has been reached
            if (rServoCurrent == rServoOut) {
              rSpoutMovesOut = false;
            }
          }
        }
      }
    }

    // check if all spout movements are complete
    if (!lSpoutMovesIn && !lSpoutMovesOut && !lSpoutMovesAdjust && !rSpoutMovesIn && !rSpoutMovesOut && !rSpoutMovesAdjust){ 
      spoutMoves = false;
    }
  }
}

float Spouts::AdjustServo(float Position, float Target, float Increment) {
  if ((Target - Position) < 0) { // desired is lower as current position
    if ((Position - Increment) <= Target) { // check if target is reached at next incremental change
      Position = Target;
    }
    else {
      Position = Position - Increment; // decrease position until target position is reached
    }
  }

  if ((Target - Position) > 0) { // desired is higher as current position
    if ((Position + Increment) >= Target) { // check if target is reached at next incremental change
      Position = Target;
    }
    else {
      Position = Position + Increment; // increase position until target position is reached
    }
  }
  return Position;
}

void Spouts::sendStep(int cPin, int pulseTime_in_us) { // send stepper pulse as long as control signal is high
    digitalWriteFast(cPin, HIGH); // send step
    delayMicroseconds(pulseTime_in_us); // keep step signal high for pulseTime in microseconds. Should be at least 2 or longer.
    digitalWriteFast(cPin, LOW);
}

float Spouts::moveLeftSpout(float current, float target, int pulseDur) {
  if (current < target) { // spout moves towards the animal
	digitalWriteFast(_PIN_SPOUTDIR_L, LOW); // make sure spout is moving in the right direction
  }
  else {  // spout move away from the animal
	digitalWriteFast(_PIN_SPOUTDIR_L, HIGH); // make sure spout is moving in the right direction
  }
  delayMicroseconds(10); // short delay to ensure direction has changed
  sendStep(_PIN_SPOUTSTEP_L, pulseDur); // make a step
  current = AdjustServo(current, target, 1); // adjust current servo position
  if (!digitalReadFast(_PIN_SPOUTOUT_L)){
    current = 0; // if zero-pin is touched, set current position to zero  
  }
  return current;
}

float Spouts::moveRightSpout(float current, float target, int pulseDur) {
  if (current < target) { // spout moves towards the animal
    digitalWriteFast(_PIN_SPOUTDIR_R, HIGH); // make sure spout is moving in the right direction
  }
  else {  // spout move away from the animal
    digitalWriteFast(_PIN_SPOUTDIR_R, LOW); // make sure spout is moving in the right direction
  }
  delayMicroseconds(10); // short delay to ensure direction has changed
  sendStep(_PIN_SPOUTSTEP_R, pulseDur); // make a step
  current = AdjustServo(current, target, 1); // adjust current servo position
  if (!digitalReadFast(_PIN_SPOUTOUT_R)){
    current = 0; // if zero-pin is touched, set current position to zero  
  }
  return current;
}

void Spouts::command_LeftSpoutOut() {
  spoutMoves = true;
  if (lServoOut == 0) { // move left spout to zero position (absolute outer limits)
    findSpoutOut[0] = true; // find outer limit for left stepper
  }
  lSpoutClocker = micros() - lSpoutInc; // initialize timer for spout movement
  lSpoutMovesIn = false; lSpoutMovesOut = true; lSpoutMovesAdjust = false;  // flag that left spout moves to outer position
}

void Spouts::command_RightSpoutOut() {
  spoutMoves = true;
  if (rServoOut == 0) { // move left spout to zero position (absolute outer limits)
    findSpoutOut[1] = true; // find outer limit for right stepper
  }
  rSpoutClocker = micros() - rSpoutInc; // initialize timer for spout movement
  rSpoutMovesIn = false; rSpoutMovesOut = true; rSpoutMovesAdjust = false;  // flag that right spout moves to outer position
}

void Spouts::command_SpoutsIn() {
  spoutMoves = true;
  if (lServoIn == 0) { // move left spout to zero position (absolute outer limits)
    findSpoutOut[0] = true; // find outer limit for left stepper
  }
  if (rServoIn == 0) { // move left spout to zero position (absolute outer limits)
    findSpoutOut[1] = true; // find outer limit for right stepper
  }
      
  lSpoutClocker = micros() - lSpoutInc; // initialize timer for spout movement
  lSpoutMovesIn = true; lSpoutMovesOut = false; lSpoutMovesAdjust = false;  // flag that left spout moves to inner position
  
  rSpoutClocker = micros() - rSpoutInc; // initialize timer for spout movement
  rSpoutMovesIn = true; rSpoutMovesOut = false; rSpoutMovesAdjust = false;  // flag that left spout moves to inner position
}

void Spouts::command_AdjustSpoutSpeed(float new_spoutSpeed) {
  // only update SpoutSpeed if Input is provided. Otherwise leave Speed as is.
  if (new_spoutSpeed > 0) {
    spoutSpeed = new_spoutSpeed * 1000;
  }
  // float distance_l = lServoIn - lServoOut;
  // float distance_r = rServoIn - rServoOut;
  float distance_l = 15;
  float distance_r = 15;
  lSpoutInc = round(spoutSpeed / abs(distance_l)); // time between steps to move at requested left spout speed.     
  rSpoutInc = round(spoutSpeed / abs(distance_r)); // time between steps to move at requested right spout speed.     
}

void Spouts::command_AdjustSpouts(float new_lServoAdjust, float new_rServoAdjust) {
  spoutMoves = true;

  lServoAdjust = new_lServoAdjust;
  rServoAdjust = new_rServoAdjust;

  // Set new Position for the left Spout Motor
  lSpoutClocker = micros() - lSpoutInc; // initialize timer for spout movement
  lSpoutMovesIn = false; lSpoutMovesOut = false; lSpoutMovesAdjust = true;  // flag that left spout moves to adjusted position
  
  if (lServoAdjust == 0 && lServoCurrent != 0) { // move handles to zero position (absolute outer limits)
    findSpoutOut[0] = true; // find outer limit for left stepper
  }
  
  // Now the right Motor
  rSpoutClocker = micros() - rSpoutInc; // initialize timer for spout movement
  rSpoutMovesIn = false; rSpoutMovesOut = false; rSpoutMovesAdjust = true;  // flag that right spout moves to adjusted position
  
  if (rServoAdjust == 0 && rServoCurrent != 0) { // move handles to zero position (absolute outer limits)
    findSpoutOut[1] = true; // find outer limit for right stepper
  }
}
