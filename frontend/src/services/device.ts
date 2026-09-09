const DEVICE_KEY='smartDriveDeviceKey'; const VEHICLE_KEY='smartDriveVehicleId';
export function getDeviceKey(){let id=localStorage.getItem(DEVICE_KEY);if(!id){id=crypto.randomUUID();localStorage.setItem(DEVICE_KEY,id)}return id}
export function getAssignedVehicleId(){return localStorage.getItem(VEHICLE_KEY)}
export function setAssignedVehicleId(id:string){localStorage.setItem(VEHICLE_KEY,id)}
