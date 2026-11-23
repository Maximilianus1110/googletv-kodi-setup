# ⏩ Autoplay, Episoden-Schublade & Stream-Auswahl

In diesem Setup sind erweiterte Streaming-Features integriert, die das Serienschauen so komfortabel machen wie bei Netflix oder Amazon Prime Video.

---

## 1. 🚀 Nahtloses Autoplay & Hintergrund-Vorabladen (Preloading)

### Wie es funktioniert:
1. **Automatisches Queueing:** Wenn eine Serienfolge gestartet wird, reiht TMDb Helper im Hintergrund automatisch alle verbleibenden Folgen der aktuellen Staffel in die Video-Playlist ein.
2. **Background Preloading:** Nach ca. 8 Sekunden Laufzeit der aktuellen Folge startet im Hintergrund der Scraper für die **nächste Folge (N+1)**. Er testet die verfügbaren Hoster (VAVOO Mirrors, SerienStream, VOE usw.) und legt den ersten funktionierenden Stream im RAM-Cache ab.
3. **UpNext Einblendung:** 15 Sekunden vor Episodenende erscheint unten rechts das UpNext-Popup („Nächste Folge in 15 Sekunden...“):
   - **Jetzt abspielen:** Startet die nächste Folge sofort.
   - **Abbrechen:** Verhindert das automatische Weiterschalten.
4. **Sofortstart (0 Sekunden Ladezeit):** Läuft der Countdown ab oder endet das Video, greift xStream Scraper auf den vorbereiteten Stream zurück und startet ohne erneute Suche und ohne Wartezeit direkt die nächste Folge.

---

## 2. 📺 In-Player Episoden-Schublade ("Nach unten drücken: Playlist")

### Wie bei Amazon Prime Video:
- **Taste Steuerkreuz Unten (▼)** während der Videowiedergabe drücken.
- Es öffnet sich direkt von unten die **Staffel-Episoden-Schublade (Window 1140)**.
- Du kannst horizontal durch alle Folgen der aktuellen Staffel blättern, Titel und Zusammenfassungen sehen und mit der Auswahltaste direkt zu einer anderen Folge springen.
- Mit der **Zurück-Taste (Back)** schließt du die Schublade wieder, ohne die Wiedergabe zu unterbrechen.

---

## 3. 🎯 Smarter Stream- / Hoster-Wechsler (Qualität & Speed)

Standardmäßig wählt xStream Scraper vollautomatisch den schnellsten, stabilsten Stream aus. Wenn ein Stream einmal schlechte Bildqualität hat oder ruckelt, hast du zwei komfortable Möglichkeiten, manuell eine andere Quelle mit **Qualitäts- und Geschwindigkeitsanzeige** zu wählen:

### Was dir die Liste direkt anzeigt:
* **Ampel-Symbol:** `🟢` schneller/geprüfter Stream (< 280 ms), `🟡` normaler/unbekannter Ping, `🔴` langsam (> 650 ms) oder zuletzt fehlerhaft.
* **Hoster, Qualität & Ping:** z. B. `🟢 1. [VOE • HD • 85ms] Serienstream (DE)` oder nach Prüfung `🟢 ✅ 1. [Filemoon • 1080p • 140ms] Kinoger [Geprüft]`.
* **Live-Speedtest (Eintrag 0):** Über **`⚡ [Live-Speedtest: Top-5 Streams auflösen & echte Auflösung messen]`** werden die besten 5 Kandidaten direkt vorab aufgelöst, auf tatsächliche Video-Daten geprüft und mit ihrer **echten Auflösung** (`4K`, `1080p`, `720p`) sowie realen Antwortzeit ganz nach oben sortiert.

### Option A: Mitten im Video wechseln (In-Player)
1. **Steuerkreuz Oben (▲)** drücken, um die Timeline / das OSD einzublenden.
2. In der unteren Steuerungsleiste ganz nach rechts auf das **🔄-Symbol** ("Stream / Quelle wechseln") navigieren und auswählen.
3. Das Video pausiert und ein sortierter Dialog listet alle gefundenen Streams mit Ampel, Qualität & Ping auf.
4. Optional **⚡ Live-Speedtest** wählen oder direkt eine Quelle anklicken -> Der Stream wird geprüft und das Video setzt **an der exakten Sekunde** fort.

### Option B: Bereits vor dem Start auswählen
1. In den Startseiten-Widgets oder Serienübersichten auf die gewünschte Folge navigieren.
2. Die **Auswahltaste lange gedrückt halten** (Kontextmenü öffnen).
3. **„Abspielen mit...“** wählen.
4. **„xStream Scraper (Quelle manuell wählen)“** auswählen.
5. Die sortierte Liste der Hoster öffnet sich direkt vor dem Abspielen.
