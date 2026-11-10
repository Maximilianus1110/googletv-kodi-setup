import sys, os, io, traceback
from os.path import join
from xbmc import executebuiltin
from xbmcaddon import Addon


def run(action=None, payload=None, **parameters):
    if action == 'run_tmp':
        out_path = '/data/local/tmp/kodijob_out.txt'
        try:
            with open('/data/local/tmp/kodijob.py', 'r', encoding='utf-8') as f:
                code = f.read()
            from contextlib import redirect_stdout, redirect_stderr
            f_out = io.StringIO()
            with redirect_stdout(f_out), redirect_stderr(f_out):
                exec(code, {'__name__': '__main__'})
            output = f_out.getvalue()
            with open(out_path, 'w', encoding='utf-8') as out:
                out.write("SUCCESS\n" + output)
        except Exception as e:
            err_msg = traceback.format_exc()
            try:
                with open(out_path, 'w', encoding='utf-8') as out:
                    out.write(f"ERROR: {e}\n{err_msg}")
            except Exception:
                pass
        return

    if action == 'sync_shortcuts':
        import shutil, xbmcvfs, xbmc
        try:
            nodes_dir = xbmcvfs.translatePath("special://profile/addon_data/script.skinvariables/nodes/skin.arctic.fuse.2/")
            os.makedirs(nodes_dir, exist_ok=True)
            src_dir = xbmcvfs.translatePath("special://skin/shortcuts/")
            for name in ["skinvariables-shortcut-homemenu.json", "skinvariables-shortcut-sidemenu.json"]:
                s = os.path.join(src_dir, name)
                d = os.path.join(nodes_dir, name)
                shutil.copyfile(s, d)
            executebuiltin("Skin.Reset(script-skinvariables-generator-hash)")
            executebuiltin("Skin.Reset(script-skinvariables-generator-kodiprofile-8c34d337b002490eda7727171fcb9dbf-hash)")
            executebuiltin("Skin.Reset(Shortcuts.RebuildDateTime)")
            
            skinvar_path = xbmcvfs.translatePath("special://home/addons/script.skinvariables/")
            if skinvar_path not in sys.path:
                sys.path.insert(0, skinvar_path)
            from resources.lib.shortcuts.template.controller import ShortcutsTemplate
            st = ShortcutsTemplate(template=None)
            st.update_xml(force=True, no_reload=False)
            xbmc.log("SYNC_SHORTCUTS: Completed successfully!", xbmc.LOGINFO)
        except Exception as e:
            xbmc.log(f"SYNC_SHORTCUTS_ERROR: {e}\n{traceback.format_exc()}", xbmc.LOGERROR)
        return

    if action is None:
        executebuiltin(
            'RunScript(plugin.video.themoviedb.helper,configure_sync_provider,'
            'addon_id=script.module.tmdbhelper.sync.trakt)')
        return
    sys.path.insert(0, join(Addon('plugin.video.themoviedb.helper').getAddonInfo('path'), 'resources'))
    from tmdbhelper.lib.sync.providers.registry import SyncProviderRegistry
    provider = SyncProviderRegistry().find_provider('trakt')
    if provider is None:
        return
    if action in ('authenticate', 'revoke'):
        from tmdbhelper_sync_trakt.account import TraktAccountActions
        actions = TraktAccountActions(provider)
        return {'authenticate': actions.authenticate, 'revoke': actions.revoke}[action]()
    if payload is not None:
        from json import loads
        from urllib.parse import unquote
        parameters.update(loads(unquote(payload)))
    from tmdbhelper_sync_trakt.diagnostics import run_diagnostic
    return run_diagnostic(provider, action, **parameters)


if __name__ == '__main__':
    run(**dict(arg.split('=', 1) for arg in sys.argv[1:]))
