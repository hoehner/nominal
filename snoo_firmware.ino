#include <Arduino.h>
#include <Servo.h>

const int LINE_MAX = 96;

char  line[LINE_MAX];
int   char_buffer = 0;
float snoo_temp = 0;
int snoo_mic = 0;
unsigned int mic_sample;
int snoo_fan = 0;
int snoo_wiggle = 0;


Servo wiggle_servo; // create servo object

void setup() {
  Serial.begin(115200);
  while (!Serial) { } // for native USB boards'
  wiggle_servo.attach(5);
}

void loop() {
  unsigned long mic_startMillis = millis(); // Start of sample window
  unsigned int peakToPeak = 0;   // peak-to-peak level
  unsigned int signalMax = 0;
  unsigned int signalMin = 1024;
  
  while (Serial.available()) {
    char c = (char)Serial.read();

    if (c == '\r') continue;          // ignore CR
    if (c == '\n') {
      // terminate and process
      line[char_buffer] = 0;

      // -----------------------------------------
      // ----- process any incoming commands -----
      // -----------------------------------------
      
      if (char_buffer == 0) {
        // ignore empty
      } else if (strcmp(line, "*IDN?") == 0) {                // Query - Identify yourself (simple identification)
        Serial.println(F("(NOMINAL) SNOO BETA"));
      } else if (strcmp(line, "PING?") == 0) {                // Query - Requesting a PONG back (simple heartbeat)
        Serial.print(F("PONG "));
        Serial.println(millis());
      } else if (strcmp(line, "SNOO:TEMP?") == 0) {           // Query - Get the SNOO:TEMP value (temp from TMP36 sensor)
        int tempValue = analogRead(A1);
        float voltage = tempValue * (5.0 / 1024.0);
        float temp_c = (voltage - 0.5) * 100;
        float temp_f = (temp_c * 9 / 5) + 32;
        snoo_temp = temp_f;
        Serial.println(snoo_temp, 3);
      } else if (strcmp(line, "SNOO:MIC?") == 0) {            // Query - Get the SNOO:MIC value (max from traling 2 sec)
          while (millis() - mic_startMillis < 20)             // 20ms sample window
          {
            mic_sample = analogRead(A0);
            if (mic_sample < 1024)  // toss out spurious readings
            {
              if (mic_sample > signalMax)
              {
                signalMax = mic_sample;  // save just the max levels
              }
              else if (mic_sample < signalMin)
              {
                signalMin = mic_sample;  // save just the min levels
              }
            }
          }
        snoo_mic = signalMax - signalMin;  // max - min = peak-peak amplitude
        Serial.println(snoo_mic);
      } else if (strcmp(line, "SNOO:FAN?") == 0) {            // Query - Get the SNOO:FAN speed (float)
        Serial.println(snoo_fan, DEC);
      } else if (strcmp(line, "SNOO:WIGGLE?") == 0) {         // Query - Get SNOO:WIGGLE status (ON/OFF)
          if (snoo_wiggle == 0) {
            Serial.println(F("OFF"));
          } else if (snoo_wiggle == 1) {
            Serial.println(F("ON"));
          } else {
            Serial.println(F("BAD CMD SYNTAX"));
          }
      } else if (strncmp(line, "SNOO:FAN ", 9) == 0) {        // Command - Set SNOO:FAN speed
        snoo_fan = atof(line + 9);
        wiggle_servo.write(snoo_fan);
        Serial.println(F("ACCEPTED"));
      } else if (strncmp(line, "SNOO:WIGGLE ", 9) == 0) {     // Command - Set SNOO:WIGGLE status (ON/OFF)
        snoo_wiggle = atof(line + 9);
        Serial.println(F("ACCEPTED"));
      } else {
        Serial.println(F("CMD NOT SUPPORTED"));
      }

      // reset buffer
      char_buffer = 0;
      return; // process one line per loop spin (keeps latency predictable)
    } else if (char_buffer < LINE_MAX - 1) {
      line[char_buffer++] = c;               // accumulate
    } else {
      // overflow: cap and respond with error on next newline
      // (optional) you could also flush here.
    }
  }
}
