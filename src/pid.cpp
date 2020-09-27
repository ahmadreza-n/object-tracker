#include <Arduino.h>
#include "pid.h"

PID::PID(const double &Kp, const double &Ki, const double &Kd)
    : _Kp{Kp}, _Ki{Ki}, _Kd{Kd}, lastErr{0}, lastTime{0}, maxIntegral{Ki == 0 ? 0 : 180 / Ki}
{
}

void PID::setParams(const double &Kp, const double &Ki, const double &Kd)
{
  _Kp = Kp;
  _Ki = Ki;
  _Kd = Kd;
}

int PID::compute(const double &err)
{
  const long currentTime = millis();
  double Ts = lastTime == 0 ? 0 : (currentTime - lastTime) / 1000.0;
  if (Ts > 0.5)
  {
    Ts = 0;
    integral = 0;
  }
  lastTime = currentTime;
  const double derivative = Ts == 0 ? 0 : (err - lastErr) / Ts;
  integral += err * Ts;

  if (integral > maxIntegral)
    integral = maxIntegral;
  else if (integral < -maxIntegral)
    integral = -maxIntegral;
  if (integral * err <= 0)
    integral = 0;

  lastErr = err;
  return round((err * _Kp) + (derivative * _Kd) + (integral * _Ki));
}
