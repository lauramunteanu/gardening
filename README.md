# Calendrier de culture · Saint-Genis-Pouilly

Calendrier de semis, plantation et récolte, en une seule page.

- `index.html` — la page (source d'origine conservée dans `calendrier-cultures.html`)
- `sw.js` — service worker : la page et les polices sont mises en cache à la première visite, puis consultables hors ligne
- `manifest.webmanifest` — permet d'ajouter le calendrier à l'écran d'accueil

Publié via GitHub Pages depuis la branche `main`.

## Mettre à jour

Modifier `index.html`, incrémenter `CACHE` dans `sw.js` (`calendrier-v3` → `calendrier-v4`, …)
pour que les appareils déjà visités récupèrent la nouvelle version, puis pousser sur `main`.

Le mois affiché est déduit de l'horloge de l'appareil : rien à modifier au fil des mois.
Seul le millésime du titre (« 2026–27 ») est écrit à la main, comme le contenu du calendrier.
