# Demo

Start the dashboard, select a scenario, then press START. `front_approach`, `left_approach`, `right_approach`, `behind`, `multiple`, `camera_only`, and `fused` exercise the live risk and visual layers. The phone page is `/mobile-gps`; on the same Wi-Fi use `http://<mac-local-ip>:5173/mobile-gps`.

The application starts in LIVE mode. To enable phone geolocation from another device, install `mkcert`, run `mkcert -install && mkcert <mac-local-ip> localhost 127.0.0.1`, set `VITE_HTTPS_CERT` and `VITE_HTTPS_KEY` in `.env`, and restart Vite. Open `https://<mac-local-ip>:5173/mobile-gps` on the phone and accept the locally trusted certificate. This uses the browser's real secure-context Geolocation API.
