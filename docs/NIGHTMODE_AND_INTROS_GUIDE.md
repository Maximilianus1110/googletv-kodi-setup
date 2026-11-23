# 🌙 Nachtmodus & ⏩ Intro-Überspringen

Diese Dokumentation beschreibt die neuen Sehkomfort-Funktionen im Mediacenter.

---

## 1. 📺 Neuer OSD-Header & 5-Sekunden Auto-Hide

* **Echter Medien-Titel statt „Es läuft“:**
  * Wenn du während eines Videos **Steuerkreuz Oben (▲)** drückst, erscheint oben auf der Timeline direkt der vollständige Titel:
    * **Serien:** `[Serientitel] • [Staffel]x[Folge] • [Episodentitel]` (z. B. `My Name Is Earl • 1x01 • Pilot`)
    * **Filme:** `[Filmtitel]` (z. B. `Der Astronaut`)
    * **Live-TV:** `[Sendername] • [Aktuelle Sendung]`
    * **Bei Pause:** `Pause • [Titel]`
* **Automatisches Ausblenden (Auto-Hide nach 5 Sekunden):**
  * Nach genau 5 Sekunden ohne Tastendruck verschwindet die Timeline und die Menüleiste automatisch, sodass das Bild sofort wieder ungestört ist.
  * Jeder Tastendruck auf dem Steuerkreuz setzt den 5-Sekunden-Timer zurück.

---

## 2. 🌙 Nachtmodus / Dialog-Booster (Dynamic Range Compression)

### Das Problem:
Bei vielen Filmen und Serien sind Stimmen und Dialoge sehr leise abgemischt, während Actionszenen, Schüsse oder Explosionen extrem laut sind. Vor allem abends muss man ständig zur Fernbedienung greifen, um lauter oder leiser zu stellen.

### Die Lösung:
* Ein Klick auf das **🌙-Symbol** in der Player-Leiste schaltet den Nachtmodus ein:
  * **+10 dB Dialog-Boost:** Leise Dialoge und Flüstern werden kristallklar angehoben.
  * **Peak Limiter:** Explosionen und laute Soundeffekte werden abgefedert und nicht übersteuert.
* Ein erneuter Klick auf **🌙** schaltet das System zurück in den 0 dB Standardmodus für das Heimkino.

---

## 3. ⏩ Intro überspringen (Skip Intro)

### Zwei perfekt kombinierte Erkennungsmethoden:

1. **Vollautomatische Online-Erkennung (TheIntroDB):**
   * Beim Start einer Serienfolge gleicht das System die TMDb-ID, Staffel und Episode blitzschnell im Hintergrund mit der weltweiten Datenbank von **TheIntroDB** ab.
   * Wird ein Intro-Segment gefunden, erscheint während des Intros automatisch unten rechts das dezente Popup **`⏩ Intro überspringen`**.
   * Ein einfacher Druck auf die mittlere Taste überspringt das Intro sekundengenau zum Beginn der Handlung!
   * Wer das Intro doch sehen will: Einfach weiterlaufen lassen oder mit **Zurück** das Popup schließen.

2. **Manueller 1-Klick-Introsprung im OSD (Button ⏩):**
   * Falls für eine sehr neue oder seltene Serie noch keine Online-Timestamps vorliegen, drückst du einfach **Steuerkreuz Oben (▲)** und wählst den neuen Button **`⏩`**.
   * Das System springt automatisch um 85 Sekunden vorwärts (die durchschnittliche Standard-Dauer von Serienintros).
