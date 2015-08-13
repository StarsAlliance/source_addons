import es
import popuplib
import playerlib
import os.path
import string
from xa import xa

#plugin information
info = es.AddonInfo()
info.name       = "Map Management"
info.version    = "1.0"
info.author     = "Unknown"
info.basename   = "xamapmanagement"

gActions = {}
gMapCycle = []
gCurrentMap = None
gDefaultMaps = ('cs_assault','cs_compound','cs_havana','cs_italy','cs_militia','cs_office','de_aztec','de_cbble','de_chateau','de_dust','de_dust2','de_inferno','de_nuke','de_piranesi','de_port','de_prodigy','de_tides','de_train')

xamapmanagement = xa.register('xamapmanagement')
xalanguage = xamapmanagement.language.getLanguage()
xa_announce_setnextmap = xamapmanagement.setting.createVariable('announce_setnextmap', 1, "Announce that a new map has been set in chat to all players?")

nextmapvar = es.ServerVar('eventscripts_nextmapoverride')

def load():
    xamapmainmenu = popuplib.easymenu('xamapmainmenu',None,xamapmainmenu_handler)
    xamapmainmenu.settitle(xalanguage['map management'])
    xamapmainmenu.addoption('changemap',xalanguage['change map'])
    xamapmainmenu.addoption('setnextmap',xalanguage['set map'])
    xamapmanagement.addMenu('xamapmainmenu',xalanguage['map management'],'xamapmainmenu','manage_maps','ADMIN')
    xamapmanagement.addCommand('nextmap',show_nextmap,'use_nextmap','UNRESTRICTED').register(('console', 'say'))
    xamapmanagement.addCommand('xa_setnextmap',set_nextmap,'manage_maps','ADMIN').register(('server','console'))
    map_menu()
    map_cycle()

def unload():
    xamapmanagement.unregister()

def es_map_start(event_var):
    global gCurrentMap
    map_menu()
    map_cycle()
    if event_var['mapname'] in gMapCycle:
        if not gCurrentMap or (gMapCycle.index(event_var['mapname']) != gCurrentMap+1):
            gCurrentMap = gMapCycle.index(event_var['mapname'])
        else:
            gCurrentMap += 1
    else:
        gCurrentMap = -1

def map_check(mapname):
    if mapname in gDefaultMaps or os.path.isfile(xa.gamedir() + '/maps/%s.bsp' % mapname):
        return True
    else:
        if not mapname.startswith('//') and mapname != '':
            es.dbgmsg(0, 'XAMapManagement: Unable to find map: %s.' % mapname)
        return False

def map_menu():
    if popuplib.exists('xamapmenu'):
        popuplib.delete('xamapmenu')
    maplist_path = xa.gamedir() + '/maplist.txt'
    if os.path.isfile(maplist_path):
        mapfile = open(maplist_path, 'r')
        maplist = filter(map_check,map(string.strip,mapfile.readlines()))
        mapfile.close()
        if 'test_speakers' in maplist:
            maplist.remove('test_speakers')
        if 'test_hardware' in maplist:
            maplist.remove('test_hardware')
        maplist = sorted(maplist, key=lambda x: str(x).lower())
    else:
        maplist = gDefaultMaps
    xamapmenu = popuplib.easymenu('xamapmenu',None,mapmenu_handler)
    xamapmenu.settitle('Choose a map:')
    xamapmenu.submenu(10, 'xamapmainmenu')
    for mapname in maplist:
        xamapmenu.addoption(mapname,mapname)

def map_cycle():
    global gMapCycle
    gMapCycle = []
    mapcycle_path = xa.gamedir() + '/' + str(es.ServerVar('mapcyclefile'))
    if os.path.isfile(mapcycle_path):
        mapfile = open(mapcycle_path, 'r')
        gMapCycle = filter(map_check,map(string.strip,mapfile.readlines()))
        mapfile.close()
    else:
        gMapCycle = [es.ServerVar('eventscripts_currentmap')]

def show_nextmap():
    userid = es.getcmduserid()
    if str(nextmapvar) != '':
        nextmap = str(nextmapvar)
    else:
        nextmap = gMapCycle[gCurrentMap+1]
    es.tell(userid,'#multi','#green[XA] #default',xalanguage('show next map',{'mapname':nextmap},playerlib.getPlayer(userid).get('lang')))

def xamapmainmenu_handler(userid,choice,popupname):
    gActions[userid] = choice
    popuplib.send('xamapmenu',userid)

def mapmenu_handler(userid,choice,popupname):
    if gActions[userid] == 'changemap':
        es.server.cmd('changelevel '+choice)
    elif gActions[userid] == 'setnextmap':
        nextmapvar.set(choice)
        if str(xa_announce_setnextmap) == '1':
            for player in playerlib.getPlayerList():
                es.tell(player.userid, xalanguage('new next map', {'mapname':choice}, player.get('lang')))
    del gActions[userid]

def set_nextmap():
    mapname = es.getargv(1)
    if map_check(mapname):
        nextmapvar.set(mapname)
        if str(xa_announce_setnextmap) == '1':
            for player in playerlib.getPlayerList():
                es.tell(player.userid, xalanguage('new next map', {'mapname':mapname}, player.get('lang')))
    else:
        userid = int(es.getcmduserid())
        if userid:
            es.tell(userid,'#multi','#green[XA] #default',xalanguage('invalid map',{'mapname':mapname},playerlib.getPlayer(userid).get('lang')))
