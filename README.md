# 🎬 Google TV & Android TV – Kodi Mediacenter Setup (Ultimate Edition)

[![Kodi](https://img.shields.io/badge/Kodi-21.2%20Omega-blue.svg)](https://kodi.tv)
[![Platform](https://img.shields.io/badge/Platform-Google%20TV%20%7C%20Android%20TV-green.svg)](https://android.com/tv)
[![Interface](https://img.shields.io/badge/Skin-Arctic%20Fuse%202-purple.svg)](https://github.com/jurialmunkey/skin.arctic.fuse.2)
[![Trakt](https://img.shields.io/badge/Sync-Trakt.tv-red.svg)](https://trakt.tv)

Ein vollkommen schlüsselfertiges, optimiertes Kodi-Setup für den **Google TV Streamer**, **Chromecast mit Google TV**, **Nvidia Shield TV** oder jede andere **Android TV / Fire TV** Box.

Dieses Setup verwandelt dein Kodi in ein blitzschnelles, modernes Mediacenter im **Netflix-Design** – inklusive automatischem Multi-Source Streaming, geräteübergreifender Trakt-Synchronisation („Weiterschauen“ wie bei Netflix), YouTube mit persönlichen Vorschlägen, intuitivem Fernbedienungs-Layout und diskretem Jugendschutzbereich.

---

## ✨ Features im Überblick

* 🎨 **Modernes Netflix-UI (Arctic Fuse 2):**
  * Film- & Serien-Trends, Live-TV und personalisierte Empfehlungen direkt auf der Startseite.
  * Flüssige Navigation ohne Ruckler oder Deadlocks.
* ⚡ **Intelligenter Multi-Source Stream-Scraper:**
  * Ein Klick auf ein Film-/Serien-Poster genügt: xStream Scraper durchsucht automatisch 14 deutsche Streaming-Anbieter & VAVOO-Mirrors.
  * Automatischer Vorab-Test (max. 10 s): Fehlerhafte oder tote Streams werden übersprungen, der beste funktionierende Stream startet sofort.
* ▶️ **„Weiterschauen“ & „Nächste Episoden“ (Trakt.tv Sync):**
  * Angefangene Filme und Serienfolgen erscheinen direkt mit Fortschrittsbalken auf der Startseite.
  * Beendete Folgen schalten automatisch die nächste Episode frei.
* ⏩ **Nahtloses Autoplay & Hintergrund-Vorabladen (Preloading):**
  * Nächste Episoden werden wie bei Netflix/Prime Video automatisch abgespielt.
  * Hintergrund-Preloading (8 Sekunden nach Start): Der Stream für Folge N+1 wird bereits im RAM gecacht – 0 Sekunden Wartezeit beim Episodenwechsel!
  * Eingebauter UpNext-Countdown 15 Sekunden vor Episodenende.
* 📺 **In-Player Episoden-Schublade & Stream-Auswahl:**
  * **Steuerkreuz Unten (▼):** Öffnet direkt im laufenden Video die **Staffel-Episoden-Schublade** (wie bei Prime Video) zum schnellen Folgenwechsel.
  * **OSD-Button 🔄:** Mitten im Video alternative Hoster/Streams auswählen (bei schlechter Videoqualität) und an exakt derselben Sekunde fortsetzen.
  * Optional auch vor dem Abspielen über das Kontextmenü (*Abspielen mit...* -> *Quelle manuell wählen*).
* 🌙 **Nachtmodus / Dialog-Booster (DRC):**
  * Per 1-Klick (OSD-Button 🌙) schaltet Kodi eine +10 dB Dynamikkompression ein: Leise Stimmen werden verständlich und laut, laute Explosionen sanft gedämpft.
* ⏩ **Intro überspringen (TheIntroDB & 1-Klick OSD):**
  * Erkennt Intros bekannter Serien automatisch online über TheIntroDB und zeigt das dezente Popup `⏩ Intro überspringen`.
  * Zusätzlicher 1-Klick-Button ⏩ im Player OSD (+85s Sprung).
* ⏱️ **Timeline mit echtem Serientitel & 5s Auto-Hide:**
  * OSD zeigt nun vollständigen Serientitel, Staffel und Episodennummer statt nur „Es läuft“.
  * Timeline blendet sich nach 5 Sekunden Inaktivität automatisch aus.
* 📺 **YouTube & SmartTube Integration:**
  * Echte persönliche Empfehlungen deines Google-Kontos auf der Startseite (`FEwhat_to_watch`).
  * Gepatchter TV-OAuth Flow: Anmeldung über `google.com/device` ohne nervige Google-Sicherheitsblockaden.
  * Verlinkung zur werbefreien Android-App **SmartTube**.
* 🎮 **Streaming-Standard Fernbedienung:**
  * **Oben (▲):** Zeitbalken (Timeline) & Filmtitel einblenden (OSD).
  * **Unten (▼):** Zeitbalken sofort ausblenden.
  * **Links / Rechts (◄ / ►):** 10 Sekunden vor- / zurückspulen.
  * **Mitte:** Play / Pause.
* 🔒 **Diskreter Erwachsenenbereich (+18 / XXX):**
  * PIN-geschützt (**Standard-PIN: `0000`**).
  * Schnellaufruf durch **5 Sekunden langes Drücken der Zurück-Taste** (Long-Press Back).
  * 306 Quellen, weltweite Suche & Kategorien.
  * Automatisches 5-Minuten-RAM-Sitzungsfenster; keine Spuren im Verlauf oder auf der Startseite.

---

## 🚀 Schnellstart: 1-Klick Installation via ADB

### Voraussetzungen
1. Ein Google TV / Android TV Gerät mit aktiviertem **Entwicklermodus & USB-/Netzwerk-Debugging**.
2. **Kodi 21.2 (Omega)** auf dem Gerät installiert (aus dem Google Play Store oder per APK).
3. Ein PC (Linux, macOS oder Windows mit WSL/Git-Bash) mit installiertem `adb`.

### Installation in 3 Schritten:

```bash
# 1. Repository klonen
git clone git@github.com:Maximilianus1110/googletv-kodi-setup.git
cd googletv-kodi-setup

# 2. Gerät anschließen (USB) oder per WLAN verbinden
adb connect <IP-DEINES-FERNSEHERS>:5555

# 3. Installations-Skript ausführen
./install.sh
```

Das Skript sichert automatisch deine bisherigen Keymaps, überträgt alle vorkonfigurierten Add-ons, Tastenbelegungen und Skin-Settings und startet Kodi frisch auf deinem Fernseher!

---

## 📖 Ausführliche Anleitungen & Dokumentation

Alle Spezialbereiche sind detailliert im Ordner [`docs/`](docs/) beschrieben:

* 🎮 [**Fernbedienungs-Belegung & Gesten**](docs/REMOTE_CONTROLS.md): Detaillierte Übersicht aller Tastenfunktionen während der Wiedergabe und im Hauptmenü.
* 🌙 [**Nachtmodus, Intro-Skip & Timeline**](docs/NIGHTMODE_AND_INTROS_GUIDE.md): Dialog-Verstärkung, Intro-Erkennung via TheIntroDB und automatische Timeline-Ausblendung.
* ⏩ [**Autoplay, Episodenschublade & Stream-Auswahl**](docs/AUTOPLAY_AND_STREAM_SELECT.md): Nahtlose Wiedergabe, Vorabladen im Hintergrund, Prime-Video-Episodenauswahl & Quellenwechsler.
* 🎬 [**Trakt-Einrichtung („Weiterschauen“)**](docs/TRAKT_SETUP.md): Wie du dein kostenloses Trakt-Konto mit Kodi verbindest und den Netflix-Fortschrittsbalken aktivierst.
* 📺 [**YouTube-Login & Startseite**](docs/YOUTUBE_SETUP.md): Google TV Geräte-Login ohne Sicherheitswarnung und Personalisierung deiner Empfehlungen.
* 🔒 [**Erwachsenenbereich (+18)**](docs/ADULT_SETUP.md): Alles zum PIN-Code `0000`, der 5-Minuten-Sitzungsverwaltung und der Tarnung.
* 🛠️ [**Fehlerbehebung (Troubleshooting)**](docs/TROUBLESHOOTING.md): Schnelle Lösungen bei Stream-Abbrüchen, Pufferung oder Bildschirmsperren.

---

## 📦 Enthaltene Add-ons & Versionen

| Add-on / Modul | ID | Version / Patch |
| :--- | :--- | :--- |
| **Arctic Fuse 2** | `skin.arctic.fuse.2` | Gepatcht (OSD Close on Down, Shortcut-Menüs, PIN-Script) |
| **TheMovieDb Helper** | `plugin.video.themoviedb.helper` | 6.21.2 (Gepatcht: Trakt-Listenfix & Daemon-Service) |
| **xStream** | `plugin.video.xstream` | 2026.10.06~nightly (QuietWindows & DNS-Bypass) |
| **xStream Scraper** | `script.module.xstreamscraper` | 2026.11.02.7 (Gepatcht: TMDb-Metadaten für Trakt) |
| **YouTube** | `plugin.video.youtube` | 7.4.4 (Gepatcht: TV-Client OAuth, kein Google-Block) |
| **AdultHideout** | `plugin.video.adulthideout` | 1.0.27 (Gepatcht: Core PIN `0000` & 5-Min Timeout) |
| **AdultHideout Core** | `service.adulthideout.core` | 1.0.1 (Gepatcht: Python-Fallback) |
| **Up Next (Autoplay)** | `service.upnext` | 1.3.4 (Automatischer Episodenübergang & Preload) |
| **VAVOO.TO** | `plugin.video.vavooto` | 2026.11.02.5 (Deutsche Live-TV Kanäle) |
| **ResolveURL** | `script.module.resolveurl` | Aktuell (VOE, DoodStream, Filemoon etc.) |
| **Trakt Sync** | `script.module.tmdbhelper.sync.trakt` | 1.2.9 (Cloud-Scrobbling) |

---

## 🛠️ Wartungs-Befehle

```bash
# Nur die Tastenbelegung neu übertragen
./install.sh --keymaps-only

# Ein lokales Backup des aktuellen Kodi-Stands auf den PC ziehen
./backup.sh

# Kodi über ADB neu starten
adb shell "am force-stop org.xbmc.kodi; am start -n org.xbmc.kodi/.Main"
```

---

## ⚖️ Lizenz & Haftungsausschluss

Dieses Repository dient rein privaten Archivierungs- und Dokumentationszwecken. Sämtliche Add-ons sind Open-Source-Projekte dritter Entwickler. Es werden keine urheberrechtlich geschützten Medieninhalte gehostet.
