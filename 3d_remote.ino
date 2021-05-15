#include <ESP8266WiFi.h>
#include <WiFiUdp.h>

#include "WiFi_ssid_pass.h"

#define PORT 9999

WiFiUDP UDP;

char reply[] = "Hello\n";

char packetBuffer[UDP_TX_PACKET_MAX_SIZE + 1];

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

  UDP.begin(PORT);

}

void loop() {
  int packetSize = UDP.parsePacket();
  if (packetSize) {
    int n = UDP.read(packetBuffer, UDP_TX_PACKET_MAX_SIZE);
    packetBuffer[n] = 0;
    Serial.println("Contents:");
    Serial.println(packetBuffer);

    UDP.beginPacket("192.168.1.100", UDP.remotePort());
    UDP.write(reply);
    Serial.println(UDP.remotePort());
    UDP.endPacket();
    //delay(500);
  }  
}
