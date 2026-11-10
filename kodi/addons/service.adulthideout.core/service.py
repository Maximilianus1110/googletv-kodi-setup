import xbmc

def run_kodi_service():
    xbmc.log("[AdultHideoutCore] Service standby (native Python fallback mode active).", xbmc.LOGINFO)
    monitor = xbmc.Monitor()
    while not monitor.abortRequested():
        if monitor.waitForAbort(10):
            break

if __name__ == "__main__":
    run_kodi_service()
