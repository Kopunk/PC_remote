#include <ESP8266WiFi.h>
#include <WiFiUdp.h>

#include <Adafruit_MPU6050.h>
#include <Wire.h>

#include "WIFI_CONFIG.h"

#include <string>

WiFiUDP UDP;

Adafruit_MPU6050 MPU;

sensors_event_t acc, gyro, temp;
float sensors[7];

const int buttonPinMain = D3;
const int buttonPinSec = D4;

bool buttonPressedMain = false;
bool buttonPressedSec = false;

const char endMsg[] = ":end";
const char pressSecMsg[] = ":spec";
const char releaseSecMsg[] = ":rel";

void setup() {
  Serial.begin(115200);

  // Initialize button
  pinMode(buttonPinMain, INPUT);
  pinMode(buttonPinSec, INPUT);

  // Initialize MPU
  while (!MPU.begin()) {
    Serial.println("Failed to initialize MPU6050");
  }

  // Initialize UDP

  WiFi.mode(WIFI_STA);
  WiFi.begin(SSID, PASS);

  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(100);
  }

  Serial.println("\n Connected");
  Serial.println("My IP is:");
  Serial.println(WiFi.localIP());

  UDP.begin(PORT_LOCAL);

  while (true) {
    int packetSize = UDP.parsePacket();
    if (packetSize) { break; }
  }
}

void loop() {
  MPU.getEvent(&acc, &gyro, &temp);

  // arduino float is 32 bits
  sensors[0] = acc.acceleration.x;
  sensors[1] = acc.acceleration.y;
  sensors[2] = acc.acceleration.z;

  sensors[3] = gyro.gyro.x;
  sensors[4] = gyro.gyro.y;
  sensors[5] = gyro.gyro.z;

  sensors[6] = temp.temperature;

  String msg = "";

  for (int i = 0; i < 6; i++) {  // temp sensor isn't necessary
    msg = String(msg + ':' + sensors[i]);
  }

  if (buttonHold(buttonPinMain)) {
    buttonPressedMain = true;
    UDP.beginPacket(IP_REMOTE, PORT_REMOTE);  // UDP.remotePort()
    UDP.write(msg.c_str());
    Serial.println("sent");
    UDP.endPacket();
  } else if (buttonPressedMain == true){
    buttonPressedMain = false;
    UDP.beginPacket(IP_REMOTE, PORT_REMOTE);  // UDP.remotePort()
    UDP.write(endMsg);
    Serial.println("sent endMsg");
    UDP.endPacket();
  }

  if (buttonHold(buttonPinSec)) {
    buttonPressedSec = true;
    UDP.beginPacket(IP_REMOTE, PORT_REMOTE);  // UDP.remotePort()
    UDP.write(pressSecMsg);
    Serial.println("sent pressSecMsg");
    UDP.endPacket();
  } else if (buttonPressedSec == true){  // signals releasing of secondary button
    buttonPressedSec = false;
    UDP.beginPacket(IP_REMOTE, PORT_REMOTE);  // UDP.remotePort()
    UDP.write(releaseSecMsg);
    Serial.println("sent releaseSecMsg");
    UDP.endPacket();

  }
}

// // UNUSED
// bool buttonPress(int buttonPinMain) {
//   // register button press on release
//   if (!digitalRead(buttonPinMain)) {
//     delay(50);
//     if (digitalRead(buttonPinMain)) {
//       return true;
//     }
//   }
//   return false;
// }

bool buttonHold(int buttonPinMain) {
  if (!digitalRead(buttonPinMain)) {
    return true;
  }
  return false;
}