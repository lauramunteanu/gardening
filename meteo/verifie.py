#!/usr/bin/env python3
"""Vérification météo du jardin, lancée deux fois par jour par GitHub Actions.

Lit la prévision Open-Meteo pour le jardin, les règles de meteo/regles.json et les
trois calendriers, puis écrit data-meteo.json :
  - taches     : ce que la météo demande aujourd'hui (arrosage, engrais, gel, tâche
                 de nouveau faisable) ;
  - reportees  : tâches du mois que la météo repousse (sol gelé, pluie, gel…) ;
  - etat       : la mémoire du script (dernier arrosage et dernier engrais supposés,
                 rappels déjà envoyés).

Une notification ntfy part au plus une fois par jour, le matin, s'il y a quelque chose
à faire. Le soir, rien ne part, sauf un gel que la prévision du matin n'annonçait pas.

Sans dépendance : bibliothèque standard de Python 3.9+.
Essai local : python3 meteo/verifie.py --essai --force
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

RACINE = Path(__file__).resolve().parent.parent
REGLES = RACINE / 'meteo' / 'regles.json'
SORTIE = RACINE / 'data-meteo.json'
CALENDRIERS = {'potager': 'data-potager.json', 'fleurs': 'data-fleurs.json', 'arbustes': 'data-arbustes.json'}

# Eau perdue par jour, en mm sur la surface du pot, = ET0 × coefficient. Le coefficient
# tient compte du feuillage qui déborde du pot : une tomate boit bien plus que la
# surface de son pot ne le laisse croire.
COEF_SOIF = {'faible': 0.6, 'moyenne': 1.2, 'forte': 2.0}
RESERVE_PAR_CM = 0.4      # réserve utile d'un pot, mm par cm de diamètre (35 cm → 14 mm)
RESERVE_TERRE = 25.0      # pleine terre
JOURS_MAX_ABRI = 21       # un pot sous l'avancée est vérifié au moins toutes les 3 semaines
FENETRE = 30              # on ne remonte pas plus loin dans le passé

MOIS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']
JOURS = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']


# ---------------------------------------------------------------- outils

def degres(t):
    """−4 °C avec un vrai signe moins, arrondi au degré."""
    n = round(t)
    return f"{'−' if n < 0 else ''}{abs(n)} °C"


def date_courte(d):
    return f"{d.day} {MOIS[d.month - 1]}"


def jour_semaine(d, aujourdhui):
    if d == aujourdhui + timedelta(days=1):
        return 'demain'
    return f"{JOURS[d.weekday()]} {d.day}"


def hache(s):
    """Même empreinte que hache() dans index.html, pour retrouver les tâches du site."""
    h = 5381
    for c in s:
        h = (h * 33 + ord(c)) & 0xFFFFFFFF
    chiffres = '0123456789abcdefghijklmnopqrstuvwxyz'
    out = ''
    while True:
        h, r = divmod(h, 36)
        out = chiffres[r] + out
        if h == 0:
            return out


def sans_balises(t):
    return re.sub(r'<[^>]+>', '', t)


def dans_fenetre(d, du, au):
    """du / au au format MM-JJ ; une fenêtre peut passer par le 1er janvier."""
    md = d.strftime('%m-%d')
    return du <= md <= au if du <= au else (md >= du or md <= au)


def debut_fenetre(d, du, au):
    """Premier jour de l'occurrence de la fenêtre qui contient d."""
    m, j = map(int, du.split('-'))
    debut = date(d.year, m, j)
    return debut if debut <= d else date(d.year - 1, m, j)


def saison(d):
    a = d.year if d.month >= 9 else d.year - 1
    return f"{a}-{str(a + 1)[2:]}"


# ---------------------------------------------------------------- météo

class Meteo:
    def __init__(self, brut):
        dj = brut['daily']
        self.jours = {}
        for i, t in enumerate(dj['time']):
            v = lambda k: (dj.get(k) or [None] * len(dj['time']))[i]
            self.jours[date.fromisoformat(t)] = {
                'tmax': v('temperature_2m_max'), 'tmin': v('temperature_2m_min'),
                'pluie': v('precipitation_sum') or 0.0, 'neige': v('snowfall_sum') or 0.0,
                'et0': v('et0_fao_evapotranspiration') or 0.0,
            }
        hj = brut['hourly']
        self.heures = []
        for i, t in enumerate(hj['time']):
            self.heures.append((datetime.fromisoformat(t), hj['temperature_2m'][i],
                                (hj.get('soil_temperature_6cm') or [None] * len(hj['time']))[i]))

    def jour(self, d):
        return self.jours.get(d)

    def _min(self, debut, fin, champ=1):
        vals = [h[champ] for h in self.heures if debut <= h[0] < fin and h[champ] is not None]
        return min(vals) if vals else None

    def nuit(self, d):
        """Minimum de la nuit qui suit le jour d : de 18 h à 9 h le lendemain."""
        debut = datetime(d.year, d.month, d.day, 18)
        return self._min(debut, debut + timedelta(hours=15))

    def matin(self, d):
        """Minimum de 0 h à 10 h : le gel encore dans le bois au moment de tailler."""
        debut = datetime(d.year, d.month, d.day)
        return self._min(debut, debut + timedelta(hours=10))

    def sol(self, d):
        """Sol à 6 cm, minimum pendant les heures où l'on jardine."""
        debut = datetime(d.year, d.month, d.day, 8)
        return self._min(debut, debut + timedelta(hours=10), champ=2)

    def dernier_jour(self):
        return max(self.jours)


def telecharge_meteo(lieu):
    q = {
        'latitude': lieu['latitude'], 'longitude': lieu['longitude'], 'elevation': lieu['altitude'],
        'timezone': lieu['fuseau'], 'past_days': FENETRE + 1, 'forecast_days': 7,
        'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,snowfall_sum,et0_fao_evapotranspiration',
        'hourly': 'temperature_2m,soil_temperature_6cm',
    }
    url = 'https://api.open-meteo.com/v1/forecast?' + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers={'User-Agent': 'jardin-lauramunteanu (GitHub Actions)'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


# ---------------------------------------------------------------- calendriers

def taches_du_mois(m):
    """Les tâches datées du mois, avec le même identifiant que la page d'accueil."""
    l = []

    def ajoute(src, texte):
        texte = sans_balises(texte)
        l.append({'id': hache(f"{src}|{texte}"), 'src': src, 'texte': texte})

    def lit(nom):
        try:
            return json.loads((RACINE / CALENDRIERS[nom]).read_text(encoding='utf-8'))
        except (OSError, ValueError) as e:
            print(f"! {CALENDRIERS[nom]} illisible : {e}", file=sys.stderr)
            return None

    pot, fle, arb = lit('potager'), lit('fleurs'), lit('arbustes')
    if pot:
        for t in pot.get('speciales', []):
            if t.get('m') == m:
                ajoute('potager', t['nom'] + (' — ' + t['extra'] if t.get('extra') else ''))
    if fle:
        for _, t in fle.get('taches', {}).get(str(m), []):
            ajoute('fleurs', t)
    if arb:
        for p in arb.get('plantes', []):
            for t in (p.get('taches') or {}).get(str(m), []):
                ajoute('arbustes', p['nom'] + (' — ' + t if t else ''))
        for t in arb.get('ponctuelles', []):
            if t.get('m') == m:
                ajoute('arbustes', t['nom'] + (' — ' + t['extra'] if t.get('extra') else ''))
    quotidien = re.compile(r'arros[^.]*(chaque jour|quotidien)|(chaque jour|quotidien)[^.]*arros', re.I)
    return [t for t in l if not quotidien.search(t['texte'])]


# ---------------------------------------------------------------- règles

class Verification:
    def __init__(self, regles, meteo, maintenant, precedent):
        self.r = regles
        self.m = meteo
        self.auj = maintenant.date()
        self.maintenant = maintenant
        self.prec = precedent or {}
        etat = self.prec.get('etat') or {}
        self.etat = {
            'arrosage': dict(etat.get('arrosage') or {}),
            'engrais': dict(etat.get('engrais') or {}),
            'une_fois': dict(etat.get('une_fois') or {}),
            'notifie': dict(etat.get('notifie') or {}),
            'passages': dict(etat.get('passages') or {}),
        }
        self.premier_passage = self.prec.get('jour') != self.auj.isoformat()

    # ---- arrosage
    def arrosage(self):
        taches = []
        aj = self.m.jour(self.auj)
        demain = self.m.jour(self.auj + timedelta(days=1)) or {'pluie': 0}
        nuit = self.m.nuit(self.auj)
        gel = aj['tmax'] is not None and aj['tmax'] < 4 or (nuit is not None and nuit < -3)
        for g in self.r['arrosage']:
            gid = g['id']
            actif = self.auj.month in g['mois'] and (not g.get('depuis') or self.auj >= date.fromisoformat(g['depuis']))
            ref = self.etat['arrosage'].get(gid)
            if not actif or not ref:
                # hors saison, ou première vérification : on part d'un pot arrosé aujourd'hui
                self.etat['arrosage'][gid] = self.auj.isoformat()
                continue
            ref = date.fromisoformat(ref)
            abrite = g['abri'] == 'abri'
            reserve = RESERVE_TERRE if g.get('pot_cm') is None else g['pot_cm'] * RESERVE_PAR_CM
            coef = COEF_SOIF[g['soif']]
            deficit, d = 0.0, max(ref + timedelta(days=1), self.auj - timedelta(days=FENETRE))
            while d <= self.auj:
                j = self.m.jour(d)
                if j:
                    pluie = 0.0 if abrite else j['pluie']
                    deficit = max(0.0, deficit + j['et0'] * coef - pluie)
                d += timedelta(days=1)
            if deficit < reserve:
                # la pluie a tout remis à zéro : le pot repart plein
                if deficit == 0.0 and not abrite:
                    self.etat['arrosage'][gid] = self.auj.isoformat()
                if not (abrite and (self.auj - ref).days >= JOURS_MAX_ABRI):
                    continue
            if gel:
                continue                      # jamais sur un pot gelé : on attend le redoux
            if not abrite and aj['pluie'] + demain['pluie'] >= 5:
                continue                      # la pluie s'en charge
            if abrite:
                titre = 'Vérifier l\'arrosage'
                detail = f"{g['nom']} : sous l'avancée, pas d'arrosage supposé depuis le {date_courte(ref)} : arroser si sec à 3–4 cm."
            elif g['abri'] == 'terre':
                titre = 'Arroser au pied'
                detail = f"{g['nom']} : ≈ {round(deficit)} mm évaporés sans pluie utile. Arrosage copieux plutôt que fréquent."
            else:
                titre = 'Arroser'
                detail = f"{g['nom']} : ≈ {round(deficit)} mm évaporés depuis la dernière pluie utile."
            taches.append({'id': f'arrosage:{gid}', 'type': 'arrosage', 'titre': titre, 'detail': detail})
            self.etat['arrosage'][gid] = self.auj.isoformat()   # supposé fait aujourd'hui
        return taches

    # ---- engrais
    def engrais(self):
        taches = []
        prochains = [self.m.jour(self.auj + timedelta(days=i)) for i in range(3)]
        moyenne = [(j['tmax'] + j['tmin']) / 2 for j in prochains if j and j['tmax'] is not None]
        nuits = [n for n in (self.m.nuit(self.auj), self.m.nuit(self.auj + timedelta(days=1))) if n is not None]
        trop_froid = (moyenne and sum(moyenne) / len(moyenne) < 8) or (nuits and min(nuits) < 0)
        for e in self.r['engrais']:
            if not dans_fenetre(self.auj, e['du'], e['au']):
                continue
            if e.get('exterieur', True) and trop_froid:
                continue                      # racines au repos : l'engrais attendra
            dernier = self.etat['engrais'].get(e['id'])
            debut = debut_fenetre(self.auj, e['du'], e['au'])
            if dernier:
                dernier = date.fromisoformat(dernier)
                if dernier >= debut and (self.auj - dernier).days < e['tous_les_jours']:
                    continue
            taches.append({'id': f"engrais:{e['id']}", 'type': 'engrais', 'titre': 'Engrais',
                           'detail': f"{e['nom']} : {e['quoi']}."})
            self.etat['engrais'][e['id']] = self.auj.isoformat()
        return taches

    # ---- gel
    def gel(self):
        taches = []
        nuit = self.m.nuit(self.auj)
        if nuit is None:
            return taches
        s = saison(self.auj)
        for p in self.r['protections']:
            if not dans_fenetre(self.auj, p['du'], p['au']) or nuit > p['seuil']:
                continue
            if p.get('une_fois'):
                if self.etat['une_fois'].get(p['id']) == s:
                    continue
                self.etat['une_fois'][p['id']] = s
            titre = f"⚠ Gel ce soir ({degres(nuit)})" if nuit <= 0 else f"Nuit froide ({degres(nuit)})"
            taches.append({'id': f"gel:{p['id']}", 'type': 'gel', 'alerte': True, 'titre': titre, 'detail': p['quoi'] + '.'})
        return taches

    # ---- reports
    def _empeche(self, genre, d):
        """Pourquoi la tâche ne peut pas se faire le jour d (None si elle le peut)."""
        j = self.m.jour(d)
        if not j or j['tmax'] is None:
            return 'prévision indisponible'
        R = self.r['reports']
        if genre in ('plantation', 'plantation_frileux'):
            sol = self.m.sol(d)
            if sol is not None and sol <= 0:
                return 'sol gelé'
            if j['neige'] >= 1:
                return 'neige'
            if j['tmax'] < 2:
                return f"journée à {degres(j['tmax'])} au plus"
            if j['pluie'] >= 15:
                return f"forte pluie, {round(j['pluie'])} mm"
            if genre == 'plantation_frileux':
                fr = R['plantation_frileux']
                nuits = [self.m.nuit(d + timedelta(days=i)) for i in range(fr['nuits'])]
                if any(n is None for n in nuits):
                    return 'nuits suivantes pas encore prévues'
                if min(nuits) < fr['nuit_min']:
                    return f"nuits à {degres(min(nuits))} dans les {fr['nuits']} jours"
            return None
        if genre == 'taille':
            matin = self.m.matin(d)
            if j['tmax'] < 0:
                return 'gel toute la journée'
            if matin is not None and matin < -3:
                return f"bois gelé, {degres(matin)} le matin"
            return None
        if genre == 'traitement':
            if j['pluie'] >= 1:
                return f"pluie, {round(j['pluie'])} mm"
            if j['tmax'] < 5:
                return f"journée à {degres(j['tmax'])} au plus"
            return None
        return None

    def _genre(self, texte):
        R = self.r['reports']
        texte = texte.replace('(à planter)', '')   # nom de plante, pas une consigne
        trouve = lambda motif: re.search(motif, texte, re.I)
        if trouve(R['plantation']['motif']) and not trouve(R['plantation']['sauf']):
            fr = R['plantation_frileux']
            if self.auj.month in fr['mois'] and trouve(fr['motif']):
                return 'plantation_frileux'
            return 'plantation'
        if trouve(R['taille']['motif']) and not trouve(R['taille']['sauf']):
            return 'taille'
        if trouve(R['traitement']['motif']):
            return 'traitement'
        return None

    def reports(self):
        reportees, levees = [], []
        avant = {t['id'] for t in (self.prec.get('reportees') or [])} if self.premier_passage else set()
        for t in taches_du_mois(self.auj.month):
            genre = self._genre(t['texte'])
            if not genre:
                continue
            motif = self._empeche(genre, self.auj)
            if motif is None:
                if t['id'] in avant:
                    levees.append({'id': f"levee:{t['id']}", 'type': 'levee', 'titre': 'De nouveau faisable',
                                   'detail': t['texte']})
                continue
            jusqu_a, d = None, self.auj + timedelta(days=1)
            while d <= self.m.dernier_jour():
                if self._empeche(genre, d) is None:
                    jusqu_a = d.isoformat()
                    break
                d += timedelta(days=1)
            reportees.append({'id': t['id'], 'src': t['src'], 'texte': t['texte'], 'motif': motif, 'jusqu_a': jusqu_a})
        return reportees, levees

    # ---- ensemble
    def lance(self):
        prec_taches = [] if self.premier_passage else (self.prec.get('taches') or [])
        reportees, levees = self.reports()
        if self.premier_passage:
            taches = levees + self.arrosage() + self.engrais()
        else:
            # arrosage et engrais sont décidés au premier passage du jour et n'en bougent plus
            taches = [t for t in prec_taches if t['type'] != 'gel']
            # une tâche annoncée faisable le matin mais que la prévision du soir repousse
            repoussees = {f"levee:{r['id']}" for r in reportees}
            taches = [t for t in taches if t['id'] not in repoussees]
        gel_avant = {t['id']: t for t in prec_taches if t['type'] == 'gel'}
        for t in self.gel():
            gel_avant[t['id']] = t                # une alerte annoncée reste dans la liste du jour
        ordre = {'gel': 0, 'levee': 1, 'arrosage': 2, 'engrais': 3}
        taches = sorted(list(gel_avant.values()) + taches, key=lambda t: ordre[t['type']])
        return {
            'version': 1,
            'jour': self.auj.isoformat(),
            'taches': taches,
            'reportees': reportees,
            'etat': self.etat,
        }


# ---------------------------------------------------------------- notification

def message(resultat, nouvelles, aujourdhui):
    """Le détail des reports et des tâches de nouveau faisables reste sur le site, où les
    tâches déjà cochées sont rangées : la notification n'en donne que le compte."""
    icone = {'arrosage': '💧', 'engrais': '🌱'}
    lignes = []
    gels = [t for t in nouvelles if t['type'] == 'gel']
    if gels:
        lignes.append(f"❄ {gels[0]['titre'].replace('⚠ ', '')} :")
        lignes += [f"  · {t['detail']}" for t in gels]
    lignes += [f"{icone[t['type']]} {t['titre']} : {t['detail']}" for t in nouvelles if t['type'] in icone]
    levees = [t for t in nouvelles if t['type'] == 'levee']
    if levees:
        lignes.append(f"✔ {len(levees)} tâche{'s' if len(levees) > 1 else ''} reportée{'s' if len(levees) > 1 else ''} "
                      f"de nouveau faisable{'s' if len(levees) > 1 else ''} (voir le site)")
    rep = resultat['reportees']
    if rep:
        motifs = sorted({r['motif'].split(',')[0] for r in rep})
        lignes.append(f"↷ {len(rep)} tâche{'s' if len(rep) > 1 else ''} du mois reportée{'s' if len(rep) > 1 else ''} "
                      f"({', '.join(motifs)}), voir le site")
    return '\n'.join(lignes)


def envoie(titre, corps, priorite, site):
    sujet = os.environ.get('NTFY_TOPIC', '').strip()
    if not sujet:
        print('! NTFY_TOPIC absent : notification non envoyée', file=sys.stderr)
        return False
    serveur = os.environ.get('NTFY_SERVER', 'https://ntfy.sh').rstrip('/')
    charge = {'topic': sujet, 'title': titre, 'message': corps, 'priority': priorite,
              'tags': ['seedling'], 'click': site}
    req = urllib.request.Request(serveur, data=json.dumps(charge).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=30) as r:
        return 200 <= r.status < 300


# ---------------------------------------------------------------- principal

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--essai', action='store_true', help="n'écrit rien et n'envoie rien, affiche le résultat")
    ap.add_argument('--force', action='store_true', help='ignore les créneaux horaires')
    ap.add_argument('--meteo', help='fichier de réponse Open-Meteo, au lieu du téléchargement')
    ap.add_argument('--maintenant', help='date et heure locales simulées, AAAA-MM-JJTHH:MM')
    ap.add_argument('--precedent', help='data-meteo.json de départ (par défaut celui du dépôt)')
    ap.add_argument('--sortie', help='où écrire (par défaut data-meteo.json)')
    a = ap.parse_args()

    regles = json.loads(REGLES.read_text(encoding='utf-8'))
    lieu = regles['lieu']
    tz = ZoneInfo(lieu['fuseau'])
    maintenant = datetime.fromisoformat(a.maintenant) if a.maintenant else datetime.now(tz).replace(tzinfo=None)

    # GitHub lance le workflow toutes les heures, mais retarde ou saute souvent les
    # déclenchements planifiés. Le script ne dépend donc pas de l'heure exacte : il fait
    # le passage du matin au premier lancement à partir de 7 h, celui du soir au premier
    # lancement à partir de 17 h, et laisse filer les autres sans rien télécharger.
    chemin_prec = Path(a.precedent) if a.precedent else SORTIE
    try:
        precedent = json.loads(chemin_prec.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        precedent = {}
    h = maintenant.hour
    creneau = 'matin' if h < 17 else 'soir'
    faits = (precedent.get('etat') or {}).get('passages') or {}
    faits = set(faits.get('faits', [])) if faits.get('jour') == maintenant.date().isoformat() else set()
    if not a.force:
        if h < 7:
            print(f"Trop tôt ({maintenant:%H:%M} à Paris) : rien à faire.")
            return
        if creneau in faits or (creneau == 'matin' and 'soir' in faits):
            print(f"Passage du {creneau} déjà fait aujourd'hui ({maintenant:%H:%M} à Paris).")
            return

    brut = json.loads(Path(a.meteo).read_text()) if a.meteo else telecharge_meteo(lieu)
    meteo = Meteo(brut)
    if maintenant.date() not in meteo.jours:
        sys.exit(f"La prévision ne couvre pas le {maintenant.date()}.")

    v = Verification(regles, meteo, maintenant, precedent)
    res = v.lance()
    # un premier passage tardif (le soir) tient lieu des deux
    res['etat']['passages'] = {'jour': maintenant.date().isoformat(),
                               'faits': sorted(faits | {creneau} | ({'matin'} if v.premier_passage else set()))}

    # ---- notification : au plus une par jour, sauf un gel nouveau le soir
    aujourd = maintenant.date()
    notifie = res['etat']['notifie']
    deja = set(notifie.get('ids', [])) if notifie.get('jour') == aujourd.isoformat() else set()
    nouvelles = [t for t in res['taches'] if t['id'] not in deja]
    if creneau == 'matin' or v.premier_passage:
        # une tâche de nouveau faisable ne justifie pas à elle seule une notification :
        # elle est peut-être déjà faite et cochée sur le site
        a_envoyer = any(t['type'] != 'levee' for t in nouvelles)
    else:
        a_envoyer = any(t['type'] == 'gel' for t in nouvelles)

    if a_envoyer:
        gel = any(t['type'] == 'gel' for t in nouvelles)
        titre = ("Jardin · gel ce soir" if creneau == 'soir' and gel else
                 f"Jardin · {JOURS[aujourd.weekday()]} {date_courte(aujourd)}")
        corps = message(res, nouvelles, aujourd)
        print(f"--- notification ---\n{titre}\n{corps}\n---")
        envoye = False
        if not a.essai:
            try:
                envoye = envoie(titre, corps, 4 if gel else 3, lieu['site'])
            except OSError as e:
                print(f"! envoi ntfy impossible : {e}", file=sys.stderr)
        if envoye:
            res['etat']['notifie'] = {'jour': aujourd.isoformat(), 'ids': sorted(deja | {t['id'] for t in nouvelles})}
    else:
        print('Rien de nouveau à signaler : pas de notification.')

    # ---- écriture, seulement si quelque chose a changé
    comparable = lambda d: {k: v for k, v in d.items() if k != 'maj'}
    if comparable(res) == comparable(precedent):
        print('data-meteo.json inchangé.')
        return
    res['maj'] = maintenant.strftime('%Y-%m-%dT%H:%M')
    texte = json.dumps(res, ensure_ascii=False, indent=1) + '\n'
    if a.essai:
        print(texte)
    else:
        Path(a.sortie or SORTIE).write_text(texte, encoding='utf-8')
        print('data-meteo.json mis à jour.')


if __name__ == '__main__':
    main()
