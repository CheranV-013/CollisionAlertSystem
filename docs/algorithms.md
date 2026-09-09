# Algorithms and limitations

Distance uses Haversine and direction uses initial great-circle bearing. Relative bearing is normalized to -180..180, where positive is right. TTC is distance divided by positive closing speed; no TTC is reported when the target is not closing. The risk score blends proximity, closing speed, TTC, and lateral alignment with configurable thresholds in `backend/app/risk.py`. NEO-6M accuracy is consumer-grade, nRF24 is transport, MPU6050 is motion-only, and ESP32-CAM distance is not metric without calibration.

