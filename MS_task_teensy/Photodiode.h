#ifndef Photodiode_h
#define Photodiode_h

#include "Arduino.h"

class Photodiode {
  public:
    Photodiode(byte Pin); // constructor
	  void recalibrate(); // calibarte for 2s
    bool update(); // call for calibration and to read value
    
    // After every trial set this to false, so this function doens't blcok in case the confirmation was missed
    bool flip_detected = false;
    bool calibration = true;

  private:
    void calibrate(); // calibarte for 2s
    
    int _Pin; // byte to send
    float n_samples = 0; // for calibration
    float mean = 0; // measured during calibration
    float sd = 0; // measured during calibration
    bool first = true; // for calibration
    unsigned long threshold = 0; // result of calibration
    unsigned long sensor_value = 0;

    // Clocks
    unsigned int _clock; // clock for calibration
};

#endif
