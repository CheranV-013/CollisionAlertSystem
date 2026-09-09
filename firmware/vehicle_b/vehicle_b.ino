// Vehicle B is intentionally the same replaceable transport interface as Vehicle A.
// Replace the temporary phone source by wiring NEO-6M to SoftwareSerial and changing ID.
#include <Arduino.h>
#include <SPI.h>
#include <RF24.h>
struct __attribute__((packed)) V2VPacket { char vehicle_id[4]; int32_t latitude_e7; int32_t longitude_e7; uint16_t speed_cms; uint16_t heading_cdeg; uint16_t sequence; uint8_t flags; uint16_t checksum; };
RF24 radio(4,15); uint16_t sequence=0;
uint16_t checksum(const V2VPacket& p){const uint8_t* b=(const uint8_t*)&p;uint16_t s=0;for(size_t i=0;i<sizeof(p)-2;i++)s=(s<<1)^b[i];return s;}
void setup(){Serial.begin(115200);radio.begin();radio.setDataRate(RF24_250KBPS);radio.openWritingPipe(0xAABBCCDDEE);radio.stopListening();}
void loop(){V2VPacket p={{'B','0','1',0},110168000,769558000,500,9000,sequence++,1,0};p.checksum=checksum(p);radio.write(&p,sizeof(p));delay(100);}

