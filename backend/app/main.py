import asyncio, math, os, time
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from .geo import haversine_distance_m, initial_bearing_deg, relative_bearing_deg
from .models.domain import *
from .risk import risk_score, time_to_collision
from .simulation import Simulator

STALE_TIMEOUT_S = float(os.getenv("GPS_STALE_TIMEOUT_S", "5"))

class SimulationCommand(BaseModel): scenario: str | None = None
class ModeCommand(BaseModel): mode: str
class PositionUpdate(BaseModel):
    source: DetectionSource = DetectionSource.NEO6M
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    altitude_m: float | None = None
    speed_mps: float | None = Field(default=None, ge=0, le=150)
    heading_deg: float | None = Field(default=None, ge=0, lt=360)
    accuracy_m: float | None = Field(default=None, ge=0)
    gps_fix: bool = True
    satellites: int = Field(default=0, ge=0, le=99)
    timestamp: float = Field(default_factory=time.time)

    @field_validator("timestamp")
    @classmethod
    def finite_timestamp(cls, value: float) -> float:
        if not math.isfinite(value): raise ValueError("timestamp must be finite")
        return value

class RegistryEntry:
    def __init__(self, state: GPSState): self.state, self.last_update, self.previous = state, time.time(), None
    def update(self, state: GPSState): self.previous, self.state, self.last_update = self.state, state, time.time()
    @property
    def stale(self): return time.time() - self.last_update > STALE_TIMEOUT_S

registry: dict[str, RegistryEntry] = {}
clients: set[WebSocket] = set()
mode = "LIVE"
sim = Simulator(float(os.getenv("HOST_LATITUDE", "11.0168")), float(os.getenv("HOST_LONGITUDE", "76.9558")))
sim.running = False

def put_state(vehicle_id: str, update: PositionUpdate) -> GPSState:
    if update.gps_fix and (update.latitude is None or update.longitude is None):
        raise HTTPException(422, "latitude and longitude are required when gps_fix is true")
    state = GPSState(vehicle_id=vehicle_id, fix=update.gps_fix, **update.model_dump(exclude={"gps_fix"}))
    if vehicle_id in registry: registry[vehicle_id].update(state)
    else: registry[vehicle_id] = RegistryEntry(state)
    return state

def current_states() -> tuple[GPSState | None, list[GPSState]]:
    if mode == "DEMO":
        return sim.tick()
    host_entry = registry.get("HOST")
    host = host_entry.state if host_entry and not host_entry.stale and host_entry.state.fix else None
    targets = [e.state for vid, e in registry.items() if vid != "HOST" and not e.stale and e.state.fix]
    return host, targets

def build_world() -> WorldState:
    host, targets = current_states()
    if host is None: host = GPSState(vehicle_id="HOST", source=DetectionSource.NEO6M, fix=False, timestamp=time.time())
    vehicles: list[UnifiedVehicleState] = []
    for target in targets:
        if host.latitude is None or host.longitude is None or target.latitude is None or target.longitude is None: continue
        distance = haversine_distance_m(host.latitude, host.longitude, target.latitude, target.longitude)
        bearing = initial_bearing_deg(host.latitude, host.longitude, target.latitude, target.longitude)
        rel = relative_bearing_deg(bearing, host.heading_deg) if host.heading_deg is not None else 0
        closing = max(0.0, (host.speed_mps or 0) - (target.speed_mps or 0)) if abs(rel) < 70 else 0.0
        ttc = time_to_collision(distance, closing)
        score, level = risk_score(distance, closing, ttc, rel)
        metrics = RiskMetrics(distance_m=distance, bearing_deg=bearing, relative_bearing_deg=rel, closing_speed_mps=closing, ttc_s=ttc, score=score, level=level)
        vehicles.append(UnifiedVehicleState(vehicle_id=target.vehicle_id, latitude=target.latitude, longitude=target.longitude, speed_mps=target.speed_mps, heading_deg=target.heading_deg, distance_m=distance, bearing_deg=bearing, relative_bearing_deg=rel, source=target.source, confidence=.96 if target.source in (DetectionSource.NEO6M, DetectionSource.PHONE_GPS) else .7, risk=level, risk_metrics=metrics, updated_at=target.timestamp, accuracy_m=target.accuracy_m, status="SIMULATED" if mode == "DEMO" else "LIVE"))
    status = {"host_gps": "SIMULATED" if mode == "DEMO" else ("LIVE" if "HOST" in registry and not registry["HOST"].stale and registry["HOST"].state.fix else "NO_FIX"), "phone_b01": "SIMULATED" if mode == "DEMO" else ("LIVE" if "B01" in registry and not registry["B01"].stale and registry["B01"].state.fix else ("STALE" if "B01" in registry else "WAITING")), "backend": "CONNECTED", "camera": "DISCONNECTED", "imu": "DISCONNECTED", "v2v": "DISCONNECTED", "mode": mode, "stale_timeout_s": STALE_TIMEOUT_S}
    return WorldState(host_vehicle=host, vehicles=vehicles, system_status=status, mode=mode, scenario=sim.scenario if mode == "DEMO" else None, demo_running=mode == "DEMO" and sim.running)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(broadcast_loop()); yield; task.cancel()
app = FastAPI(title="SIH26007 Collision Alert System", version="0.2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
def health(): return {"status": "ok", "mode": mode, "timestamp": time.time()}
@app.get("/api/config")
def config(): return {"mode": mode, "stale_timeout_s": STALE_TIMEOUT_S, "map_api_key": os.getenv("MAP_API_KEY", ""), "map_style_url": os.getenv("MAP_STYLE_URL", "")}
@app.get("/api/world", response_model=WorldState)
def world(): return build_world()
@app.get("/api/vehicles")
def vehicles(): return build_world().vehicles
@app.post("/api/mode")
def set_mode(command: ModeCommand):
    global mode
    requested = command.mode.upper()
    if requested not in ("LIVE", "DEMO"): raise HTTPException(400, "mode must be LIVE or DEMO")
    mode = requested; sim.running = requested == "DEMO"; return build_world()
@app.post("/api/simulation/start")
def start(cmd: SimulationCommand | None = None):
    global mode
    mode = "DEMO"; sim.running = True; sim.reset(cmd.scenario if cmd else None); return build_world()
@app.post("/api/simulation/stop")
def stop():
    global mode
    mode = "LIVE"; sim.running = False; return build_world()
@app.post("/api/simulation/reset")
def reset(cmd: SimulationCommand | None = None):
    global mode
    mode = "DEMO"; sim.reset(cmd.scenario if cmd else None); sim.running = True; return build_world()
@app.post("/api/vehicle/{vehicle_id}/position")
def position(vehicle_id: str, update: PositionUpdate):
    if vehicle_id not in ("HOST", "B01"): raise HTTPException(400, "only HOST and B01 are supported in live mode")
    return put_state(vehicle_id, update)
@app.get("/api/camera/status")
def camera_status(): return {"available": False, "mode": "disconnected", "fps": 0}

@app.websocket("/ws")
async def websocket(ws: WebSocket):
    await ws.accept(); clients.add(ws)
    try:
        await ws.send_json(build_world().model_dump(mode="json"))
        while True: await ws.receive_text()
    except (WebSocketDisconnect, RuntimeError): clients.discard(ws)

@app.websocket("/ws/mobile-gps")
async def mobile_gps(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_json(); data["source"] = DetectionSource.PHONE_GPS; data["gps_fix"] = True
            put_state("B01", PositionUpdate.model_validate(data))
            await ws.send_json({"type": "ack", "vehicle_id": "B01", "timestamp": time.time()})
    except (WebSocketDisconnect, ValueError): return

async def broadcast_loop():
    while True:
        if clients:
            payload = build_world().model_dump(mode="json"); dead = []
            for client in clients:
                try: await client.send_json(payload)
                except Exception: dead.append(client)
            for client in dead: clients.discard(client)
        await asyncio.sleep(.1)
