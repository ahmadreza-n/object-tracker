#include <Arduino.h>
#include <Servo.h>
#include "pid.h"

Servo tilt; // Ver
Servo pan;  // Hor

const int DELAY_MILIS = 1;
const double TILT_Kp{0.4}, TILT_Ki{0.2}, TILT_Kd{0.2};
PID TILT_PID = PID(TILT_Kp, TILT_Ki, TILT_Kd, 0);

const double PAN_Kp{0.4}, PAN_Ki{0.2}, PAN_Kd{0.05};
PID PAN_PID = PID(PAN_Kp, PAN_Ki, PAN_Kd, 0);

void setDegree(const int &, const int &);

void setup()
{
  tilt.write(20);
  tilt.attach(4);

  pan.write(90);
  pan.attach(16);

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
    for (size_t i = 0; i < input.length(); i++)
    {
      if (input.charAt(i) == ' ')
      {
        tiltIn = input.substring(0, i);
        panIn = input.substring(i + 1, input.length());
      }
    }
    tiltErr = tiltIn.toDouble();
    panErr = panIn.toDouble();

    tiltOutput = TILT_PID.compute(tiltErr);
    panOutput = PAN_PID.compute(panErr);

    setDegree(tiltOutput, panOutput);
    Serial.print(String(tiltOutput) + " " + String(panOutput) + " #");
  }
}

void setDegree(const int &tiltOutput, const int &panOutput)
{
  const int tiltAbs{abs(tiltOutput)}, panAbs{abs(panOutput)};

  const int maximum{max(tiltAbs, panAbs)};
  const int panSign{panOutput == 0 ? 0 : panOutput / panAbs},
      tiltSign{tiltOutput == 0 ? 0 : tiltOutput / tiltAbs};
  const int tiltCurr{tilt.read()}, panCurr{pan.read()};
  for (int i = 0; i < maximum; i++)
  {
    if (tiltSign != 0 && i < tiltAbs)
    {
      const int pos{tiltCurr + tiltSign * i};
      if (pos >= 3 && pos <= 120)
        tilt.write(pos);
    }
    if (panSign != 0 && i < panAbs)
      pan.write(panCurr + panSign * i);
    delay(DELAY_MILIS);
  }
}
