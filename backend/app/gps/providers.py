from typing import Protocol

class GPSProvider(Protocol):
    async def start(self) -> None: ...

class PhoneGPSProvider:
    """Transport boundary for browser location_update messages."""

class SerialGPSProvider:
    """Hardware boundary for a future NEO-6M serial gateway."""

class SimulationGPSProvider:
    """Explicit DEMO-mode provider boundary."""
