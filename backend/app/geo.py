import math

EARTH_RADIUS_M = 6_371_000.0

def normalize_bearing(degrees: float) -> float:
    return (degrees + 180) % 360 - 180

def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.atan2(math.sqrt(a), math.sqrt(max(0, 1 - a)))

def initial_bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return math.degrees(math.atan2(y, x)) % 360

def relative_bearing_deg(target_bearing: float, host_heading: float) -> float:
    return normalize_bearing(target_bearing - host_heading)

def offset_coordinate(lat: float, lon: float, north_m: float, east_m: float) -> tuple[float, float]:
    return lat + north_m / EARTH_RADIUS_M * 180 / math.pi, lon + east_m / (EARTH_RADIUS_M * math.cos(math.radians(lat))) * 180 / math.pi

