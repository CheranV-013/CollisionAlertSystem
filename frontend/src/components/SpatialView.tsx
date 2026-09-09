import type {Vehicle} from '../types';
function x(b:number){return 50+Math.max(-42,Math.min(42,b/90*42))} function y(d:number){return Math.max(13,Math.min(83,82-d/60*70))}
export function SpatialView({vehicles}:{vehicles:Vehicle[]}){return <div className="spatial"><div className="lane left"/><div className="lane right"/><div className="you"><div className="host-car"><span/></div><small>YOU</small></div>{vehicles.map(v=><div key={v.vehicle_id} className={`detected ${v.risk.toLowerCase()}`} style={{left:`${x(v.relative_bearing_deg)}%`,top:`${y(v.distance_m)}%`}}><div className="vehicle-icon"/><strong>{Math.round(v.distance_m)}m</strong><small>{v.vehicle_id} · {v.source === 'CONNECTED_GPS'?'V2V':'CAMERA'}</small></div>)}</div>}

