import time
from fastapi.testclient import TestClient
from app.main import app, registry
import app.main as main_module

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

def test_shared_websocket_accepts_phone_update_and_broadcasts():
    registry.clear(); main_module.device_assignments.clear(); main_module.device_roles.clear(); main_module.host_vehicle_id = None; main_module.next_member_number = 1
    with TestClient(app) as client:
        with client.websocket_connect('/ws') as host_socket:
            host_socket.receive_json()
            host_socket.send_json({'type':'DEVICE_JOIN','device_id':'device-host','role':'HOST'})
            assert host_socket.receive_json()['type'] == 'DEVICE_REGISTERED'
        with client.websocket_connect('/ws') as socket:
            socket.receive_json()
            socket.send_json({'type':'DEVICE_JOIN','device_id':'device-member','role':'MEMBER'})
            ack = socket.receive_json()
            assert (ack['vehicle_id'], ack['role']) == ('MEMBER-001', 'MEMBER')
            socket.receive_json()
            socket.send_json({'type':'LOCATION_UPDATE','device_key':'device-member','latitude':11.0,'longitude':76.001,'accuracy_m':7,'speed_mps':None,'heading_deg':None,'timestamp':time.time()})
            message = socket.receive_json()
            assert message.get('type') == 'world_state'
            assert registry['MEMBER-001'].state.source.value == 'BROWSER_GPS'

def test_backend_assigns_one_host_and_subsequent_trucks(monkeypatch):
    registry.clear(); main_module.device_assignments.clear(); main_module.device_roles.clear(); main_module.host_vehicle_id = None; main_module.next_member_number = 1
    async def no_ip_geo(_): return None
    monkeypatch.setattr(main_module.ipgeo, 'lookup', no_ip_geo)
    with TestClient(app) as client:
        with client.websocket_connect('/ws') as first:
            first.receive_json(); first.send_json({'type':'DEVICE_JOIN','device_id':'device-a','role':'HOST'}); ack_a = first.receive_json()
        with client.websocket_connect('/ws') as second:
            second.receive_json(); second.send_json({'type':'DEVICE_JOIN','device_id':'device-b','role':'MEMBER'}); ack_b = second.receive_json()
    assert (ack_a['vehicle_id'], ack_a['role']) == ('HOST-001', 'HOST')
    assert (ack_b['vehicle_id'], ack_b['role']) == ('MEMBER-001', 'MEMBER')

def test_second_host_is_rejected(monkeypatch):
    registry.clear(); main_module.device_assignments.clear(); main_module.device_roles.clear(); main_module.host_vehicle_id = None; main_module.next_member_number = 1
    async def no_ip_geo(_): return None
    monkeypatch.setattr(main_module.ipgeo, 'lookup', no_ip_geo)
    with TestClient(app) as client:
        with client.websocket_connect('/ws') as first:
            first.receive_json(); first.send_json({'type':'DEVICE_JOIN','device_id':'device-a','role':'HOST'}); first.receive_json()
        with client.websocket_connect('/ws') as second:
            second.receive_json(); second.send_json({'type':'DEVICE_JOIN','device_id':'device-b','role':'HOST'}); rejection = second.receive_json()
    assert rejection == {'type':'ROLE_REJECTED','reason':'HOST_ALREADY_ACTIVE'}
