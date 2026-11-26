# 🚀 Kodi Autostart, Standby Keep-Alive & Google TV Launcher-Ersetzung

Diese Dokumentation beschreibt im Detail, was die Skripte [`install.sh`](../install.sh) und [`autostart-kodi.sh`](../autostart-kodi.sh) auf Android-Systemebene via ADB konfigurieren, damit Kodi beim Einschalten des Fernsehers sofort verfügbar ist.

---

## 🧭 Funktions-Schnellindex

| Stufe / Funktion | Auslöser / Skript-Befehl | Beteiligte Datei & Funktion | Was technisch auf Android TV passiert |
| :--- | :--- | :--- | :--- |
| **[1. Warum Google-TV-Kacheln nicht Kodi öffnen](#1-technischer-hintergrund-android-tv-empfehlungs-intents)** | Systemverhalten von Google TV (`LauncherX`) | Android Package-Intents | Google-TV-Empfehlungen sind fest an Paketnamen wie `com.netflix.ninja` oder `com.amazon.avod.thirdpartyclient` verdrahtet und können ohne Root nicht auf `org.xbmc.kodi` umgebogen werden. |
| **[2. Stufe A: Standby Keep-Alive](#2-stufe-a-standby-keep-alive--doze-whitelist-automatisch)** | Automatisch bei `./install.sh` oder `./autostart-kodi.sh --keep-alive` | [`install.sh`](../install.sh) (Zeilen 229–234)<br>[`autostart-kodi.sh`](../autostart-kodi.sh) → `apply_keep_alive()` | Fügt `org.xbmc.kodi` zur Android-Doze-Whitelist hinzu und erlaubt `RUN_IN_BACKGROUND`, `RUN_ANY_IN_BACKGROUND` & `SYSTEM_ALERT_WINDOW`. Kodi wird im TV-Standby nicht mehr von Android beendet. |
| **[3. Stufe B: Kaltstart-Autostart & Projectivy-Rechte](#3-stufe-b-kaltstart-autostart--automatische-projectivy-berechtigungen)** | Projectivy Launcher + `./autostart-kodi.sh` | [`autostart-kodi.sh`](../autostart-kodi.sh) → `enable_projectivy_permissions()` (Zeilen 67–87) | Erkennt `com.spocky.projengmenu` und trägt dessen `AccessibilityService` sowie `SYSTEM_ALERT_WINDOW` vollautomatisch per ADB in Androids `settings put secure` ein. |
| **[4. Stufe C: Google-TV-Werbe-Launcher deaktivieren](#4-stufe-c-google-tv-standard-launcher-deaktivieren--wiederherstellen)** | `./autostart-kodi.sh --disable-google-launcher` | [`autostart-kodi.sh`](../autostart-kodi.sh) → `disable_google_launcher()` (Zeilen 89–120) | Prüft zwingend auf einen installierten Ersatz-Launcher (`ALT_LAUNCHERS`) und deaktiviert danach `com.google.android.apps.tv.launcherx` & `setupwraith` für `user 0` (ohne Root). |

---

## 1. 🧠 Technischer Hintergrund: Android TV Empfehlungs-Intents

Auf dem Werks-Startbildschirm von Google TV (`com.google.android.apps.tv.launcherx`) sind alle Film- und Serien-Vorschläge mit expliziten Android-App-Intents verknüpft (`com.amazon.avod.thirdpartyclient`, `com.netflix.ninja`, `com.disney.disneyplus`, `com.google.android.youtube.tv`).
* Das Android-Sicherheitssystem verhindert, dass eine Drittanbieter-App wie Kodi (`org.xbmc.kodi`) Intents abfängt, die explizit an einen fremden Paketnamen adressiert sind.
* Deshalb setzt dieses Projekt darauf, **Kodi dauerhaft im Vordergrund zu halten (Stufe A)** bzw. **direkt als Standard-Oberfläche beim Booten zu starten (Stufe B & C)**.

---

## 2. 🔋 Stufe A: Standby Keep-Alive & Doze-Whitelist (Automatisch)

Standardmäßig versetzt Android TV Apps nach einigen Minuten im Standby (Fernseher per Fernbedienung ausgeschaltet) in den Deep-Doze-Modus oder beendet sie bei Speicherdruck, sodass man beim Einschalten wieder auf dem Google-TV-Homescreen landet.

### Was im Code ([`install.sh`](../install.sh), Zeilen 229–234 & [`autostart-kodi.sh`](../autostart-kodi.sh), Zeilen 58–65) ausgeführt wird:
```bash
adb -s "$DEVICE_ID" shell "dumpsys deviceidle whitelist +org.xbmc.kodi"
adb -s "$DEVICE_ID" shell "cmd appops set org.xbmc.kodi RUN_IN_BACKGROUND allow"
adb -s "$DEVICE_ID" shell "cmd appops set org.xbmc.kodi RUN_ANY_IN_BACKGROUND allow"
adb -s "$DEVICE_ID" shell "cmd appops set org.xbmc.kodi SYSTEM_ALERT_WINDOW allow"
```

* **`dumpsys deviceidle whitelist +org.xbmc.kodi`:** Nimmt Kodi von der Android-Akku-/Standby-Optimierung (Doze Mode) aus.
* **`RUN_IN_BACKGROUND` & `RUN_ANY_IN_BACKGROUND`:** Erlaubt den Hintergrunddiensten von Kodi (`TMDb Helper`, `service.upnext`, `xStream`), auch bei ausgeschaltetem HDMI-Ausgang weiterzulaufen.
* **`SYSTEM_ALERT_WINDOW`:** Erlaubt Kodi das Zeichnen von Overlays und hält den Prozess in einer höheren Android-OOM-Prioritätsklasse.

---

## 3. ⚡ Stufe B: Kaltstart-Autostart & Automatische Projectivy-Berechtigungen

Wenn die Box komplett stromlos war (Kaltstart), startet Android zunächst den aktiven System-Launcher. Um Kodi auch nach einem Kaltstart automatisch zu öffnen:

1. Installiere aus dem Google Play Store auf dem Fernseher den kostenlosen **Projectivy Launcher** (`com.spocky.projengmenu`).
2. Stelle in Projectivy unter **Einstellungen → Power → Autostart on Boot** die App **`Kodi`** ein.

### Automatische Berechtigungs-Injektion durch [`autostart-kodi.sh`](../autostart-kodi.sh) (`enable_projectivy_permissions`, Zeilen 67–87)
Auf vielen Google-TV-Geräten ist das manuelle Aktivieren der Bedienungshilfen (Accessibility Service) für Projectivy in den Android-Systemeinstellungen verbuggt oder versteckt. Sobald `autostart-kodi.sh` das Paket `com.spocky.projengmenu` auf der Box erkennt, setzt es diese Systemrechte vollautomatisch per ADB:
1. Erlaubt Overlay-Rechte: `cmd appops set com.spocky.projengmenu SYSTEM_ALERT_WINDOW allow`
2. Liest `settings get secure enabled_accessibility_services` aus und hängt – falls noch nicht vorhanden – `com.spocky.projengmenu/com.spocky.projengmenu.services.AccessibilityService` an.
3. Aktiviert den Dienst global: `settings put secure accessibility_enabled 1`.

---

## 4. 🛡️ Stufe C: Google-TV-Standard-Launcher deaktivieren & wiederherstellen

Wenn du den werbelastigen Google-TV-Startbildschirm komplett abschalten möchtest, damit selbst die **Home-Taste** der Fernbedienung ausschließlich deinen eigenen Launcher bzw. Kodi nutzt:

```bash
./autostart-kodi.sh --disable-google-launcher
```

### Sicherheits-Check & Ablauf in `disable_google_launcher()` ([`autostart-kodi.sh`](../autostart-kodi.sh), Zeilen 89–120)
1. **Black-Screen-Schutz (`ALT_LAUNCHERS`, Zeilen 22–29 & 90–107):**
   Das Skript liest zuerst über `pm list packages` alle installierten Pakete aus und prüft, ob mindestens einer der folgenden alternativen Launcher installiert ist:
   * `com.spocky.projengmenu` (*Projectivy Launcher*)
   * `me.efesser.flauncher` (*FLauncher*)
   * `com.awe.dev.pro.tv` / `ca.dstudio.atvlauncher.pro` / `ca.dstudio.atvlauncher.free` (*ATV Launcher*)
   * `com.wolf.firelauncher` (*Wolf Launcher*)
   Ist **kein** alternativer Launcher installiert, bricht das Skript mit einem `SICHERHEITS-STOPP` (`exit 1`) ab, damit der Fernseher niemals ohne Homescreen (schwarzer Bildschirm) dasteht.
2. **Deaktivierung der Google-Launcher-Pakete (`GOOGLE_LAUNCHERS`, Zeilen 18–21 & 112–118):**
   Für den aktuellen Android-Nutzer (`--user 0`, benötigt kein Root) werden folgende Systempakete deaktiviert:
   ```bash
   adb -s "$DEVICE_ID" shell "pm disable-user --user 0 com.google.android.apps.tv.launcherx"
   adb -s "$DEVICE_ID" shell "pm disable-user --user 0 com.google.android.tungsten.setupwraith"
   ```

### Wiederherstellung des originalen Google-TV-Launchers (`restore_google_launcher()`, Zeilen 122–128)
Mit einem einzigen Befehl lässt sich der Werks-Startbildschirm jederzeit wieder aktivieren:
```bash
./autostart-kodi.sh --restore-google-launcher
```
Dies führt für beide Pakete `pm enable com.google.android.apps.tv.launcherx` und `pm enable com.google.android.tungsten.setupwraith` aus.

---

## 🛠️ Alle Aufruf-Parameter von `autostart-kodi.sh`

| Befehl | Funktion |
| :--- | :--- |
| `./autostart-kodi.sh` *(oder `./install.sh --autostart`)* | Öffnet das interaktive Auswahlmenü (`1–4`) im Terminal. |
| `./autostart-kodi.sh --keep-alive` | Setzt nur die Doze-Whitelist und Hintergrund-AppOps für Kodi (`Stufe A`). |
| `./autostart-kodi.sh --disable-google-launcher` | Setzt Keep-Alive, schaltet die Projectivy-Accessibility-Rechte frei und deaktiviert den Google-TV-Launcher (`Stufe A + B + C`). |
| `./autostart-kodi.sh --restore-google-launcher` | Aktiviert den originalen Google-TV-Startbildschirm wieder. |
