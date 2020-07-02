#include <Arduino.h>
#include <Servo.h>

Servo tilt; // Ver
Servo pan;  // Hor

String input;

int SAMPLETIME = 50;

void setPropotionalDeg();
void setErrDeg();

void setup()
{
  tilt.write(3);
  tilt.attach(5);

  pan.write(90);
  pan.attach(4);

  Serial.begin(115200);
  Serial.print("ready");
}

void loop()
{
  if (Serial.available())
  {
    input = Serial.readString();
    // Serial.println("Input data: " + input);

    setPropotionalDeg();
    // setErrDeg();
    Serial.print("ready");
  }
}

void setPropotionalDeg()
{
  String tiltIn, panIn;
  for (size_t i = 0; i < input.length(); i++)
  {
    if (input.charAt(i) == ' ')
    {
      tiltIn = input.substring(0, i);
      panIn = input.substring(i + 1);
    }
  }

  int tiltDeg{tiltIn.toInt()}, panDeg{panIn.toInt()};

  // if (tiltDeg)
  //   tilt.write(tilt.read() + panDeg);
  // if (panDeg)
  //   pan.write(pan.read() + panDeg);

  int tiltDegAbs{abs(tiltDeg)}, panDegAbs{abs(panDeg)};

  int maximum{max(tiltDegAbs, panDegAbs)};
  int panSign{panDeg == 0 ? 0 : panDeg / panDegAbs},
      tiltSign{tiltDeg == 0 ? 0 : tiltDeg / tiltDegAbs};
  int tiltCurr{tilt.read()}, panCurr{pan.read()};
  for (int i = 0; i < maximum; i++)
  {
    if (tiltSign != 0 && i < tiltDegAbs)
    {
      int pos{tiltCurr + tiltSign * i};
      if (pos >= 3 && pos <= 120)
        tilt.write(pos);
    }
    if (panSign != 0 && i < panDegAbs)
      pan.write(panCurr + panSign * i);
    delay(SAMPLETIME);
  }
}

void setErrDeg()
{
  const double k = 0.1;
  String tiltIn, panIn;

  for (size_t i = 0; i < input.length(); i++)
  {
    if (input.charAt(i) == ' ')
    {
      tiltIn = input.substring(0, i);
      panIn = input.substring(i + 1);
      Serial.println("Tilt err: " + tiltIn);
      Serial.println("Pan err: " + panIn);
    }
  }

  float tiltErr = tiltIn.toFloat();
  float panErr = panIn.toFloat();

  if (tiltErr != 0)
  {
    for (double i = tilt.read(); i >= 3 && i <= 120; i += (tiltErr > 0))
    {
      tilt.write(int(i));
      delay(int(1.0 / tiltErr));
    }
  }

  if (panErr != 0)
  {
    for (double i = pan.read(); i >= 0 && i <= 180; i += k * (panErr > 0))
    {
      pan.write(int(i));
      delay(int(1.0 / panErr));
    }
  }
}
