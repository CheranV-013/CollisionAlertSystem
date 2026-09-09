# Hardware

Vehicle A/B use ESP8266, NEO-6M, MPU6050 and nRF24L01. Keep nRF24 at 3.3 V with a local 10–47 µF capacitor. MPU6050 uses I2C: SDA D2 and SCL D1 on NodeMCU. GPS serial pins must be crossed and level-safe. The ESP32-CAM sketch uses the AI Thinker camera pin map; verify the exact board. Never commit Wi-Fi credentials; the included sketch uses placeholders.

