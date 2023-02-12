/*
  Morse.h - Library for flashing Morse code.
  Created by David A. Mellis, November 2, 2007.
  Released into the public domain.
*/

#ifndef Spouts_h
#define Spouts_h

#include "Arduino.h"

class Spouts
{
  public:
    // constructor
    Spouts(int PIN_SPOUTDIR_L, int PIN_SPOUTDIR_R, int PIN_SPOUTSTEP_L, int PIN_SPOUTSTEP_R, int PIN_SPOUTOUT_L, int PIN_SPOUTOUT_R);
	
	// public void to update spout movements, call every loop() iteration
	void SpoutMovements();
	
	// functions to adjust Spout behavior. Externally called over Serial-Communication.
	void command_LeftSpoutOut();
	void command_RightSpoutOut();
	void command_SpoutsIn();
	void command_AdjustSpoutSpeed(float new_spoutSpeed = -1);
	void command_AdjustSpouts(float lServoAdjust, float rServoAdjust);

	// Servo vars
	bool spoutMoves = true;
	float lServoIn = 20; // position to be reached when spouts are moved in by bpod trigger.
	float lServoOut = 10;  // position to be reached when spouts are moved outin by bpod trigger.
	float lServoAdjust = 0; // position that is taken when matlab changes spout position via the ADJUST_SPOUTS event.
	float lServoCurrent = 0; // current servo position - tracks where the servo currently is.
	float rServoIn = 20; // position to be reached when spouts are moved in by bpod trigger.
	float rServoOut = 10;  // position to be reached when spouts are moved out by bpod trigger.
	float rServoAdjust = 0; // position that is taken when matlab changes spout position via the ADJUST_SPOUTS event.
	float rServoCurrent = 0; // current servo position - tracks where the servo currently is.
	
	bool findSpoutOut[2] = { true, true }; // flag that stepper motors are being moved out.
	
	// Movement parameters
	float spoutSpeed = 150000;
    unsigned int lSpoutInc = 5000; // incremental left spout motion to modulate speed
    unsigned int rSpoutInc = 5000; // incremental right spout motion to modulate speed

  private:
    // Internal functions
	float AdjustServo(float Position, float Target, float Increment);
	float moveLeftSpout(float current, float target, int pulseDur);
    float moveRightSpout(float current, float target, int pulseDur);
	void sendStep(int cPin, int pulseTime_in_us);

	// PINs
	int _PIN_SPOUTDIR_L;
	int _PIN_SPOUTDIR_R;
    int _PIN_SPOUTSTEP_L;
    int _PIN_SPOUTSTEP_R;
	int _PIN_SPOUTOUT_L;
	int _PIN_SPOUTOUT_R;

	// State Variables
	bool lSpoutMovesIn = false;
    bool lSpoutMovesOut = false;
    bool lSpoutMovesAdjust = false;

    bool rSpoutMovesIn = false;
    bool rSpoutMovesOut = false;
	bool rSpoutMovesAdjust = false;

	// Clocks
	unsigned long lSpoutClocker; // timer to modulate speed of left spout
	unsigned long rSpoutClocker; // timer to modulate speed of right spout

    // Movement parameters
    int stepPulse = 10; // duration of stepper pulse in microseconds
};

#endif
