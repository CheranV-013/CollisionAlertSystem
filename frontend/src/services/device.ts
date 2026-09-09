const DEVICE_KEY='smartDriveDeviceId'; const LEGACY_DEVICE_KEY='smartDriveDeviceKey'; const VEHICLE_KEY='smartDriveVehicleId';
export function getDeviceKey(){let id=localStorage.getItem(DEVICE_KEY)||localStorage.getItem(LEGACY_DEVICE_KEY);if(!id){id=crypto.randomUUID();localStorage.setItem(DEVICE_KEY,id)}else if(!localStorage.getItem(DEVICE_KEY))localStorage.setItem(DEVICE_KEY,id);return id}
export function getAssignedVehicleId(){return localStorage.getItem(VEHICLE_KEY)}
export function setAssignedVehicleId(id:string){localStorage.setItem(VEHICLE_KEY,id)}
export function clearDeviceSession(){localStorage.removeItem(DEVICE_KEY);localStorage.removeItem(LEGACY_DEVICE_KEY);localStorage.removeItem(VEHICLE_KEY);localStorage.removeItem('smartDriveRole')}
export function getDeviceName(){const ua=navigator.userAgent;const mobile=/Android|iPhone|iPad|Mobile/i.test(ua);return /iPhone/i.test(ua)?'iPhone':/Android/i.test(ua)?'Android Phone':mobile?'Mobile Device':/Macintosh/i.test(ua)?'Mac Desktop':/Windows/i.test(ua)?'Windows PC':'Desktop'}
