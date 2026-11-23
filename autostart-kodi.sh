#!/usr/bin/env bash
# ==============================================================================
# Google TV & Android TV – Kodi Autostart & Standby Keep-Alive Setup
# Sorgt dafür, dass Kodi nach dem Einschalten sofort startet, im Standby offen
# bleibt und optional der Google TV Werbe-Launcher ersetzt wird.
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

KODI_PKG="org.xbmc.kodi"
GOOGLE_LAUNCHERS=(
    "com.google.android.apps.tv.launcherx"
    "com.google.android.tungsten.setupwraith"
)
ALT_LAUNCHERS=(
    "com.spocky.projengmenu"   # Projectivy Launcher
    "me.efesser.flauncher"     # FLauncher
    "com.awe.dev.pro.tv"       # ATV Launcher Pro
    "ca.dstudio.atvlauncher.pro"
    "ca.dstudio.atvlauncher.free"
    "com.wolf.firelauncher"    # Wolf Launcher
)

connect_device() {
    if ! command -v adb &>/dev/null; then
        echo -e "${RED}Fehler: 'adb' wurde nicht auf deinem PC gefunden.${NC}"
        exit 1
    fi

    local devices
    devices=$(adb devices | grep -v "List" | grep "device$" || true)
    if [ -z "$devices" ]; then
        echo -e "${YELLOW}Kein Gerät direkt über USB gefunden.${NC}"
        read -rp "IP-Adresse der Google-TV-Box eingeben (oder Enter zum Abbruch): " TV_IP
        if [ -n "$TV_IP" ]; then
            adb connect "${TV_IP}:5555"
        else
            echo -e "${RED}Abbruch.${NC}"
            exit 1
        fi
    fi

    DEVICE_ID=$(adb devices | grep -v "List" | grep "device$" | head -n 1 | awk '{print $1}')
    if [ -z "$DEVICE_ID" ]; then
        echo -e "${RED}Kein verbundenes Gerät gefunden.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Verbunden mit Gerät:${NC} ${CYAN}${DEVICE_ID}${NC}"
}

apply_keep_alive() {
    echo -e "\n${YELLOW}Aktiviere Standby Keep-Alive & Hintergrundrechte für Kodi...${NC}"
    adb -s "$DEVICE_ID" shell "dumpsys deviceidle whitelist +${KODI_PKG}" >/dev/null 2>&1 || true
    adb -s "$DEVICE_ID" shell "cmd appops set ${KODI_PKG} RUN_IN_BACKGROUND allow" >/dev/null 2>&1 || true
    adb -s "$DEVICE_ID" shell "cmd appops set ${KODI_PKG} RUN_ANY_IN_BACKGROUND allow" >/dev/null 2>&1 || true
    adb -s "$DEVICE_ID" shell "cmd appops set ${KODI_PKG} SYSTEM_ALERT_WINDOW allow" >/dev/null 2>&1 || true
    echo -e "${GREEN}✓ Kodi bleibt im Standby aktiv und wird von Android nicht beendet.${NC}"
}

enable_projectivy_permissions() {
    local proj_pkg="com.spocky.projengmenu"
    if adb -s "$DEVICE_ID" shell "pm list packages" | grep -q "$proj_pkg"; then
        echo -e "${CYAN}-> Projectivy Launcher erkannt – erteile Overlay- & Bedienungshilfe-Rechte...${NC}"
        adb -s "$DEVICE_ID" shell "cmd appops set ${proj_pkg} SYSTEM_ALERT_WINDOW allow" >/dev/null 2>&1 || true
        local acc_svc="${proj_pkg}/com.spocky.projengmenu.services.AccessibilityService"
        local current_acc
        current_acc=$(adb -s "$DEVICE_ID" shell "settings get secure enabled_accessibility_services" 2>/dev/null | tr -d '\r' || true)
        if [[ "$current_acc" != *"$proj_pkg"* ]]; then
            local new_acc
            if [ -z "$current_acc" ] || [ "$current_acc" = "null" ]; then
                new_acc="$acc_svc"
            else
                new_acc="${current_acc}:${acc_svc}"
            fi
            adb -s "$DEVICE_ID" shell "settings put secure enabled_accessibility_services '${new_acc}'" >/dev/null 2>&1 || true
            adb -s "$DEVICE_ID" shell "settings put secure accessibility_enabled 1" >/dev/null 2>&1 || true
        fi
        echo -e "${GREEN}✓ Projectivy-Berechtigungen gesetzt (für automatischen Start in Kodi & Home-Taste).${NC}"
    fi
}

disable_google_launcher() {
    echo -e "\n${YELLOW}Prüfe installierte alternative Launcher (Sicherheits-Check)...${NC}"
    local installed_pkgs
    installed_pkgs=$(adb -s "$DEVICE_ID" shell "pm list packages" | tr -d '\r')
    local found_alt=""
    for pkg in "${ALT_LAUNCHERS[@]}"; do
        if echo "$installed_pkgs" | grep -q "package:${pkg}"; then
            found_alt="$pkg"
            break
        fi
    done

    if [ -z "$found_alt" ] && ! echo "$installed_pkgs" | grep -qiE "flauncher|atvlauncher|wolf|projengmenu"; then
        echo -e "${RED}SICHERHEITS-STOPP: Kein alternativer Launcher (z. B. Projectivy Launcher) gefunden!${NC}"
        echo -e "Wenn der Google-TV-Launcher ohne Ersatz deaktiviert wird, bleibt nur ein schwarzer Bildschirm."
        echo -e "Bitte installiere zuerst ${CYAN}Projectivy Launcher${NC} aus dem Google Play Store auf der Box,"
        echo -e "stelle dort ${YELLOW}Autostart -> Kodi${NC} ein und führe dieses Skript danach erneut aus."
        exit 1
    fi

    echo -e "${GREEN}✓ Alternativer Launcher gefunden (${found_alt:-erkannt}).${NC}"
    enable_projectivy_permissions

    echo -e "${YELLOW}Deaktiviere Standard Google-TV-Launcher (ohne Root)...${NC}"
    for gpkg in "${GOOGLE_LAUNCHERS[@]}"; do
        if echo "$installed_pkgs" | grep -q "package:${gpkg}"; then
            adb -s "$DEVICE_ID" shell "pm disable-user --user 0 ${gpkg}" || true
        fi
    done
    echo -e "${GREEN}✓ Google-TV-Launcher deaktiviert! Ab sofort ist dein eigener Launcher / Kodi Standard.${NC}"
    echo -e "${CYAN}Hinweis:${NC} Zum Rückgängigmachen einfach ${YELLOW}./autostart-kodi.sh --restore-google-launcher${NC} ausführen."
}

restore_google_launcher() {
    echo -e "\n${YELLOW}Stelle Standard Google-TV-Launcher wieder her...${NC}"
    for gpkg in "${GOOGLE_LAUNCHERS[@]}"; do
        adb -s "$DEVICE_ID" shell "pm enable ${gpkg}" 2>/dev/null || true
    done
    echo -e "${GREEN}✓ Google-TV-Launcher wurde wieder aktiviert.${NC}"
}

MODE="${1:-}"
connect_device

case "$MODE" in
    --keep-alive)
        apply_keep_alive
        ;;
    --disable-google-launcher)
        apply_keep_alive
        disable_google_launcher
        ;;
    --restore-google-launcher)
        restore_google_launcher
        ;;
    "")
        echo -e "${BLUE}================================================================${NC}"
        echo -e "${CYAN}🚀  Google TV – Kodi Autostart & Launcher-Manager${NC}"
        echo -e "${BLUE}================================================================${NC}"
        echo " 1) Standby Keep-Alive aktivieren (Kodi bleibt im Standby immer offen)"
        echo " 2) Google-TV-Launcher deaktivieren + Keep-Alive (Projectivy/FLauncher muss installiert sein!)"
        echo " 3) Google-TV-Launcher wiederherstellen"
        echo " 4) Abbrechen"
        echo ""
        read -rp "Auswahl [1-4]: " CHOICE
        case "$CHOICE" in
            1)
                apply_keep_alive
                ;;
            2)
                apply_keep_alive
                disable_google_launcher
                ;;
            3)
                restore_google_launcher
                ;;
            *)
                echo "Abgebrochen."
                exit 0
                ;;
        esac
        ;;
    *)
        echo "Verwendung: $0 [--keep-alive | --disable-google-launcher | --restore-google-launcher]"
        exit 1
        ;;
esac
