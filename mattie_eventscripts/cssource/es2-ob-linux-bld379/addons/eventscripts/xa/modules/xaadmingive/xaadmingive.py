# ==============================================================================
#   IMPORTS
# ==============================================================================
# EventScripts Imports
import es
import gamethread
import popuplib
import playerlib
import weaponlib

# XA Imports
from xa import xa

# ==============================================================================
#   ADDON REGISTRATION
# ==============================================================================
# Register with EventScripts
info = es.AddonInfo()
info.name       = 'Admin Give'
info.version    = '1.1'
info.author     = 'freddukes'
info.basename   = 'xaadmingive'

# Register with XA
xaadmingive  			 = xa.register('xaadmingive')
xalanguage 			     = xaadmingive.language.getLanguage()
admingive_anonymous      = xaadmingive.setting.createVariable('admingive_anonymous' , 0, 'Whether or not giving a player a weapon is anonymous... 1 = Anonymous, 0 = Global')
admingive_stripfirst     = xaadmingive.setting.createVariable("admingive_stripfirst", 1, 'Whether or not the target is striped of their weapon before being gave another.\n // Will only strip the same slot as their being given.')

# ==============================================================================
#   GLOBALS
# ==============================================================================
weapons = {}
weapons['pistols']  = set(weaponlib.getWeaponNameList('#pistol'))
weapons['shotguns'] = set(weaponlib.getWeaponNameList('#shotgun'))
weapons['smgs']     = set(weaponlib.getWeaponNameList('#smg'))
weapons['snipers']  = set(weaponlib.getWeaponNameList('#sniper'))
weapons['rifles']   = set(weaponlib.getWeaponNameList('#rifle'))
weapons['rifles']   = weapons['rifles'].difference(weapons['snipers'])
weapons['grenades'] = set(weaponlib.getWeaponNameList('#grenade'))
weapons['all']      = set(weaponlib.getWeaponNameList("#all"))
weapons['others']   = weapons['all'].difference(weapons['pistols']).difference(weapons['shotguns']).difference(weapons['smgs']).difference(weapons['rifles']).difference(weapons['snipers']).difference(weapons['grenades'])
weaponsOrder = ('pistols', 'shotguns', 'smgs', 'snipers', 'rifles', 'grenades', 'all', 'others')
admins   = {}
gamename = str(es.ServerVar('eventscripts_gamedir')).replace('\\', '/').split('/')[~0]

# ==============================================================================
#   GAME EVENTS
# ==============================================================================
def load():
    admingivemenu = popuplib.easymenu("admingive", "_tempcore", _select_give)
    admingivemenu.settitle(xalanguage["give object"])
    xaadmingive.addMenu("admingive", xalanguage["give"], "admingive", "give", "ADMIN")
    admingivemenu.addoption("weapon", xalanguage["give weapon"])
    admingivemenu.addoption("health", xalanguage["give health"])
    if gamename == 'cstrike': 
        admingivemenu.addoption("cash", xalanguage["give cash"])
    
    giveweapon = popuplib.easymenu("admingiveweapon", '_tempcore', _select_give)
    giveweapon.settitle(xalanguage["select weapon type"])
    for weaponType in weaponsOrder:
        giveweapon.addoption(weaponType, xalanguage[weaponType])
    giveweapon.submenu(10, "admingive")
    
    for weaponType, weaponSet in weapons.iteritems():
        popupmenu = popuplib.easymenu("admingive%s" % weaponType, "_tempcore", _give)
        for weapon in weaponSet:
            popupmenu.addoption(weapon, _remove_prefix(weapon))
        popupmenu.submenu(10, 'admingiveweapon')
        popupmenu.settitle(xalanguage[weaponType])
    
    targetmenu = popuplib.easymenu("targetmenu", "_tempcore", _select_target)
    targetmenu.settitle(xalanguage["choose target"])
    targetmenu.addoption("player", xalanguage["select a player"])
    targetmenu.addoption("bots", xalanguage["bots"])
    targetmenu.addoption("team3", xalanguage["counter terrorists"])
    targetmenu.addoption("team2", xalanguage["terrorists"])
    targetmenu.addoption("all", xalanguage["all players"])
    
    cash = popuplib.easymenu("admingivecash", "_tempcore", _select_cash_amount)
    addInteger(cash, 10, "$")
    addInteger(cash, 100, "$")
    addInteger(cash, 500, "$")
    addInteger(cash, 1000, "$")
    addInteger(cash, 2000, "$")
    addInteger(cash, 4000, "$")
    addInteger(cash, 8000, "$")
    addInteger(cash, 16000, "$")
    cash.settitle(xalanguage["give cash"])
    cash.submenu(10, 'admingive')
    
    health = popuplib.easymenu("admingivehealth", "_tempcore", _select_health_amount)
    addInteger(health, 1)
    addInteger(health, 5)
    addInteger(health, 10)
    addInteger(health, 50)
    addInteger(health, 100)
    addInteger(health, 1000)
    addInteger(health, 10000)
    addInteger(health, 100000)
    health.settitle(xalanguage["give health"])
    health.submenu(10, 'admingive')
    
def unload():
    for popup in ['pistols', 'shotguns', 'smgs', 'rifles', 'snipers', 'machinegun', 'grenades', 'others', 'all', 'health', 'cash', '']:
        if popuplib.exists('admingive' + popup):
            popuplib.close('admingive' + popup, es.getUseridList())
            popuplib.delete('admingive' + popup)
    for popup in ['targetmenu', 'giveplayermenu']:
        if popuplib.exists(popup):
            popuplib.close(popup, es.getUseridList())
            popuplib.delete(popup)
    xaadmingive.unregister()

def player_disconnect(ev):
    if admins.has_key(int(ev['userid'])):
        del admins[int(ev['userid'])]

# ==============================================================================
#   HELPER METHODS
# ==============================================================================
def _select_target(userid, choice, popupid):
    if userid not in admins:
        return
    if choice == "player":
        giveplayermenu = popuplib.construct("giveplayermenu", "players", "#alive")
        giveplayermenu.settitle(xalanguage["choose player"])
        giveplayermenu.menuselectfb = _select_player
        giveplayermenu.send(userid)
    else:
        if choice == "team3":
            playerlist = filter(lambda x: es.getplayerteam(x) == 3, es.getUseridList())
        elif choice == "team2":
            playerlist = filter(lambda x: es.getplayerteam(x) == 2, es.getUseridList())
        elif choice == "bots":
            playerlist = filter(lambda x: es.isbot(x), es.getUseridList())
        elif choice == "all":
            playerlist = es.getUseridList()
        playerlist = filter(lambda x: not es.getplayerprop(x, 'CBasePlayer.pl.deadflag'), playerlist)
        for player in playerlist:
            giveObject(userid, player)
            
def giveObject(adminid, userid):
    command = admins[adminid]['command']
    if command.startswith(('health_', 'cash_')):
        prop   = 'CBasePlayer.m_iHealth' if command.startswith('health_') else 'CCSPlayer.m_iAccount'
        amount = int(command.replace('health_', '').replace('cash_', ''))
        currentAmount  = es.getplayerprop(userid, prop)
        es.setplayerprop(userid, prop, currentAmount + amount)
        # issue #70 :: value formatting error
        strInt = str(amount)
        thousands = []
        while strInt:
            thousands.append(strInt[-3:])
            strInt = strInt[:-3]
        formattedAmount = ",".join(reversed(thousands))
        tokens = {}
        tokens['admin'] = es.getplayername(adminid)
        tokens['user']  = es.getplayername(userid)
        tokens['item']  =  '#green%s #lightgreen%s' % (formattedAmount, 'cash' if command.startswith('cash_') else 'health')
        for tellplayer in playerlib.getPlayerList('#human'):
            es.tell(int(tellplayer), '#multi', xalanguage('admin give', tokens, tellplayer.get("lang")))
        xaadmingive.logging.log("has given player %s %s" % (tokens['user'], tokens['item']), adminid, True) 
    else:
        weaponName = _remove_prefix(command)
        fullName   = _prepend_prefix(command)
        if int(admingive_stripfirst) == 1:
            if fullName in weaponlib.getWeaponNameList('#secondary'):
                weapon = playerlib.getPlayer(userid).get('secondary')
            else:
                weapon = playerlib.getPlayer(userid).get('primary')
            if weapon:
                _remove_weapon(userid, weapon)
        es.delayed(0.1, 'es_xgive %s %s' % (userid, fullName))
        if str(admingive_anonymous) == '0':
            tokens = {}
            tokens['admin'] = es.getplayername(adminid)
            tokens['user']  = es.getplayername(userid)
            for tellplayer in playerlib.getPlayerList('#human'):
                tokens['item'] = '#greena #lightgreen%s' % weaponName
                es.tell(int(tellplayer), '#multi', xalanguage('admin give', tokens, tellplayer.get("lang")))
        xaadmingive.logging.log("has given player %s %s" % (tokens['user'], tokens['item']), adminid, True)            

def addInteger(popupInstance, integer, prefix=""):
    formattedStr = ""
    strInt = str(integer)
    strInt = strInt[::-1]
    while strInt:
        formattedStr += strInt[:3] + ","
        strInt = strInt[3:]
    formattedStr = formattedStr[:-1]
    popupInstance.addoption(integer, prefix + formattedStr[::-1])

def _select_player(userid, choice, popupid):
    giveObject(userid, choice)
    
def _select_cash_amount(userid, choice, popupid):
    if userid not in admins:
        admins[userid] = {}
    admins[userid]['command'] = 'cash_%s' % choice
    popuplib.send('targetmenu', userid)
        
def _select_health_amount(userid, choice, popupid):
    if userid not in admins:
        admins[userid] = {}
    admins[userid]['command'] = 'health_%s' % choice
    popuplib.send('targetmenu', userid)

def _give(userid, choice, popupid):
    if not admins.has_key(userid):
        admins[userid] = {}
    admins[userid]['command'] = choice
    popuplib.send('targetmenu', userid)
        
def _select_give(userid, choice, popupid):
    popuplib.send("admingive%s" % choice, userid)

def _remove_weapon(userid, weapon):
    handle = es.getplayerhandle(userid)
    weapon = _prepend_prefix(weapon)
    for index in es.createentitylist(weapon):
        if es.getindexprop(index, 'CBaseEntity.m_hOwnerEntity') == handle:
            es.server.cmd('es_xremove %s' % index)
            break
            
def _prepend_prefix(weapon):
    if not weapon.startswith(('tf_weapon_', 'weapon_')):
        if gamename != "tf":
            weapon = "weapon_%s" % weapon
        else:
            weapon = "tf_weapon_%s" % weapon
    return weapon

def _remove_prefix(weapon):
    if not weapon.startswith(('tf_weapon_', 'weapon_')):
        return weapon
    return weapon.replace('tf_weapon_', '').replace('weapon_', '')
