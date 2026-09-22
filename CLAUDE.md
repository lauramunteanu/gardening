# Le jardin — trois calendriers

Site publié sur GitHub Pages : https://lauramunteanu.github.io/gardening/

`index.html` est une page d'accueil qui laisse choisir entre les trois calendriers :

| Page | Sujet | Contenu |
|---|---|---|
| `index.html` | accueil / choix | — |
| `potager.html` | légumes & aromatiques | `data-potager.json` |
| `fleurs.html` | fleurs & floraisons | `data-fleurs.json` |
| `arbustes.html` | arbres, arbustes, grimpants | `data-arbustes.json` |

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

`data-arbustes.json` :

```
{
  "plantes":     [ { nom, nomLatin, emplacement, type, contenant, bois, taille,
                     vieuxBois, saigne, hivernage, rusticite, plantation, etabli, taches } ],
  "ponctuelles": [ { m, nom, extra } ]
}
```

Les quatre vues dérivent toutes de `plantes` :

- `taille` = `{ mois, legere, interdit, bloque, note }`. `bloque: true` grise les douze
  mois et affiche « à déterminer » — c'est l'état du framboisier tant que son type
  n'est pas identifié, et de la haie de Lonicera qui part à l'arrachage.
- `vieuxBois: false` veut dire **ne repart pas du bois brun** (romarin, sauge,
  conifères). C'est un drapeau permanent, pas un mois.
- `saigne: true` déclenche l'alerte rouge de la vue « Le mois ».
- `hivernage` : `hors-gel`, `pot emmailloté`, `feuillage protégé`, `souche buttée`
  ou `aucun`. `feuillage protégé` implique aussi l'emmaillotage du pot.
- `plantation` (`YYYY-MM`) + `etabli: false` alimentent « Jeunes plants » et
  l'entrée disparaît d'elle-même au bout de trois ans.

`ponctuelles` est une extension au modèle du spec : elle accueille ce qui n'est
pas une plante suivie (datura à arracher, semis spontané dans le mur).

## Fichiers

- `index.html` — page d'accueil, choix entre les trois calendriers
- `potager.html`, `fleurs.html`, `arbustes.html` — les calendriers : mise en page et logique
- `data-potager.json`, `data-fleurs.json`, `data-arbustes.json` — le contenu
- `sw.js` — service worker (hors ligne)
- `manifest.webmanifest`, `icon.svg` — ajout à l'écran d'accueil
- `calendrier-cultures.html`, `calendrier-fleurs.html` — sources d'origine, figées, non servies.
  **Attention** : un spec qui vise `calendrier-fleurs.html` vise en réalité
  `data-fleurs.json` (contenu) ou `fleurs.html` (mise en page). Éditer le fichier
  d'origine ne change rien sur le site.

## Après modification

- Un `data-*.json` seul : pousser sur `main`, rien d'autre. Le service worker les
  récupère en réseau d'abord, la nouvelle version apparaît au chargement suivant.
- Un fichier HTML, `sw.js` ou un asset : incrémenter `CACHE` dans `sw.js`
  (`calendrier-v8` → `calendrier-v9`, …) pour que les appareils déjà visités
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

## Page du jour (accueil)

`index.html` affiche en tête « Aujourd'hui » : les tâches du mois courant tirées des
trois JSON — `speciales` du potager, `taches` des fleurs, `taches` et `ponctuelles`
des arbustes. Elle n'a **aucune donnée propre** : pour qu'une tâche y apparaisse,
on l'ajoute dans le calendrier concerné. Les fenêtres de culture (tableaux `s`, `p`,
`r` des cartes) n'y figurent pas — ce sont des périodes, pas des tâches.

Ce que le texte d'une tâche change à son affichage :

- **« chaque jour » ou « quotidien » dans une phrase qui parle d'arrosage** → rangée
  dans « Chaque jour », décochée chaque matin. Les autres « chaque jour » (dessaler
  les olives) restent des tâches ordinaires.
- **« début », « mi- » ou « fin » suivi du nom du mois courant** (« mi-octobre »,
  « Mi à fin octobre ») → « Plus tard ce mois-ci » jusqu'au 1er, 11 ou 21. Sans le nom
  du mois derrière, rien : « mi-ombre » n'est pas une date.
- **« ⚠ » dans le titre** → remontée en tête de liste.
- Un arbre avec `saigne: true` dont le mois courant est `interdit` → bandeau rouge.

Les cases cochées vivent dans le `localStorage` du navigateur : propres à chaque
appareil, ni partagées ni sauvegardées. Clé = mois (ou jour pour l'arrosage) + calendrier
+ texte de la tâche : **reformuler une tâche la décoche.** La dernière semaine du mois,
un aperçu du mois suivant apparaît en bas.

## Ce qui est encore en suspens

- **Framboisier** : type inconnu. La seule canne vivante est sortie en 2026 et n'a
  pas fructifié, ce qui plaide contre un remontant — mais `data-potager.json`
  l'appelle encore « Framboisier remontant 'Heritage' ». Tant que ce n'est pas
  tranché, aucune taille : une coupe au ras sur un non-remontant supprimerait la
  récolte de juin, et il ne reste qu'une canne. Verdict à la première fructification.
- **Fraisiers 'Charlotte'** : emplacement non tranché (massif en novembre, ou bac
  début mars). La carte, la tâche de plantation de novembre, l'alerte « déplacer la
  courgette » et l'entrée de février sur la terre neuve du bac se décident ensemble.
- **Appleblossom** : cité dans le semis de février de `data-fleurs.json` sans carte
  correspondante. Soit la variété sort de la commande, soit il lui faut une carte.
- **AquaBloom** : plus utilisé, toutes les références sont retirées des calendriers
  jusqu'à nouvel ordre.
