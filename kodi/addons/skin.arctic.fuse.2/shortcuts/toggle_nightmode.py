# -*- coding: utf-8 -*-
import xbmc, xbmcgui

win = xbmcgui.Window(10000)
is_active = win.getProperty("NightMode_Active") == "true"

if not is_active:
    # Activate Night Mode: Boost speech by +10dB and compress loud peaks
    for _ in range(10):
        xbmc.executebuiltin("Action(volampup)")
    win.setProperty("NightMode_Active", "true")
    xbmcgui.Dialog().notification("🌙 Nachtmodus", "Aktiviert (+10 dB Dialog-Boost & DRC)", xbmcgui.NOTIFICATION_INFO, 2500)
else:
    # Deactivate Night Mode: Return to standard dynamic range
    for _ in range(10):
        xbmc.executebuiltin("Action(volampdown)")
    win.setProperty("NightMode_Active", "false")
    xbmcgui.Dialog().notification("☀️ Normalmodus", "Deaktiviert (0 dB Standard)", xbmcgui.NOTIFICATION_INFO, 2500)
