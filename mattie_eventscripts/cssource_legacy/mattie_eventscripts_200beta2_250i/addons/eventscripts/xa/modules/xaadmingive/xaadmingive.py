import es
import gamethread
import popuplib
import playerlib

from xa import xa

import psyco
psyco.full()

info = es.AddonInfo()
info.name     = 'Admin Give'
info.version  = '1.0.4'
info.basename = 'xaadmingive'

xaadmingive  			 = xa.register('xaadmingive')
xalanguage 			     = xaadmingive.language.getLanguage()
admingive_anonymous      = xaadmingive.setting.createVariable('admingive_anonymous' , 0, 'Whether or not giving a player a weapon is anonymous... 1 = Anonymous, 0 = Global')
admingive_stripfirst     = xaadmingive.setting.createVariable("admingive_stripfirst", 1, 'Whether or not the target is striped of their weapon before being gave another.\n // Will only strip the same slot as their being given.')

pistols  = ('usp','glock','p228','deagle','elite','fiveseven')
shotguns = ('m3','xm1014')
smgs     = ('tmp','mac10','mp5navy','ump45','p90')
rifles   = ('famas','galil','ak47','m4a1','sg552','aug')
snipers  = ('scout','sg550','g3sg1','awp')
grenades = ('hegrenade','smokegrenade','flashbang')
items    = ('vest','vesthelm','nvgs','c4','defuser')
admins   = {}
gamename = str(es.ServerVar('eventscripts_gamedir')).replace('\\', '/').split('/')[~0]

####################
# EVENTS
def player_disconnect(ev):
    if admins.has_key(int(ev['userid'])):
        del admins[int(ev['userid'])]
####################

def load():
    admingivemenu = popuplib.easymenu("admingive", "_tempcore", _select_give)
    admingivemenu.settitle(xalanguage["give object"])
    xaadmingive.addMenu("admingive", xalanguage["give"], "admingive", "give", "ADMIN")
    admingivemenu.addoption(1, xalanguage["give weapon"])
    admingivemenu.addoption(2, xalanguage["give item"])
    admingivemenu.addoption(3, xalanguage["give health"])
    if gamename == 'cstrike': 
        admingivemenu.addoption(4, xalanguage["give cash"])
    
    giveweapon = popuplib.easymenu("admingiveweapon", '_tempcore', _select_weapon_type)
    giveweapon.settitle(xalanguage["select weapon type"])
    giveweapon.addoption(1, xalanguage["pistols"])
    giveweapon.addoption(2, xalanguage["shotguns"])
    giveweapon.addoption(3, xalanguage["smgs"])
    giveweapon.addoption(4, xalanguage["rifles"])
    giveweapon.addoption(5, xalanguage["snipers"])
    giveweapon.addoption(6, xalanguage["machinegun"])
    giveweapon.addoption(7, xalanguage["grenades"])
    giveweapon.submenu(10, "admingive")
    
    pistolsmenu = popuplib.easymenu("admingivepistols", '_tempcore', _give)
    for weapon in pistols:
        pistolsmenu.addoption('weapon_' + weapon, xalanguage[weapon])
    pistolsmenu.submenu(10, "admingiveweapon")
    pistolsmenu.settitle(xalanguage["pistols"])
    
    shotgunsmenu = popuplib.easymenu("admingiveshotguns", '_tempcore', _give)
    for weapon in shotguns:
        shotgunsmenu.addoption('weapon_' + weapon, xalanguage[weapon])
    shotgunsmenu.submenu(10, "admingiveweapon")
    shotgunsmenu.settitle(xalanguage["shotguns"])
    
    smgsmenu = popuplib.easymenu("admingivesmgs", '_tempcore', _give)
    for weapon in smgs:
        smgsmenu.addoption('weapon_' + weapon, xalanguage[weapon])
    smgsmenu.submenu(10, "admingiveweapon")
    smgsmenu.settitle(xalanguage["smgs"])
    
    riflesmenu = popuplib.easymenu("admingiverifles", '_tempcore', _give)
    for weapon in rifles:
        riflesmenu.addoption('weapon_' + weapon, xalanguage[weapon])
    riflesmenu.submenu(10, "admingiveweapon")
    riflesmenu.settitle(xalanguage["rifles"])
    
    snipersmenu = popuplib.easymenu("admingivesnipers", '_tempcore', _give)
    for weapon in snipers:
        snipersmenu.addoption('weapon_' + weapon, xalanguage[weapon])
    snipersmenu.submenu(10, "admingiveweapon")
    snipersmenu.settitle(xalanguage["snipers"])
    
    machine = popuplib.easymenu("admingivemachinegun", '_tempcore', _give)
    machine.addoption('weapon_m249', xalanguage['m249'])
    machine.submenu(10, "admingiveweapon")
    machine.settitle(xalanguage["machinegun"])
    
    greandesmenu = popuplib.easymenu("admingivegrenades", '_tempcore', _give)
    for weapon in grenades:
        greandesmenu.addoption('weapon_' + weapon, xalanguage[weapon])
    greandesmenu.submenu(10, "admingiveweapon")
    greandesmenu.settitle(xalanguage["grenades"])
    
    giveitem = popuplib.easymenu("admingiveitem", '_tempcore', _give)
    for item in items:
        if item == 'c4':
            giveitem.addoption('weapon_' + item, xalanguage[item])
        else:
            if 'vest' in item and gamename == 'cstrike':
                giveitem.addoption('item_' + item, xalanguage[item])
            elif 'vest' not in item:
                giveitem.addoption('item_' + item, xalanguage[item])
    giveitem.submenu(10, "admingive")
    giveitem.settitle(xalanguage["select item"])
    
    targetmenu = popuplib.easymenu("targetmenu", "_tempcore", _select_target)
    targetmenu.settitle(xalanguage["choose target"])
    targetmenu.addoption("player", xalanguage["select a player"])
    targetmenu.addoption("bots", xalanguage["bots"])
    targetmenu.addoption("team3", xalanguage["counter terrorists"])
    targetmenu.addoption("team2", xalanguage["terrorists"])
    targetmenu.addoption("all", xalanguage["all players"])
    
    cash = popuplib.easymenu("admingivecash", "_tempcore", _select_cash_amount)
    for b in ('10','100','500','1000','2000','4000','8000','16000'):
        d = b
        c = ''
        while len(b) > 3:
            c = ',' + b[-3:]
            b = b[0:-3]
        c = '$' + b + c
        cash.addoption(int(d), c)
    cash.settitle(xalanguage["give cash"])
    cash.submenu(10, 'admingive')
    
    health = popuplib.easymenu("admingivehealth", "_tempcore", _select_health_amount)
    for b in ('1','5','10','50','100','1000','10000','100000'):
        d = b
        c = ''
        while len(b) > 3:
            c = ',' + b[-3:]
            b = b[0:-3]
        c = b + c
        health.addoption(int(d), c)
    health.settitle(xalanguage["give health"])
    health.submenu(10, 'admingive')
    
def unload():
    for popup in ['pistols','shotguns','smgs','rifles','snipers','machinegun','grenades','item','health','cash','']:
        if popuplib.exists('admingive' + popup):
            popuplib.close('admingive' + popup, es.getUseridList())
            popuplib.delete('admingive' + popup)
    for popup in ['targetmenu','giveplayermenu']:
        if popuplib.exists(popup):
            popuplib.close(popup, es.getUseridList())
            popuplib.delete(popup)
    xaadmingive.unregister()
    
def _select_target(userid, choice, popupid):
    if not admins.has_key(userid):
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
            command = admins[userid]['command']
            if command.startswith('weapon_') or command.startswith('item_'):
                if str(admingive_anonymous) == '0':
                    tokens = {}
                    tokens['admin'] = es.getplayername(userid)
                    tokens['user']  = es.getplayername(player)
                    for myplayer in playerlib.getPlayerList('#human'):
                        tokens['item'] = '#greena #lightgreen' + str(xalanguage(command.replace('weapon_','').replace('item_',''), lang=myplayer.get("lang")))
                        es.tell(int(myplayer), '#multi', xalanguage('admin give', tokens, myplayer.get("lang")))
                if 'vest' not in command:
                    if str(admingive_stripfirst) == '1':
                        if command.replace('weapon_','') in pistols:
                            secondary = playerlib.getPlayer(player).get('secondary') 
                            if secondary:
                                RemoveWeapon(player, secondary)
                        elif command.replace('weapon_','') in (list(shotguns) + list(smgs) + list(rifles) + list(snipers) + ['m249']):
                            primary = playerlib.getPlayer(player).get('primary') 
                            if primary:
                                RemoveWeapon(player, primary)
                    gamethread.delayed(0.1, es.server.queuecmd, 'es_xgive %s %s'%(player, command))
                else:
                    if 'helm' in command:
                        es.setplayerprop(player, 'CCSPlayer.m_bHasHelmet', 1)
                    es.setplayerprop(player, 'CCSPlayer.m_ArmorValue', 100)
            elif command.startswith('health_'):
                if str(admingive_anonymous) == '0':
                    tokens = {}
                    tokens['admin'] = es.getplayername(userid)
                    tokens['user']  = es.getplayername(player)
                    health = command.replace('health_','')
                    c = ''
                    while len(health) > 3:
                        c = ',' + health[-3:]
                        health = health[0:-3]
                    c = health + c
                    tokens['item'] = '#green' + c + ' #lightgreenhealth'
                    for myplayer in playerlib.getPlayerList('#human'):
                        es.tell(int(myplayer), '#multi', xalanguage('admin give', tokens, myplayer.get("lang")))
                es.setplayerprop(player, 'CBasePlayer.m_iHealth', es.getplayerprop(player, 'CBasePlayer.m_iHealth') + int(command.replace('health_','')))
            elif command.startswith('cash_'):
                if str(admingive_anonymous) == '0':
                    tokens = {}
                    tokens['admin'] = es.getplayername(userid)
                    tokens['user']  = es.getplayername(player)
                    cash = command.replace('cash_','')
                    c = ''
                    while len(cash) > 3:
                        c = ',' + cash[-3:]
                        cash = cash[0:-3]
                    c = '$' + cash + c
                    tokens['item'] = '#green' + c
                    for myplayer in playerlib.getPlayerList('#human'):
                        es.tell(int(myplayer), '#multi', xalanguage('admin give', tokens, myplayer.get("lang")))
                es.setplayerprop(player, 'CCSPlayer.m_iAccount', es.getplayerprop(player, 'CCSPlayer.m_iAccount') + int(command.replace('cash_','')))

def _select_player(userid, choice, popupid):
    command = admins[userid]['command']
    if command.startswith('weapon_') or command.startswith('item_'):
        if 'vest' not in command:
            if str(admingive_stripfirst) == '1':
                if command.replace('weapon_','') in pistols:
                    secondary = playerlib.getPlayer(choice).get('secondary') 
                    if secondary:
                        RemoveWeapon(choice, secondary)
                elif command.replace('weapon_','') in (list(shotguns) + list(smgs) + list(rifles) + list(snipers) + ['m249']):
                    primary = playerlib.getPlayer(choice).get('primary') 
                    if primary:
                        RemoveWeapon(choice, primary)
            gamethread.delayed(0.1, es.server.queuecmd, 'es_xgive %s %s'%(choice, command))
        else:
            if 'helm' in command:
                es.setplayerprop(choice, 'CCSPlayer.m_bHasHelmet', 1)
            es.setplayerprop(choice, 'CCSPlayer.m_ArmorValue', 100)
        if str(admingive_anonymous) == '0':
            tokens = {}
            tokens['admin'] = es.getplayername(userid)
            tokens['user']  = es.getplayername(choice)
            for myplayer in playerlib.getPlayerList('#human'):
                tokens['item'] = '#greena #lightgreen' + str(xalanguage(command.replace('weapon_','').replace('item_',''), lang=myplayer.get("lang")))
                es.tell(int(myplayer), '#multi', xalanguage('admin give', tokens, myplayer.get("lang")))
    elif command.startswith('health_'):
        if str(admingive_anonymous) == '0':
            tokens = {}
            tokens['admin'] = es.getplayername(userid)
            tokens['user']  = es.getplayername(choice)
            health = command.replace('health_','')
            c = ''
            while len(health) > 3:
                c = ',' + health[-3:]
                health = health[0:-3]
            c = health + c
            tokens['item'] = '#green' + c + ' #lightgreenhealth'
            for myplayer in playerlib.getPlayerList('#human'):
                es.tell(int(myplayer), '#multi', xalanguage('admin give', tokens, myplayer.get("lang")))
        es.setplayerprop(choice, 'CBasePlayer.m_iHealth', es.getplayerprop(choice, 'CBasePlayer.m_iHealth') + int(command.replace('health_','')))
    elif command.startswith('cash_'):
        if str(admingive_anonymous) == '0':
            tokens = {}
            tokens['admin'] = es.getplayername(userid)
            tokens['user']  = es.getplayername(choice)
            cash = command.replace('cash_','')
            c = ''
            while len(cash) > 3:
                c = ',' + cash[-3:]
                cash = cash[0:-3]
            c = '$' + cash + c
            tokens['item'] = '#green' + c
            for myplayer in playerlib.getPlayerList('#human'):
                es.tell(int(myplayer), '#multi', xalanguage('admin give', tokens, myplayer.get("lang")))
        es.setplayerprop(choice, 'CCSPlayer.m_iAccount', es.getplayerprop(choice, 'CCSPlayer.m_iAccount') + int(command.replace('cash_','')))
    
def _select_cash_amount(userid, choice, popupid):
    if not admins.has_key(userid):
        admins[userid] = {}
    admins[userid]['command'] = 'cash_%s'%choice
    popuplib.send('targetmenu', userid)
        
def _select_health_amount(userid, choice, popupid):
    if not admins.has_key(userid):
        admins[userid] = {}
    admins[userid]['command'] = 'health_%s'%choice
    popuplib.send('targetmenu', userid)
    
def _select_give(userid, choice, popupid):
    if choice == 1:
        popuplib.send('admingiveweapon', userid)
    elif choice == 2:
        popuplib.send('admingiveitem', userid)
    elif choice == 3:
        popuplib.send('admingivehealth', userid)
    elif choice == 4:
        popuplib.send('admingivecash', userid)
        
def _select_weapon_type(userid, choice, popupid):
    if choice == 1:
        popuplib.send("admingivepistols", userid)
    elif choice == 2:
        popuplib.send("admingiveshotguns", userid)
    elif choice == 3:
        popuplib.send("admingivesmgs", userid)
    elif choice == 4:
        popuplib.send("admingiverifles", userid)
    elif choice == 5:
        popuplib.send("admingivesnipers", userid)
    elif choice == 6:
        popuplib.send("admingivemachinegun", userid)
    elif choice == 7:
        popuplib.send("admingivegrenades", userid)
        
def _give(userid, choice, popupid):
    if not admins.has_key(userid):
        admins[userid] = {}
    admins[userid]['command'] = choice
    popuplib.send('targetmenu', userid)

def RemoveWeapon(userid, weapon):
    handle = es.getplayerhandle(userid)
    if not weapon.startswith('weapon_'):
        weapon = "weapon_" + weapon
    for index in es.createentitylist(weapon):
        if es.getindexprop(index, 'CBaseEntity.m_hOwnerEntity') == handle:
            es.server.cmd('es_xremove %s' % index)
            break