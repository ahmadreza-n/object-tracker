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

PID TILT_PID = PID(0.1, 0, 0);
PID PAN_PID = PID(0.1, 0, 0);

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
      if (abs(tiltErr) <= 3)
        tiltErr = 0;
      panErr = panIn.toInt();
      if (abs(panErr) <= 3)
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
  if (tiltOutput != 0)
  {
    int tiltPos{TILT.read() + tiltOutput};
    if (tiltPos < 3)
      tiltPos = 3;
    else if (tiltPos > 120)
      tiltPos = 120;
    TILT.write(tiltPos);
  }

  if (panOutput != 0)
  {
    int panPos{PAN.read() + panOutput};
    if (panPos < 3)
      panPos = 3;
    else if (panPos > 177)
      panPos = 177;
    PAN.write(panPos);
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
    TILT_PID.setParams(0.18, 0.065, 0.009); 
    // Ku = 0.4, Tu = 2
    // PI = 0.18, 0.108
    // classic PID = 0.32, 0.24, 0.06
    // no overshoot = 0.2, 0.08, 0.0534
    // manual = 0.18, 0.065, 0.009
    PAN_PID.setParams(0.15, 0.05, 0.0075); 
    // Ku = 0.3, Tu = 2.4
    // PI = 0.135, 0.0675
    // classic PID = 0.18, 0.15, 0.054
    // no overshoot = 0.15, 0.05, 0.048
    // manual = 0.15, 0.05, 0.0075
  }
  else if (trackerType == "kcf")
  {
    TILT_PID.setParams(0.1, 0.1, 0.0045);
    PAN_PID.setParams(0.09, 0.09, 0.0038);
  }
  else if (trackerType == "moss")
  {
  }
  else if (trackerType == "boosting")
  {
  }
  else if (trackerType == "mil")
  {
  }
  else if (trackerType == "tld")
  {
  }
  else if (trackerType == "medianflow")
  {
  }
  else if (trackerType == "goturn")
  {
  }
}