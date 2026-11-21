"""Veille GTA VI GUIDE : tourne chaque jour sur GitHub Actions, sans Claude.

Lit quelques guides publics, repère les codes de triche et les armes uniques
qui étaient encore inconnus, et les ajoute à gta6-by-mgm/nouveautes.json.
L'app lit ce fichier à chaque ouverture : rien d'autre à faire.
Si un site change sa page ou bloque le robot, le script ne casse rien : il n'ajoute juste rien.
"""
import datetime, html, json, pathlib, re, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
NEWS = ROOT / "nouveautes.json"
TODAY = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1))).date()
MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]

CHEAT_SOURCES = [
    "https://meowdb.com/gta6/cheats",
    "https://gtaside.com/tips/gta6/cheat-codes/",
    "https://www.vice.com/en/article/gta-6-cheat-codes-list/",
    "https://www.gtabase.com/gta-6/gta-6-cheats-ps5-cheat-codes",
]
WEAPON_SOURCES = [
    "https://showgamer.com/en/guides/8035-vse-legendarnoe-oruzhie-v-gta-6-gde-nayti-unikalnye-pushki-i-nozhi",
]

# nom anglais dans les guides -> nom affiché dans l'app (triches dont le code manquait au lancement)
CHEATS_SANS_CODE = {
    "Drunk": "Bourré", "No Fall Damage": "Pas de dégâts de chute", "Parachute": "Parachute",
    "Repair Vehicle": "Réparer le véhicule", "Unlimited Nitrous": "Nitro illimitée",
    "All Explosive Weapons": "Toutes les armes explosives", "Incendiary Ammo": "Balles incendiaires",
    "Exploding Bottles": "Bouteilles explosives", "Explosive Shotgun": "Fusil à pompe explosif",
    "Hauners H-AT": "Hauners H-AT", "Hauners Rhino Tank": "Hauners Rhino Tank",
    "Hauners P-996 Lazer": "Hauners P-996 Lazer", "Nagasaki Sea Sparrow": "Nagasaki Sea Sparrow",
    "Progen Emerus": "Progen Emerus", "Bravado Banshee": "Bravado Banshee",
    "Nagasaki Carbon RS": "Nagasaki Carbon RS", "Vapid Dominator": "'65 Vapid Dominator",
    "Speeder 700 GT": "Speeder 700 GT", "Truffade Thrax": "Truffade Thrax",
    "Western Zombie Bobber": "Western Zombie Bobber", "Maibatsu Sanchez": "Maibatsu Sanchez",
    "Lapwing Mallard": "Lapwing Mallard", "Brimstone Golfer": "Brimstone Golfer",
    "Stanier G2 Taxi": "Vapid Stanier G2 Taxi", "Airboat 09": "Airboat 09", "Tuff BMX": "Tuff BMX",
    "Interstate Ambulance": "Interstate Ambulance", "Inflatable Flamingo": "Flamant gonflable",
    "Move Time Forward": "Avancer l'heure", "Pause Time of Day": "Figer l'heure",
    "Golden Hour": "Golden Hour", "Powdered Sugar": "Powdered Sugar", "Pinhole": "Pinhole",
    "Neon Jungle": "Neon Jungle", "Yesteryear": "Yesteryear", "Videotape": "Videotape",
    "Dark Mirror": "Dark Mirror", "Migraine": "Migraine", "Bubblegum": "Bubblegum",
    "Fast Forward": "Fast Forward", "Fisheye": "Fisheye", "Pixel Art": "Pixel Art", "Hellscape": "Hellscape",
}

# armes encore introuvables au lancement -> type affiché dans l'app
ARMES_INCONNUES = {
    "Raul's CQB 556": "Fusil d'assaut", "Raul's Heist 556": "Fusil d'assaut", "Pete's KZ-59": "Fusil d'assaut",
    "Bae-Lux's W-10": "SMG", "Roxy's W-10": "SMG", "Tyrone's W-10": "SMG", "Furry DW-9": "SMG",
    "Midlife Crisis VF5": "SMG", "Francisco's LMG 6": "Mitrailleuse", "CPD Moreland 850": "Fusil à pompe",
    "Copperheads W-14": "Fusil tactique", "Mister Mangrove Laird 350": "Sniper", "Gun Nut SMS-01": "Sniper",
    "Island Poacher FF-50": "Sniper", "Low Point Nipper .38": "Pistolet", "Caminos Signature K17": "Pistolet",
    "DWNPLY's K17": "Pistolet", "EJ's K17": "Pistolet", "Dumpster K17 MCD": "Pistolet",
    "Brainwasher 1992": "Pistolet", "Brian's 1992": "Pistolet", "Monty's 1992": "Pistolet",
    "Raul's 1992": "Pistolet", "Russo's 1992": "Pistolet", "Convict Kalinga .50": "Pistolet",
    "Gil's Kalinga .50": "Pistolet",
}
PAS_TROUVE = re.compile(r"^\W*(not (yet )?discovered|unknown|location not|tbc|tba|coming soon|n/?a)\b", re.I)

ARROWS = {"↑": "↑", "↓": "↓", "←": "←", "→": "→", "⬆": "↑", "⬇": "↓", "⬅": "←", "➡": "→"}
WORDS = {"up": "↑", "down": "↓", "left": "←", "right": "→"}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (GTA VI GUIDE veille; +https://mathysmgm.github.io/gta6-by-mgm/)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8", "replace")
    except Exception as e:
        print(f"  ! {url} : {e}")
        return ""
    raw = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?i)</(td|th)>", " | ", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</(p|li|tr|div|h\d|table|ul|ol)>", "\n", raw)
    txt = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    return re.sub(r"[ \t ]+", " ", txt)


def code_after(text, name):
    """Cherche un code à la croix juste après le nom de la triche."""
    for m in re.finditer(re.escape(name), text, re.I):
        chunk = text[m.end(): m.end() + 260].split("\n", 1)[0]  # même ligne / même rangée seulement
        arrows = re.search(r"((?:[↑↓←→⬆⬇⬅➡]\s*[,·\-]?\s*){4,})", chunk)
        if arrows:
            return "".join(ARROWS[c] for c in arrows.group(1) if c in ARROWS)
        words = re.search(r"\b((?:(?:up|down|left|right)\s*[,\-]?\s*){4,})", chunk, re.I)
        if words:
            return "".join(WORDS[w.lower()] for w in re.findall(r"up|down|left|right", words.group(1), re.I))
    return ""


def main():
    data = json.loads(NEWS.read_text("utf-8"))
    for k in ("fiches", "triches", "digicodes", "trouvees"):
        data.setdefault(k, [])
    deja_triches = {t["n"] for t in data["triches"] if t.get("code")}
    deja_armes = set(data["trouvees"])
    jour = TODAY.isoformat()
    ajouts = []

    # 1) codes de triche
    textes = [fetch(u) for u in CHEAT_SOURCES]
    for en, fr in CHEATS_SANS_CODE.items():
        if fr in deja_triches:
            continue
        votes = {}
        for t in textes:
            c = code_after(t, en) if t else ""
            if 4 <= len(c) <= 14:
                votes[c] = votes.get(c, 0) + 1
        if votes:
            code, n = max(votes.items(), key=lambda kv: kv[1])
            # une seule source suffit si aucune autre ne contredit ; sinon il faut la majorité
            if n >= 1 and (len(votes) == 1 or n >= 2):
                data["triches"].append({"n": fr, "code": code, "a": jour})
                ajouts.append(f"triche {fr} : {code}")

    # 2) armes uniques trouvées
    for url in WEAPON_SOURCES:
        t = fetch(url)
        if not t:
            continue
        for nom, typ in ARMES_INCONNUES.items():
            if nom in deja_armes:
                continue
            m = re.search(re.escape(nom) + r"\s*[:\-–|]\s*([^\n]{6,220})", t)
            if not m:
                continue
            lieu = m.group(1).strip(" .|-")
            if PAS_TROUVE.search(lieu):
                continue
            data["fiches"].append({
                "c": "armes", "t": typ, "n": nom, "z": lieu,
                "h": "Emplacement trouvé par la communauté (détail en anglais : " + lieu + "). Regarde la vidéo pour le chemin exact.",
                "tg": [["Nouveau", "new"]], "a": jour,
            })
            data["trouvees"].append(nom)
            deja_armes.add(nom)
            ajouts.append(f"arme {nom} : {lieu}")

    if ajouts:
        data["maj"] = f"{TODAY.day} {MOIS[TODAY.month - 1]} {TODAY.year}"
        NEWS.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
        print("Ajouts :\n- " + "\n- ".join(ajouts))
    else:
        print("Rien de neuf aujourd'hui.")


if __name__ == "__main__":
    sys.exit(main())
