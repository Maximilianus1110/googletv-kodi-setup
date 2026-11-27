# 🔄 Google TV – Kodi Setup Updater (`script.googletv.updater`)

[![Kodi](https://img.shields.io/badge/Kodi-21.2%20Omega-blue.svg)](https://kodi.tv)
[![Platform](https://img.shields.io/badge/Platform-Google%20TV%20%7C%20Android%20TV-green.svg)](https://android.com/tv)
[![Target Repo](https://img.shields.io/badge/Setup%20Repo-googletv--kodi--setup-00bfa5.svg)](https://github.com/Maximilianus1110/googletv-kodi-setup)

Ein eigenständiges Kodi 21 (Omega) Programm- und Service-Add-on (`script.googletv.updater`), mit dem das komplette [**`googletv-kodi-setup`**](https://github.com/Maximilianus1110/googletv-kodi-setup) **direkt am Fernseher per Fernbedienung** über GitHub aktualisiert werden kann – ganz ohne PC oder ADB-Verbindung.

---

## ✨ Kernfunktionen

1. **🌿 Freie GitHub-Branch-Auswahl direkt am TV:**
   * Ruft über die GitHub REST API (`api.github.com/repos/<owner>/<repo>/branches`) live alle verfügbaren Branches inklusive des aktuellen Commit-Hashes (`short_sha`), Datums und der Commit-Nachricht ab.
   * Ermöglicht den jederzeitigen Wechsel zwischen `main` und Feature-/Test-Branches (inkl. manueller Eingabe beliebiger Branch-Namen) mit direkter Installations-Option.
2. **🚀 Zwei Update-Modi (Voll-Update & Schnell-Update):**
   * **Voll-Update (`mode="full"`):** Lädt das gesamte Branch-Archiv mit Live-Fortschrittsbalken (`MB / MB`) herunter, sichert vorab die bestehende Konfiguration, aktualisiert alle Add-ons & Userdata, räumt archivierte Alt-Komponenten auf, setzt die Kodi-21-Performance-Parameter (`64 MB` RAM-Cache, `24p`-Sync, `general.addonupdates = 1`) via JSON-RPC + `guisettings.xml` und aktiviert alle enthaltenen Add-ons.
   * **Schnell-Update (`mode="quick"`):** Aktualisiert in wenigen Sekunden ausschließlich die Fernbedienungs-Keymaps (`userdata/keymaps/`), `advancedsettings.xml` sowie die Arctic-Fuse-2-Shortcuts/Menüs und lädt Tastenbelegung (`Action(reloadkeymaps)`) und Skin (`ReloadSkin()`) ohne Kodi-Neustart sofort neu.
3. **🔒 Automatischer Schutz deiner Logins & Daten (wie in `install.sh`):**
   * **Trakt.tv:** Liest den bestehenden `trakt_token` aus `plugin.video.themoviedb.helper/settings.xml` sowie die OAuth-Sitzung aus `script.module.tmdbhelper.sync.trakt/settings.xml` vor dem Update aus und injiziert sie nach dem Entpacken wieder.
   * **YouTube TV-OAuth:** Bewahrt `access_manager.json`, `api_keys.json` und `settings.xml` von `plugin.video.youtube`.
   * **xStream Stream-Historie:** Bewahrt `stream_history.json` von `script.module.xstreamscraper`, damit bereits gesehene Streams/Hoster erhalten bleiben.
4. **💾 Integrierter Backup- & Rollback-Manager:**
   * Erstellt vor jedem Voll-Update (oder manuell per Klick) ein komprimiertes lokales ZIP-Backup (`userdata/keymaps`, `userdata/addon_data`, `userdata/advancedsettings.xml` – ohne große Bild-/Datenbank-Caches) unter `special://profile/addon_data/script.googletv.updater/backups/`.
   * Behält automatisch die letzten `N` Backups (Standard: `3`) und erlaubt per 1-Klick-Rollback die sofortige Wiederherstellung eines früheren Stands am Fernseher.
5. **🔔 Hintergrund-Update-Prüfung beim Kodi-Start (`service.py`):**
   * Prüft nach dem Kodi-Start (Standard: `15` Sekunden Verzögerung, nur wenn kein Video abgespielt wird) den gewählten Branch auf neue Commits.
   * Drei einstellbare Modi:
     * `Aus (Nur manuell)`
     * `Prüfen & Hinweis anzeigen` (Standard: zeigt Commit-Vergleich und fragt, ob aktualisiert werden soll)
     * `Automatisch installieren` (installiert neue Commits auf dem aktiven Branch automatisch im Hintergrund)
6. **🛠️ On-TV Wartung:**
   * Löscht per 1-Klick die 60-Minuten-Hoster-Fehlersperre (`stream_failures.json`), wofür bisher ein ADB-Befehl vom PC nötig war.

---

## 🎮 Bedienung am Fernseher (Arctic Fuse 2)

Das Add-on ist direkt in [**`googletv-kodi-setup`**](https://github.com/Maximilianus1110/googletv-kodi-setup) vorinstalliert und an zwei Stellen erreichbar:

1. **Über das Power-/System-Menü von Arctic Fuse 2:**
   * Auf der Startseite links unten auf das **Power-Symbol (`⏻`)** klicken → **`Setup Updater`** auswählen.
2. **Über die Programm-Add-ons:**
   * *Einstellungen → Add-ons → Programm-Add-ons → **Google TV Setup Updater***.

### Unterstützte `RunScript`-Parameter (für eigene Skin-Shortcuts / Keymaps)

```xml
<!-- Hauptmenü öffnen -->
<onclick>RunScript(script.googletv.updater)</onclick>

<!-- Direkt Voll-Update des aktiven Branches starten -->
<onclick>RunScript(script.googletv.updater,action=update)</onclick>

<!-- Direkt Schnell-Update (nur Keymaps & Skin) starten -->
<onclick>RunScript(script.googletv.updater,action=quick)</onclick>

<!-- Direkt die GitHub Branch-Auswahl öffnen -->
<onclick>RunScript(script.googletv.updater,action=branch)</onclick>

<!-- Direkt auf neue Commits prüfen -->
<onclick>RunScript(script.googletv.updater,action=check)</onclick>

<!-- Direkt den Backup & Rollback Manager öffnen -->
<onclick>RunScript(script.googletv.updater,action=backups)</onclick>
```

---

## 🗂️ Projektstruktur

| Datei | Aufgabe |
| :--- | :--- |
| [`addon.xml`](addon.xml) | Add-on-Manifest (`script.googletv.updater`, Programm-Add-on + Startup-Service, reine Python-3-Standardbibliothek ohne Drittanbieter-Abhängigkeiten). |
| [`default.py`](default.py) | Haupteinstiegspunkt für Menü-Aufrufe und `RunScript(script.googletv.updater,action=...)`-Parameter. |
| [`service.py`](service.py) | Hintergrund-Service beim Kodi-Start (`run_startup_check`) mit Abspiel-Schutz (`!Player().isPlaying()`). |
| [`resources/settings.xml`](resources/settings.xml) | Kodi-Einstellungen für GitHub-Owner/Repo, aktiven Branch, optionales GitHub-Token, Startup-Modus und Backup-/Login-Schutz. |
| [`resources/lib/github_api.py`](resources/lib/github_api.py) | GitHub REST API Client (`fetch_branches`, `fetch_branch_details`) & gestreamter ZIP-Downloader (`download_branch_zip`) mit Abbruch-Unterstützung. |
| [`resources/lib/installer.py`](resources/lib/installer.py) | Entpackt `kodi/addons` & `kodi/userdata` im Voll- oder Schnell-Modus, bereinigt Altlasten und patcht `guisettings.xml`. |
| [`resources/lib/backup_manager.py`](resources/lib/backup_manager.py) | Extrahiert und restauriert Trakt-/YouTube-Logins & Stream-Historie und verwaltet komprimierte lokale Rollback-Archive. |
| [`resources/lib/state.py`](resources/lib/state.py) | Speichert den aktuell installierten Branch, Commit-Hash (`SHA`) und Zeitstempel in `addon_data/script.googletv.updater/state.json`. |
| [`resources/lib/ui.py`](resources/lib/ui.py) | Kodi-Dialogführung (`xbmcgui.Dialog`, `DialogProgress`) sowie Live-Aktivierung über JSON-RPC (`Addons.SetAddonEnabled`, `Settings.SetSettingValue`, `ReloadSkin`). |
| [`tests/test_updater.py`](tests/test_updater.py) | Automatisierte Unit- und Integrations-Tests für GitHub-API, Credential-Erhalt, ZIP-Installation, Rollback und Service-Logik. |

---

## 🧪 Tests ausführen

```bash
python3 -m unittest discover -s tests -v
```
