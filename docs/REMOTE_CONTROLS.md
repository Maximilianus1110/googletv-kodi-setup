# 🎮 Fernbedienungs-Belegung, OSD-Buttons & Fenster-IDs

> [!NOTE]
> Eine Übersicht aller behobenen Abweichungen zwischen früherer Doku und aktuellem Code findest du in [**`docs/ABWEICHUNGEN_ALT_VS_CODE.md`**](ABWEICHUNGEN_ALT_VS_CODE.md).

---

## 🧭 Funktions-Schnellindex

| Bereich | Konfigurationsdatei | Beschreibung |
| :--- | :--- | :--- |
| **[1. Tasten während der Video-Wiedergabe](#1-tastenbelegung-whrend-der-video-wiedergabe-fullscreenvideo--fullscreenlivetv)** | [`kodi/userdata/keymaps/player_controls.xml`](../kodi/userdata/keymaps/player_controls.xml) | Überschreibt Kodis 10-Minuten-Sprünge auf Hoch/Runter durch Streaming-Standard (`OSD` auf `▲`, `Window 1140` auf `▼`, 10s-Seek auf `◄`/`►`). |
| **[2. Alle 10 Buttons in der OSD-Steuerleiste](#2-alle-buttons-im-video-osd-videoosdxml)** | [`kodi/addons/skin.arctic.fuse.2/1080i/VideoOSD.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/VideoOSD.xml)<br>[`Includes_Actions.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/Includes_Actions.xml) | Die komplette untere Button-Reihe (`6001`–`6010`) sowie der Timeline-Slider (`8200`) mit 5-Sekunden-Auto-Hide-Reset. |
| **[3. Dynamische Einblend-Popups (`Intro skip` & `UpNext`)](#3-dynamische-overlays-whrend-der-wiedergabe-intro-skip--upnext)** | [`service.upnext/resources/lib/skip.py`](../kodi/addons/service.upnext/resources/lib/skip.py)<br>[`skin.arctic.fuse.2/1080i/Includes_OSD.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/Includes_OSD.xml) | Tastenverhalten bei eingeblendetem `Intro skip`-Button (`3010`) und `UpNext`-Popup (`3012` / `4013`). |
| **[4. Hauptmenü & Seitenleiste](#4-navigation-im-hauptmen--seitenleiste-arctic-fuse-2)** | [`skinvariables-shortcut-sidemenu.json`](../kodi/userdata/addon_data/script.skinvariables/nodes/skin.arctic.fuse.2/skinvariables-shortcut-sidemenu.json) | Steuerung durch die Seitenleiste, Widgets und das Kontextmenü. |

---

## 1. 🎬 Tastenbelegung während der Video-Wiedergabe (`FullscreenVideo` & `FullscreenLiveTV`)

Definiert in [`kodi/userdata/keymaps/player_controls.xml`](../kodi/userdata/keymaps/player_controls.xml) (gilt identisch für `<remote>` und `<keyboard>`):

| Taste (Fernbedienung / Tastatur) | Kodi-Kontext | Exakte XML-Aktion | Was im Code passiert |
| :--- | :--- | :--- | :--- |
| **Steuerkreuz Oben (`▲`)** | `FullscreenVideo` & `FullscreenLiveTV` | `<up>OSD</up>` | Öffnet [`VideoOSD.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/VideoOSD.xml) (inkl. [`DialogSeekBar.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/DialogSeekBar.xml) mit Titel-Header `Label_OSD_Header`) und startet den 5-Sekunden-Timer `AlarmClock(osd_timeout, ..., 00:05)`. |
| **Steuerkreuz Unten (`▼`)** | `FullscreenVideo` | `<down>ActivateWindow(1140)</down>` | Öffnet [`Custom_1140_OSD_Playlist.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/Custom_1140_OSD_Playlist.xml):<br>• **Serien / aktive Playlist:** Zeigt die horizontale Episoden-Schublade (`Container 7000`, `Path_OSD_Episodes`).<br>• **Einzel-Filme (`!$EXP[Exp_OSD_HasPlaylist]`):** Schließt `1140` sofort im `<onload>` und öffnet `ActivateWindow(1141)` (Schauspieler / Cast-Schublade). |
| **Steuerkreuz Unten (`▼`)** | `FullscreenLiveTV` | `<down>OSD</down>` | Öffnet bei Live-TV das normale Video-OSD statt der Episoden-Schublade. |
| **Steuerkreuz Links (`◄`)** | `FullscreenVideo` | `<left>StepBack</left>` | Spult **10 Sekunden zurück** und blendet für **2 Sekunden** (`Player.HasPerformedSeek(2)`) die untere Zeitleiste (`DialogSeekBar.xml`) mit Offset-Anzeige (`Suche -00:10`) ein. |
| **Steuerkreuz Rechts (`►`)** | `FullscreenVideo` | `<right>StepForward</right>` | Spult **10 Sekunden vor** und blendet für **2 Sekunden** die untere Zeitleiste mit Offset-Anzeige (`Suche +00:10`) ein. |
| **Auswahltaste (`Mitte / OK`)** (`return` / `enter` / `space`) | `FullscreenVideo` & `FullscreenLiveTV` | `<select>PlayPause</select>` | Pausiert die Wiedergabe bzw. setzt sie fort. Bei Pause bleibt `DialogSeekBar.xml` mit `Pause • [Titel]` sichtbar. |
| **Zurück-Taste (`Back`)** (`escape` / `backspace` / `browser_back`) | `VideoOSD` | `<back>Close</back>` | Schließt das geöffnete `VideoOSD` (bzw. offene OSD-Unterfenster `1140`–`1149`), ohne das Video zu stoppen. Ist kein OSD offen, beendet `Back` im Vollbild die Wiedergabe. |

---

## 2. 🎛️ Alle Buttons im Video-OSD (`VideoOSD.xml`)

Wenn du im Video **Steuerkreuz Oben (`▲`)** drückst, liegt der Fokus standardmäßig auf **Button `6001` (Play/Pause)**.
* Jeder Fokuswechsel (`<onfocus>`) zwischen den Buttons oder auf den **Timeline-Slider (`Control 8200`)** setzt über `Action_OSD_Button` ([`Includes_Actions.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/Includes_Actions.xml), Zeile 740) den 5-Sekunden-Timer `AlarmClock(osd_timeout, ..., 00:05, silent)` zurück.
* Mit **Steuerkreuz Oben (`▲`)** aus der Button-Reihe gelangst du auf den **Timeline-Slider (`Control 8200`)** zum freien Spulen; mit **Steuerkreuz Unten (`▼`)** öffnet sich aus dem OSD ebenfalls die Episoden-/Cast-Schublade (`$VAR[Action_OSD_Main_OnDown]` → `1140` bzw. `1141`).

### Linke Button-Gruppe (`grouplist` ID `6091`)
| Control-ID | Icon | Funktion | Exakte Aktion im Code ([`VideoOSD.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/VideoOSD.xml)) |
| :--- | :--- | :--- | :--- |
| **`6001`** *(Default)* | Play / Pause | Wiedergabe / Pause | `<onclick>PlayerControl(Play)</onclick>` + 5s-Timer-Reset. |
| **`6002`** | Zurück / TV-Guide | Vorherige Folge / Kapitel (bzw. TV-Guide bei Live-TV) | Video: `$VAR[Action_OSD_SkipPrev]` (`PlayerControl(Previous)`).<br>Live-TV: `CancelAlarm(osd_timeout,true)` → `Close` → `ActivateWindow(TVGuide)`. |
| **`6003`** | Weiter / Aufnahme | Vorschau nächste Folge (`Window 1143`) | Öffnet bereits beim Fokussieren (`<onfocus>`) das Overlay [`Custom_1143_OSD_NextOverlay.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/Custom_1143_OSD_NextOverlay.xml) mit Vorschau auf das nächste Playlist-Element. |
| **`6004`** | Stop | Wiedergabe beenden | `CancelAlarm(osd_timeout,true)` → `PlayerControl(Stop)`. |

### Rechte Button-Gruppe (`grouplist` ID `6092`)
| Control-ID | Icon | Funktion | Exakte Aktion im Code ([`VideoOSD.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/VideoOSD.xml)) |
| :--- | :--- | :--- | :--- |
| **`6005`** | `i` (Info) | Infos & Wikipedia | Öffnet bei `<onfocus>` `Window 1145`; bei `<onclick>` `CancelAlarm(osd_timeout,true)` + `$VAR[Action_OSD_WikiInfo]`. |
| **`6006`** | Lautsprecher | Tonspur & Audio-Menü | Zeigt aktuelle Audiosprache (`VideoPlayer.AudioLanguage`), öffnet bei `<onfocus>` Schnellauswahl `Window 1146` und bei `<onclick>` `ActivateWindow(osdaudiosettings)`. |
| **`6007`** | Sprechblase | Untertitel-Menü | Zeigt Untertitelsprache, öffnet bei `<onfocus>` Schnellauswahl `Window 1147` und bei `<onclick>` `ActivateWindow(osdsubtitlesettings)`. |
| **`6008`** | Filmstreifen | Video-Einstellungen | Öffnet bei `<onfocus>` `Window 1148` und bei `<onclick>` `ActivateWindow(osdvideosettings)`. |
| **`6009`** | **`🔄` (Pfeile)** | **Stream / Hoster wechseln** *(nur bei Filmen & Serien, nicht Live-TV)* | `CancelAlarm(osd_timeout,true)` → `Dialog.Close(videoosd)` → `RunScript(special://skin/shortcuts/change_stream.py)`. Pausiert das Video, öffnet die Hoster-Liste mit TCP-Ping-Ampel & Voll-Speedtest und setzt an derselben Sekunde (`resume`) fort. |
| **`6010`** | **`🌙` (Mond)** | **Nachtmodus / Dialog-Booster** | `RunScript(special://skin/shortcuts/toggle_nightmode.py)` + 5s-Timer-Reset über `Defs_OSD_Button`. Schaltet `+10 dB` (`10× volampup`) ein bzw. aus (`10× volampdown`) und blendet das OSD 5 Sekunden danach automatisch aus. |

---

## 3. ⏩ Dynamische Overlays während der Wiedergabe (`Intro skip` & `UpNext`)

Diese beiden Dialoge sind eigenständige, nicht-modale `WindowXMLDialog`-Fenster von `service.upnext`:

### A. `Intro skip`-Button (`script-upnext-skip.xml` / [`skip.py`](../kodi/addons/service.upnext/resources/lib/skip.py))
* **Sichtbarkeit:** Nur wenn TheIntroDB für die laufende Folge ein gültiges Intro-Segment (`>= 3.0s`) geliefert hat und `start <= play_time < end - 1.0` gilt.
* **Fokus:** Liegt sofort auf Button **`3010`** (`Intro skip`).
* **Tasten:**
  * **Mitte / OK:** Springt sofort zu `segment['end']` (`player.seekTime`) und schließt das Overlay.
  * **Zurück (`Back`):** Setzt `dismissed = True` und blendet den Button für den Rest des Intros aus.

### B. `UpNext`-Popup (`script-upnext-upnext.xml` / [`Includes_OSD.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/Includes_OSD.xml))
* **Sichtbarkeit:** Zu Beginn des Abspanns (`notification_offset` aus TheIntroDB) oder `15` Sekunden vor Episodenende (auch beim Wechsel auf die nächste Staffel `S+1, E01`).
* **Fokus:** Liegt sofort auf Button **`3012`** (*„Abspielen“*).
* **Tasten:**
  * **Mitte / OK (auf `3012`):** Startet sofort die nächste Folge (`set_watch_now(True)` → `player.playnext()`).
  * **Rechts + Mitte / OK (auf `4013` → triggert `3013` *„Abbrechen“*):** Bricht den Countdown ab (`set_cancel(True)`). Da `stopAfterClose = false` gesetzt ist, läuft der Abspann der aktuellen Folge bis zum Ende weiter, ohne danach automatisch weiterzuschalten.
  * **Zurück (`Back`):** Schließt das Popup ebenfalls ohne Folgenwechsel (`dismissed = True`, `set_cancel(True)`).
  * **Keine Taste drücken:** Nach Ablauf des **15-Sekunden-Countdowns** (`autoPlayCreditsTime = 15` bzw. `autoPlayTime = 15`) startet automatisch die nächste Folge über `player.playnext()`.

---

## 4. 🏠 Navigation im Hauptmenü & Seitenleiste (Arctic Fuse 2)

Definiert über [`skinvariables-shortcut-sidemenu.json`](../kodi/userdata/addon_data/script.skinvariables/nodes/skin.arctic.fuse.2/skinvariables-shortcut-sidemenu.json) und [`skinvariables-shortcut-homemenu.json`](../kodi/userdata/addon_data/script.skinvariables/nodes/skin.arctic.fuse.2/skinvariables-shortcut-homemenu.json):

| Taste | Aktion im Hauptmenü |
| :--- | :--- |
| **Steuerkreuz Links (`◄`)** (am linken Rand einer Reihe) | Öffnet die linke **Seitenleiste (SideMenu)** mit den 5 Hauptbereichen:<br>1. **Entdecken** (`ActivateWindow(1105)` – Suche & globale Widgets)<br>2. **Filme** (`plugin.video.themoviedb.helper/?info=dir_movie`)<br>3. **Serien** (`plugin.video.themoviedb.helper/?info=dir_tv`)<br>4. **Live-TV** (`plugin.video.vavooto/?action=live`)<br>5. **YouTube & SmartTube** (`StartAndroidActivity(org.smarttube.stable)`) |
| **Steuerkreuz Rechts (`►`)** | Wechselt aus der Seitenleiste zurück in die Widget-Karussells bzw. scrollt horizontal durch die Poster/Thumbnails. |
| **Steuerkreuz Oben / Unten (`▲` / `▼`)** | Wechselt vertikal zwischen den einzelnen Widget-Reihen (z. B. *Weiterschauen*, *Nächste Episoden*, *Meine Trakt Watchlist*, *Weil du geschaut hast*, *Meine YouTube Vorschläge*, *Meine Abonnements*, *Trends*). |
| **Auswahltaste (`Mitte / OK`)** (kurz drücken) | Startet bei einem Film oder einer Episode direkt den Standard-Player **`xstream.json`** (`xStream Scraper (Auto-Play + Vavoo)`). Bei einer Serie öffnet sich die Staffel-/Episodenübersicht. |
| **Auswahltaste (`Mitte / OK`)** (gedrückt halten) | Öffnet das **Kodi-Kontextmenü** (u. a. für *„Abspielen mit...“* → *„xStream Scraper (Quelle manuell wählen)“* via [`xstream_select.json`](../kodi/userdata/addon_data/plugin.video.themoviedb.helper/players/xstream_select.json) oder Trakt-Watchlist-Verwaltung). |
