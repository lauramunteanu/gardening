# Le jardin · Saint-Jean-de-Gonville

Deux calendriers de jardin, consultables hors ligne :
**https://lauramunteanu.github.io/gardening/**

- **L'année au jardin** (`potager.html`) — semis, plantations et récoltes
- **Toujours en fleurs** (`fleurs.html`) — floraisons, mois par mois

La page d'accueil laisse choisir entre les deux et rappelle, pour chacun, ce qu'il
y a à faire ce mois-ci.

## Fichiers

- `index.html` — page d'accueil
- `potager.html`, `fleurs.html` — les calendriers : mise en page et logique
- `data-potager.json`, `data-fleurs.json` — **tout le contenu du jardin** ; ce sont
  les seuls fichiers à modifier pour ajouter une plante ou changer un mois
- `sw.js` — service worker : les pages, les données et les polices sont mises en
  cache à la première visite, puis consultables hors ligne
- `manifest.webmanifest`, `icon.svg` — ajout à l'écran d'accueil
- `calendrier-cultures.html`, `calendrier-fleurs.html` — sources d'origine, conservées

## Mettre à jour

Pour le contenu : modifier le `data-*.json` concerné et pousser sur `main`. Rien
d'autre à faire — le service worker le charge en réseau d'abord, la nouvelle version
apparaît au chargement suivant.

Pour la mise en page (HTML, `sw.js`, assets) : incrémenter aussi `CACHE` dans `sw.js`
(`calendrier-v5` → `calendrier-v6`, …) pour que les appareils déjà visités récupèrent
la nouvelle version.

Le mois affiché et le millésime (« 2026–27 », qui bascule le 1er septembre) sont
déduits de l'horloge de l'appareil : rien à modifier au fil des mois ni des années.
