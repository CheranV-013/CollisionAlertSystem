import asyncio, json, logging, math, os, time, uuid, ipaddress
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from .geo import haversine_distance_m, initial_bearing_deg, relative_bearing_deg
from .models.domain import *
from .risk import risk_score, time_to_collision
from .simulation import Simulator
from .gps.ipgeo import IPGeoProvider, IPGeoResult

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sih26007")
STALE_TIMEOUT_S = float(os.getenv("STALE_TIMEOUT_SECONDS", os.getenv("GPS_STALE_TIMEOUT_S", "5")))
OFFLINE_TIMEOUT_S = STALE_TIMEOUT_S * 2

class SimulationCommand(BaseModel): scenario: str | None = None
class ModeCommand(BaseModel): mode: str
class PositionUpdate(BaseModel):
    source: DetectionSource = DetectionSource.BROWSER_GPS
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
    def __init__(self, state: GPSState, ip: str | None = None, geo: IPGeoResult | None = None):
        self.state, self.ip_address, self.ip_geo, self.last_update = state, ip, geo, time.time()
    def update(self, state: GPSState): self.state, self.last_update = state, time.time()
    @property
    def age(self): return time.time() - self.last_update
    @property
    def status(self): return "ONLINE" if self.age <= STALE_TIMEOUT_S else ("STALE" if self.age <= OFFLINE_TIMEOUT_S else "OFFLINE")

registry: dict[str, RegistryEntry] = {}
clients: set[WebSocket] = set()
host_vehicle_id: str | None = None
mode = "LIVE"
sim = Simulator(float(os.getenv("HOST_LATITUDE", "11.0168")), float(os.getenv("HOST_LONGITUDE", "76.9558")))
sim.running = False
ipgeo = IPGeoProvider()

def client_ip(ws: WebSocket) -> str | None:
    candidate = ws.client.host if ws.client else None
    if os.getenv("TRUST_PROXY_HEADERS", "false").lower() == "true":
        forwarded = ws.headers.get("x-forwarded-for") or ws.headers.get("x-real-ip")
        if forwarded: candidate = forwarded.split(",")[0].strip()
    try: ipaddress.ip_address(candidate or ""); return candidate
    except ValueError: return None

def state_from_update(vehicle_id: str, update: PositionUpdate) -> GPSState:
    if update.gps_fix and (update.latitude is None or update.longitude is None):
        raise HTTPException(422, "latitude and longitude are required when gps_fix is true")
    return GPSState(vehicle_id=vehicle_id, fix=update.gps_fix, location_source=update.source, **update.model_dump(exclude={"gps_fix"}))

async def register_device(vehicle_id: str, ws: WebSocket) -> dict:
    global host_vehicle_id
    if not vehicle_id or len(vehicle_id) > 64: raise ValueError("invalid vehicle_id")
    ip = client_ip(ws); geo = await ipgeo.lookup(ip)
    if vehicle_id in registry: entry = registry[vehicle_id]; entry.ip_address, entry.ip_geo, entry.last_update = ip, geo, time.time()
    else:
        source = DetectionSource.IP_APPROXIMATE
        state = GPSState(vehicle_id=vehicle_id, source=source, location_source=source, latitude=geo.latitude if geo else None, longitude=geo.longitude if geo else None, fix=False, timestamp=time.time())
        registry[vehicle_id] = RegistryEntry(state, ip, geo)
    if host_vehicle_id is None: host_vehicle_id = vehicle_id
    log.info("device joined vehicle_id=%s ip_geo=%s host=%s", vehicle_id, bool(geo), host_vehicle_id == vehicle_id)
    return {"vehicle_id": vehicle_id, "role": "HOST" if host_vehicle_id == vehicle_id else "VEHICLE", "ip_location": bool(geo)}

def put_state(vehicle_id: str, update: PositionUpdate, ip: str | None = None) -> GPSState:
    global host_vehicle_id
    state = state_from_update(vehicle_id, update)
    if vehicle_id in registry: registry[vehicle_id].update(state)
    else: registry[vehicle_id] = RegistryEntry(state, ip)
    if host_vehicle_id is None and vehicle_id == "HOST": host_vehicle_id = vehicle_id
    log.info("location update vehicle_id=%s source=%s fix=%s", vehicle_id, state.source.value, state.fix)
    return state

def current_states() -> tuple[GPSState | None, list[tuple[GPSState, RegistryEntry]]]:
    if mode == "DEMO":
        host, targets = sim.tick()
        return host, [(target, RegistryEntry(target)) for target in targets]
    host_entry = registry.get(host_vehicle_id or "")
    host = host_entry.state if host_entry and host_entry.status != "OFFLINE" else None
    targets = [(entry.state, entry) for vid, entry in registry.items() if vid != host_vehicle_id and entry.status != "OFFLINE" and entry.state.latitude is not None and entry.state.longitude is not None]
    return host, targets

def build_world() -> WorldState:
    host, targets = current_states()
    if host is None: host = GPSState(vehicle_id=host_vehicle_id or "HOST", source=DetectionSource.BROWSER_GPS, location_source=DetectionSource.BROWSER_GPS, fix=False, timestamp=time.time())
    vehicles: list[UnifiedVehicleState] = []
    for target, entry in targets:
        if host.latitude is None or host.longitude is None or target.latitude is None or target.longitude is None: continue
        distance = haversine_distance_m(host.latitude, host.longitude, target.latitude, target.longitude)
        bearing = initial_bearing_deg(host.latitude, host.longitude, target.latitude, target.longitude)
        rel = relative_bearing_deg(bearing, host.heading_deg) if host.heading_deg is not None else 0
        closing = max(0.0, (host.speed_mps or 0) - (target.speed_mps or 0)) if abs(rel) < 70 else 0.0
        ttc = time_to_collision(distance, closing)
        score, level = risk_score(distance, closing, ttc, rel)
        if target.location_source == DetectionSource.IP_APPROXIMATE or host.location_source == DetectionSource.IP_APPROXIMATE:
            score, level, ttc = 0.0, RiskLevel.SAFE, None
        metrics = RiskMetrics(distance_m=distance, bearing_deg=bearing, relative_bearing_deg=rel, closing_speed_mps=closing, ttc_s=ttc, score=score, level=level)
        geo = entry.ip_geo
        vehicles.append(UnifiedVehicleState(vehicle_id=target.vehicle_id, latitude=target.latitude, longitude=target.longitude, speed_mps=target.speed_mps, heading_deg=target.heading_deg, distance_m=distance, bearing_deg=bearing, relative_bearing_deg=rel, source=target.source, confidence=.96 if target.location_source == DetectionSource.BROWSER_GPS else .25, risk=level, risk_metrics=metrics, updated_at=target.timestamp, accuracy_m=target.accuracy_m, status="SIMULATED" if mode == "DEMO" else entry.status, location_source=target.location_source, ip_city=geo.city if geo else None, ip_region=geo.region if geo else None, ip_country=geo.country if geo else None, gps_permission="active" if target.location_source == DetectionSource.BROWSER_GPS else "unknown"))
    host_entry = registry.get(host_vehicle_id or "")
    host_status = "SIMULATED" if mode == "DEMO" else (host_entry.status if host_entry else "WAITING")
    status = {"system": "ONLINE", "host_gps": "SIMULATED" if mode == "DEMO" else (host.location_source.value if host.location_source else host_status), "trucks_online": sum(1 for _, entry in targets if entry.status == "ONLINE"), "camera": "DISCONNECTED", "imu": "DISCONNECTED", "v2v": "DISCONNECTED", "mode": mode, "stale_timeout_s": STALE_TIMEOUT_S}
    return WorldState(host_vehicle=host, vehicles=vehicles, system_status=status, mode=mode, scenario=sim.scenario if mode == "DEMO" else None, demo_running=mode == "DEMO" and sim.running, host_vehicle_id=host_vehicle_id)

def origins(): return [item.strip() for item in os.getenv("ALLOWED_ORIGINS", "").split(",") if item.strip()]

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(broadcast_loop()); yield; task.cancel()
app = FastAPI(title="SIH26007 Collision Alert System", version="0.3.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=origins() or ["http://localhost:5173", "http://localhost:5174"], allow_origin_regex=r"https://.*\.vercel\.app", allow_credentials=True, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["*"])

@app.get("/api/health")
def health(): return {"status":"ok", "backend":"ok", "websocket":"ready", "gps":"device_registry", "simulation":mode == "DEMO", "mode":mode, "version":"0.3.0", "timestamp":time.time()}
@app.get("/api/world", response_model=WorldState)
def world(): return build_world()
@app.get("/api/config")
def config(): return {"mode":mode, "stale_timeout_s":STALE_TIMEOUT_S, "map_api_key":os.getenv("MAP_API_KEY", ""), "map_style_url":os.getenv("MAP_STYLE_URL", "")}
@app.post("/api/mode")
def set_mode(command: ModeCommand):
    global mode
    if command.mode.upper() not in ("LIVE", "DEMO"): raise HTTPException(400, "mode must be LIVE or DEMO")
    mode = command.mode.upper(); sim.running = mode == "DEMO"; return build_world()
@app.post("/api/simulation/start")
def start(cmd: SimulationCommand | None = None):
    global mode
    mode = "DEMO"; sim.running = True; sim.reset(cmd.scenario if cmd else None); return build_world()
@app.post("/api/simulation/stop")
def stop():
    global mode
    mode = "LIVE"; sim.running = False; return build_world()
@app.post("/api/vehicle/{vehicle_id}/position")
def position(vehicle_id: str, update: PositionUpdate): return put_state(vehicle_id, update)

@app.websocket("/ws")
async def websocket(ws: WebSocket):
    await ws.accept(); clients.add(ws); log.info("WebSocket connected clients=%d", len(clients))
    try:
        await ws.send_json(build_world().model_dump(mode="json"))
        while True:
            try: raw = await asyncio.wait_for(ws.receive_text(), timeout=20)
            except asyncio.TimeoutError: await ws.send_json({"type":"ping","timestamp":time.time()}); continue
            if not raw: continue
            try: message = json.loads(raw)
            except json.JSONDecodeError: continue
            kind = message.get("type")
            if kind == "pong": continue
            if kind == "DEVICE_JOIN":
                ack = await register_device(str(message.get("vehicle_id", "")), ws); await ws.send_json({"type":"device_ack", **ack}); await broadcast_now(); continue
            if kind == "DEVICE_HEARTBEAT":
                vehicle_id = str(message.get("vehicle_id", ""));
                if vehicle_id in registry: registry[vehicle_id].last_update = time.time()
                continue
            if kind in ("LOCATION_UPDATE", "PHONE_GPS_UPDATE") or message.get("vehicle_id"):
                vehicle_id = str(message.get("vehicle_id", ""))
                if vehicle_id not in registry: await register_device(vehicle_id, ws)
                message["source"] = DetectionSource.BROWSER_GPS; message["gps_fix"] = True
                put_state(vehicle_id, PositionUpdate.model_validate(message), client_ip(ws)); await broadcast_now()
    except (WebSocketDisconnect, RuntimeError, ValueError) as exc:
        log.info("WebSocket disconnected: %s", exc)
    finally:
        clients.discard(ws); log.info("WebSocket disconnected clients=%d", len(clients))

async def broadcast_now():
    payload = build_world().model_dump(mode="json"); dead=[]
    for client in clients:
        try: await client.send_json(payload)
        except Exception: dead.append(client)
    for client in dead: clients.discard(client)

async def broadcast_loop():
    while True:
        if clients: await broadcast_now()
        await asyncio.sleep(.1)
