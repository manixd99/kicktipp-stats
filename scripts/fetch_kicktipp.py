"""Holt die Gesamtübersicht einer Kicktipp-Runde und schreibt sie als data.json.

Aufruf:  python scripts/fetch_kicktipp.py [RUNDE] [AUSGABE] [--voll]
Standard: RUNDE=champions-l-202627, AUSGABE=data.json
"""
import json
import re
import sys
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

RUNDE = sys.argv[1] if len(sys.argv) > 1 else "champions-l-202627"
AUSGABE = Path(sys.argv[2] if len(sys.argv) > 2 else "data.json")
URL = f"https://www.kicktipp.de/{RUNDE}/gesamtuebersicht"


def zahl(wert):
    """Zelle -> int oder None (leere Zellen sind noch nicht gespielt)."""
    if wert is None or (isinstance(wert, float) and pd.isna(wert)):
        return None
    if isinstance(wert, (int, float)):
        return int(round(wert))
    text = str(wert).strip().replace(".", "").replace(",", ".")
    if text in ("", "-", "nan"):
        return None
    try:
        return int(round(float(text)))
    except ValueError:
        return None


def parse(html):
    tabellen = pd.read_html(StringIO(html), decimal=",", thousands=".")
    tabelle = next(
        (t for t in tabellen if {"Pos", "Name"} <= {str(c).strip() for c in t.columns}),
        None,
    )
    if tabelle is None:
        raise RuntimeError("Keine Tabelle mit den Spalten 'Pos' und 'Name' gefunden.")

    spalten = [str(c).strip() for c in tabelle.columns]
    tabelle.columns = spalten
    i_name, i_bonus = spalten.index("Name"), spalten.index("B")
    runden_spalten = spalten[i_name + 1 : i_bonus]

    # Doppelte KO-Spalten (pandas macht daraus "Zw" und "Zw.1") -> Zw1, Zw2
    basis = [re.sub(r"\.\d+$", "", s) for s in runden_spalten]
    labels = []
    for s, b in zip(runden_spalten, basis):
        labels.append(f"{b}{basis[: len(labels) + 1].count(b)}" if basis.count(b) > 1 else b)

    spieler = []
    for _, zeile in tabelle.iterrows():
        name = str(zeile["Name"]).strip()
        if not name or name == "nan":
            continue
        spieler.append(
            {
                "name": name,
                "punkte": [zahl(zeile[s]) for s in runden_spalten],
                "bonus": zahl(zeile["B"]) or 0,
                "gesamt": zahl(zeile["G"]) or 0,
            }
        )
    if not spieler:
        raise RuntimeError("Tabelle gefunden, aber keine Spieler darin.")

    gespielt = [i for i in range(len(labels)) if any(p["punkte"][i] is not None for p in spieler)]
    for p in spieler:
        summe = sum(v or 0 for v in p["punkte"]) + p["bonus"]
        if summe != p["gesamt"]:
            print(f"Warnung: {p['name']}: Summe {summe} != Gesamt {p['gesamt']}", file=sys.stderr)
    return {"runden": labels, "gespielt": gespielt, "spieler": spieler}


# ---------------------------------------------------------------- Einzeltipps

TOR = re.compile(r"(\d{1,2})\s*:\s*(\d{1,2})")


def _text(el):
    return re.sub(r"\s+", " ", el.text_content()).strip()


def _tippzelle(td):
    """Zelle der Tippübersicht -> [heim, gast, punkte] oder None.
    Kicktipp schreibt die Punkte als eigenes Element hinter den Tipp (z. B. 1:2 + <sub>3</sub>)."""
    voll = _text(td)
    if not voll or ":" not in voll:
        return None
    punkte = None
    for el in td.iter():
        if el is td or el.tag in ("br",):
            continue
        t = _text(el)
        if re.fullmatch(r"\d{1,2}", t) and ":" not in t:
            punkte = int(t)
    if punkte is None:  # kein eigenes Element: "1:23" = Tipp 1:2, 3 Punkte
        m1 = re.fullmatch(r"(\d):(\d)(\d)?", voll.replace(" ", ""))
        if m1:
            return [int(m1[1]), int(m1[2]), int(m1[3] or 0)]
    rest = voll
    if punkte is not None and rest.endswith(str(punkte)):
        rest = rest[: -len(str(punkte))].strip()
    m = re.fullmatch(r"(\d{1,2})\s*:\s*(\d{1,2})", rest)
    if not m:  # Rückfall: "1:23" = Tipp 1:2, 3 Punkte
        m2 = re.fullmatch(r"(\d):(\d)(\d{1,2})?", voll.replace(" ", ""))
        if not m2:
            return None
        return [int(m2[1]), int(m2[2]), int(m2[3]) if m2[3] else 0]
    return [int(m[1]), int(m[2]), punkte if punkte is not None else 0]


def parse_spieltag(html):
    from lxml import html as lh

    doc = lh.fromstring(html)
    spiele, tipps = [], {}
    for tab in doc.xpath("//table"):
        kopf = [_text(th) for th in tab.xpath(".//thead//th") or tab.xpath(".//tr[1]/th")]
        if "Heim" in kopf and "Gast" in kopf and not spiele:
            ih, ig = kopf.index("Heim"), kopf.index("Gast")
            ie = next((i for i, k in enumerate(kopf) if k.startswith("Ergebnis")), None)
            it = kopf.index("Termin") if "Termin" in kopf else None
            for tr in tab.xpath(".//tbody/tr"):
                tds = tr.xpath("./td")
                if len(tds) <= max(ih, ig):
                    continue
                erg = TOR.search(_text(tds[ie])) if ie is not None and ie < len(tds) else None
                spiele.append({
                    "heim": _text(tds[ih]), "gast": _text(tds[ig]),
                    "termin": _text(tds[it]) if it is not None and it < len(tds) else "",
                    "ergebnis": [int(erg[1]), int(erg[2])] if erg else None,
                })
        elif "Name" in kopf and "P" in kopf:
            i_name, i_p = kopf.index("Name"), kopf.index("P")
            for tr in tab.xpath(".//tbody/tr"):
                tds = tr.xpath("./td")
                if len(tds) < i_p:
                    continue
                name = _text(tds[i_name])
                if name:
                    tipps[name] = [_tippzelle(td) for td in tds[i_name + 1 : i_p]]
    if not spiele:
        raise RuntimeError("Spielplan-Tabelle (Heim/Gast) nicht gefunden.")
    for name, t in tipps.items():
        if len(t) != len(spiele):
            raise RuntimeError(f"{name}: {len(t)} Tipps, aber {len(spiele)} Spiele.")
    return {"spiele": spiele, "tipps": tipps}


def hole(url):
    antwort = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (kicktipp-stats)", "Accept-Language": "de"},
        timeout=30,
    )
    antwort.raise_for_status()
    return antwort.text


def main():
    voll = "--voll" in sys.argv
    html = hole(URL)
    daten = parse(html)
    alt = json.loads(AUSGABE.read_text("utf-8")) if AUSGABE.exists() else {}

    # Einzeltipps: nur Spieltage neu holen, die fehlen, noch offen sind oder der neueste sind
    saison = re.search(r"tippsaisonId=(\d+)", html)
    alte_tage = alt.get("tage") or {}
    tage = {}
    for i in daten["gespielt"]:
        key = str(i)
        vorher = alte_tage.get(key)
        offen = vorher is None or any(s["ergebnis"] is None for s in vorher["spiele"])
        if voll or offen or i == daten["gespielt"][-1] or not saison:
            try:
                q = f"tippsaisonId={saison[1]}&" if saison else ""
                tage[key] = parse_spieltag(hole(f"https://www.kicktipp.de/{RUNDE}/tippuebersicht?wertung=einzelwertung&{q}spieltagIndex={i + 1}"))
            except Exception as e:  # Tipps sind ein Extra: Tabelle trotzdem aktualisieren
                print(f"Warnung: Tipps für Spieltag {i + 1} nicht lesbar: {e}", file=sys.stderr)
                if vorher:
                    tage[key] = vorher
        else:
            tage[key] = vorher
    daten["tage"] = tage

    if {k: alt.get(k) for k in daten} == daten:
        print("Keine Änderung.")
        return
    daten = {
        "runde": RUNDE,
        "quelle": URL,
        "aktualisiert": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **daten,
    }
    AUSGABE.write_text(json.dumps(daten, ensure_ascii=False, separators=(",", ":")), "utf-8")
    print(f"Aktualisiert: {len(daten['spieler'])} Spieler, {len(daten['gespielt'])} Spieltage, Tipps für {len(tage)}.")


if __name__ == "__main__":
    main()
