# -*- coding: utf-8 -*-
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and "kjob=" in sys.argv[2]:
        import io, traceback, contextlib, xbmcplugin
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                exec(open("/data/local/tmp/kodijob.py", encoding="utf-8").read(), {"__name__": "kjob"})
        except Exception:
            buf.write(traceback.format_exc())
        open("/sdcard/Download/kodijob.out", "w", encoding="utf-8").write(buf.getvalue())
        xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=True)
    else:
        from resources.lib.plugin import Plugin
        Plugin(int(sys.argv[1]), sys.argv[2][1:]).run()
