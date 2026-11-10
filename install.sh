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

# 4. Backup des alten Setups erstellen
echo -e "\n${YELLOW}[3/5] Erstelle Backup der bisherigen Kodi-Konfiguration auf dem Gerät...${NC}"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
adb -s "$DEVICE_ID" shell "
if [ -d $REMOTE_KODI_DIR/userdata/keymaps ]; then
    mkdir -p /sdcard/kodi_backup_${BACKUP_DATE}
    cp -r $REMOTE_KODI_DIR/userdata/keymaps /sdcard/kodi_backup_${BACKUP_DATE}/ 2>/dev/null || true
fi
"
echo -e "${GREEN}✓ Sicherung abgelegt in: /sdcard/kodi_backup_${BACKUP_DATE}${NC}"

# 5. Dateien übertragen
echo -e "\n${YELLOW}[4/5] Übertrage optimierte Add-ons, Skin & Konfigurationen...${NC}"
STAGE_DIR="/sdcard/Download/kodi_setup_stage"
adb -s "$DEVICE_ID" shell "rm -rf $STAGE_DIR && mkdir -p $STAGE_DIR/addons $STAGE_DIR/userdata/keymaps $STAGE_DIR/userdata/addon_data"

echo -e "-> Übertrage Fernbedienungs-Keymaps (player_controls.xml, secret_remote.xml)..."
adb -s "$DEVICE_ID" push "$SCRIPT_DIR/kodi/userdata/keymaps/"* "$STAGE_DIR/userdata/keymaps/"

echo -e "-> Übertrage Addon-Einstellungen (TMDb Helper, xStream, Scraper, UpNext)..."
adb -s "$DEVICE_ID" push "$SCRIPT_DIR/kodi/userdata/addon_data/"* "$STAGE_DIR/userdata/addon_data/"

echo -e "-> Übertrage gepatchte Add-ons & Arctic Fuse 2 Skin (ca. 120 MB, bitte kurz warten)..."
adb -s "$DEVICE_ID" push "$SCRIPT_DIR/kodi/addons/"* "$STAGE_DIR/addons/"

echo -e "-> Installiere Dateien im Kodi-Hauptverzeichnis..."
adb -s "$DEVICE_ID" shell "
mkdir -p $REMOTE_KODI_DIR/addons $REMOTE_KODI_DIR/userdata/keymaps $REMOTE_KODI_DIR/userdata/addon_data
cp -rf $STAGE_DIR/* $REMOTE_KODI_DIR/
rm -rf $STAGE_DIR
"

# 6. Kodi neu starten
echo -e "\n${YELLOW}[5/5] Starte Kodi neu...${NC}"
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
echo -e " 2. ${YELLOW}YouTube verbinden (für persönliche Vorschläge):${NC}"
echo -e "    YouTube & SmartTube -> 'YouTube Konto verbinden'"
echo -e "    Code auf ${CYAN}https://google.com/device${NC} eingeben (ohne Sicherheitswarnung)."
echo -e ""
echo -e " 3. ${YELLOW}Erwachsenenbereich (+18 / XXX):${NC}"
echo -e "    PIN ist standardmäßig ${GREEN}0000${NC}."
echo -e "    Schnellaufruf: Halte die Zurück-Taste für 5 Sekunden gedrückt."
echo -e ""
echo -e "Ausführliche Anleitungen findest du im Ordner: ${BLUE}docs/${NC}"
echo -e "Viel Spaß mit deinem neuen Heimkino! 🍿"
