# Trace

Ein lokaler Arbeitsraum für Zeiterfassung, Tagesberichte und projektbezogene Dokumentation. Arbeitsintervalle und Tagesnotizen speisen die Berichtsvorbereitung; Projektdokumente bilden davon getrenntes, langlebiges Wissen und erscheinen gemeinsam mit verknüpften Arbeitstagen im Netzwerk.

## Lokal starten

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Danach ist die Anwendung unter `http://127.0.0.1:8000` erreichbar. Die Datenbankdatei `timekeeper.db` wird beim ersten Start angelegt.

### Einfacher Start unter Windows

Nach der ersten Einrichtung kannst du einfach `start-app.bat` doppelklicken. Die Anwendung öffnet sich dann automatisch im Browser. Das geöffnete Konsolenfenster muss während der Nutzung geöffnet bleiben; mit `Strg+C` wird der Server beendet.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Konfiguration und Sicherheit

Kopiere `.env.example` in die Umgebung deiner Wahl und setze Variablen vor dem Start. Für eine öffentliche Bereitstellung `AUTH_ENABLED=true` sowie ein eigenes starkes `AUTH_USERNAME` und `AUTH_PASSWORD` setzen. Der Platzhalter `change-me` wird bei aktiviertem Schutz abgelehnt. Formulare sind durch ein Same-Site-CSRF-Token geschützt; zusätzlich setzt die App grundlegende Sicherheitsheader. Öffentlich sollte der Server trotzdem ausschließlich über HTTPS erreichbar sein.

## Docker

```bash
docker build -t arbeitsraum .
docker run -p 8000:8000 -v arbeitsraum-data:/data -e AUTH_ENABLED=true -e AUTH_PASSWORD='ein-starkes-passwort' arbeitsraum
```

## Architekturentscheidungen

- `WorkDay` besitzt Datum und Tätigkeitsnotiz; `TimeEntry` enthält die einzelnen Intervalle.
- Dauerwerte werden aus Intervallen berechnet, nicht zusätzlich gespeichert. Live-Kennzahlen enthalten die laufende Phase; Historie, Bericht und CSV führen nur abgeschlossene Zeit zuverlässig als Dauer.
- Der Server arbeitet standardmäßig in `Europe/Berlin`; Zeiten werden als lokale Tageszeiten gespeichert, passend zur persönlichen Einzelnutzung.
- Die Oberfläche nutzt FastAPI mit Jinja2 und minimales Vanilla-JavaScript für Navigation, Dialoge, Monatswechsel, Live-Timer und Netzwerk.
