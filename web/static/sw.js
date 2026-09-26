const CACHE='vetlens-public-v1';
const PUBLIC=['/static/offline.html','/static/install.html','/static/manifest.webmanifest','/static/pwa.js','/static/install.css','/static/icons/icon-192.png','/static/icons/icon-512.png','/static/icons/apple-touch-icon.png','/static/icons/maskable-512.png'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(PUBLIC))));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(names=>Promise.all(names.filter(name=>name.startsWith('vetlens-public-')&&name!==CACHE).map(name=>caches.delete(name)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{
 const request=event.request,url=new URL(request.url);
 if(request.method!=='GET'||url.origin!==self.location.origin||url.pathname.startsWith('/api/'))return;
 if(request.mode==='navigate'){
   event.respondWith(fetch(request,{cache:'no-store'}).catch(()=>caches.match(url.pathname==='/install'?'/static/install.html':'/static/offline.html')));return;
 }
 if(PUBLIC.includes(url.pathname))event.respondWith(fetch(request).then(response=>{if(response.ok){const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(request,copy));}return response;}).catch(()=>caches.match(request)));
});
