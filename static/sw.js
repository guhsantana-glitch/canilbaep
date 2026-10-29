/* Service Worker do Canil 10° BAEP — shell offline + cache de estáticos. */
const VERSAO = "canil-v2";
const NUCLEO = ["/", "/static/manifest.json"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(VERSAO).then((cache) => cache.addAll(NUCLEO)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((chaves) =>
      Promise.all(chaves.filter((k) => k !== VERSAO).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  // Só gerencia mesma origem.
  if (url.origin !== self.location.origin) return;

  // Navegação: rede primeiro, cai para cache da home offline.
  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req).catch(() => caches.match("/"))
    );
    return;
  }

  // Estáticos/imagens: cache primeiro, atualiza em segundo plano.
  // /media/ NÃO é cacheado: fotos e documentos são protegidos por canil —
  // em aparelho compartilhado, o cache vazaria dados de outro usuário.
  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      caches.match(req).then((hit) => {
        const busca = fetch(req).then((resp) => {
          if (resp && resp.ok) {
            const copia = resp.clone();
            caches.open(VERSAO).then((cache) => cache.put(req, copia));
          }
          return resp;
        }).catch(() => hit);
        return hit || busca;
      })
    );
  }
});
