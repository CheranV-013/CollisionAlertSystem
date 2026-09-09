export function StatusPill({label,status}:{label:string;status:string|number|boolean}){const good=['CONNECTED','SIMULATED'].includes(String(status)); return <span className="status-pill"><i className={good?'on':''}/>{label} <b>{String(status)}</b></span>}

