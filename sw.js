// Ancien service worker de la racine : il se désinstalle et nettoie ses copies, l'app vit maintenant dans /REVISION-BTS-NDRC-BY-MGM/.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k.startsWith('bts-ndrc-')).map(k => caches.delete(k)));
    await self.registration.unregister();
    const wins = await self.clients.matchAll({type: 'window'});
    wins.forEach(w => w.navigate(w.url).catch(() => {}));
  })());
});
