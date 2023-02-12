#include "Arduino.h"
#include "Photodiode.h"

Photodiode::Photodiode(byte Pin) {
  _Pin = Pin;
  _clock = millis();

  analogReadResolution(10); 
  analogReadAveraging(4);
}

void Photodiode::calibrate() {
  if (millis() - _clock < 1000.) {
    mean += sensor_value;
    n_samples += 1;
  } else if (millis() - _clock < 2000.) {
    if (first) {
      // compute the mean once
      first = false;
      mean = (float)mean / (float)n_samples;
      n_samples = 0;
    }

    sd += sq(sensor_value - mean);
    n_samples += 1;
  } else {
    // finish by computing sd
    sd = sqrt(sd/ (n_samples - 1));

    // calculate threshold as mean + certain number of sd's
    threshold = (unsigned long) round(mean + 5 * sd);
    calibration = false;
  }
}

void Photodiode::recalibrate() {
  calibration = true;
  n_samples = 0; // for calibration
  mean = 0; // measured during calibration
  sd = 0; // measured during calibration
  first = true; // for calibration
  _clock = millis();
}

bool Photodiode::update() {
  sensor_value = analogRead(_Pin);

  if (calibration) {
    calibrate();
    flip_detected = false;
  } else {
    flip_detected = sensor_value > threshold;
    // Serial.print(mean);
    // Serial.print(",");
    // Serial.print(mean + 5 * sd);
    // Serial.print(",");
    // Serial.println(sensor_value);
  }

  return flip_detected;
}
