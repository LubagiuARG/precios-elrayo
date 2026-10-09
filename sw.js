// La lista de precios: siempre intenta traer la versión nueva; si no hay señal, muestra la última guardada.
// Las fotos: se muestran al instante desde el celular y se actualizan en segundo plano.
const CACHE = "rayo-v4";
const FOTOS = "rayo-fotos-v1";

self.addEventListener("install", () => self.skipWaiting());

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(claves => Promise.all(claves.filter(c => c !== CACHE && c !== FOTOS).map(c => caches.delete(c))))
      .then(() => clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || !req.url.startsWith(self.location.origin)) return;

  // Fotos de productos: primero lo guardado, y de paso se busca una versión nueva por si la cambiaron
  if (new URL(req.url).pathname.includes("/img/")) {
    e.respondWith(caches.open(FOTOS).then(async cache => {
      const guardada = await cache.match(req);
      const nueva = fetch(req).then(r => {
        if (r.ok) cache.put(req, r.clone());
        return r;
      }).catch(() => guardada);
      if (guardada) {
        e.waitUntil(nueva);
        return guardada;
      }
      return nueva;
    }));
    return;
  }

  // Todo lo demás (la app con los precios): primero internet, y si no hay señal, lo guardado
  e.respondWith(
    fetch(req).then(r => {
      const copia = r.clone();
      caches.open(CACHE).then(c => c.put(req, copia));
      return r;
    }).catch(() => caches.match(req))
  );
});