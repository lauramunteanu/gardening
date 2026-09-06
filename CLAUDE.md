# Calendrier de culture

Page unique publiée sur GitHub Pages : https://lauramunteanu.github.io/gardening/

## Où modifier quoi

**Tout le contenu du jardin s'édite dans `data.json`, jamais dans `index.html`.**
Cultures, mois de semis/plantation/récolte/soins, notes, tags, tâches ponctuelles :
tout vit dans `data.json`.

`index.html` ne change que pour la mise en page ou le comportement (styles, roue SVG,
panneau mensuel, rendu des fiches). Le fichier lit `data.json` au chargement et
n'embarque plus aucune donnée de culture.

## Structure de `data.json`

```
{
  "sections": [ { id, titre, lieu, note?, crops: [ … ] } ],
  "speciales": [ { m, g, nom, extra? } ]
}
```

Champs d'une culture : `nom`, `tag`, `ach`, `stype`, `meta`, `note`, `warn`, `wheel`,
et les tableaux de mois `a` (acheter), `s` (semer), `p` (planter), `r` (récolter),
`c` (soins) — les mois vont de 1 à 12.

`meta` et `note` sont rendus en HTML : les balises (`<b>`, `<br>`…) y sont volontaires.
`wheel: false` retire la culture du décompte de la roue.

## Fichiers

- `index.html` — mise en page et logique
- `data.json` — contenu du jardin
- `sw.js` — service worker (hors ligne)
- `manifest.webmanifest`, `icon.svg` — ajout à l'écran d'accueil
- `calendrier-cultures.html` — source d'origine, figée, non servie

## Après modification

- `data.json` seul : pousser sur `main`, rien d'autre. Le service worker le récupère
  en réseau d'abord, la nouvelle version apparaît au chargement suivant.
- `index.html`, `sw.js` ou les assets : incrémenter `CACHE` dans `sw.js`
  (`calendrier-v4` → `calendrier-v5`, …) pour que les appareils déjà visités
  ne restent pas sur l'ancienne version.

## Mois courant

Déduit de l'horloge de l'appareil (`moisCourant()`), pas codé en dur. Il se
remet à jour au retour sur l'onglet et via un minuteur. Un mois choisi à la main
sur la roue n'est pas écrasé au changement de mois. Seul le millésime du titre
(« 2026–27 ») est écrit à la main dans `index.html`.
