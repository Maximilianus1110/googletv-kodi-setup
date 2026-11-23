#!/usr/bin/env bash
# ==============================================================================
# Google TV – Kodi Mediacenter Setup Installer
# Überträgt das optimierte Kodi-Setup inklusive aller Patches, Keymaps & Add-ons
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KODI_PKG="org.xbmc.kodi"
REMOTE_KODI_DIR="/sdcard/Android/data/org.xbmc.kodi/files/.kodi"

# Prüfe Autostart-Flag (vor normalem Ablauf)
if [[ "${1:-}" == "--autostart" ]]; then
    shift
    exec "$SCRIPT_DIR/autostart-kodi.sh" "$@"
fi

echo -e "${BLUE}================================================================${NC}"
echo -e "${CYAN}🎬  Google TV & Android TV – Kodi Mediacenter Installer${NC}"
echo -e "${BLUE}================================================================${NC}"

# 1. Prüfe ADB Verfügbarkeit
if ! command -v adb &>/dev/null; then
    echo -e "${RED}Fehler: 'adb' wurde nicht auf deinem PC gefunden.${NC}"
    echo -e "Bitte installiere Android platform-tools (z. B. 'sudo pacman -S android-tools' oder 'sudo apt install adb')."
    exit 1
fi

# 2. Prüfe Geräte-Verbindung
echo -e "\n${YELLOW}[1/5] Suche nach verbundenem Android TV / Google TV Gerät...${NC}"
DEVICES=$(adb devices | grep -v "List" | grep "device$" || true)

if [ -z "$DEVICES" ]; then
    echo -e "${YELLOW}Kein Gerät direkt über USB gefunden.${NC}"
    read -rp "Möchtest du dich per WLAN verbinden? Gib die IP-Adresse des Fernsehers ein (oder Enter zum Abbruch): " TV_IP
    if [ -n "$TV_IP" ]; then
        echo -e "Verbinde mit ${CYAN}${TV_IP}:5555${NC}..."
        adb connect "${TV_IP}:5555"
    else
        echo -e "${RED}Abbruch. Bitte schließe das Gerät per USB an oder aktiviere ADB über Netzwerk.${NC}"
        exit 1
    fi
fi

DEVICE_ID=$(adb devices | grep -v "List" | grep "device$" | head -n 1 | awk '{print $1}')
echo -e "${GREEN}✓ Verbunden mit Gerät:${NC} ${CYAN}${DEVICE_ID}${NC}"

# Prüfe nur Keymaps-Flag
if [[ "${1:-}" == "--keymaps-only" ]]; then
    echo -e "\n${YELLOW}Übertrage nur die Fernbedienungs-Keymaps...${NC}"
    adb -s "$DEVICE_ID" shell "mkdir -p /sdcard/Download/kodi_stage/keymaps"
    adb -s "$DEVICE_ID" push "$SCRIPT_DIR/kodi/userdata/keymaps/"* "/sdcard/Download/kodi_stage/keymaps/"
    adb -s "$DEVICE_ID" shell "mkdir -p $REMOTE_KODI_DIR/userdata/keymaps && cp -rf /sdcard/Download/kodi_stage/keymaps/* $REMOTE_KODI_DIR/userdata/keymaps/ && rm -rf /sdcard/Download/kodi_stage"
    echo -e "${GREEN}✓ Keymaps erfolgreich aktualisiert!${NC}"
    exit 0
fi

# 3. Kodi Status prüfen & stoppen
echo -e "\n${YELLOW}[2/5] Prüfe Kodi-Installation...${NC}"
if ! adb -s "$DEVICE_ID" shell "pm list packages" | grep -q "$KODI_PKG"; then
    echo -e "${RED}Warnung: Kodi ('$KODI_PKG') ist auf dem Gerät noch nicht installiert!${NC}"
    echo -e "Bitte installiere Kodi 21.2 (Omega) zuerst über den Google Play Store oder per APK."
    read -rp "Möchtest du trotzdem fortfahren, sobald Kodi installiert ist? (j/n): " CONT
    if [[ "$CONT" != "j" && "$CONT" != "J" ]]; then
        exit 1
    fi
fi

echo -e "Beende Kodi für eine saubere Dateiübertragung..."
adb -s "$DEVICE_ID" shell "am force-stop $KODI_PKG" || true

# 4. Backup des alten Setups erstellen & bestehendes Trakt-Login auslesen
echo -e "\n${YELLOW}[3/5] Erstelle Backup der bisherigen Kodi-Konfiguration auf dem Gerät...${NC}"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
adb -s "$DEVICE_ID" shell "
mkdir -p /sdcard/kodi_backup_${BACKUP_DATE}
if [ -d $REMOTE_KODI_DIR/userdata/keymaps ]; then
    cp -r $REMOTE_KODI_DIR/userdata/keymaps /sdcard/kodi_backup_${BACKUP_DATE}/ 2>/dev/null || true
fi
if [ -d $REMOTE_KODI_DIR/userdata/addon_data ]; then
    cp -r $REMOTE_KODI_DIR/userdata/addon_data /sdcard/kodi_backup_${BACKUP_DATE}/ 2>/dev/null || true
fi
if [ -f $REMOTE_KODI_DIR/userdata/advancedsettings.xml ]; then
    cp $REMOTE_KODI_DIR/userdata/advancedsettings.xml /sdcard/kodi_backup_${BACKUP_DATE}/ 2>/dev/null || true
fi
"
echo -e "${GREEN}✓ Sicherung abgelegt in: /sdcard/kodi_backup_${BACKUP_DATE}${NC}"

EXISTING_TRAKT_TOKEN=$(adb -s "$DEVICE_ID" shell "sed -n 's/.*<setting id=\"trakt_token\"[^>]*>\(.*\)<\/setting>.*/\1/p' $REMOTE_KODI_DIR/userdata/addon_data/plugin.video.themoviedb.helper/settings.xml 2>/dev/null" | tr -d '\r' || true)
TMP_TRAKT_SYNC_SETTINGS=""
if adb -s "$DEVICE_ID" shell "test -s $REMOTE_KODI_DIR/userdata/addon_data/script.module.tmdbhelper.sync.trakt/settings.xml" >/dev/null 2>&1; then
    TMP_TRAKT_SYNC_SETTINGS=$(mktemp -t kodi_trakt_sync_settings.XXXXXX)
    if ! adb -s "$DEVICE_ID" pull "$REMOTE_KODI_DIR/userdata/addon_data/script.module.tmdbhelper.sync.trakt/settings.xml" "$TMP_TRAKT_SYNC_SETTINGS" >/dev/null 2>&1; then
        rm -f "$TMP_TRAKT_SYNC_SETTINGS"
        TMP_TRAKT_SYNC_SETTINGS=""
    fi
fi

# 5. Dateien übertragen
echo -e "\n${YELLOW}[4/5] Übertrage optimierte Add-ons, Skin & Konfigurationen...${NC}"
LOCKED_ADDONS=""
for addon_dir in plugin.video.themoviedb.helper service.upnext script.skinvariables; do
    if adb -s "$DEVICE_ID" shell "ls -ld $REMOTE_KODI_DIR/addons/$addon_dir 2>/dev/null" | grep -q "u0_a"; then
        LOCKED_ADDONS="${LOCKED_ADDONS} ${addon_dir}"
    fi
done
if [ -n "$LOCKED_ADDONS" ]; then
    echo -e "${RED}Warnung: Durch Kodi Auto-Updates unter Android 11+ gesperrte Add-on-Ordner gefunden:${NC}${YELLOW}${LOCKED_ADDONS}${NC}"
    echo -e "${YELLOW}Falls das Entpacken mit Permission Denied scheitert, diese Add-ons zuerst über Kodi deinstallieren/bereinigen oder Kodi-Daten neu initialisieren.${NC}"
fi
TRANSFER_OK=false
if command -v tar &>/dev/null && adb -s "$DEVICE_ID" shell "command -v tar" &>/dev/null; then
    echo -e "-> Übertrage gebündeltes Setup via tar-Archiv (deutlich schneller über WLAN/USB)..."
    TMP_TAR=$(mktemp -t kodi_setup_bundle.XXXXXX)
    if tar --exclude='__pycache__' --exclude='*.pyc' --exclude='.DS_Store' --exclude='script-skinvariables-generator-includes--kodiprofile-*.xml' -cf "$TMP_TAR" -C "$SCRIPT_DIR/kodi" addons userdata &&
       adb -s "$DEVICE_ID" push "$TMP_TAR" "/sdcard/Download/kodi_setup_bundle.tar" &&
       adb -s "$DEVICE_ID" shell "mkdir -p $REMOTE_KODI_DIR && tar -xf /sdcard/Download/kodi_setup_bundle.tar -C $REMOTE_KODI_DIR && rm -f /sdcard/Download/kodi_setup_bundle.tar"; then
        TRANSFER_OK=true
    else
        echo -e "${YELLOW}Hinweis: tar-Übertragung fehlgeschlagen, wechsle auf Standard-Übertragung...${NC}"
        adb -s "$DEVICE_ID" shell "rm -f /sdcard/Download/kodi_setup_bundle.tar" || true
    fi
    rm -f "$TMP_TAR"
fi

if [ "$TRANSFER_OK" != "true" ]; then
    STAGE_DIR="/sdcard/Download/kodi_setup_stage"
    adb -s "$DEVICE_ID" shell "rm -rf $STAGE_DIR && mkdir -p $STAGE_DIR/addons $STAGE_DIR/userdata/keymaps $STAGE_DIR/userdata/addon_data"

    echo -e "-> Übertrage Fernbedienungs-Keymaps (player_controls.xml, secret_remote.xml)..."
    adb -s "$DEVICE_ID" push "$SCRIPT_DIR/kodi/userdata/keymaps/"* "$STAGE_DIR/userdata/keymaps/"

    echo -e "-> Übertrage Addon-Einstellungen (TMDb Helper, xStream, Scraper, UpNext)..."
    adb -s "$DEVICE_ID" push "$SCRIPT_DIR/kodi/userdata/addon_data/"* "$STAGE_DIR/userdata/addon_data/"

    if [ -f "$SCRIPT_DIR/kodi/userdata/advancedsettings.xml" ]; then
        echo -e "-> Übertrage Performance-Einstellungen (advancedsettings.xml)..."
        adb -s "$DEVICE_ID" push "$SCRIPT_DIR/kodi/userdata/advancedsettings.xml" "$STAGE_DIR/userdata/"
    fi

    echo -e "-> Übertrage gepatchte Add-ons & Arctic Fuse 2 Skin (ca. 120 MB, bitte kurz warten)..."
    adb -s "$DEVICE_ID" push "$SCRIPT_DIR/kodi/addons/"* "$STAGE_DIR/addons/"

    echo -e "-> Installiere Dateien im Kodi-Hauptverzeichnis..."
    adb -s "$DEVICE_ID" shell "
mkdir -p $REMOTE_KODI_DIR/addons $REMOTE_KODI_DIR/userdata/keymaps $REMOTE_KODI_DIR/userdata/addon_data
cp -rf $STAGE_DIR/* $REMOTE_KODI_DIR/
rm -rf $STAGE_DIR
"
fi

if [ -n "$EXISTING_TRAKT_TOKEN" ]; then
    echo -e "-> Stelle vorhandenes Trakt-Login auf der Box wieder her..."
    TMP_TMDB_SETTINGS=$(mktemp -t kodi_tmdb_settings.XXXXXX)
    if command -v python3 &>/dev/null; then
        EXISTING_TRAKT_TOKEN="$EXISTING_TRAKT_TOKEN" python3 -c '
import os, re, sys
token = os.environ["EXISTING_TRAKT_TOKEN"]
with open(sys.argv[1], "r", encoding="utf-8") as f:
    content = f.read()
replacement = f"<setting id=\"trakt_token\">{token}</setting>"
content = re.sub(r"<setting id=\"trakt_token\"[^>]*(?:/>|>.*?</setting>)", lambda _: replacement, content)
with open(sys.argv[2], "w", encoding="utf-8") as f:
    f.write(content)
' "$SCRIPT_DIR/kodi/userdata/addon_data/plugin.video.themoviedb.helper/settings.xml" "$TMP_TMDB_SETTINGS"
    else
        ESCAPED_TOKEN=$(printf '%s\n' "$EXISTING_TRAKT_TOKEN" | sed 's/[&/|\\]/\\&/g')
        sed "s|<setting id=\"trakt_token\"[^>]*/>|<setting id=\"trakt_token\">${ESCAPED_TOKEN}</setting>|g; s|<setting id=\"trakt_token\"[^>]*>.*</setting>|<setting id=\"trakt_token\">${ESCAPED_TOKEN}</setting>|g" \
            "$SCRIPT_DIR/kodi/userdata/addon_data/plugin.video.themoviedb.helper/settings.xml" > "$TMP_TMDB_SETTINGS"
    fi
    adb -s "$DEVICE_ID" push "$TMP_TMDB_SETTINGS" "/sdcard/Download/kodi_tmdb_settings.xml" >/dev/null
    adb -s "$DEVICE_ID" shell "cp -f /sdcard/Download/kodi_tmdb_settings.xml $REMOTE_KODI_DIR/userdata/addon_data/plugin.video.themoviedb.helper/settings.xml && rm -f /sdcard/Download/kodi_tmdb_settings.xml"
    rm -f "$TMP_TMDB_SETTINGS"
    echo -e "${GREEN}✓ Bestehender Trakt-Token wurde übernommen!${NC}"
fi

if [ -n "$TMP_TRAKT_SYNC_SETTINGS" ] && [ -s "$TMP_TRAKT_SYNC_SETTINGS" ]; then
    echo -e "-> Stelle Trakt-Sync OAuth-Sitzung (script.module.tmdbhelper.sync.trakt) wieder her..."
    adb -s "$DEVICE_ID" push "$TMP_TRAKT_SYNC_SETTINGS" "/sdcard/Download/kodi_trakt_sync_settings.xml" >/dev/null
    adb -s "$DEVICE_ID" shell "mkdir -p $REMOTE_KODI_DIR/userdata/addon_data/script.module.tmdbhelper.sync.trakt && cp -f /sdcard/Download/kodi_trakt_sync_settings.xml $REMOTE_KODI_DIR/userdata/addon_data/script.module.tmdbhelper.sync.trakt/settings.xml && chmod 777 $REMOTE_KODI_DIR/userdata/addon_data/script.module.tmdbhelper.sync.trakt/settings.xml && rm -f /sdcard/Download/kodi_trakt_sync_settings.xml"
    rm -f "$TMP_TRAKT_SYNC_SETTINGS"
    echo -e "${GREEN}✓ Trakt-Sync OAuth-Credentials wurden übernommen!${NC}"
fi

if command -v python3 &>/dev/null && adb -s "$DEVICE_ID" shell "test -f $REMOTE_KODI_DIR/userdata/guisettings.xml" >/dev/null 2>&1; then
    TMP_GUI_SETTINGS=$(mktemp -t kodi_guisettings.XXXXXX)
    if adb -s "$DEVICE_ID" pull "$REMOTE_KODI_DIR/userdata/guisettings.xml" "$TMP_GUI_SETTINGS" >/dev/null 2>&1; then
        echo -e "-> Setze Auto-Update-Schutz, Kodi 21 Stream-Cache (64 MB) & 24p-Bildsync in guisettings.xml..."
        python3 -c '
import re, sys
path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    txt = f.read()
updates = {
    "general.addonupdates": "1",
    "filecache.buffermode": "4",
    "filecache.memorysize": "64",
    "filecache.readfactor": "400",
    "videoplayer.adjustrefreshrate": "2",
}
for key, val in updates.items():
    pat = rf"<setting id=\"{re.escape(key)}\"[^>]*(?:/>|>.*?</setting>)"
    repl = f"<setting id=\"{key}\">{val}</setting>"
    if re.search(pat, txt):
        txt = re.sub(pat, lambda _: repl, txt)
    else:
        txt = txt.replace("</settings>", f"    {repl}\n</settings>")
with open(path, "w", encoding="utf-8") as f:
    f.write(txt)
' "$TMP_GUI_SETTINGS"
        adb -s "$DEVICE_ID" push "$TMP_GUI_SETTINGS" "/sdcard/Download/kodi_guisettings.xml" >/dev/null
        adb -s "$DEVICE_ID" shell "cp -f /sdcard/Download/kodi_guisettings.xml $REMOTE_KODI_DIR/userdata/guisettings.xml && chmod 777 $REMOTE_KODI_DIR/userdata/guisettings.xml && rm -f /sdcard/Download/kodi_guisettings.xml"
        echo -e "${GREEN}✓ guisettings.xml optimiert (Updates=Notify, Cache=64 MB, 24p-Sync=2)!${NC}"
    fi
    rm -f "$TMP_GUI_SETTINGS"
fi

adb -s "$DEVICE_ID" shell "chmod -R 777 $REMOTE_KODI_DIR/addons $REMOTE_KODI_DIR/userdata 2>/dev/null || true"

# 6. Standby Keep-Alive setzen & Kodi neu starten
echo -e "\n${YELLOW}[5/5] Aktiviere Standby Keep-Alive & starte Kodi neu...${NC}"
adb -s "$DEVICE_ID" shell "dumpsys deviceidle whitelist +$KODI_PKG" >/dev/null 2>&1 || true
adb -s "$DEVICE_ID" shell "cmd appops set $KODI_PKG RUN_IN_BACKGROUND allow" >/dev/null 2>&1 || true
adb -s "$DEVICE_ID" shell "cmd appops set $KODI_PKG RUN_ANY_IN_BACKGROUND allow" >/dev/null 2>&1 || true
adb -s "$DEVICE_ID" shell "cmd appops set $KODI_PKG SYSTEM_ALERT_WINDOW allow" >/dev/null 2>&1 || true
adb -s "$DEVICE_ID" shell "am start -n $KODI_PKG/.Main"

echo -e "\n${GREEN}================================================================${NC}"
echo -e "${GREEN}🎉  Installation erfolgreich abgeschlossen!${NC}"
echo -e "${GREEN}================================================================${NC}"
echo -e ""
echo -e "${CYAN}Wichtige nächste Schritte für die Ersteinrichtung:${NC}"
echo -e " 1. ${YELLOW}Trakt verbinden (für 'Weiterschauen' wie Netflix):${NC}"
echo -e "    Add-ons -> TMDb Helper -> Einstellungen -> Trakt -> Konto autorisieren"
echo -e "    Code auf ${CYAN}https://trakt.tv/activate${NC} eingeben."
echo -e ""
echo -e " 2. ${YELLOW}YouTube Empfehlungen & SmartTube App:${NC}"
echo -e "    Öffne in Kodi das YouTube Add-on (einmalig) und melde dich über"
echo -e "    ${CYAN}https://google.com/device${NC} an (TV-OAuth ohne Sicherheitsblock)."
echo -e "    Alternativ öffnet 'YouTube & SmartTube' auch die werbefreie SmartTube-App."
echo -e ""
echo -e " 3. ${YELLOW}Erwachsenenbereich (+18 / XXX):${NC}"
echo -e "    PIN ist standardmäßig ${GREEN}0000${NC}."
echo -e "    Schnellaufruf: Halte die Zurück-Taste für 5 Sekunden gedrückt."
echo -e ""
echo -e "Ausführliche Anleitungen findest du im Ordner: ${BLUE}docs/${NC}"
echo -e "Viel Spaß mit deinem neuen Heimkino! 🍿"
