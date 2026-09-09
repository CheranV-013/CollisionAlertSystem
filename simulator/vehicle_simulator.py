"""Convenience entry point: the live simulator is owned by backend.app.simulation."""
from backend.app.simulation import Simulator

if __name__ == "__main__":
    sim = Simulator(11.0168, 76.9558)
    host, vehicles = sim.tick()
    print(host.model_dump_json())
    for vehicle in vehicles:
        print(vehicle.model_dump_json())
