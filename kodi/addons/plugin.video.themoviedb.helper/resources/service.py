# -*- coding: utf-8 -*-
if __name__ == "__main__":
    from threading import Thread
    from tmdbhelper.lib.items.database.details.service import DetailsService
    from tmdbhelper.lib.monitor.service import ServiceMonitor
    t = Thread(target=lambda: DetailsService().run(), daemon=True)
    t.start()
    ServiceMonitor().run()
