export const API_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
export const WS_URL = (import.meta.env.VITE_WS_URL || (API_URL ? API_URL.replace(/^http/, 'ws') + '/ws' : `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws`)).replace(/\/$/, '');
