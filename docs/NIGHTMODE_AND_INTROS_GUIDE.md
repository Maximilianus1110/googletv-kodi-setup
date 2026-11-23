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

## 3. ⏩ Intro überspringen („Intro skip“-Button)

### Dynamische Online-Erkennung (TheIntroDB, kein Auto-Skip):

* Beim Start einer Serienfolge gleicht das System die TMDb-ID, Staffel und Episode im Hintergrund mit **TheIntroDB** ab.
* Nur wenn ein **gültiges Intro-Segment** für die Episode vorliegt (und exakt während dieses Intro-Zeitfensters), erscheint unten rechts der Button **`Intro skip`**.
* **Kein automatisches Überspringen:** Das Intro läuft ganz normal weiter, bis du den Button aktiv mit der **Auswahltaste (Mitte / OK)** bestätigst.
* Sobald du drückst, springt die Wiedergabe sekundengenau ans Ende des Intros.
* Mit **Zurück** lässt sich der Button schließen; am Ende des Intro-Zeitfensters verschwindet er automatisch.
* Gibt es für die Folge kein bekanntes Intro, wird kein Button eingeblendet.
