import es
import popuplib
import playerlib

import cPickle
import os

from xa import xa

info                = es.AddonInfo() 
info.basename       = "xateleport"
info.name           = "Telport"
info.version        = "1.0.1"

xateleport   = xa.register(info.basename)
xalanguage   = xateleport.language.getLanguage() 

xa_anonymous = xateleport.setting.createVariable('teleport_anonymous', 0, "When an admin teleports a player, is it anonymous?")

def load():
    global locations
    strPath = os.path.join(es.getAddonPath("xa"), "data", "locations.db")
    if not os.path.isfile(strPath):
        fStream = open(strPath, "w")
        cPickle.dump({}, fStream)
        fStream.close()
    fStream   = open(strPath, "r")
    locations = cPickle.load(fStream)
    fStream.close()
    
    """ Popup register """
    xateleportmenu = popuplib.easymenu("xa_teleport_menu", "_popup_choice", sendFirstPlayer)
    xateleportmenu.settitle(xalanguage["teleport"])
    xateleportmenu.addoption(1, xalanguage["save"])
    xateleportmenu.addoption(2, xalanguage["teleport to saved"])
    xateleportmenu.addoption(3, xalanguage["teleport to other"])
    
    xateleport.addMenu("xa_teleport_menu", xalanguage["teleport"], "xa_teleport_menu", "teleport_players", "ADMIN")
    
def unload():
    xateleport.unregister()
    
def saveDatabase():
    strPath = os.path.join(es.getAddonPath("xa"), "data", "locations.db")
    fStream = open(strPath, "w")
    cPickle.dump(locations, fStream)
    fStream.close()
    
def sendFirstPlayer(userid, choice, popupid):
    if 3 < choice < 10:
        xateleportmenu.send(userid)
    if choice == 1:
        steamid = playerlib.uniqueid(userid, False)
        if steamid not in locations:
            locations[steamid] = {}
        locations[steamid][str(es.ServerVar('eventscripts_currentmap'))] = es.getplayerlocation(userid)
        lang    = playerlib.getPlayer(userid).get("lang")
        saveDatabase()
        es.tell(userid, "#green", xalanguage("location saved", {}, lang) )
    elif 4 > choice > 1:
        lang = playerlib.getPlayer(userid).get("lang")
        popupMenu = popuplib.easymenu("xa_teleport_players", "_popup_choice", sendSecondMenu)
        popupMenu.settitle(xalanguage["player select"])
        for player in filter(lambda x: not es.getplayerprop(x, "CBasePlayer.pl.deadflag"), es.getUseridList()):
            popupMenu.addoption([choice, player], es.getplayername(player), lang=lang)
        popupMenu.send(userid)
    
def sendSecondMenu(userid, choice, popupid):
    oldChoice, target = choice
    if oldChoice == 2:
        steamid           = playerlib.uniqueid(userid, False)
        lang              = playerlib.getPlayer(userid).get("lang")
        if steamid not in locations:
            es.tell(userid, "#green", xalanguage("no locations", {}, lang) )
            return
        currentMap = str(es.ServerVar('eventscripts_currentmap'))
        if currentMap not in locations[steamid]:
            es.tell(userid, "#green", xalanguage("no map locations", {}, lang) )
            return
        if es.getplayerprop(target, 'CBasePlayer.pl.deadflag'):
            es.tell(userid, xalanguage('one player died', {}, playerlib.getPlayer(userid).get("lang") ) )
            return
        x, y, z = locations[steamid][currentMap]
        es.server.queuecmd('es_xsetpos %s %s %s %s' % (target, x, y, z + 10) )
        if not int(xa_anonymous):
            args           = {}
            args["player"] = es.getplayername(target)
            args["admin"]  = es.getplayername(userid)
            for player in playerlib.getPlayerList("#all"):
                es.tell(int(player), xalanguage("teleport to location", args, player.get("lang") ) )
    else:
        lang = playerlib.getPlayer(userid).get("lang")
        popupMenu = popuplib.easymenu("xa_teleport_players", "_popup_choice", teleportPlayerToPlayer)
        popupMenu.settitle(xalanguage["player select to send to"])
        for player in filter(lambda x: not es.getplayerprop(x, "CBasePlayer.pl.deadflag"), es.getUseridList()):
            popupMenu.addoption([target, player], es.getplayername(player), lang=lang)
        popupMenu.send(userid)
        
def teleportPlayerToPlayer(userid, choice, popupid):
    target, recipient = choice
    if es.getplayerprop(target, 'CBasePlayer.pl.deadflag') or es.getplayerprop(recipient, 'CBasePlayer.pl.deadflag'):
        es.tell(userid, xalanguage('one player died', {}, playerlib.getPlayer(userid).get("lang") ) )
        return
    x, y, z = es.getplayerlocation(recipient)
    z += 100
    es.server.queuecmd('es_xsetpos %s %s %s %s' % (target, x, y, z) )
    if not int(xa_anonymous):
        args              = {}
        args["admin"]     = es.getplayername(userid)
        args["target"]    = es.getplayername(target)
        args["recipient"] = es.getplayername(recipient) 
        for player in playerlib.getPlayerList("#all"):
            es.tell(int(player), xalanguage("player sent to player", args, player.get("lang") ) )