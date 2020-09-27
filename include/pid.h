#ifndef PID_H
#define PID_H

#include <Arduino.h>

class PID
{
public:
  PID() = default;
  PID(const double &, const double &, const double &);
  int compute(const double &);
  void setParams(const double &, const double &, const double &);
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