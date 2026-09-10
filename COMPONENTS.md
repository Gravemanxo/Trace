# UI-Komponenten

## App-Shell

`base.html` stellt Rail, Kontext-Sidebar, mobile Kopfzeile und Arbeitsfläche bereit. Neue Hauptseiten werden genau einer der drei Sektionen zugeordnet.

## Page Header und Panel

`.page-header` enthält Eyebrow, genau eine `h1`, Erklärung und optional eine Hauptaktion. `.panel` ist der Standardcontainer; `.panel-heading` bündelt Titel und Aktion/Zähler. Spezialisierte Varianten sind `.timer-panel`, `.editor-panel` und `.network-panel`. Panels werden nicht unnötig verschachtelt.

## Buttons

- `.button.primary`: wichtigste Aktion
- `.button.secondary`: ergänzende Aktion
- `.button.compact`: Aktion in dichter Zeile
- `.icon-button`: bekannte Einzelaktion, immer mit `aria-label`
- `.icon-button.danger`: destruktiv, zusätzlich mit `data-confirm`

## Formulare

Jedes schreibende Formular enthält ein CSRF-Feld:

```html
<input type="hidden" name="csrf_token" value="{{ csrf_token(request) }}">
```

Labels enthalten sichtbare Beschriftung und Feld. Fehler erscheinen als `.alert[role="alert"]`. Speichern folgt Post/Redirect/Get.

## Dialog

Native `dialog.dialog` werden über `data-dialog-open="id"` geöffnet und mit `data-dialog-close` geschlossen. Escape und Fokus übernimmt der Browser; `app.js` ergänzt den Backdrop-Klick.

## Monatsnavigation und Kalender

`.month-toolbar` enthält Pfeillinks, sichtbaren Monat und ein natives Monatsfeld mit `data-month-picker` und `data-target`. Auswahl navigiert sofort. Jede `.calendar-day` ist ein echter Link, auch ohne Daten. Zustände: `intensity-0` bis `intensity-3`, `is-weekend`, `is-today`.

## Ressourcenliste und Tabellen

`.resource-row` zeigt Icon, Titel, Vorschau, Metadaten und Chevron; die ganze Zeile ist ein Link. Tabellen liegen in `.table-wrap`. Tabellenzeilen werden nicht per JavaScript klickbar gemacht, sondern enthalten echte Links.

## Kennzahlen und leere Zustände

`.metric-strip` verdichtet zwei bis vier Kennzahlen in einem Panel. `.empty-state` enthält SVG-Icon, konkrete Aussage, Hilfetext und höchstens eine nächste Aktion.

## JavaScript-Hooks

Verhaltens-Hooks verwenden `data-*`, keine Präsentationsklassen. Standardinteraktionen liegen in `app/static/app.js`, die Netzwerkansicht in `app/static/network.js`.
