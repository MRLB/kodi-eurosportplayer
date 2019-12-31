# coding: utf8

import sys
import xbmcgui
import xbmcplugin
import urllib
import urlparse
import xbmc
import xbmcaddon

import json
import datetime

import requests

reload(sys)
sys.setdefaultencoding('utf8')

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
#xbmcplugin.setContent(addon_handle, 'movies')

_addon_id      = 'plugin.video.eurosportplayer'
_addon         = xbmcaddon.Addon(id=_addon_id)
_addon_name    = _addon.getAddonInfo('name')
_addon_handler = int(sys.argv[1])
_addon_url     = sys.argv[0]
_addon_path    = xbmc.translatePath(_addon.getAddonInfo("path") )

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

mode = args.get('mode', None)

#Rohdaten
now = datetime.datetime.now()
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0'
header = {
    'Host': 'eu3-prod-direct.eurosportplayer.com',
    'User-Agent': user_agent,
    'Cookie': '[ausfuellen]',
}

#territory = 'de'
urlEPG = 'https://eu3-prod-direct.eurosportplayer.com/cms/routes/home?include=default'
urlMe = 'https://eu3-prod-direct.eurosportplayer.com/users/me'
urlStream1 = 'https://eu3-prod-direct.eurosportplayer.com/playback/v2/videoPlaybackInfo/'
urlStream2 = '?usePreAuth=true'

if mode is None:
    #Territory herausfinden
    meData = requests.get(url=urlMe, headers=header)
    meData = meData.json()

    territory = str(meData['data']['attributes']['verifiedHomeTerritory'])
    #print('ESP-Test' + str(meData['data']['attributes']['packages']))


    #Main auslesen:
    espplayerMain = requests.get(url=urlEPG, headers=header)
    espplayerMain = espplayerMain.json()
    i = 0
    i1 = 0
    availableInTerritory = False
    j = 0
    while i < len(espplayerMain['included']):
        # print(str(i))
        try:
            if espplayerMain['included'][i]['attributes']['videoType'] == 'LIVE':
                j = 0
                availableInTerritory = False
                while j < len(espplayerMain['included'][i]['attributes']['playableTerritories']['territories']):
                    if espplayerMain['included'][i]['attributes']['playableTerritories']['territories'][j] == territory:
                        availableInTerritory = True
                        break
                    j = j + 1
                if availableInTerritory:
                    #espplayerMain['included'][i]['attributes']['scheduleStart']
                    datetime_start = datetime.datetime(
                        int(espplayerMain['included'][i]['attributes']['availabilityWindows'][0]['playableStart'][:4]),
                        int(espplayerMain['included'][i]['attributes']['availabilityWindows'][0]['playableStart'][
                            5:7]), int(
                            espplayerMain['included'][i]['attributes']['availabilityWindows'][0]['playableStart'][8:10]), int(
                            espplayerMain['included'][i]['attributes']['availabilityWindows'][0]['playableStart'][11:13]), int(
                            espplayerMain['included'][i]['attributes']['availabilityWindows'][0]['playableStart'][14:16]), int(
                            espplayerMain['included'][i]['attributes']['availabilityWindows'][0]['playableStart'][17:19]))
                    #5 min vor Streamstart anzeigen
                    if (datetime.datetime.utcnow() - datetime_start > datetime.timedelta(seconds=-300)):
                        #Umrechnung Zeitzone
                        t = str(datetime.datetime.now() - datetime.datetime.utcnow())
                        h, m, s = t.split(':')
                        secondsDelta = int(
                            datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s)).total_seconds())
                        datetime_start_local = datetime_start + datetime.timedelta(seconds=secondsDelta)

                        sender = espplayerMain['included'][i]['attributes']['path'].split('/')

                        #endzeit
                        datetime_ende = datetime.datetime(
                            int(espplayerMain['included'][i]['attributes']['scheduleEnd'][
                                :4]),
                            int(espplayerMain['included'][i]['attributes']['scheduleEnd'][
                                5:7]), int(
                                espplayerMain['included'][i]['attributes']['scheduleEnd'][
                                8:10]), int(
                                espplayerMain['included'][i]['attributes']['scheduleEnd'][
                                11:13]), int(
                                espplayerMain['included'][i]['attributes']['scheduleEnd'][
                                14:16]), int(
                                espplayerMain['included'][i]['attributes']['scheduleEnd'][
                                17:19]))
                        datetime_ende_local = datetime_ende + datetime.timedelta(seconds=secondsDelta)

                        #Bild:
                        j = 0
                        while j < len(espplayerMain['included']):
                            if espplayerMain['included'][j]['id'] == espplayerMain['included'][i]['relationships']['images']['data'][0]['id']:
                                bildurl = espplayerMain['included'][j]['attributes']['src']
                                break
                            j = j + 1

                        foldername = str(str(i)+' '+str(datetime_start_local)[11:16]+' - '+str(datetime_ende_local)[11:16]+ ' Uhr: '+
                              sender[0]+': '+espplayerMain['included'][i]['attributes']['name'] +' ('+espplayerMain['included'][i]['attributes']['broadcastType']+ ') ('+espplayerMain['included'][i]['attributes']['materialType']+')')
                        url = build_url({'mode': 'playStream', 'foldername': foldername, 'streamID': espplayerMain['included'][i]['id']})
                        li = xbmcgui.ListItem(foldername, iconImage=bildurl)
                        li.setProperty('IsPlayable', 'true')
                        li.setInfo('video', {'plot': str(espplayerMain['included'][i]['attributes']['scheduleStart']+" - "+espplayerMain['included'][i]['attributes']['secondaryTitle'])})
                        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
                    # print(datetime.datetime.now())
        except KeyError:
            i1 = i1 + 1
        i = i + 1

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'playStream':
    urlStream = urlStream1 + args['streamID'][0] + urlStream2
    espplayerStream = requests.get(url=urlStream, headers=header)
    if str(espplayerStream) == '<Response [403]>':
        xbmcgui.Dialog().ok(_addon_name, "Stream hat noch nicht begonnen oder ist schon zu Ende")
        xbmcplugin.setResolvedUrl(_addon_handler, False, xbmcgui.ListItem())
    else:
        espplayerStream = espplayerStream.json()
        xbmc.log(str(espplayerStream))
        streamURL = str(espplayerStream['data']['attributes']['streaming']['mss'])
        xbmc.log('hierasd '+streamURL)
        #listitem = xbmcgui.ListItem(path=streamURL + "|" + user_agent)
        #listitem = xbmcgui.ListItem(path=streamURL)
        #listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
        #listitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        #listitem.setInfo('video', '')
        #listitem.setIsFolder(False)
        #listitem.setProperty('IsPlayable', 'true')
        #xbmcplugin.setResolvedUrl(_addon_handler, True, listitem)

        listitem = xbmcgui.ListItem()
        listitem.setContentLookup(False)
        listitem.setMimeType('application/dash+xml')
        listitem.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
        listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
        listitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        #listitem.setProperty('inputstream.adaptive.license_key', license_key)
        listitem.setPath(streamURL)
        #xbmc.Player().play(streamURL, listitem)
        xbmcplugin.setResolvedUrl(_addon_handler, True, listitem)