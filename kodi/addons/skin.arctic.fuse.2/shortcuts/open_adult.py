# -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import time

def main():
    dialog = xbmcgui.Dialog()
    pin = dialog.numeric(0, "PIN eingeben (0000)")
    if pin == "0000":
        home_win = xbmcgui.Window(10000)
        home_win.setProperty('adulthideout_auth_ts', str(time.time()))
        xbmc.executebuiltin("ActivateWindow(videos, plugin://plugin.video.adulthideout/, return)")
    elif pin:
        dialog.notification("Sicherheit", "Falscher PIN-Code", xbmcgui.NOTIFICATION_ERROR, 3000)

if __name__ == '__main__':
    main()
