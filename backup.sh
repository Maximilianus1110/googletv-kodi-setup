#!/usr/bin/env bash
# ==============================================================================
# Google TV – Kodi Mediacenter Backup Utility
# Zieht die aktuelle Konfiguration und Keymaps vom TV auf den PC
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backups/kodi_backup_$(date +%Y%m%d_%H%M%S)"
REMOTE_KODI_DIR="/sdcard/Android/data/org.xbmc.kodi/files/.kodi"

echo "Erstelle lokales Backup in: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

if ! command -v adb &>/dev/null; then
    echo "Fehler: adb nicht installiert."
    exit 1
fi

DEVICE_ID=$(adb devices | grep -v "List" | grep "device$" | head -n 1 | awk '{print $1}' || true)
if [ -z "$DEVICE_ID" ]; then
    echo "Kein Gerät gefunden. Bitte per USB anschließen oder IP eingeben:"
    read -rp "IP: " TV_IP
    adb connect "${TV_IP}:5555"
    DEVICE_ID=$(adb devices | grep -v "List" | grep "device$" | head -n 1 | awk '{print $1}')
fi

echo "Sichere Keymaps..."
adb -s "$DEVICE_ID" pull "$REMOTE_KODI_DIR/userdata/keymaps" "$BACKUP_DIR/" || true

echo "Sichere Add-on-Einstellungen..."
adb -s "$DEVICE_ID" pull "$REMOTE_KODI_DIR/userdata/addon_data" "$BACKUP_DIR/" || true

echo "✓ Backup erfolgreich in $BACKUP_DIR abgeschlossen!"
