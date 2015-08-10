import es
import playerlib
import popuplib
import gamethread
from xa import xa

#bugfix: need to import random!
import random

#plugin information
info = es.AddonInfo()
info.name           = "Player Punishments"
info.version        = "0.2"
info.author         = "Hunter"
info.basename       = "xapunishments"

punishment_choice = {}
punishment_method = {}
punishment_display = {}
punishment_target = {}
punishment_targetlist = {}
punishment_pmenus = {}
punishment_argc = {}
punishment_cross_ref = {}
punishment_ondead = {}
dead_delayed = {}

xapunishments               = xa.register(info.basename)
xalanguage                  = xapunishments.language.getLanguage()
xa_adminburn_anonymous      = xapunishments.setting.createVariable('adminburn_anonymous', 0, "When an admin burns a player, will the text be cut out from chat?")
xa_adminslap_anonymous      = xapunishments.setting.createVariable('adminslap_anonymous', 0, "When an admin slaps a player, will the text be cut out from chat?")
xa_adminslay_anonymous      = xapunishments.setting.createVariable('adminslay_anonymous', 0, "When an admin slays a player, will the text be cut out from chat?")
xa_admin_burn_time          = xapunishments.setting.createVariable('admin_burn_time', 20, "The amount of time (in seconds) to burna  player for")
xa_slap_to_damage           = xapunishments.setting.createVariable('slap_to_damage', 10, "How much health to slap a player to")

def load():
    #Load Function for Player Settings for XA.
    xapunishmentmenu = popuplib.easymenu("xapunishmentmenu", "_tempcore", _select_punishment)
    xapunishmentmenu.settitle(xalanguage["choose punishment"])
    xapunishments.addMenu("xapunishmentmenu", xalanguage["punish players"], "xapunishmentmenu", "punish_player", "ADMIN")
    
    xapunishtargetmenu = popuplib.easymenu("xapunishtargetmenu", "_tempcore", _select_target)
    xapunishtargetmenu.settitle(xalanguage["choose target"])
    xapunishtargetmenu.addoption("player", xalanguage["select a player"])
    xapunishtargetmenu.addoption("team3", xalanguage["counter terrorists"])
    xapunishtargetmenu.addoption("team2", xalanguage["terrorists"])
    xapunishtargetmenu.addoption("all", xalanguage["all players"])
    xapunishtargetmenu.submenu(10, xapunishmentmenu)
    
    xapunishsuremenu = popuplib.easymenu("xapunishsuremenu", "_tempcore", _select_sure)
    xapunishsuremenu.settitle(xalanguage["are you sure"])
    xapunishsuremenu.addoption(True, xalanguage["yes"])
    xapunishsuremenu.addoption(False, xalanguage["no"])
    xapunishsuremenu.submenu(10, xapunishtargetmenu)

    xapunishments.registerPunishment("burn", xalanguage["burn"], _punishment_burn, 1)
    xapunishments.registerPunishment("extinguish", xalanguage["extinguish"], _punishment_extinguish, 1)
    xapunishments.registerPunishment("slap", xalanguage["slap"], _punishment_slap, 1)
    xapunishments.registerPunishment("slay", xalanguage["slay"], _punishment_slay, 1)

def unload():
    for userid in es.getUseridList():
        gamethread.cancelDelayed('burn_%s'%userid)
    for punishment in punishment_method:
        xapunishments.unregisterPunishment(punishment)
    popuplib.delete("xapunishmentmenu")
    popuplib.delete("xapunishtargetmenu")
    popuplib.delete("xapunishsuremenu")
    for page in punishment_pmenus:
        punishment_pmenus[page].delete()
    xapunishments.unregister()

def round_freeze_end(event_var):
    remove = []
    for userid in dead_delayed:
        if es.getplayerteam(userid) != 1:
            for punishment,adminid,args,force in dead_delayed[userid]:
                _punish_player(userid,punishment,adminid,args,force)
            remove.append(userid)
        else:
            xapunishments.logging.log("is in spectator mode and will be punished when he next spawns", userid)
    for userid in remove:
        del dead_delayed[userid]
        
def _select_punishment(userid, choice, name):
    punishment_choice[userid] = choice
    if not userid in punishment_target:
        popuplib.send("xapunishtargetmenu", userid)
    else:
        _punish_player(punishment_target[userid], punishment_choice[userid], userid)
        del punishment_target[userid]
    
def _select_target(userid, choice, name):
    if choice == "player":
        if userid in punishment_pmenus:
            punishment_pmenus[userid].delete()
        punishment_pmenus[userid] = popuplib.construct("xapunishplayermenu"+str(userid), "players", "#alive")
        punishment_pmenus[userid].settitle(xalanguage["choose player"])
        punishment_pmenus[userid].menuselectfb = _select_player
        punishment_pmenus[userid].submenu(10, "xapunishtargetmenu")
        punishment_pmenus[userid].send(userid)
    else:
        if choice == "team3":
            playerlist = playerlib.getUseridList("#ct")
        elif choice == "team2":
            playerlist = playerlib.getUseridList("#t")
        elif choice == "all":
            playerlist = es.getUseridList()
        if playerlist:
            punishment_targetlist[userid] = playerlist
            popuplib.send("xapunishsuremenu", userid)
        else:
            popuplib.send("xapunishtargetmenu", userid)

def _select_sure(userid, choice, name):
    if choice and punishment_targetlist[userid] and punishment_choice[userid]:
        for player in punishment_targetlist[userid]:
            _punish_player(player, punishment_choice[userid], userid)
    else:
        popuplib.send("xapunishtargetmenu", userid)

def _select_player(userid, choice, name):
    _punish_player(choice, punishment_choice[userid], userid)
    
def _command_player():
    adminid = es.getcmduserid()
    if adminid > 0:
        admin = playerlib.getPlayer(adminid)
    cmd = es.getargv(0).replace(str(es.ServerVar('xa_sayprefix')), 'xa_', 1).replace('ma_', 'xa_', 1)
    if cmd in punishment_cross_ref:
        punishment = punishment_cross_ref[cmd]
        if punishment in punishment_argc:
            argc = es.getargc()
            if argc > punishment_argc[punishment]:
                args = []
                for i in range(1, argc):
                    args.append(es.getargv(i))
                user = es.getargv(1)
                for userid in playerlib.getUseridList(user):
                    _punish_player(userid, punishment, adminid, args)
            elif adminid > 0:
                es.tell(adminid, xalanguage("not enough args", (), admin.get("lang")))
            else:
                es.dbgmsg(0, xalanguage("not enough args"))

def _punish_player(userid, punishment, adminid, args = [], force = False):
    if adminid == 0 or xapunishments.isUseridAuthorized(adminid, punishment+"_player") or force:
        if (not xapunishments.isUseridAuthorized(userid, "immune_"+punishment)) or (userid == adminid) or force:
            if userid in playerlib.getUseridList("#alive") or True == punishment_ondead[punishment]:
                if callable(punishment_method[punishment]):
                    xapunishments.logging.log("used punishment %s on user %s [%s]" % (punishment, es.getplayername(userid), es.getplayersteamid(userid)), adminid, True)
                    try:
                        punishment_method[punishment](userid, adminid, args, force)
                    except TypeError:
                        try:
                            punishment_method[punishment](userid, adminid, args)
                        except TypeError:
                            punishment_method[punishment](userid, adminid)
                    return True
                else:
                    es.dbgmsg(0, "xapunishments.py: Cannot find method '"+str(punishment_method[punishment])+"'!")
                    return False
            else:
                if userid not in dead_delayed:
                    dead_delayed[userid] = []
                dead_delayed[userid].append(punishment,adminid,args,force)
                xapunishments.logging.log("will be punished when he next spawns", userid)
                es.tell(adminid, xalanguage("dead", {'username':es.getplayername(userid)}, playerlib.getPlayer(adminid).get("lang")))
                return False
        else:
            es.tell(adminid, xalanguage("immune", {'username':es.getplayername(userid)}, playerlib.getPlayer(adminid).get("lang")))
            return False
    else:
        es.tell(adminid, xalanguage("not allowed", (), playerlib.getPlayer(adminid).get("lang")))
        return False

def registerPunishment(module, punishment, name, method, argc = 0, activeOnDeadPlayers = False):
    if not punishment in punishment_method:
        punishment_method[punishment] = method
        punishment_display[punishment] = name
        punishment_argc[punishment] = argc
        punishment_ondead[punishment] = activeOnDeadPlayers
        punishment_cross_ref['xa_'+punishment] = punishment
        xapunishmentmenu = popuplib.find("xapunishmentmenu")
        xapunishmentmenu.addoption(punishment, name, 1)
        xapunishments.registerCapability("immune_"+punishment, "ADMIN", "IMMUNITY")
        if punishment_argc[punishment] > 0:
            xapunishments.addCommand('xa_'+punishment, _command_player, punishment+"_player", "ADMIN", name["en"]+" punishment", True).register(('say', 'console','server'))
        return True
    else:
        return False
    
def unregisterPunishment(module, punishment):
    if punishment in punishment_method:
        xapunishmentmenu = popuplib.find("xapunishmentmenu")
        xapunishmentmenu.addoption(punishment, 'Unloaded', 0)
        punishment_method[punishment] = None
        try:
            del punishment_display[punishment]
            del punishment_argc[punishment]
            del punishment_cross_ref['xa_'+punishment]
        except:
            pass
        return True
    else:
        return False
        
def punishPlayer(punishment, userid, adminid, args = [], force = False):
    if punishment in punishment_method:
        return _punish_player(userid, punishment, adminid, args, force)
    else:
        return False

def sendPunishmentMenu(userid, victimid):
    for user in list(userid):
        punishment_target[user] = victimid
        xapunishmentmenu.send(user)

# The default punishments that ship with the module
def _punishment_burn(userid, adminid, args, force):
    if len(args) > 1:
        burntime = args[1]
    else:
        burntime = xa_admin_burn_time
    if str(xa_adminburn_anonymous) == '0' and not force:
        tokens = {}
        tokens['admin']   = es.getplayername(adminid)
        tokens['user']    = es.getplayername(userid)
        for user in playerlib.getPlayerList():
            es.tell(user, xalanguage("admin burn", tokens, user.get("lang")))
    player = playerlib.getPlayer(userid)
    player.set('burn')
    if int(burntime) > 0:
        gamethread.delayedname(int(burntime), 'burn_%s'%userid, _punishment_extinguish, (userid, adminid, (), True))

def _punishment_extinguish(userid, adminid, args, force):
    if str(xa_adminburn_anonymous) == '0' and not force:
        tokens = {}
        tokens['admin']   = es.getplayername(adminid)
        tokens['user']    = es.getplayername(userid)
        for user in playerlib.getPlayerList():
            es.tell(user, xalanguage("admin extinguish", tokens, user.get("lang")))
    # Copied from un-released playerlib
    flamelist = es.createentitylist("entityflame") 
    handle = es.getplayerhandle(userid) 
    for flame_entity in flamelist: 
        string = es.getindexprop(flame_entity, 'CEntityFlame.m_hEntAttached') 
        if string == handle: 
            es.setindexprop(flame_entity, 'CEntityFlame.m_flLifetime', 0) 
            break

def _punishment_slap(userid, adminid, args, force):
    if len(args) > 1:
        health = args[1]
    else:
        health = xa_slap_to_damage
    if str(xa_adminslap_anonymous) == '0' and not force:
        tokens = {}
        tokens['admin']   = es.getplayername(adminid)
        tokens['user']    = es.getplayername(userid)
        tokens['health']  = str(health)
        for user in playerlib.getPlayerList():
            es.tell(int(user), xalanguage("admin slap", tokens, user.get("lang")))
    player = playerlib.getPlayer(userid)
    player.set('health', int(health))
    es.emitsound('player', userid, 'player/damage2.wav', '1.0', '0.5')
    es.setplayerprop(userid, 'CCSPlayer.baseclass.localdata.m_vecBaseVelocity', '%s,%s,%s'%(random.randint(-255, 255), random.randint(-255, 255), random.randint(-100, 255)))
    if player.get('health') <= 0:
        player.kill()

def _punishment_slay(userid, adminid, args, force):
    if str(xa_adminslay_anonymous) == '0' and not force:
        tokens = {}
        tokens['admin']   = es.getplayername(adminid)
        tokens['user']    = es.getplayername(userid)
        for user in playerlib.getPlayerList():
            es.tell(int(userid), xalanguage("admin slay", tokens, user.get("lang")))
    player = playerlib.getPlayer(userid)
    player.kill()
