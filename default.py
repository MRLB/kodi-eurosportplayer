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
_addon_path    = xbmc.translatePath(_addon.getAddonInfo('path') )

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

def availableInTerritoryCheck(i,id):
    j = 0
    availableInTerritory = False
    if id == 0:
        while j < len(espplayerMain['included'][i]['attributes']['playableTerritories']['territories']):
            if espplayerMain['included'][i]['attributes']['playableTerritories']['territories'][j] == territory:
                availableInTerritory = True
                break
            j = j + 1
    elif id == 1:
        while j < len(espplayerArchiveAuswahl['included'][i]['attributes']['playableTerritories']['territories']):
            if espplayerArchiveAuswahl['included'][i]['attributes']['playableTerritories']['territories'][j] == territory:
                availableInTerritory = True
                break
            j = j + 1
    elif id == 2:
        while j < len(espplayerSchedule['included'][i]['attributes']['playableTerritories']['territories']):
            if espplayerSchedule['included'][i]['attributes']['playableTerritories']['territories'][j] == territory:
                availableInTerritory = True
                break
            j = j + 1
    return availableInTerritory

def zeitformatierung(time):
    return datetime.datetime(int(time[:4]),
    int(time[
        5:7]), int(
        time[8:10]), int(
        time[11:13]), int(
        time[14:16]), int(
        time[17:19]))

def bildurlherausfinden(i, id):
    j = 0
    if id == 0:
        while j < len(espplayerMain['included']):
            if espplayerMain['included'][j]['id'] == espplayerMain['included'][i]['relationships']['images']['data'][0][
                'id']:
                bildurl = espplayerMain['included'][j]['attributes']['src']
                break
            j = j + 1
    elif id == 1:
        while j < len(espplayerArchiveAuswahl['included']):
            if espplayerArchiveAuswahl['included'][j]['id'] == espplayerArchiveAuswahl['included'][i]['relationships']['images']['data'][0][
                'id']:
                bildurl = espplayerArchiveAuswahl['included'][j]['attributes']['src']
                break
            j = j + 1
    elif id == 2:
        while j < len(espplayerSchedule['included']):
            if espplayerSchedule['included'][j]['id'] == \
                    espplayerSchedule['included'][i]['relationships']['images']['data'][0][
                        'id']:
                bildurl = espplayerSchedule['included'][j]['attributes']['src']
                break
            j = j + 1
    return bildurl

def umrechnungZeitzoneUnterschiedSekunden():
    # Umrechnung Zeitzone
    t = str(datetime.datetime.now() - datetime.datetime.utcnow())
    h, m, s = t.split(':')
    secondsDelta = int(h) * 60 * 60 + int(m) * 60
    # +int (s) ; macht mit Android probleme
    return secondsDelta

def createOrdner(mode, foldername):
    url = build_url(
        {'mode': mode, 'foldername': foldername})
    li = xbmcgui.ListItem(foldername, iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

def createOrdnerwithURL(mode, foldername, url):
    url = build_url(
        {'mode': mode, 'foldername': foldername, 'url': url})
    li = xbmcgui.ListItem(foldername, iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

mode = args.get('mode', None)

#Rohdaten
now = datetime.datetime.now()
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0'
header = {
    'Host': 'eu3-prod-direct.eurosportplayer.com',
    'User-Agent': user_agent,
    'Cookie': '[Cookie hier eintragen]',
}

#territory = 'de'
urlEPG = 'https://eu3-prod-direct.eurosportplayer.com/cms/routes/home?include=default'
urlMe = 'https://eu3-prod-direct.eurosportplayer.com/users/me'
urlStream1 = 'https://eu3-prod-direct.eurosportplayer.com/playback/v2/videoPlaybackInfo/'
urlStream2 = '?usePreAuth=true'
urlArchiveAuswahl = 'https://eu3-prod-direct.eurosportplayer.com/cms/routes/on-demand?include=default'
urlStart = 'https://eu3-prod-direct.eurosportplayer.com/cms/routes'
urlSchedule = 'https://eu3-prod-direct.eurosportplayer.com/cms/routes/schedule?include=default'

if mode is None:
    #Territory herausfinden
    meData = requests.get(url=urlMe, headers=header)
    meData = meData.json()

    #try:
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
                if availableInTerritoryCheck(i,0):
                    #espplayerMain['included'][i]['attributes']['scheduleStart']
                    datetime_start = zeitformatierung(espplayerMain['included'][i]['attributes']['availabilityWindows'][0]['playableStart'])
                    #5 min vor Streamstart anzeigen
                    if (datetime.datetime.utcnow() - datetime_start > datetime.timedelta(seconds=-300)):
                        datetime_start_local = datetime_start + datetime.timedelta(seconds=int(umrechnungZeitzoneUnterschiedSekunden()))
                        sender = espplayerMain['included'][i]['attributes']['path'].split('/')

                        #endzeit
                        datetime_ende = zeitformatierung(espplayerMain['included'][i]['attributes']['scheduleEnd'])
                        datetime_ende_local = datetime_ende + datetime.timedelta(seconds=umrechnungZeitzoneUnterschiedSekunden())

                        if espplayerMain['included'][i]['attributes']['broadcastType'] == 'LIVE':
                            foldername = str(
                                espplayerMain['included'][i]['attributes']['broadcastType']+' - '+str(datetime_start_local)[11:16] + ' - ' + str(datetime_ende_local)[11:16] + ' Uhr: ' +
                                sender[0] + ': ' + espplayerMain['included'][i]['attributes']['name'] + ' (' +
                                espplayerMain['included'][i]['attributes']['materialType'] + ')')
                        else:
                            foldername = str(str(datetime_start_local)[11:16]+' - '+str(datetime_ende_local)[11:16]+ ' Uhr: '+
                              sender[0]+': '+espplayerMain['included'][i]['attributes']['name'] +' ('+espplayerMain['included'][i]['attributes']['broadcastType']+ ') ('+espplayerMain['included'][i]['attributes']['materialType']+')')
                        url = build_url({'mode': 'playStream', 'foldername': foldername, 'streamID': espplayerMain['included'][i]['id']})
                        li = xbmcgui.ListItem(foldername, iconImage=bildurlherausfinden(i,0))
                        li.setProperty('IsPlayable', 'true')
                        li.setInfo('video', {'plot': str(espplayerMain['included'][i]['attributes']['scheduleStart']+' - '+espplayerMain['included'][i]['attributes']['secondaryTitle'])})
                        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
                    # print(datetime.datetime.now())
        except KeyError:
            i1 = i1 + 1
        i = i + 1
    createOrdner('Archive', 'Archive')

    'Schedule:'
    foldername = '--------------------------------------'
    li = xbmcgui.ListItem(foldername, iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url='', listitem=li)

    createOrdner('Schedule', 'Schedule Eurosport 1')
    createOrdner('Schedule', 'Schedule Eurosport 2')

    foldername = '--------------------------------------'
    li = xbmcgui.ListItem(foldername, iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url='', listitem=li)

    foldername ='Nächste Liveevents:'
    li = xbmcgui.ListItem(foldername, iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url='', listitem=li)

    espplayerSchedule = requests.get(url=urlSchedule, headers=header)
    espplayerSchedule = espplayerSchedule.json()
    i = 0
    i1 = 0
    availableInTerritory = False
    j = 0
    while i < len(espplayerSchedule['included']):
        # print(str(i))
        try:
            if espplayerSchedule['included'][i]['attributes']['broadcastType'] == 'LIVE':
                if availableInTerritoryCheck(i, 2):
                    datetime_start = zeitformatierung(
                        espplayerSchedule['included'][i]['attributes']['availabilityWindows'][0]['playableStart'])
                    # 5 min vor Streamstart anzeigen
                    if (datetime.datetime.utcnow() - datetime_start < datetime.timedelta(seconds=-299)):
                        datetime_start_local = datetime_start + datetime.timedelta(
                            seconds=int(umrechnungZeitzoneUnterschiedSekunden()))

                        sender = espplayerSchedule['included'][i]['attributes']['path'].split('/')

                        # endzeit
                        datetime_ende = zeitformatierung(espplayerSchedule['included'][i]['attributes']['scheduleEnd'])
                        datetime_ende_local = datetime_ende + datetime.timedelta(
                            seconds=umrechnungZeitzoneUnterschiedSekunden())

                        foldername = str(
                            str(datetime_start_local)[8:10]+'.'+str(datetime_start_local)[5:7]+'.'+str(datetime_start_local)[0:4]+' '+str(datetime_start_local)[11:16] + ' - ' + str(datetime_ende_local)[11:16] + ' Uhr: ' +
                            sender[0] + ': ' + espplayerSchedule['included'][i]['attributes']['name'] + ' (' +
                            espplayerSchedule['included'][i]['attributes']['materialType'] + ')')

                        url = build_url({'mode': 'playStream', 'foldername': foldername,
                                         'streamID': espplayerSchedule['included'][i]['id']})
                        li = xbmcgui.ListItem(foldername, iconImage=bildurlherausfinden(i, 2))
                        li.setProperty('IsPlayable', 'true')
                        li.setInfo('video', {'plot': str(
                            espplayerSchedule['included'][i]['attributes']['scheduleStart'] + ' - ' +
                            espplayerSchedule['included'][i]['attributes']['secondaryTitle'])})
                        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
        except KeyError:
            i1 = i1 + 1
        i = i + 1



    xbmcplugin.endOfDirectory(addon_handle)

    #except:
    #    xbmcgui.Dialog().ok(_addon_name, str(meData))
    #    xbmcplugin.setResolvedUrl(_addon_handler, False, xbmcgui.ListItem())

elif mode[0] == 'Schedule':
    if args['foldername'][0] == 'Schedule Eurosport 1':
        suchsender = 'eurosport-1'
        foldername = 'Schedule Eurosport 1:'
        li = xbmcgui.ListItem(foldername, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url='', listitem=li)

    elif args['foldername'][0] == 'Schedule Eurosport 2':
        suchsender = 'eurosport-2'
        foldername ='Schedule Eurosport 2:'
        li = xbmcgui.ListItem(foldername, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url='', listitem=li)
    else:
        suchsender = ''
        foldername = 'Error'
        li = xbmcgui.ListItem(foldername, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url='', listitem=li)

    espplayerSchedule = requests.get(url=urlSchedule, headers=header)
    espplayerSchedule = espplayerSchedule.json()
    i = 0
    i1 = 0
    availableInTerritory = False
    j = 0
    while i < len(espplayerSchedule['included']):
        # print(str(i))
        try:
            sender = espplayerSchedule['included'][i]['attributes']['path'].split('/')
            if sender[0][0:11] == suchsender:
                if availableInTerritoryCheck(i, 2):
                    datetime_start = zeitformatierung(
                        espplayerSchedule['included'][i]['attributes']['availabilityWindows'][0]['playableStart'])
                    # 5 min vor Streamstart anzeigen
                    if (datetime.datetime.utcnow() - datetime_start < datetime.timedelta(seconds=-299)):
                        datetime_start_local = datetime_start + datetime.timedelta(
                            seconds=int(umrechnungZeitzoneUnterschiedSekunden()))

                        sender = espplayerSchedule['included'][i]['attributes']['path'].split('/')

                        # endzeit
                        datetime_ende = zeitformatierung(espplayerSchedule['included'][i]['attributes']['scheduleEnd'])
                        datetime_ende_local = datetime_ende + datetime.timedelta(
                            seconds=umrechnungZeitzoneUnterschiedSekunden())

                        foldername = str(
                            str(datetime_start_local)[8:10]+'.'+str(datetime_start_local)[5:7]+'.'+str(datetime_start_local)[0:4]+' '+str(datetime_start_local)[11:16] + ' - ' + str(datetime_ende_local)[11:16] + ' Uhr: ' +
                            espplayerSchedule['included'][i]['attributes']['name'] + ' ('+sender[0] + ')')

                        url = build_url({'mode': 'playStream', 'foldername': foldername,
                                         'streamID': espplayerSchedule['included'][i]['id']})
                        li = xbmcgui.ListItem(foldername, iconImage=bildurlherausfinden(i, 2))
                        li.setProperty('IsPlayable', 'true')
                        li.setInfo('video', {'plot': str(
                            espplayerSchedule['included'][i]['attributes']['scheduleStart'] + ' - ' +
                            espplayerSchedule['included'][i]['attributes']['secondaryTitle'])})
                        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
        except KeyError:
            i1 = i1 + 1
        i = i + 1



    xbmcplugin.endOfDirectory(addon_handle)


elif mode[0] == 'Archive':
    archiveAuswahl = requests.get(url=urlArchiveAuswahl, headers=header)
    archiveAuswahl = archiveAuswahl.json()
    i = 0
    i1 = 0
    name = ''
    while i < len(archiveAuswahl['included']):
        try:
            if archiveAuswahl['included'][i]['type'] == 'route':
                if archiveAuswahl['included'][i]['attributes']['url'][:7] == '/sport/':
                    #Beschriftund herausfinden (geht noch nicht)
                    j = 0
                    while j < len(archiveAuswahl['included']):
                        if archiveAuswahl['included'][j]['id'] == \
                                archiveAuswahl['included'][i]['id']:
                            if not(i == j):
                                name = archiveAuswahl['included'][j]['attributes']['name']
                                break
                        j = j + 1

                    if name == '':
                        createOrdnerwithURL('archiveAuswahl', archiveAuswahl['included'][i]['attributes']['url'], archiveAuswahl['included'][i]['attributes']['url'])
                    else:
                        createOrdnerwithURL('archiveAuswahl',name, archiveAuswahl['included'][i]['attributes']['url'])
        except KeyError:
            i1 = i1 + 1
        i = i + 1
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'archiveAuswahl':
    xbmc.log(str(args['url'][0]))

 #Main auslesen:
    #urlStart+str(args['url'][0])+'?include=default'
    xbmc.log('URL123: '+urlStart+str(args['url'][0])+'?include=default')
    espplayerArchiveAuswahl = requests.get(url=urlStart+str(args['url'][0])+'?include=default', headers=header)
    espplayerArchiveAuswahl = espplayerArchiveAuswahl.json()
    i = 0
    i1 = 0
    availableInTerritory = False
    j = 0
    xbmc.log(str(espplayerArchiveAuswahl))
    while i < len(espplayerArchiveAuswahl['included']):
        # print(str(i))
        try:
            if espplayerArchiveAuswahl['included'][i]['attributes']['videoType'] == 'STANDALONE':
                if availableInTerritoryCheck(i, 1):
                    #espplayerMain['included'][i]['attributes']['scheduleStart']
                        xbmc.log('hier')
                    #+' ('+espplayerArchiveAuswahl['included'][i]['attributes']['broadcastType']+ ') ('+espplayerArchiveAuswahl['included'][i]['attributes']['materialType']+')'
                        foldername = str(espplayerArchiveAuswahl['included'][i]['attributes']['scheduleStart']+': '+espplayerArchiveAuswahl['included'][i]['attributes']['name']+' - '+espplayerArchiveAuswahl['included'][i]['attributes']['secondaryTitle'])
                        url = build_url({'mode': 'playStream', 'foldername': foldername, 'streamID': espplayerArchiveAuswahl['included'][i]['id']})
                        li = xbmcgui.ListItem(foldername, iconImage=bildurlherausfinden(i,1))
                        li.setProperty('IsPlayable', 'true')
                        li.setInfo('video', {'plot': str(espplayerArchiveAuswahl['included'][i]['attributes']['scheduleStart']+' - '+espplayerArchiveAuswahl['included'][i]['attributes']['secondaryTitle'])})
                        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
        except KeyError:
            i1 = i1 + 1
        i = i + 1
    xbmcplugin.endOfDirectory(addon_handle)


elif mode[0] == 'playStream':
    urlStream = urlStream1 + args['streamID'][0] + urlStream2
    espplayerStream = requests.get(url=urlStream, headers=header)
    if str(espplayerStream) == '<Response [403]>':
        xbmcgui.Dialog().ok(_addon_name, 'Stream hat noch nicht begonnen oder ist schon zu Ende')
        xbmcplugin.setResolvedUrl(_addon_handler, False, xbmcgui.ListItem())
    else:
        espplayerStream = espplayerStream.json()
        xbmc.log(str(espplayerStream))
        streamURL = str(espplayerStream['data']['attributes']['streaming']['mss']['url'])

        li = xbmcgui.ListItem(path=streamURL)
        li.setProperty('inputstreamaddon', 'inputstream.adaptive')
        li.setProperty('inputstream.adaptive.manifest_type', 'ism')
        #li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        li.setContentLookup(False)
        xbmcplugin.setResolvedUrl(_addon_handler, True, listitem=li)
