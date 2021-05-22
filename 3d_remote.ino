#include <ESP8266WiFi.h>
#include <WiFiUdp.h>

#include <Adafruit_MPU6050.h>
#include <Wire.h>

#include "WiFi_ssid_pass.h"

#include <string>

#define IP_REMOTE "192.168.1.100"
#define PORT_LOCAL 2999
#define PORT_REMOTE 3999

WiFiUDP UDP;

Adafruit_MPU6050 MPU;

sensors_event_t acc, gyro, temp;
float sensors[7];

int buttonPin = D3;

bool buttonPressed = false;
const char endMsg[] = ":end";

void setup() {
  Serial.begin(115200);

  // Initialize button
  pinMode(buttonPin, INPUT);

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
  Serial.println(WiFi.localIP());
  Serial.println(UDP.remotePort());

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

  if (buttonHold(buttonPin)) {
    buttonPressed = true;
    UDP.beginPacket(IP_REMOTE, PORT_REMOTE);  // UDP.remotePort()
    UDP.write(msg.c_str());
    Serial.println("sent");
    UDP.endPacket();
  } else if (buttonPressed == true){
    buttonPressed = false;
    UDP.beginPacket(IP_REMOTE, PORT_REMOTE);  // UDP.remotePort()
    UDP.write(endMsg);
    Serial.println("sent endMsg");
    UDP.endPacket();
  }
}

bool buttonPress(int buttonPin) {
  // register button press on release
  if (!digitalRead(buttonPin)) {
    delay(50);
    if (digitalRead(buttonPin)) {
      return true;
    }
  }
  return false;
}

bool buttonHold(int buttonPin) {
  if (!digitalRead(buttonPin)) {
    return true;
  }
  return false;
}