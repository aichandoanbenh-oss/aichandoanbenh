if ('serviceWorker' in navigator && window.isSecureContext) {
  window.addEventListener('load', () => navigator.serviceWorker.register('/sw.js').catch(() => {}));
}
const installButton=document.querySelector('#install-pwa');
let installPrompt;
window.addEventListener('beforeinstallprompt',event=>{
  event.preventDefault();installPrompt=event;
  if(installButton)installButton.hidden=false;
});
if(installButton)installButton.onclick=async()=>{
  if(!installPrompt)return;
  await installPrompt.prompt();await installPrompt.userChoice;
  installPrompt=null;installButton.hidden=true;
};
window.addEventListener('appinstalled',()=>{if(installButton)installButton.hidden=true;});
const connection=document.querySelector('#connection-state');
function updateConnection(){if(connection){connection.hidden=navigator.onLine;connection.textContent='Bạn đang offline. Kết nối Internet để phân tích ảnh và xem lịch sử.';}}
window.addEventListener('online',updateConnection);window.addEventListener('offline',updateConnection);updateConnection();
