#include <Arduino.h>
#include <Servo.h>
#include "pid.h"

Servo TILT; // Ver
Servo PAN;  // Hor

#define TILT_PIN D4
#define PAN_PIN D2

float Ts{};

const int TILT_INIT_VALUE{20};
const int PAN_INIT_VALUE{90};

PID TILT_PID = PID(0.5, 0, 0);
PID PAN_PID = PID(0, 0, 0);

void setDegree(const int &, const int &);
void setParams(const String &);

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

    if (input.endsWith("@"))
    {
      setParams(input);

      Serial.print("@#");
    }
    else
    {
      for (size_t i = 0; i < input.length(); i++)
        if (input.charAt(i) == ' ')
        {
          tiltIn = input.substring(0, i);
          panIn = input.substring(i + 1, input.length());
        }
      tiltErr = tiltIn.toInt();
      if (abs(tiltErr) <= 2)
        tiltErr = 0;
      panErr = panIn.toInt();
      if (abs(panErr) <= 2)
        panErr = 0;

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

void setParams(const String &input)
{
  String trackerType{};
  for (size_t i = 0; i < input.length(); i++)
    if (input.charAt(i) == ' ')
    {
      trackerType = input.substring(0, i);
      break;
    }
  if (trackerType == "csrt")
  {
    Ts = 0.08;
    TILT_PID.setParams(0.495, 0.457, 0);
    PAN_PID.setParams(0.585, 0.468, 0);
  }
  else if (trackerType == "kcf")
  {
    TILT_PID.setParams(0.225, 0.208, 0);
    PAN_PID.setParams(0.266, 0.213, 0);
    Ts = 0.014;
  }
  else if (trackerType == "moss")
  {
    Ts = 0.0056;
  }
  else if (trackerType == "boosting")
  {
    Ts = 0.1;
  }
  else if (trackerType == "mil")
  {
    Ts = 0.09;
  }
  else if (trackerType == "tld")
  {
    Ts = 0.087;
  }
  else if (trackerType == "medianflow")
  {
    Ts = 0.0074;
  }
  else if (trackerType == "goturn")
  {
    Ts = 0.1;
  }
}