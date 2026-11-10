# 🔒 Erwachsenenbereich (+18 / XXX) & PIN-Schutz

Dieses Setup enthält eine vollständig integrierte Mediathek für Erwachseneninhalte mit striktem Jugendschutz und vollständiger Tarnung.

---

## 1. Sicherheits-PIN & Zugangswege

* **Standard-PIN:** **`0000`** (vier Nullen).

### Weg A: Über das Menü
1. Navigiere in der linken Seitenleiste zu **Add-ons & Live-TV**.
2. Wähle den diskreten Menüpunkt **„🔒 Archiv (+18 PIN)“**.
3. Es öffnet sich das Nummern-Tastenfeld. Gib `0000` ein und bestätige.

### Weg B: Geheime Tastenkombination auf der Fernbedienung
* Halte die **Zurück-Taste für ca. 5 Sekunden gedrückt** (Long-Press Back).
* Das PIN-Eingabefeld öffnet sich direkt, egal wo du dich im Hauptmenü befindest.

---

## 2. Intelligente In-RAM Sitzungssteuerung (5 Minuten)

* Sobald du den PIN `0000` korrekt eingegeben hast, wird im Arbeitsspeicher ein Sitzungs-Token für **300 Sekunden (5 Minuten)** hinterlegt.
* Während dieser Zeit kannst du frei durch alle 306 Kategorien, Kanäle und Genres navigieren, ohne den PIN jedes Mal neu eingeben zu müssen.
* **Automatisches Sperren:**
  * Wenn du 5 Minuten lang inaktiv bist, verfällt die Sitzung.
  * Wenn du Kodi beendest oder das Gerät neu startest, ist sofort wieder der PIN nötig.
  * Auch wenn jemand versucht, das Add-on direkt über die Add-on-Liste oder den internen Verlauf aufzurufen, erzwingt die Service-Schicht (`default.py`) die PIN-Abfrage.

---

## 3. Vollständige Tarnung (Zero-Leak)

* **Keine Startseiten-Einträge:** Gesehene Videos werden weder auf der Startseite noch in den Karussells angezeigt.
* **Kein Trakt-Scrobble:** Erwachseneninhalte werden nicht an Trakt übertragen.
* **Keine Verwirrung:** Alte, tote VAVOO-Zahnrad-Verlinkungen wurden restlos entfernt.
