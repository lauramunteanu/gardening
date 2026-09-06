# Calendrier de culture · Saint-Genis-Pouilly

Calendrier de semis, plantation et récolte, en une seule page.

- `index.html` — la page : mise en page et logique uniquement
- `data.json` — **tout le contenu du jardin** ; c'est le seul fichier à modifier pour
  ajouter une culture ou changer un mois
- `sw.js` — service worker : la page et les polices sont mises en cache à la première visite, puis consultables hors ligne
- `calendrier-cultures.html` — source d'origine, conservée telle quelle
- `manifest.webmanifest` — permet d'ajouter le calendrier à l'écran d'accueil

Publié via GitHub Pages depuis la branche `main`.

## Mettre à jour

Pour le contenu : modifier `data.json` et pousser sur `main`. Rien d'autre à faire —
le service worker le charge en réseau d'abord, la nouvelle version apparaît au
chargement suivant.

Pour la mise en page (`index.html`, `sw.js`, assets) : incrémenter aussi `CACHE` dans
`sw.js` (`calendrier-v4` → `calendrier-v5`, …) pour que les appareils déjà visités
récupèrent la nouvelle version.

Le mois affiché est déduit de l'horloge de l'appareil : rien à modifier au fil des mois.
Seul le millésime du titre (« 2026–27 ») est écrit à la main, comme le contenu du calendrier.
