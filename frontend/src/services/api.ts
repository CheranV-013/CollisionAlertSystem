import {API_URL} from './config';
export async function simulation(action:'start'|'stop'|'reset',scenario?:string){await fetch(`${API_URL}/api/simulation/${action}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(scenario?{scenario}:{})})}
export async function setMode(mode:'LIVE'|'DEMO'){await fetch(`${API_URL}/api/mode`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode})})}
