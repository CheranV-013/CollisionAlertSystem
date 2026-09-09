import React from 'react'; import {createRoot} from 'react-dom/client'; import App from './App'; import {MobileGps} from './components/MobileGps';
createRoot(document.getElementById('root')!).render(location.pathname==='/mobile-gps'?<MobileGps/>:<App/>);

