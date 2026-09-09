import { defineConfig } from 'vite'; import react from '@vitejs/plugin-react'; import fs from 'node:fs';
const cert=process.env.VITE_HTTPS_CERT, key=process.env.VITE_HTTPS_KEY;
export default defineConfig({plugins:[react()],server:{host:'0.0.0.0',port:5173,https:cert&&key&&fs.existsSync(cert)&&fs.existsSync(key)?{cert:fs.readFileSync(cert),key:fs.readFileSync(key)}:undefined,proxy:{'/api':'http://localhost:8000'}}});
