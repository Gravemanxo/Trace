# Designsystem „Trace"

## Leitidee

Trace ist eine ruhige, dichte Desktop-Arbeitsoberfläche – kein buntes Dashboard. Die Referenz wird als System aus dunkler Werkzeugleiste, heller kontextueller Navigation und klarer Arbeitsfläche übersetzt. Halbtransparente Materialien, Lichtkanten und Hintergrundunschärfe erzeugen eine kontrollierte Liquid-Glass-Anmutung. Hierarchie entsteht weiterhin über Kontrast, Typografie und Abstände. Das Logo visualisiert eine fortlaufende Spur mit drei verbundenen Knoten für Zeit, Projekte und Wissen.

## Informationsarchitektur

1. **Dunkle Rail:** wechselt zwischen Arbeitszeit, Dokumentation und Auswertung. Sie wiederholt keine Unterseiten.
2. **Kontextleiste:** zeigt nur die Unterseiten des aktiven Bereichs.
3. **Arbeitsfläche:** enthält Seitentitel, Hauptaktion und Arbeitsinhalt.

- Arbeitszeit: Dashboard, Zeiten
- Dokumentation: Bericht, Projekte, Netzwerk
- Auswertung: Statistik, CSV-Export

Mobil wird die Rail ausgeblendet und die Kontextleiste über einen beschrifteten Menüschalter als Drawer geöffnet.

## Farben und Oberflächen

Die Oberfläche ist monochrom und neutral; es gibt kein blaues Branding.

- `--bg: #e9e9e6` – App-Hintergrund
- `--surface: #f8f8f6` – Standardfläche
- `--surface-strong: #ffffff` – Eingaben und hervorgehobene Innenflächen
- `--surface-muted: #efefec` – Navigation und Sekundärflächen
- `--ink: #181817` – Primärtext und Hauptaktionen
- `--ink-soft: #62625f` – Metadaten und Hilfstext
- `--line: #d7d7d2` – Standardkontur
- `--rail: #20201f` – Bereichsnavigation
- `--success: #39735a` – ausschließlich Status
- `--danger: #9a332c` – ausschließlich Fehler/destruktive Aktionen

Subtile neutrale Verläufe simulieren Materialtiefe. Neonfarben und farbige Glasflächen bleiben ausgeschlossen. Hauptaktionen sind dunkel auf hell.

## Typografie und Raster

**Satoshi** ist die primäre UI-Schrift und wird in Regular 400, Medium 500 und Bold 700 lokal ausgeliefert. Ihre geometrischen, leicht weichen Formen übernehmen die Typografiewirkung der Referenz. Seitentitel stehen in Bold, Navigation und Aktionen in Medium. Zahlen und Zeiten verwenden tabellarische Ziffern; Editoren bleiben Monospace. Das Grundraster nutzt 4, 8, 12, 16, 24, 32 und 48 Pixel. Die Arbeitsfläche ist auf 1180 Pixel begrenzt.

## Konturen, Radien und Schatten

- kleine Elemente: 8 Pixel Radius
- Navigation und Formgruppen: 12 Pixel
- große Panels und Dialoge: 18 Pixel
- Pillenformen nur für Zähler und Status
- Glasflächen verwenden halbtransparente Hintergründe, `backdrop-filter`, eine helle obere Innenkante und eine sichtbare Außenkontur
- Konturen bleiben sichtbar; Schatten weich und räumlich
- stärkere Schatten nur für schwebende Navigation, Dialog und dunkles Timerpanel

## Interaktion und Barrierefreiheit

- Hover verändert Kontur, Hintergrund oder Position nur leicht.
- Fokus ist immer sichtbar; `prefers-reduced-motion` wird respektiert.
- Buttons haben mindestens 42 Pixel Höhe, Icon-Buttons 40 × 40 Pixel.
- Primäraktionen verwenden Verb + Objekt.
- Destruktive Aktionen benötigen Bestätigung.
- Formfehler stehen im Arbeitskontext und verwenden `role="alert"`.
- Jede Seite besitzt genau eine `h1`; Tabellen bleiben horizontal scrollbar.

## Icons

Icons kommen ausschließlich aus `app/templates/macros/icons.html`. Es sind einfarbige SVG-Linienicons mit `currentColor`. Emojis und Unicode-Symbole sind nicht zulässig. Reine Icon-Buttons benötigen immer einen zugänglichen Namen.

## Seitenmuster

- **Dashboard:** dominantes Status-/Timerpanel, kompakte Kennzahlenleiste, sekundäre Arbeitskarten.
- **Zeiten:** sofortige Monatsnavigation, GitHub-artiger Kalender, semantische Tabelle.
- **Tag:** editierbare Arbeitsphasen; Tagesnotiz und Projektzuordnung getrennt.
- **Projekte:** Ressourcenliste; neue Objekte in modalen Dialogen.
- **Dokument:** fokussierter Editor mit erreichbarer Speicheraktion.
- **Bericht:** Quellen links, zusammengeführte Vorlage rechts.
- **Netzwerk:** Werkzeugzeile und große Visualisierungsfläche.
- **Statistik:** verdichtete Zeitbilanz und einfache Wochenverteilung.

## Responsive Regeln

Unter 760 Pixeln wird die Kontextleiste zum Drawer. Inhalte werden einspaltig, Hauptaktionen breit und Kalenderzellen kompakter. Kein Inhalt darf horizontales Seiten-Scrolling erzeugen.

## Nicht verwenden

- blaues Produkt-Branding
- doppelte Navigationsziele in Rail und Kontextleiste
- Emojis oder Unicode-Icons
- drei riesige Statistik-Karten untereinander
- versteckte Navigation ohne mobile Alternative
- Inline-Skripte oder Inline-Eventhandler
- neue UI-Bibliotheken für Standardinteraktionen
