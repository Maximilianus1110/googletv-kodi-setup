# -*- coding: utf-8 -*-
import xbmc, xbmcgui

player = xbmc.Player()
if not player.isPlayingVideo():
    xbmcgui.Dialog().notification("xStream", "Kein Video wird abgespielt", xbmcgui.NOTIFICATION_INFO)
else:
    info_tag = player.getVideoInfoTag()
    tmdb_id = info_tag.getUniqueID('tmdb')
    tv_tmdb_id = info_tag.getUniqueID('tvshow.tmdb')
    media_type = info_tag.getMediaType()
    season = info_tag.getSeason()
    episode = info_tag.getEpisode()
    curr_time = int(player.getTime())

    home_win = xbmcgui.Window(10000)
    if not tmdb_id:
        tmdb_id = home_win.getProperty("TMDbHelper.playing.tmdb_id") or home_win.getProperty("TMDbHelper.ListItem.tmdb_id")
    if not tv_tmdb_id:
        tv_tmdb_id = home_win.getProperty("TMDbHelper.playing.tvshow.tmdb_id") or tmdb_id

    if (not season or season <= 0) and home_win.getProperty("TMDbHelper.playing.season"):
        try: season = int(home_win.getProperty("TMDbHelper.playing.season"))
        except: pass

    if (not episode or episode <= 0) and home_win.getProperty("TMDbHelper.playing.episode"):
        try: episode = int(home_win.getProperty("TMDbHelper.playing.episode"))
        except: pass

    is_episode = (media_type == "episode") or (season > 0 and episode > 0)
    _type = "tv" if is_episode else "movie"
    _id = tv_tmdb_id if is_episode else tmdb_id

    if not _id:
        _id = xbmc.getInfoLabel('VideoPlayer.UniqueId(tvshow.tmdb)') or xbmc.getInfoLabel('VideoPlayer.UniqueId(tmdb)')

    if not _id:
        xbmcgui.Dialog().notification("Stream wechseln", "TMDb-ID nicht gefunden", xbmcgui.NOTIFICATION_WARNING)
    else:
        # Pause playback while dialog is open
        if not xbmc.getCondVisibility("Player.Paused"):
            player.pause()
        if _type == "tv":
            xbmc.executebuiltin(f"RunPlugin(plugin://script.module.xstreamscraper/?id={_id}&season={season}&episode={episode}&select=true&resume={curr_time})")
        else:
            xbmc.executebuiltin(f"RunPlugin(plugin://script.module.xstreamscraper/?id={_id}&select=true&resume={curr_time})")
