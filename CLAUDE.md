# Le jardin — deux calendriers

Site publié sur GitHub Pages : https://lauramunteanu.github.io/gardening/

`index.html` est une page d'accueil qui laisse choisir entre les deux calendriers :

| Page | Sujet | Contenu |
|---|---|---|
| `index.html` | accueil / choix | — |
| `potager.html` | légumes & aromatiques | `data-potager.json` |
| `fleurs.html` | fleurs & floraisons | `data-fleurs.json` |

## Où modifier quoi

**Tout le contenu du jardin s'édite dans les fichiers `data-*.json`, jamais dans le HTML.**
Cultures, plantes, mois de semis/plantation/récolte/floraison/soins, notes, tags,
tâches ponctuelles : tout vit dans le JSON.

Les fichiers HTML ne changent que pour la mise en page ou le comportement.
Chacun charge son JSON au démarrage et n'embarque aucune donnée de jardin.

## Structure des données

`data-potager.json` :

```
{
  "sections":  [ { id, titre, lieu, note?, crops: [ … ] } ],
  "speciales": [ { m, g, nom, extra? } ]
}
```

Champs d'une culture : `nom`, `tag`, `ach`, `stype`, `meta`, `note`, `warn`, `wheel`,
et les tableaux de mois `a` (acheter), `s` (semer), `p` (planter), `r` (récolter),
`c` (soins).

`data-fleurs.json` :

```
{
  "sections": [ { titre, note?, plantes: [ … ] } ],
  "taches":   { "<mois 1-12>": [ ["<groupe>", "<texte>"], … ] }
}
```

Champs d'une plante : `nom`, `tag`, `chaud`, `meta`, `note`, et les tableaux de mois
`sem` (semis), `pla` (plantation), `flo` (floraison). Groupes de tâches : `a` acheter,
`s` semer, `p` planter, `c` floraison & coupe, `x` soins & permutations.

Dans les deux fichiers les mois vont de 1 à 12. `meta` et `note` sont rendus en HTML :
les balises (`<b>`, `<br>`…) y sont volontaires. Côté potager, `wheel: false` retire la
culture du décompte de la roue.

Le fichier `data-fleurs.json` a été extrait de l'original, où certains mois s'écrivaient
`r(6,10)` ; ces appels sont devenus des tableaux littéraux (`[6,7,8,9,10]`).

## Fichiers

- `index.html` — page d'accueil, choix entre les deux calendriers
- `potager.html`, `fleurs.html` — les calendriers : mise en page et logique
- `data-potager.json`, `data-fleurs.json` — le contenu
- `sw.js` — service worker (hors ligne)
- `manifest.webmanifest`, `icon.svg` — ajout à l'écran d'accueil
- `calendrier-cultures.html`, `calendrier-fleurs.html` — sources d'origine, figées, non servies

## Après modification

- Un `data-*.json` seul : pousser sur `main`, rien d'autre. Le service worker les
  récupère en réseau d'abord, la nouvelle version apparaît au chargement suivant.
- Un fichier HTML, `sw.js` ou un asset : incrémenter `CACHE` dans `sw.js`
  (`calendrier-v5` → `calendrier-v6`, …) pour que les appareils déjà visités
  ne restent pas sur l'ancienne version.
- Toute nouvelle page navigable doit être ajoutée à `SHELL` **et** à `PAGES`
  dans `sw.js` : chaque page a sa propre copie en cache, l'accueil ne peut pas
  servir de repli pour les autres.

## Mois et millésime

Le mois courant est déduit de l'horloge de l'appareil (`moisCourant()`), jamais codé
en dur. Il se remet à jour au retour sur l'onglet et via un minuteur replanifié au
plus toutes les 6 h. Un mois choisi à la main sur la roue n'est pas écrasé au
changement de mois ; seul le marqueur du jour se déplace.

Le millésime (« 2026–27 ») est calculé par `libelleSaison()` et bascule le
1er septembre, quand se commandent et se sèment les graines de l'année suivante.
Il apparaît dans le titre de l'accueil, dans celui du potager et au centre de la
roue des fleurs.
