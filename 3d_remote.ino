#include <ESP8266WiFi.h>
#include <WiFiUdp.h>

#include "WiFi_ssid_pass.h"

#define PORT_LOCAL 2999
#define PORT_REMOTE 3999

WiFiUDP UDP;

char reply[] = "Hello\r\n";

//char packetBuffer[UDP_TX_PACKET_MAX_SIZE + 1];

void setup() {
  Serial.begin(115200);

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
  UDP.beginPacket("192.168.1.100", PORT_REMOTE); // UDP.remotePort()
  UDP.write(reply);
  //Serial.println("sent");
  UDP.endPacket();
  //delay(500);
}
