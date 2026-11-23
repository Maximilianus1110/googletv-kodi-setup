# 🚀 Kodi direkt beim Start öffnen & Google TV Launcher ersetzen

Viele Nutzer fragen sich, warum der Standard-Startbildschirm von Google TV / Android TV Filme und Serien vorschlägt und ob sich diese Kacheln direkt in Kodi öffnen lassen – oder ob Kodi komplett zur Standard-Oberfläche werden kann.

---

## 1. Warum öffnen Google-TV-Vorschläge Prime Video, Netflix oder YouTube statt Kodi?

Auf dem Startbildschirm von Google TV sind die großen Empfehlungs-Kacheln fest an bestimmte Android-App-Pakete (`com.amazon.avod.thirdpartyclient`, `com.netflix.ninja`, `com.google.android.youtube.tv`) gebunden.

* **Technischer Hintergrund:** Android TV erlaubt es Drittanbieter-Apps wie Kodi aus Sicherheitsgründen **nicht**, explizite Paket-Intents anderer Apps abzufangen. Ein Klick auf eine Google-TV-Empfehlung springt daher immer direkt zu Prime/Netflix/YouTube (oder zeigt einen Play-Store-Hinweis).
* **Die saubere Lösung:** Anstatt auf dem überladenen Google-TV-Homescreen zu starten, wird **Kodi direkt zur Standard-Oberfläche** gemacht – mit deinen persönlichen **Trakt-, TMDb- & YouTube-Vorschlägen** direkt auf der Startseite!

---

## 2. Drei Stufen für „Kodi als Standard-Ansicht“

### Stufe A: Standby Keep-Alive (Automatisch bei `./install.sh`)
Bei jedem `./install.sh` setzt das Setup automatisch per ADB:
* Akku-Optimierung / Doze für Kodi deaktiviert (`dumpsys deviceidle whitelist +org.xbmc.kodi`)
* Hintergrundausführung dauerhaft erlaubt (`RUN_IN_BACKGROUND` & `RUN_ANY_IN_BACKGROUND`)

**Effekt:** Wenn du den Fernseher abends ausschaltest und am nächsten Tag wieder einschaltest, läuft Kodi einfach weiter – du landest sofort wieder in Kodi statt im Android-Menü.

---

### Stufe B: Kodi beim Kaltstart automatisch öffnen (Ohne Root – Empfohlen)
1. Installiere auf der Google-TV-Box aus dem **Google Play Store** die kostenlose App **„Projectivy Launcher“**.
2. Öffne Projectivy Launcher und aktiviere in den Einstellungen:
   * **General → Override current launcher** (über Bedienungshilfen / Accessibility)
   * **Power → Autostart on Boot:** `Kodi` auswählen
   * *(Optional)* **Buttons / Home-Taste:** Auf `Kodi` mappen, sodass selbst ein Druck auf die Home-Taste der Fernbedienung immer zurück in Kodi führt.

---

### Stufe C: Google-TV-Werbe-Launcher komplett deaktivieren (1-Klick via ADB)
Sobald **Projectivy Launcher** (oder *FLauncher* / *ATV Launcher*) auf der Box installiert ist, kannst du den Google-TV-Homescreen per Skript deaktivieren:

```bash
./autostart-kodi.sh --disable-google-launcher
```

> [!NOTE]
> **Sicherheits-Check eingebaut:** Das Skript prüft vorab, ob wirklich ein alternativer Launcher auf der Box installiert ist, damit du niemals vor einem schwarzen Bildschirm landest.

Falls du den originalen Google-TV-Startbildschirm irgendwann wieder zurückhaben möchtest:

```bash
./autostart-kodi.sh --restore-google-launcher
```

---

## 🛠️ Schnellbefehle

```bash
# Interaktives Menü für Autostart & Launcher-Verwaltung starten
./autostart-kodi.sh

# Oder direkt über den Installer aufrufen
./install.sh --autostart
```
