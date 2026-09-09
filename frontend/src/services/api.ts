export async function simulation(action:'start'|'stop'|'reset',scenario?:string){await fetch(`/api/simulation/${action}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(scenario?{scenario}:{})})}

