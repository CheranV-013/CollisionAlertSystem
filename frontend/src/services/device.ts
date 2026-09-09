const KEY='smart_drive_vehicle_id';
export function getVehicleId(){let id=localStorage.getItem(KEY);if(!id){id=`TRUCK-${crypto.randomUUID().slice(0,8).toUpperCase()}`;localStorage.setItem(KEY,id)}return id}
