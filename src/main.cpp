#include <Arduino.h>
#include <Servo.h>
// #include <LiquidCrystal_I2C.h> // Library for LCD
// #include <Wire.h> // Library for I2C communication

// LiquidCrystal_I2C lcd = LiquidCrystal_I2C(0x3F, 16, 2); // Change to (0x27,16,2) for 16x2 LCD.

Servo tilt; // Ver
Servo pan;  // Hor

String input;

int SAMPLETIME = 10;
const float H_GAIN{0.1}, W_GAIN{0.1};

int tiltDeg{}, panDeg{};

void setPropotionalDeg();

void setup()
{
  // Wire.begin(12, 13);
  // lcd.begin();

  // lcd.home();
  // lcd.print("LCD initialized");

  tilt.write(30);
  tilt.attach(5);

  pan.write(90);
  pan.attach(4);

  Serial.begin(115200);
  Serial.print("Serial initialized.");
}

void loop()
{
  if (Serial.available())
  {
    // input = "";
    // while (Serial.available())
    // {
    //   char ch = Serial.read();
    //   input += String(ch);
    // }

    input = Serial.readStringUntil('$');

    String tiltIn{}, panIn{};
    for (size_t i = 0; i < input.length(); i++)
    {
      if (input.charAt(i) == ' ')
      {
        tiltIn = input.substring(0, i);
        panIn = input.substring(i + 1, input.length());
      }
    }
    tiltDeg = tiltIn.toInt();
    panDeg = panIn.toInt();

    setPropotionalDeg();
    Serial.write("#");
  }
}

void setPropotionalDeg()
{
  int tiltDegAbs{abs(tiltDeg)}, panDegAbs{abs(panDeg)};

  tiltDegAbs = tiltDegAbs > (1.0 / H_GAIN) ? (tiltDegAbs * H_GAIN) : 8;
  panDegAbs = panDegAbs > (1.0 / W_GAIN) ? (panDegAbs * W_GAIN) : 7;

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
