# Architecture

The backend separates providers from fusion: serial GPS, phone GPS, and simulated GPS all become validated `GPSState` objects. The WebSocket world stream feeds a React awareness layer, while the map layer is independent and currently uses a key-free demo grid. Connected GPS is measured; camera metric distance is explicitly estimated; simulator values are marked simulated.

