import time
from fastapi.testclient import TestClient
from app.main import app, registry

def test_live_starts_without_demo_vehicles():
    registry.clear()
    with TestClient(app) as client:
        data = client.get('/api/world').json()
        assert data['mode'] == 'LIVE'
        assert data['vehicles'] == []
        assert data['host_vehicle']['fix'] is False

def test_host_and_phone_produce_real_world_state():
    registry.clear()
    with TestClient(app) as client:
        now = time.time()
        assert client.post('/api/vehicle/HOST/position', json={'source':'NEO6M','latitude':11.0,'longitude':76.0,'speed_mps':4,'heading_deg':90,'gps_fix':True,'timestamp':now}).status_code == 200
        assert client.post('/api/vehicle/B01/position', json={'source':'PHONE_GPS','latitude':11.0,'longitude':76.001,'speed_mps':2,'heading_deg':270,'accuracy_m':8,'gps_fix':True,'timestamp':now}).status_code == 200
        world = client.get('/api/world').json()
        assert world['vehicles'][0]['vehicle_id'] == 'B01'
        assert 100 < world['vehicles'][0]['distance_m'] < 115
        assert world['vehicles'][0]['source'] == 'PHONE_GPS'

def test_invalid_coordinates_are_rejected():
    registry.clear()
    with TestClient(app) as client:
        assert client.post('/api/vehicle/HOST/position', json={'latitude':91,'longitude':0,'gps_fix':True}).status_code == 422

