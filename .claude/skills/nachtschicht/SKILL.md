---
name: nachtschicht
description: Autonome Nacht-Session für das aktuelle Projekt – Bugs fixen, Tests schreiben, aufräumen, optimieren, dokumentieren – sicher auf eigenem Git-Branch mit NIGHT_REPORT.md am Ende. Nur auf ausdrücklichen Aufruf (/nachtschicht) verwenden.
argument-hint: "[optionaler Fokus, z. B. 'Tests für den Randomizer-Import']"
disable-model-invocation: true
---

# Nacht-Session: Autonome Wartung & Verbesserung

**Fokus dieser Nacht (falls angegeben, hat Vorrang vor allem anderen):** $ARGUMENTS

Du arbeitest diese Nacht allein an diesem Projekt. Niemand beantwortet Rückfragen – triff selbst
vernünftige Entscheidungen, dokumentiere sie und arbeite weiter. Ziel: Morgen früh ist das Projekt
nachweislich besser, und nichts ist kaputt.

## Vorab: Warten, bis alles andere fertig ist
Starte die eigentliche Arbeit erst, wenn keine andere Session mehr aktiv arbeitet.
Gibt es das Tool `mcp__ccd_session_mgmt__list_sessions` hier nicht (z. B. in einer Cloud-Session),
dann überspringe diesen Abschnitt und mach direkt mit Abschnitt 0 weiter.
1. Lade bei Bedarf das Tool per `ToolSearch` (`select:mcp__ccd_session_mgmt__list_sessions`) und
   rufe `mcp__ccd_session_mgmt__list_sessions` auf (die eigene Session ist nicht enthalten).
2. Eine Session gilt als **beschäftigt**, wenn `isRunning: true` ist UND ihre `lastActivityAt`
   weniger als 10 Minuten zurückliegt. Sessions mit `isRunning: false` sind fertig oder warten
   auf meine Antwort. Sessions mit `isRunning: true`, aber über 10 Minuten ohne Aktivität, warten
   vermutlich auf eine Bestätigung von mir. Beide zählen als **nicht beschäftigt**.
3. Ist mindestens eine Session beschäftigt: Notiere kurz, auf welche du wartest. Starte dann per
   Bash `sleep 600` mit `run_in_background: true` und beende den Zug. Wenn der Sleep endet, wirst
   du wieder aufgerufen. Dann geht es weiter bei Schritt 1. Kein Polling im Vordergrund, nichts
   anderes tun.
4. Ist keine Session beschäftigt: Notiere die Uhrzeit des Starts für den Report und mach mit
   Abschnitt 0 weiter.

## 0. Sicherheitsnetz (zuerst, Pflicht)
- Ist das Projekt ein Git-Repo? Wenn nein: `git init`, sinnvolle `.gitignore` anlegen (bin/, obj/,
  node_modules/, dist/, .env usw.) und den Ist-Zustand committen: "Baseline vor Nacht-Session".
- Uncommittete Änderungen vorhanden? Erst als "WIP vor Nacht-Session" committen.
- Neuen Branch anlegen: `night/JJJJ-MM-TT`. Arbeite NUR auf diesem Branch.
- Ausnahme Cloud-Session (Arbeitsordner ist kein lokaler Windows-Pfad): Dort geht die Arbeit ohne
  Push verloren. Pushe deshalb am Ende ausschließlich den Branch `night/...` und öffne dafür
  einen **Draft-PR**. Niemals main pushen und niemals mergen.
- Niemals (außer der Ausnahme oben): pushen, deployen, `--force`, Dateien außerhalb des Projektordners anfassen,
  Secrets/.env ändern oder ausgeben, Datenbanken/Produktivdaten verändern, Pakete auf neue
  Major-Versionen heben, Dateien endgültig löschen (lieber in `_archive/` verschieben).
- Jede abgeschlossene Änderung = eigener kleiner Commit mit klarer Nachricht.
  Build/Tests müssen nach jedem Commit grün sein. Wenn nicht: Fix oder `git revert`.

## 1. Bestandsaufnahme (ca. 10 % der Zeit)
- Lies README, CLAUDE.md und die Projektstruktur. Finde heraus, wie gebaut, gestartet und getestet wird.
- Führe Build und vorhandene Tests aus und notiere den Ausgangszustand (Fehler, Warnungen,
  Testanzahl, Laufzeit).
- Erstelle `NIGHT_REPORT.md` mit einer priorisierten Aufgabenliste für die Phasen unten.

## 2. Stabilität & Bugs (höchste Priorität)
- Build-Fehler und Compiler-/Linter-Warnungen beheben.
- Offensichtliche Bugs suchen: Null-Referenzen, nicht behandelte Exceptions, Off-by-one,
  Race Conditions, Ressourcen-Lecks, falsche async-Nutzung, harte Pfade.
- Jeden gefundenen Bug zuerst mit einem Test reproduzieren und dann beheben.

## 3. Tests
- Fehlt ein Testprojekt, lege eines im Stil des Ökosystems an (xUnit/NUnit für .NET, Vitest/Jest
  für JS usw.).
- Schreibe Tests für die wichtigste Kernlogik zuerst (Datenverarbeitung, Parser, Berechnungen),
  nicht für triviale Getter oder UI-Code.
- Tests müssen deterministisch sein: kein Netzwerk, keine echten Benutzerdateien, keine Zeitabhängigkeit.

## 4. Aufräumen & Ordnen
- Toten Code, ungenutzte Imports/Variablen/Dateien entfernen (bei Dateien: nach `_archive/`).
- Doppelten Code zusammenführen, sofern das das Verhalten nicht ändert.
- Ordnerstruktur nur dann umbauen, wenn sie klar chaotisch ist. Keine reinen Geschmacks-Refactorings.
- Einheitliche Formatierung nach den vorhandenen Projektkonventionen.

## 5. Optimierung
- Nur messbare oder offensichtliche Verbesserungen: unnötige Schleifen/Allokationen, blockierende
  I/O im UI-Thread, wiederholte teure Berechnungen, zu große Bundles.
- Kein Mikro-Tuning ohne Nutzen. Das Verhalten muss identisch bleiben (Tests beweisen das).

## 6. Dokumentation
- README aktualisieren: Was ist das Projekt, wie baut/startet/testet man es.
- Kurze Kommentare nur dort, wo Logik nicht selbsterklärend ist.

## Regeln für Entscheidungen
- Unsicher, ob eine Änderung gewollt ist? → Nicht umsetzen, sondern im Report unter
  "Vorschläge" mit Begründung notieren.
- Features, UI-Design und öffentliche Schnittstellen/Dateiformate bleiben unverändert.
- Steckst du an etwas mehr als ~20 Minuten fest: notieren, zurücksetzen, nächste Aufgabe.
- Lieber 10 saubere, verifizierte Verbesserungen als 50 halbe.
- Keine Rückfragen stellen und nicht auf Antworten warten – die Nacht läuft durch.

## Abschluss: NIGHT_REPORT.md
Am Ende enthält der Report (auf Deutsch):
1. **Zusammenfassung** in 3–5 Sätzen
2. **Vorher/Nachher**: Build-Warnungen, Testanzahl, bestandene Tests, ggf. Performance-Messungen
3. **Erledigt**: Liste der Commits mit jeweils einer Zeile Begründung
4. **Gefundene, nicht behobene Probleme** (mit Datei:Zeile und Schweregrad)
5. **Vorschläge**, die meine Entscheidung brauchen
6. **Wie ich alles prüfe bzw. rückgängig mache**: `git diff main..night/...`, `git checkout main`

Committe den Report als letzten Schritt. Mach nicht auf main weiter und merge nicht.
