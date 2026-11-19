// Ancienne adresse de l'appli : ce service worker se désinstalle et renvoie vers /budget-by-mgm/.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k.startsWith('mgm-budget-')).map(k => caches.delete(k)));
    await self.registration.unregister();
    const wins = await self.clients.matchAll({type: 'window'});
    wins.forEach(w => w.navigate(w.url).catch(() => {}));
  })());
});
