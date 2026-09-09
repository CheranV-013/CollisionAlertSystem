from dataclasses import dataclass
import ipaddress
import logging
import os
import httpx

log = logging.getLogger("sih26007.ipgeo")

@dataclass
class IPGeoResult:
    latitude: float
    longitude: float
    country: str | None = None
    region: str | None = None
    city: str | None = None
    provider: str = "ipapi.co"
    approximate: bool = True

class IPGeoProvider:
    """City-level fallback only. It is never treated as precise vehicle GPS."""
    def __init__(self): self.template = os.getenv("IP_GEO_PROVIDER_URL", "https://ipapi.co/{ip}/json/")

    async def lookup(self, ip: str | None) -> IPGeoResult | None:
        if not ip:
            return None
        try:
            parsed = ipaddress.ip_address(ip)
            if parsed.is_private or parsed.is_loopback or parsed.is_reserved:
                return None
        except ValueError:
            return None
        try:
            async with httpx.AsyncClient(timeout=2.5) as client:
                response = await client.get(self.template.format(ip=ip), headers={"Accept": "application/json"})
                response.raise_for_status(); data = response.json()
            lat, lon = data.get("latitude"), data.get("longitude")
            if lat is None or lon is None: return None
            return IPGeoResult(float(lat), float(lon), data.get("country_name") or data.get("country"), data.get("region"), data.get("city"))
        except Exception as exc:
            log.warning("IP geolocation unavailable for %s: %s", ip, exc)
            return None
