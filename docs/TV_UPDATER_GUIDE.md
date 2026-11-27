# 🔄 On-TV Setup Updater & Branch-Switcher (`script.googletv.updater`)

Diese Dokumentation beschreibt die technische Architektur und Bedienung des vorinstallierten Kodi-Add-ons **[`script.googletv.updater`](https://github.com/Maximilianus1110/googletv-kodi-updater)** ([`kodi/addons/script.googletv.updater/`](../kodi/addons/script.googletv.updater/)), mit dem das gesamte Kodi-Setup direkt am Fernseher per Fernbedienung über GitHub aktualisiert werden kann – ganz ohne PC oder ADB.

---

## 🧭 Funktions-Schnellindex

| Funktion / Thema | Beteiligte Dateien & Funktionen | Kurzbeschreibung |
| :--- | :--- | :--- |
| **[1. Aufruf über das Power-Menü & Programm-Add-ons](#1-aufruf-am-fernseher-arctic-fuse-2)** | [`skinvariables-shortcut-powermainmenu.json`](../kodi/addons/skin.arctic.fuse.2/shortcuts/skinvariables-shortcut-powermainmenu.json)<br>[`default.py`](../kodi/addons/script.googletv.updater/default.py) → `main()` | Direkt erreichbar über das **Power-Symbol (`⏻`) → `Setup Updater`** in Arctic Fuse 2 sowie unter *Programm-Add-ons*. |
| **[2. GitHub Branch-Auswahl & Commit-Vergleich](#2-freie-github-branch-auswahl--commit-vergleich)** | [`github_api.py`](../kodi/addons/script.googletv.updater/resources/lib/github_api.py) → `fetch_branches()`, `fetch_branch_details()`<br>[`ui.py`](../kodi/addons/script.googletv.updater/resources/lib/ui.py) → `select_branch_dialog()` | Listet alle Branches von `Maximilianus1110/googletv-kodi-setup` live mit Commit-Hash (`short_sha`) auf und erlaubt den Sofort-Wechsel auf jeden Branch. |
| **[3. Voll-Update vs. Schnell-Update](#3-voll-update-vs-schnell-update-nur-keymaps--skin)** | [`installer.py`](../kodi/addons/script.googletv.updater/resources/lib/installer.py) → `install_from_zip()`<br>[`ui.py`](../kodi/addons/script.googletv.updater/resources/lib/ui.py) → `run_update()`, `apply_kodi_runtime_post_install()` | **Voll-Update** aktualisiert alle Add-ons & Userdata inkl. JSON-RPC-Optimierung; **Schnell-Update** aktualisiert nur Keymaps & Skin ohne Neustart. |
| **[4. Schutz von Trakt, YouTube & Stream-Historie](#4-automatischer-schutz-von-trakt-youtube--stream-historie)** | [`backup_manager.py`](../kodi/addons/script.googletv.updater/resources/lib/backup_manager.py) → `extract_credentials()`, `restore_credentials()` | Bewahrt `trakt_token`, Trakt-Sync OAuth, YouTube TV-OAuth (`access_manager.json`) und `stream_history.json` über jedes Update hinweg. |
| **[5. Lokaler Backup- & Rollback-Manager](#5-lokaler-backup--rollback-manager)** | [`backup_manager.py`](../kodi/addons/script.googletv.updater/resources/lib/backup_manager.py) → `create_backup()`, `restore_backup()`, `prune_backups()` | Erstellt komprimierte ZIP-Sicherungen (`max_backups = 3`) auf dem TV und ermöglicht 1-Klick-Rollbacks. |
| **[6. Automatische Update-Prüfung beim Kodi-Start](#6-automatische-update-prfung-beim-kodi-start-servicepy)** | [`service.py`](../kodi/addons/script.googletv.updater/service.py) → `run_startup_check()`<br>[`state.py`](../kodi/addons/script.googletv.updater/resources/lib/state.py) → `is_update_available()` | Prüft 15 Sek. nach Kodi-Start im Hintergrund, ob auf dem gewählten Branch ein neuer Commit vorliegt (Hinweis-Dialog oder Auto-Update). |

---

## 1. 🎮 Aufruf am Fernseher (Arctic Fuse 2)

1. **Über das Power-/System-Menü:**
   * Navigiere auf der Kodi-Startseite in die linke Seitenleiste ganz nach unten auf das **Power-Symbol (`⏻`)**.
   * Wähle den Eintrag **`Setup Updater`** (`RunScript(script.googletv.updater)`).
2. **Über Programm-Add-ons:**
   * *Einstellungen → Add-ons → Programm-Add-ons → **Google TV Setup Updater***.

Das Hauptmenü zeigt direkt den aktuell aktiven GitHub-Branch sowie den lokal installierten Commit-Stand (`Installiert: main@<short_sha>`):
* `🚀 Voll-Update starten (Branch: <branch>)`
* `🌿 Branch auswählen / wechseln (Aktiv: <branch>)`
* `⚡ Schnell-Update: Nur Keymaps & Skin-Menüs (Branch: <branch>)`
* `🔍 Auf Updates prüfen & Commit-Vergleich`
* `💾 Backup & Rollback Manager`
* `🛠️ Wartung: Hoster-Fehlersperre (stream_failures.json) zurücksetzen`
* `⚙️ Add-on Einstellungen öffnen`

---

## 2. 🌿 Freie GitHub-Branch-Auswahl & Commit-Vergleich

Über **`🌿 Branch auswählen / wechseln`** ruft [`github_api.fetch_branches()`](../kodi/addons/script.googletv.updater/resources/lib/github_api.py) live `https://api.github.com/repos/Maximilianus1110/googletv-kodi-setup/branches?per_page=100` ab:
* Der Branch `main` steht immer an erster Stelle, gefolgt von allen weiteren Branches in alphabetischer Reihenfolge.
* Neben jedem Branch werden der aktuelle 7-stellige Commit-Hash sowie Status-Badges (`[AKTIV]`, `[Installiert: <sha>]`) angezeigt.
* Über den letzten Listeneintrag **`✏️ Eigenen Branch-Namen manuell eingeben...`** kann auch ein beliebiger Branch-Name direkt per Bildschirmtastatur eingegeben werden.
* Nach Auswahl eines Branches lädt `fetch_branch_details()` die neueste Commit-Nachricht und das Commit-Datum und fragt, ob das Setup sofort auf diesen Branch aktualisiert werden soll.

---

## 3. 🚀 Voll-Update vs. Schnell-Update (Nur Keymaps & Skin)

### A. Voll-Update (`mode="full"`)
1. Lädt das Branch-Archiv (`codeload.github.com/.../zip/refs/heads/<branch>`) in `64 KB`-Blöcken mit Live-Fortschrittsanzeige (`MB / MB`) und Abbruch-Möglichkeit herunter.
2. Liest vor dem Überschreiben alle bestehenden OAuth-Tokens und Logins aus (`extract_credentials()`).
3. Erstellt (sofern aktiviert) ein komprimiertes Vorab-Backup unter `userdata/addon_data/script.googletv.updater/backups/`.
4. Entpackt alle Dateien aus `kodi/addons/` und `kodi/userdata/` nach `special://home/` (ignoriert `__pycache__`, `*.pyc`, `.DS_Store` sowie profilspezifische `script-skinvariables-generator-includes--kodiprofile-*.xml`).
5. Bereinigt archivierte Alt-Komponenten (`plugin.video.adulthideout`, `service.adulthideout.core`, `secret_remote.xml`, `open_adult.py`).
6. Stellt die gesicherten Logins wieder her (`restore_credentials()`).
7. Setzt die Kodi-21-Optimierungen (`general.addonupdates = 1`, `filecache.memorysize = 64`, `filecache.buffermode = 4`, `filecache.readfactor = 400`, `videoplayer.adjustrefreshrate = 2`) sowohl in `guisettings.xml` als auch live im laufenden Kodi-Prozess über JSON-RPC (`Settings.SetSettingValue`).
8. Aktiviert alle enthaltenen Add-ons per JSON-RPC (`Addons.SetAddonEnabled`), lädt Keymaps & Skin neu und bietet einen sauberen Kodi-Neustart an.

### B. Schnell-Update (`mode="quick"`)
* Entpackt aus dem gewählten Branch ausschließlich:
  * `userdata/keymaps/` (`player_controls.xml`)
  * `userdata/advancedsettings.xml`
  * `addons/skin.arctic.fuse.2/shortcuts/` & `1080i/`
  * `userdata/addon_data/script.skinvariables/nodes/skin.arctic.fuse.2/`
* Führt sofort `Action(reloadkeymaps)`, `RunScript(script.skinvariables,action=buildtemplate,force)` und `ReloadSkin()` aus – ohne dass Kodi neu gestartet werden muss.

---

## 4. 🔒 Automatischer Schutz von Trakt, YouTube & Stream-Historie

Damit du dich nach einem Update am Fernseher niemals neu bei Trakt oder YouTube anmelden musst, sichert [`backup_manager.py`](../kodi/addons/script.googletv.updater/resources/lib/backup_manager.py) vor jedem Update automatisch:
* **Trakt-Token (TMDb Helper):** `<setting id="trakt_token">...</setting>` aus `userdata/addon_data/plugin.video.themoviedb.helper/settings.xml`.
* **Trakt-Sync OAuth-Sitzung:** `userdata/addon_data/script.module.tmdbhelper.sync.trakt/settings.xml`.
* **YouTube TV-OAuth:** `access_manager.json`, `api_keys.json` und `settings.xml` aus `userdata/addon_data/plugin.video.youtube/`.
* **xStream Stream-Historie:** `userdata/addon_data/script.module.xstreamscraper/stream_history.json`.
* **Updater-Konfiguration:** `settings.xml` und `state.json` aus `userdata/addon_data/script.googletv.updater/`.

---

## 5. 💾 Lokaler Backup- & Rollback-Manager

Unter **`💾 Backup & Rollback Manager`** können jederzeit lokale Sicherungen auf dem Fernseher erstellt, wiederhergestellt oder gelöscht werden:
* Jedes Backup wird als platzsparendes ZIP-Archiv (`kodi_backup_YYYYMMDD_HHMMSS.zip`) inklusive `_backup_manifest.json` (Zeitstempel, Branch, Commit-Hash) abgelegt.
* Große Bild- und Datenbank-Caches (`crop/`, `blur/`, `simplecache/`, `database_v*`) werden beim Backup automatisch ausgelassen, um den Flash-Speicher der Google-TV-Box zu schonen.
* `prune_backups()` behält automatisch die letzten `3` Backups (in den Add-on-Einstellungen anpassbar).

---

## 6. 🔔 Automatische Update-Prüfung beim Kodi-Start (`service.py`)

Der Hintergrund-Service [`service.py`](../kodi/addons/script.googletv.updater/service.py) startet automatisch mit Kodi:
1. Wartet standardmäßig **15 Sekunden** (`startup_delay_seconds`), damit der Kodi-Start und das Laden der Startseiten-Widgets nicht verzögert werden.
2. Prüft `xbmc.Player().isPlaying()`: Läuft bereits ein Video, wird keine Meldung eingeblendet.
3. Vergleicht den neuesten Commit-Hash des aktiven Branches auf GitHub mit `installed_sha` in `userdata/addon_data/script.googletv.updater/state.json`.
4. Je nach Einstellung **`Beim Kodi-Start auf Updates prüfen`** (`startup_check_mode`):
   * **`0` – Aus (Nur manuell):** Keine Hintergrund-Abfrage beim Start.
   * **`1` – Prüfen & Hinweis anzeigen (Standard):** Zeigt bei einem neuen Commit einen Dialog mit Commit-Nachricht und fragt, ob das Update installiert werden soll.
   * **`2` – Automatisch installieren:** Lädt und installiert neue Commits auf dem eingestellten Branch automatisch im Hintergrund.
