// AI stays on the Mac initially. This sketch exposes a JPEG stream/capture endpoint.
#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
const char* ssid="CHANGE_ME"; const char* password="CHANGE_ME";
WebServer server(80);
void setup(){Serial.begin(115200);camera_config_t c{};c.ledc_channel=LEDC_CHANNEL_0;c.ledc_timer=LEDC_TIMER_0;c.pin_d0=5;c.pin_d1=18;c.pin_d2=19;c.pin_d3=21;c.pin_d4=36;c.pin_d5=39;c.pin_d6=34;c.pin_d7=35;c.pin_xclk=0;c.pin_pclk=22;c.pin_vsync=25;c.pin_href=23;c.pin_sscb_sda=26;c.pin_sscb_scl=27;c.pin_pwdn=32;c.pin_reset=-1;c.xclk_freq_hz=20000000;c.pixel_format=PIXFORMAT_JPEG;c.frame_size=FRAMESIZE_QVGA;c.jpeg_quality=12;c.fb_count=1;esp_camera_init(&c);WiFi.begin(ssid,password);server.on("/health",[](){server.send(200,"application/json","{\"status\":\"ok\"}");});server.on("/capture",[](){camera_fb_t* f=esp_camera_fb_get();if(!f){server.send(503,"text/plain","capture failed");return;}server.send_P(200,"image/jpeg",(const char*)f->buf,f->len);esp_camera_fb_return(f);});server.begin();}
void loop(){server.handleClient();delay(2);}
