#ifndef PID_H
#define PID_H

#include <Arduino.h>

class PID
{
public:
  PID(const double &, const double &, const double &, const double & Ts=0);
  int compute(const double &);
  ~PID() = default;

private:
  double _Kp, _Ki, _Kd;
  double _Ts;
  double lastErr;
  unsigned long lastTime;
  double maxIntegral;
  double integral;
};

#endif