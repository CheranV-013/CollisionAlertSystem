// Vehicle A live GPS gateway. Install TinyGPSPlus and RF24 in Arduino IDE.
// NodeMCU: NEO-6M TX->D0, RX->D3 (SoftwareSerial), nRF24 CE=D4/CSN=D8,
// hardware SPI D5/D6/D7, MPU6050 SDA=D2/SCL=D1. Never commit credentials.
#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <SoftwareSerial.h>
#include <TinyGPSPlus.h>

const char* WIFI_SSID = "CHANGE_ME";
const char* WIFI_PASSWORD = "CHANGE_ME";
const char* BACKEND_HOST = "192.168.1.10";
const uint16_t BACKEND_PORT = 8000;
const char* VEHICLE_ID = "HOST";
SoftwareSerial gpsSerial(D0, D3); // ESP RX, ESP TX
TinyGPSPlus gps;
unsigned long lastSend = 0;

void connectWifi(){
  if(WiFi.status() == WL_CONNECTED) return;
  WiFi.mode(WIFI_STA); WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  for(uint8_t i=0; i<20 && WiFi.status()!=WL_CONNECTED; ++i) delay(500);
}

void sendState(){
  connectWifi(); if(WiFi.status()!=WL_CONNECTED) return;
  bool fix = gps.location.isValid() && gps.location.age() < 3000;
  WiFiClient client; HTTPClient http;
  String url = String("http://") + BACKEND_HOST + ":" + BACKEND_PORT + "/api/vehicle/HOST/position";
  if(!http.begin(client, url)) return;
  http.addHeader("Content-Type", "application/json");
  String body = String("{\"vehicle_id\":\"HOST\",\"source\":\"NEO6M\",\"gps_fix\":") + (fix ? "true" : "false");
  body += ",\"satellites\":" + String(gps.satellites.isValid() ? gps.satellites.value() : 0);
  body += ",\"timestamp\":" + String(millis() / 1000.0, 3);
  if(fix){
    body += ",\"latitude\":" + String(gps.location.lat(), 8) + ",\"longitude\":" + String(gps.location.lng(), 8);
    body += ",\"altitude_m\":" + String(gps.altitude.isValid() ? gps.altitude.meters() : 0.0, 2);
    body += ",\"speed_mps\":" + String(gps.speed.isValid() ? gps.speed.mps() : 0.0, 2);
    body += ",\"heading_deg\":" + String(gps.course.isValid() ? gps.course.deg() : 0.0, 2);
  }
  body += "}"; http.POST(body); http.end();
}

void setup(){Serial.begin(115200); gpsSerial.begin(9600); connectWifi();}
void loop(){while(gpsSerial.available()) gps.encode(gpsSerial.read()); if(millis()-lastSend>=1000){lastSend=millis();sendState();} delay(5);}
