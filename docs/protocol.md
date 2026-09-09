# V2V packet

The nRF24 payload is a packed 26-byte `V2VPacket`: vehicle ID 4 bytes; latitude and longitude signed integer degrees × 1e7, 4 bytes each; speed centimetres/second, 2; heading centidegrees, 2; sequence, 2; flags, 1; checksum, 2. nRF24 transports the packet only; it does not localize vehicles. The checksum is a lightweight corruption check and packets must also be rejected when stale or out of sequence.

