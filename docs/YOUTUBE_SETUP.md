# 📺 YouTube-Integration (Gepatchter TV-OAuth) & SmartTube-Brücke

> [!NOTE]
> Abweichungen zur früheren Kurz-Doku (z. B. welche YouTube-Widgets tatsächlich auf der Haupt-Startseite vs. im Untermenü *„YouTube & SmartTube“* liegen) sind in [**`docs/ABWEICHUNGEN_ALT_VS_CODE.md`**](ABWEICHUNGEN_ALT_VS_CODE.md) dokumentiert.

---

## 🧭 Funktions-Schnellindex

| Funktion | Auslöser | Beteiligte Dateien & Funktionen | Verhalten im Überblick |
| :--- | :--- | :--- | :--- |
| **[1. Gepatchter 1-Schritt TV-OAuth Login](#1-gepatchter-1-schritt-tv-oauth-login-yt_loginpy)** | Menüpunkt *„🔑 YouTube Konto verbinden (Sign-In)“* (`plugin://plugin.video.youtube/sign/in/`) | [`plugin.video.youtube/.../helper/yt_login.py`](../kodi/addons/plugin.video.youtube/resources/lib/youtube_plugin/youtube/helper/yt_login.py) → `_do_login()` (Zeile 74) | Fordert **nur ein einziges `tv`-Token** (`token_types = ['tv']`) an. Verhindert dadurch den zweiten Login-Schritt, den Google bei Drittanbieter-Desktop-Clients blockiert. |
| **[2. Persönliche Empfehlungen (`FEwhat_to_watch`)](#2-persnliche-youtube-empfehlungen-fewhat_to_watch--widgets)** | Automatisch in den Startseiten- und Hub-Widgets | [`plugin.video.youtube/.../helper/yt_specials.py`](../kodi/addons/plugin.video.youtube/resources/lib/youtube_plugin/youtube/helper/yt_specials.py) (Zeile 130)<br>[`skinvariables-shortcut-homemenu.json`](../kodi/userdata/addon_data/script.skinvariables/nodes/skin.arctic.fuse.2/skinvariables-shortcut-homemenu.json)<br>[`skinvariables-shortcut-sidemenu.json`](../kodi/userdata/addon_data/script.skinvariables/nodes/skin.arctic.fuse.2/skinvariables-shortcut-sidemenu.json) | Lädt über den TV-InnerTube-Feed `FEwhat_to_watch` deine echten persönlichen Startseiten-Vorschläge sowie Trends und Abonnements direkt in Arctic Fuse 2. |
| **[3. Native SmartTube-App starten](#3-direktstart-der-nativen-android-app-smarttube)** | Klick auf Seitenleisten-Eintrag *„YouTube & SmartTube“* | [`skinvariables-shortcut-sidemenu.json`](../kodi/userdata/addon_data/script.skinvariables/nodes/skin.arctic.fuse.2/skinvariables-shortcut-sidemenu.json) (Zeile 214) | Führt `StartAndroidActivity(org.smarttube.stable)` aus und wechselt nahtlos in die werbefreie Android-TV-App **SmartTube**. |

---

## 1. 🔑 Gepatchter 1-Schritt TV-OAuth Login (`yt_login.py`)

### Warum das unmodifizierte YouTube-Add-on bei Google scheitert
Im unmodifizierten Kodi YouTube-Add-on fordert `_do_login()` nacheinander **zwei OAuth-Tokens** an (eines für den TV-Client und eines für einen eigenen Desktop/Web-API-Key). Beim zweiten Code blockiert Google unzertifizierte OAuth-Clients mit der Fehlermeldung:
> *„Hat versucht auf vertrauliche Daten zuzugreifen – zu deinem Schutz haben wir den Zugriff blockiert.“*

### Was im Code ([`yt_login.py`](../kodi/addons/plugin.video.youtube/resources/lib/youtube_plugin/youtube/helper/yt_login.py), Zeilen 53–185) gepatcht wurde
1. **Beschränkung auf `token_types = ['tv']` (Zeile 74):**
   Die Schleife in `_do_login()` iteriert ausschließlich über `token_types = ['tv']` (`token_idx = 0`). Dadurch identifiziert sich Kodi gegenüber Google als offizieller **YouTube on TV**-Client.
2. **Geräte-Code-Abruf & 10-Minuten-Polling (Zeilen 97–160):**
   * `client.request_device_and_user_code(0)` holt von Google `device_code`, `user_code`, `interval` (Standard `5s`, gedeckelt auf max. `60s`) und die `verification_url` (Standard `google.com/device`, Fallback in Zeile 111: `youtube.com/activate`).
   * Öffnet einen Kodi-Fortschrittsdialog für **10 Minuten** (`steps = (10 * 60) // interval`, also 120 Abfragen im 5-Sekunden-Takt) und pollt `client.request_access_token(0, device_code)`.
   * Sobald du den Code auf dem Handy/PC bestätigt hast, speichert `access_manager.update_access_token()` das `access_token` und `refresh_token` für `tv` und schließt den Login nach diesem **einen** Code sofort ab.

### Schritt-für-Schritt-Anmeldung am Fernseher
1. Wähle in Kodi unter **YouTube & SmartTube** (oder im Untermenü von **Add-ons & Live-TV**) den Punkt **„🔑 YouTube Konto verbinden (Sign-In)“** (`RunPlugin(plugin://plugin.video.youtube/sign/in/)`).
2. Bestätige den Hinweis-Dialog mit **OK**.
3. Öffne auf deinem Smartphone oder PC die im Dialog angezeigte URL (in der Regel **[google.com/device](https://google.com/device)** bzw. **[youtube.com/activate](https://youtube.com/activate)**).
4. Gib den angezeigten **8-stelligen Code** ein und wähle dein Google-Konto aus.
5. Der Dialog in Kodi schließt sich innerhalb von 5 Sekunden automatisch – die Anmeldung ist fertig.

---

## 2. ⭐ Persönliche YouTube-Empfehlungen (`FEwhat_to_watch`) & Widgets

### Technischer Hintergrund (`yt_specials.py`)
In [`kodi/addons/plugin.video.youtube/resources/lib/youtube_plugin/youtube/helper/yt_specials.py`](../kodi/addons/plugin.video.youtube/resources/lib/youtube_plugin/youtube/helper/yt_specials.py) (Zeile 130) ruft der Pfad `plugin://plugin.video.youtube/special/recommendations/` über den angemeldeten TV-Client die YouTube-InnerTube-Browse-ID **`FEwhat_to_watch`** ab – exakt denselben persönlichen Startseiten-Feed wie die originale YouTube-App auf dem Smart-TV.

### Wo welches YouTube-Widget im Skin eingebunden ist
Laut [`skinvariables-shortcut-homemenu.json`](../kodi/userdata/addon_data/script.skinvariables/nodes/skin.arctic.fuse.2/skinvariables-shortcut-homemenu.json) und [`skinvariables-shortcut-sidemenu.json`](../kodi/userdata/addon_data/script.skinvariables/nodes/skin.arctic.fuse.2/skinvariables-shortcut-sidemenu.json) sind die Widgets wie folgt verteilt:

| Menübereich (Seitenleiste) | Eingebundene YouTube-Widget-Reihen | Interner Plugin-Pfad |
| :--- | :--- | :--- |
| **1. Entdecken / Start & Trends** *(Haupt-Startseite)* | • **⭐ Meine YouTube Vorschläge**<br>• **🔥 YouTube Trends** | `plugin://plugin.video.youtube/special/recommendations/`<br>`plugin://plugin.video.youtube/special/popular_right_now/` |
| **2. YouTube & SmartTube** *(Eigener Menü-Hub)* | • **⭐ Meine YouTube Vorschläge (Startseite)**<br>• **🔔 Meine Abonnements**<br>• **🔥 YouTube Trends** | `plugin://plugin.video.youtube/special/recommendations/`<br>`plugin://plugin.video.youtube/special/my_subscriptions/`<br>`plugin://plugin.video.youtube/special/popular_right_now/` |

*(Weitere Listen wie Wiedergabeverlauf, Später ansehen oder eigene Playlists sind über das Untermenü **„YouTube Add-on öffnen“** → `ActivateWindow(videos, plugin://plugin.video.youtube/, return)` direkt im Add-on erreichbar).*

---

## 3. 🚀 Direktstart der nativen Android-App „SmartTube“

* Der Hauptklick auf den Seitenleisten-Punkt **„YouTube & SmartTube“** (sowie der erste Untermenü-Punkt **„🚀 SmartTube App starten“**) führt folgenden nativen Kodi-Android-Befehl aus:
  ```text
  StartAndroidActivity(org.smarttube.stable)
  ```
* **Voraussetzung:** Die kostenlose Open-Source-App **SmartTube** (Paketname `org.smarttube.stable`) muss auf deiner Google-TV-/Android-TV-Box installiert sein.
* **Vorteil:** Während du deine persönlichen YouTube-Vorschläge und Trends direkt als Vorschau-Kacheln auf der Kodi-Startseite siehst, kannst du mit einem Klick für lange 4K-60fps-HDR-Videos oder SponsorBlock direkt in die native SmartTube-App wechseln.
