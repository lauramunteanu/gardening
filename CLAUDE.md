# Le jardin — trois calendriers

Site publié sur GitHub Pages : https://lauramunteanu.github.io/gardening/

`index.html` est une page d'accueil qui laisse choisir entre les trois calendriers :

| Page | Sujet | Contenu |
|---|---|---|
| `index.html` | accueil / choix | — |
| `potager.html` | légumes & aromatiques | `data-potager.json` |
| `fleurs.html` | fleurs & floraisons | `data-fleurs.json` |
| `arbustes.html` | arbres, arbustes, grimpants | `data-arbustes.json` |
| `soins.html` | arrosage, engrais, seuils de gel | `meteo/regles.json` + `data-meteo.json` |

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
  "sections":     [ { id, titre, lieu, note?, crops: [ … ] } ],
  "speciales":    [ { m, g, nom, extra? } ],
  "quotidiennes": [ { nom, extra?, mois: [ … ] } ]
}
```

`quotidiennes` : les gestes à refaire **tous les jours** pendant une saison, et non à
une date. Ils remontent dans « Chaque jour » sur la page d'accueil pendant les `mois`
indiqués, se décochent chaque matin, et ne figurent pas dans l'aperçu du mois suivant —
ce ne sont pas des échéances. Garder l'`extra` court : le détail appartient à la fiche
de la culture (`soins`), sinon les deux divergent.

Champs d'une culture : `nom`, `tag`, `ach`, `stype`, `meta`, `note`, `warn`, `wheel`,
et les tableaux de mois `a` (acheter), `s` (semer), `p` (planter), `r` (récolter),
`c` (soins).

Champ optionnel `soins` : `[ { freq, quoi } ]`, rendu en petite liste « Soins » sous la
note. Pour un geste qui se répète à un rythme propre à la culture, pas à un mois — une
culture sans ce champ rend exactement comme avant.

Les entrées de journal s'ajoutent en fin de `note`, sur une nouvelle ligne
(`<br>2026 : …`), sans toucher au texte existant.

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
  ou `aucun`. `feuillage protégé` implique aussi l'emmaillotage du pot. Toute autre
  valeur est traitée comme du texte libre et rendue sous « Autres protections » —
  c'est le cas des rosiers de 1re année et de la lavande.
- `plantation` (`YYYY-MM`) + `etabli: false` alimentent « Jeunes plants » et
  l'entrée disparaît d'elle-même au bout de trois ans.

Champ optionnel `journal` : `[ { date: "YYYY-MM-DD", texte } ]`, ce qui a été fait sur
la plante. Rendu en liste datée, la plus récente en tête, dans le repli de la ligne
(« Fenêtres de taille ») et dans la fiche « Jeunes plants ». Une plante sans journal
rend exactement comme avant.

`plantation` peut être **à venir** : la plante reste hors de « Jeunes plants » jusqu'au
mois venu, puis y entre toute seule (mûre et framboisier 'Heritage', plantés en
février 2027 : commande PdF du 23/11/2026, livraison à partir du 23/02).

`ponctuelles` est une extension au modèle du spec : elle accueille ce qui n'est
pas une plante suivie (datura à arracher, semis spontané dans le mur).

## Cinq plantes qu'on confond

Les noms se ressemblent, les tailles sont opposées :

| Plante | Où | Ce que c'est | Taille |
|---|---|---|---|
| **Mûrier platane** | arbustes, pelouse | l'**arbre**, planté 04/2026 | nov–janv seulement, il saigne |
| **Mûre 'Loch Ness'** | arbustes + potager | l'**arbuste à fruits**, à planter 02/2027 | après récolte, sur bois de l'an passé |
| **Framboisier en place** | arbustes, pied de mur | planté 10/2025, une canne, **type inconnu** | aucune, tant qu'il n'a pas fructifié |
| **Framboisier 'Heritage'** | arbustes + potager | remontant (automne), à planter 02/2027 | tout au ras en **février** |
| **Framboisier 'Glen Ample'** | arbustes + potager | d'été, non remontant, sans épines, à planter 02/2027 | cannes défructifiées au ras en **août**, jamais au ras en février |

Ne jamais faire correspondre une instruction par le seul mot « mûrier » ou
« framboisier » : vérifier de laquelle des cinq il s'agit.

## Fichiers

- `index.html` — page d'accueil, choix entre les trois calendriers
- `potager.html`, `fleurs.html`, `arbustes.html` — les calendriers : mise en page et logique
- `soins.html` — arrosage et engrais plante par plante (lien sous « Aujourd'hui »)
- `data-potager.json`, `data-fleurs.json`, `data-arbustes.json` — le contenu
- `sw.js` — service worker (hors ligne)
- `data-meteo.json` — écrit par la vérification météo, jamais à la main
- `meteo/regles.json`, `meteo/verifie.py`, `.github/workflows/meteo.yml` — la vérification météo
- `manifest.webmanifest`, `icon.svg` — ajout à l'écran d'accueil
- `calendrier-cultures.html`, `calendrier-fleurs.html` — sources d'origine, figées, non servies.
  **Attention** : un spec qui vise `calendrier-fleurs.html` vise en réalité
  `data-fleurs.json` (contenu) ou `fleurs.html` (mise en page). Éditer le fichier
  d'origine ne change rien sur le site.

## Après modification

- Un `data-*.json` seul : pousser sur `main`, rien d'autre. Le service worker les
  récupère en réseau d'abord, la nouvelle version apparaît au chargement suivant.
- Un fichier HTML, `sw.js` ou un asset : incrémenter `CACHE` dans `sw.js`
  (`calendrier-v14` → `calendrier-v15`, …) pour que les appareils déjà visités
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
des arbustes — plus les consignes de `data-meteo.json` (voir « Vérification météo »).
Pour qu'une tâche datée y apparaisse, on l'ajoute dans le calendrier concerné ;
`data-meteo.json` n'est jamais édité à la main. Les fenêtres de culture (tableaux `s`, `p`,
`r` des cartes) n'y figurent pas — ce sont des périodes, pas des tâches.

Ce que le texte d'une tâche change à son affichage :

- une entrée de `quotidiennes` dont le mois courant figure dans `mois` → « Chaque jour ».
  C'est la façon explicite, à préférer.
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

## Vérification météo

`.github/workflows/meteo.yml` lance `meteo/verifie.py` toutes les heures (GitHub
retarde ou saute souvent les déclenchements planifiés, parfois de plusieurs heures).
Le script fait le passage du matin au premier lancement à partir de 7 h, heure de
Paris, celui du soir au premier à partir de 17 h, et ignore les autres
(`etat.passages`). Un premier passage tombé le soir tient lieu des deux. Le script lit la prévision
Open-Meteo, `meteo/regles.json` et les trois calendriers, puis écrit `data-meteo.json` :

```
{ version, jour, maj,
  taches:    [ { id, type: gel|levee|arrosage|engrais, titre, detail, alerte? } ],
  reportees: [ { id, src, texte, motif, jusqu_a } ],
  etat:      { arrosage, engrais, une_fois, notifie, passages } }
```

- `taches` vaut pour `jour` seulement ; la page ignore un fichier d'un autre jour et
  signale une vérification en retard. Arrosage et engrais sont décidés au premier
  passage du jour ; les alertes de gel sont recalculées à chaque passage.
- `reportees[].id` est l'empreinte `hache(src + '|' + texte)` de la page d'accueil :
  **reformuler une tâche change son id**, comme pour les cases cochées. La page la
  range alors dans « Reporté par la météo » jusqu'à `jusqu_a`.
- Le script ne voit pas les cases cochées (elles restent sur l'appareil) : un pot
  signalé à arroser est supposé arrosé le jour même, un engrais signalé supposé donné.
- Arrosage : bilan quotidien ET0 × coefficient de soif − pluie (nulle pour un pot
  `abri`), signalé quand il dépasse la réserve du pot (0,4 mm par cm de diamètre,
  25 mm en pleine terre). Jamais par gel (max < 4 °C ou nuit < −3 °C), ni avant 5 mm
  de pluie annoncés pour un pot qui la reçoit. Un pot `abri` est vérifié au moins
  toutes les 3 semaines pendant ses `mois`.
- Notification ntfy (secret `NTFY_TOPIC`) : au plus une le matin, seulement si une
  tâche nouvelle autre qu'une simple levée de report ; le soir, seulement pour un gel
  nouveau. Le détail des reports reste sur le site.
- Le workflow ne commite `data-meteo.json` que s'il a changé.

`soins.html` affiche les règles et l'état de la vérification : rythme d'arrosage estimé
pour le mois, dernier arrosage supposé, prochain engrais, seuils de gel. Ses constantes
(`COEF_SOIF`, `RESERVE_PAR_CM`, `RESERVE_TERRE`, `JOURS_MAX_ABRI`) recopient celles de
`verifie.py` : **les modifier ensemble.**

Essai local : `python3 meteo/verifie.py --essai --force`, ou avec une prévision
enregistrée : `--meteo fichier.json --maintenant 2026-11-23T07:30 --precedent vide.json`.

## Ce qui est encore en suspens

- **Framboisier en place** : type inconnu. La seule canne vivante est sortie en 2026
  et n'a pas fructifié, ce qui plaide contre un remontant. Tant que ce n'est pas
  tranché, aucune taille : une coupe au ras sur un non-remontant supprimerait la
  récolte de juin, et il ne reste qu'une canne. Verdict à la première fructification.
- **Mûrier platane** : beaucoup de mûriers platanes vendus en France sont des clones
  ornementaux stériles. Le calendrier ne promet aucune récolte ; à confirmer sur
  l'étiquette si la question se pose.
- **Fraisiers remontants** : 'Charlotte' abandonnée (rupture PdF). Une dizaine de
  remontants à gros fruits ('Gento', 'Mariguette', 'Cirafine'…) à choisir et commander
  en mars 2027 pour une récolte dès l'été. L'emplacement (bac, jardinières de la
  terrasse ou carré de la courgette) décide aussi de l'alerte « déplacer la courgette ».
- **Appleblossom** : cité dans le semis de février de `data-fleurs.json` sans carte
  correspondante. Soit la variété sort de la commande, soit il lui faut une carte.
- **Figuier 'Ronde de Bordeaux'** : retiré de la commande PdF du 23/11/2026.
  Décision le 13/03/2027 entre un demi-tige de variété nommée chez Botanic et le
  demi-tige PdF (75 €, en liste d'envies). La carte potager porte `a:[3] p:[3,4]`.
- **AquaBloom** : plus utilisé, toutes les références sont retirées des calendriers
  jusqu'à nouvel ordre.
