/* EduPath Service Worker v5 — cache o'chirildi */
const CACHE = 'edupath-v5';

// Eski cachelarni o'chirish
self.addEventListener('install', e => {
    e.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', e => {
    e.waitUntil(
        caches.keys()
            .then(keys => Promise.all(keys.map(k => caches.delete(k))))
            .then(() => self.clients.claim())
    );
});

// Hech narsa cache qilmaymiz — har safar serverdan olamiz
self.addEventListener('fetch', e => {
    if (e.request.method !== 'GET') return;
    e.respondWith(fetch(e.request));
});