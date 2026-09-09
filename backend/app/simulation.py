import math, time
from dataclasses import dataclass
from .geo import offset_coordinate
from .models.domain import GPSState, DetectionSource

@dataclass
class SimVehicle:
    vehicle_id: str
    north_m: float
    east_m: float
    speed_mps: float
    heading_deg: float
    scenario: str
    vehicle_type: str = "car"

class Simulator:
    scenarios = ["safe", "front_approach", "left_approach", "right_approach", "behind", "multiple", "camera_only", "fused"]
    def __init__(self, lat: float, lon: float):
        self.lat, self.lon = lat, lon
        self.running = True
        self.scenario = "multiple"
        self.started = time.time()
        self.vehicles: list[SimVehicle] = []
        self.reset()

    def reset(self, scenario: str | None = None):
        self.scenario = scenario or self.scenario
        self.started = time.time()
        specs = {
            "safe": [("B01", 40, 8, 5, 90)], "front_approach": [("B01", 42, 0, 11, 270)],
            "left_approach": [("B01", 3, -32, 9, 0)], "right_approach": [("B01", 3, 32, 9, 180)],
            "behind": [("B01", -18, 0, 12, 90)], "multiple": [("B01", 28, -10, 6, 270), ("B02", 45, 13, 4, 270), ("B03", -25, 18, 3, 90)],
            "camera_only": [("CAM01", 18, 5, 0, 270)], "fused": [("B01", 20, 3, 7, 270)],
        }
        self.vehicles = [SimVehicle(*args, scenario=self.scenario) for args in specs.get(self.scenario, specs["multiple"])]

    def host(self, now: float) -> GPSState:
        return GPSState(vehicle_id="HOST-001", role="HOST", latitude=self.lat, longitude=self.lon, speed_mps=8.3, heading_deg=90, timestamp=now, satellites=9, source=DetectionSource.SIMULATED)

    def tick(self, dt: float = .1) -> tuple[GPSState, list[GPSState]]:
        if self.running:
            for v in self.vehicles:
                if self.scenario == "front_approach": v.north_m -= v.speed_mps * dt
                elif self.scenario == "left_approach": v.east_m += v.speed_mps * dt
                elif self.scenario == "right_approach": v.east_m -= v.speed_mps * dt
                elif self.scenario == "behind": v.east_m += v.speed_mps * dt
                else: v.east_m += math.sin(time.time() / 5 + len(v.vehicle_id)) * dt
        now = time.time()
        targets = []
        for v in self.vehicles:
            tlat, tlon = offset_coordinate(self.lat, self.lon, v.north_m, v.east_m)
            targets.append(GPSState(vehicle_id=v.vehicle_id, role="TRUCK", latitude=tlat, longitude=tlon, speed_mps=v.speed_mps, heading_deg=v.heading_deg, timestamp=now, satellites=9, source=DetectionSource.SIMULATED))
        return self.host(now), targets
