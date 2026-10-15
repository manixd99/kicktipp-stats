"""Holt die Gesamtübersicht einer Kicktipp-Runde und schreibt sie als data.json.

Aufruf:  python scripts/fetch_kicktipp.py [RUNDE] [AUSGABE]
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


def main():
    antwort = requests.get(
        URL,
        headers={"User-Agent": "Mozilla/5.0 (kicktipp-stats; einmal pro Lauf)", "Accept-Language": "de"},
        timeout=30,
    )
    antwort.raise_for_status()
    daten = parse(antwort.text)

    alt = json.loads(AUSGABE.read_text("utf-8")) if AUSGABE.exists() else {}
    if {k: alt.get(k) for k in daten} == daten:
        print("Keine Änderung.")
        return
    daten = {
        "runde": RUNDE,
        "quelle": URL,
        "aktualisiert": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **daten,
    }
    AUSGABE.write_text(json.dumps(daten, ensure_ascii=False, indent=1), "utf-8")
    print(f"Aktualisiert: {len(daten['spieler'])} Spieler, {len(daten['gespielt'])} Spieltage.")


if __name__ == "__main__":
    main()
