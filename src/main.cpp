#include <Arduino.h>
#include <Servo.h>
#include "pid.h"

Servo TILT; // Ver
Servo PAN;  // Hor

#define TILT_PIN D4
#define PAN_PIN D2

const float Ts = 0.1;

const int TILT_INIT_VALUE = 20;
const int PAN_INIT_VALUE = 90;

const double TILT_Kp{0.495}, TILT_Ki{0.457}, TILT_Kd{0};
PID TILT_PID = PID(TILT_Kp, TILT_Ki, TILT_Kd, 0);

const double PAN_Kp{0.585}, PAN_Ki{0.468}, PAN_Kd{0};
PID PAN_PID = PID(PAN_Kp, PAN_Ki, PAN_Kd, 0);

void setDegree(const int &, const int &);

void setup()
{
  TILT.write(TILT_INIT_VALUE);
  TILT.attach(TILT_PIN);

  PAN.write(PAN_INIT_VALUE);
  PAN.attach(PAN_PIN);

  Serial.begin(115200);
  Serial.print("Serial initialized.");
}

String input;
double tiltErr{}, panErr{};
int tiltOutput{}, panOutput{};
String tiltIn{}, panIn{};
void loop()
{
  if (Serial.available())
  {
    input = Serial.readStringUntil('$');

    if (input == "@")
      Serial.print("@#");
    else
    {
      for (size_t i = 0; i < input.length(); i++)
      {
        if (input.charAt(i) == ' ')
        {
          tiltIn = input.substring(0, i);
          panIn = input.substring(i + 1, input.length());
        }
      }
      tiltErr = tiltIn.toInt();

      tiltOutput = TILT_PID.compute(tiltErr);
      panOutput = PAN_PID.compute(panErr);

      setDegree(tiltOutput, panOutput);
      delay(Ts * 900);
      Serial.print(String(tiltOutput) + " " + String(panOutput) + " #");
    }
  }
}

void setDegree(const int &tiltOutput, const int &panOutput)
{
  const int tiltAbs{abs(tiltOutput)}, panAbs{abs(panOutput)};

  const int maximum{max(tiltAbs, panAbs)};
  const int panSign{panOutput == 0 ? 0 : panOutput / panAbs},
      tiltSign{tiltOutput == 0 ? 0 : tiltOutput / tiltAbs};
  const int tiltCurr{TILT.read()}, panCurr{PAN.read()};
  for (int i = 0; i < maximum; i++)
  {
    if (tiltSign != 0 && i < tiltAbs)
    {
      const int pos{tiltCurr + tiltSign * i};
      if (pos >= 3 && pos <= 120)
        TILT.write(pos);
    }
    if (panSign != 0 && i < panAbs)
    {
      const int pos{panCurr + panSign * i};
      if (pos >= 2 && pos <= 178)
        PAN.write(pos);
    }
  }
}
