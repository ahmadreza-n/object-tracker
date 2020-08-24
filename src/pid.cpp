#include <Arduino.h>
#include "pid.h"

PID::PID(const double &Kp, const double &Ki, const double &Kd, const double &Ts)
    : _Kp{Kp}, _Ki{Ki}, _Kd{Kd}, _Ts{Ts}, lastErr{0}, lastTime{0}
{
}

double PID::compute(const double &err)
{
  const long int currentTime =  millis();
  double Ts = lastTime == 0 ? 0 : (currentTime - lastTime) / 1000.0;
  // Serial.println(Ts);
  lastTime = currentTime;
  const double derivative = _Ts == 0 ? 0 : (err - lastErr) / Ts;
  integral += err * Ts;

  if (integral > 65535)
  {
    integral = 65535;
  }
  else if (integral < -65535)
  {
    integral = -65535;
  }
  if (integral * err < 0)
  {
    integral = 0;
  }

  lastErr = err;
  return (err * _Kp) + (derivative * _Kd) + (integral * _Ki);
}
