# -*- coding: utf-8 -*-
import xbmc, xbmcgui

player = xbmc.Player()
if not player.isPlayingVideo():
    xbmcgui.Dialog().notification("Intro Skip", "Kein Video wird abgespielt", xbmcgui.NOTIFICATION_INFO)
else:
    curr_time = player.getTime()
    total_time = player.getTotalTime()
    win = xbmcgui.Window(10000)
    target_time = None

    # Check if online intro end time is known
    intro_end = win.getProperty("Intro_EndTime")
    if intro_end:
        try:
            val = float(intro_end)
            if val > curr_time:
                target_time = val
        except Exception:
            pass

    # Fallback to standard +85s intro skip
    if not target_time:
        target_time = min(curr_time + 85.0, max(0.0, total_time - 10.0))

    player.seekTime(target_time)
    mins = int(target_time // 60)
    secs = int(target_time % 60)
    xbmcgui.Dialog().notification("⏩ Intro übersprungen", f"Fortgesetzt bei {mins:02d}:{secs:02d}", xbmcgui.NOTIFICATION_INFO, 2000)
