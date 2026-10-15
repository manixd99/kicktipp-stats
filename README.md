# Kicktipp-Statistiken: Champions League 2026/27

Interaktive Statistik-Seite für unsere Kicktipp-Runde. Die Daten kommen aus der öffentlichen
[Gesamtübersicht](https://www.kicktipp.de/champions-l-202627/gesamtuebersicht) und werden
automatisch aktualisiert: an CL-Abenden (Di–Do) alle 2 Minuten von 18:40 bis 23:30, sonst jeden Morgen. Die Seite lädt neue Daten selbst nach, ohne Neuladen.

- `index.html` – die Seite (Punkterennen, Platzierung, Rückstand, Kuriositäten, Steckbrief, Trefferbild, Teams, Duell, Heatmap, Tabelle)
- `data.json` – aktuelle Daten inkl. aller Einzeltipps
- `scripts/fetch_kicktipp.py` – holt die Tabelle von kicktipp.de
- `.github/workflows/update.yml` – Automatik

Manuell aktualisieren: Reiter **Actions** → „Kicktipp-Daten aktualisieren“ → **Run workflow**.
