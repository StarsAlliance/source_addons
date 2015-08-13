import es 
import playerlib
import random 
import gamethread 
import os
import effectlib
from xa import xa 

info                = es.AddonInfo() 
info.name           = "Extended Punishments" 
info.version        = "0.4s" 
info.author         = "freddukes" 
info.basename       = "xaextendedpunishments" 

xaextendedpunishments = xa.register(info.basename)
xalanguage            = xaextendedpunishments.language.getLanguage() 

####################### 
# Variables 
xa_adminblind_anonymous        = xaextendedpunishments.setting.createVariable('adminblind_anonymous',      0                  , "When an admin blinds a player, will a message be sent? 1 = no, 0 = yes") 
xa_adminfreeze_anonymous       = xaextendedpunishments.setting.createVariable('adminfreeze_anonymous',     0                  , "When an admin freezes a player, will a message be sent? 1 = no, 0 = yes") 
xa_admingimp_anonymous         = xaextendedpunishments.setting.createVariable('admingimp_anonymous',       0                  , "When an admin gimps a player, will a message be sent? 1 = no, 0 = yes") 
xa_admindrug_anonymous         = xaextendedpunishments.setting.createVariable('admindrug_anonymous',       0                  , "When an admin drugs a player, will a message be sent? 1 = no, 0 = yes") 
xa_adminbeacon_anonymous       = xaextendedpunishments.setting.createVariable('adminbeacon_anonymous',     0                  , "When an admin beacons a player, will a message be sent? 1 = no, 0 = yes") 
xa_adminbeacon_color           = xaextendedpunishments.setting.createVariable('adminbeacon_color',         '255 0 0 255'      , "The color of the beacon when the player is beaconed. \n// Maximum value for each color is 255. (red green blue alpha)") 
xa_adminnoclip_anonymous       = xaextendedpunishments.setting.createVariable('adminnoclip_anonymous',     0                  , "When an admin noclips a player, will a message be sent? 1 = no, 0 = yes") 
xa_adminbeacon_sound           = xaextendedpunishments.setting.createVariable('adminbeacon_sound',         'buttons/blip1.wav', "The sound emited from a player when beaconed (from ../sound/)") 
xa_adminbomb_sound             = xaextendedpunishments.setting.createVariable('adminbomb_sound',           'buttons/blip1.wav', "The sound emited from the player when they have a fuse lit (from ../sound/)") 
xa_adminbomb_beaconcolor       = xaextendedpunishments.setting.createVariable('adminbomb_beaconcolor',     '0 0 255 255'      , "The color of the beacon when a player has a fuse lit for a bomb. \n// Maximum value for each color is 255. (red green blue alpha)") 
xa_adminfreezebomb_anonymous   = xaextendedpunishments.setting.createVariable('adminfreezebomb_anonymous', 0                  , "When an admin freeze bombs a player, will a message be sent? 1 = no, 0 = yes") 
xa_adminfreezebomb_countdown   = xaextendedpunishments.setting.createVariable('adminfreezebomb_countdown', 10                 , "The countdown of the fuse (in seconds)") 
xa_admintimebomb_anonymous     = xaextendedpunishments.setting.createVariable('admintimebomb_anonymous',   0                  , "When an admin time bombs a player, will a message be sent? 1 = no, 0 = yes") 
xa_admintimebomb_countdown     = xaextendedpunishments.setting.createVariable('admintimebomb_countdown',   10                 , "The countdown of the fuse (in seconds)") 
xa_adminfirebomb_anonymous     = xaextendedpunishments.setting.createVariable('adminfirebomb_anonymous',   0                  , "When an admin fire bombs a player, will a message be sent? 1 = no, 0 = yes") 
xa_adminfirebomb_countdown     = xaextendedpunishments.setting.createVariable('adminfirebomb_countdown',   10                 , "The countdown of the fuse (in seconds)") 
xa_adminfirebomb_duration      = xaextendedpunishments.setting.createVariable('adminfirebomb_duration',    15                 , "How long the players will stay on fire for after a fire bomb (in seconds)")
xa_adminrocket_anonymous       = xaextendedpunishments.setting.createVariable('adminrocket_anonymous',     0                  , "When an admin rockets a player, will a message be sent? 1 = no, 0 = yes")

""" MUTE """
xa_adminmute_on                = xaextendedpunishments.setting.createVariable('adminmute_enabled',         0                  , "Whether or not mute is on\n// WARNING!!! This has been known to cause lag, so if you are experiencing lag, turn this off\n// 0 = Mute is not enabled\n// 1 = Mute is enabled")
xa_adminmute_anonymous         = xaextendedpunishments.setting.createVariable('adminmute_anonymous',       0                  , "When an admin mutes a player, will a message be sent? 1 = yes, 0 = no")
xa_adminmute_deletetime        = xaextendedpunishments.setting.createVariable('adminmute_deletetime',      600                , "How long after a person disconnects from the server that they will be able to reconnect and be unmuted (in seconds)\n// E.G If it was 600, then 10 minutes after they left, they'd be able to rejoin unmuted again.\n// If they joined before the 10 minutes were up, they'd still be muted")

if xa.isManiMode(): 
    gimpphrases = xaextendedpunishments.configparser.getList('cfg/mani_admin_plugin/gimpphrase.txt', True)
else: 
    gimpphrases = xaextendedpunishments.configparser.getList('gimpphrase.txt')

players    = {}
muted      = {}

def load():
    xaextendedpunishments.addRequirement('xapunishments')
    # xaextendedpunishments.xapunishments.registerPunishment("punishment", xalanguage["punishment"], _callback_function) 
    xaextendedpunishments.xapunishments.registerPunishment("blind",      xalanguage["blind"]     , _blind      , 1) 
    xaextendedpunishments.xapunishments.registerPunishment("freeze",     xalanguage["freeze"]    , _freeze     , 1) 
    xaextendedpunishments.xapunishments.registerPunishment("gimp",       xalanguage["gimp"]      , _gimp       , 1) 
    xaextendedpunishments.xapunishments.registerPunishment("drug",       xalanguage["drug"]      , _drug       , 1) 
    xaextendedpunishments.xapunishments.registerPunishment("beacon",     xalanguage["beacon"]    , _beacon     , 1) 
    xaextendedpunishments.xapunishments.registerPunishment("noclip",     xalanguage["noclip"]    , _noclip     , 1) 
    xaextendedpunishments.xapunishments.registerPunishment("freezebomb", xalanguage["freezebomb"], _freeze_bomb, 1) 
    xaextendedpunishments.xapunishments.registerPunishment("timebomb",   xalanguage["timebomb"]  , _time_bomb  , 1) 
    xaextendedpunishments.xapunishments.registerPunishment("firebomb",   xalanguage["firebomb"]  , _fire_bomb  , 1)
    xaextendedpunishments.xapunishments.registerPunishment("rocket",     xalanguage["rocket"]    , _rocket     , 1)
    if int(xa_adminmute_on):
        xaextendedpunishments.xapunishments.registerPunishment("mute",   xalanguage["mute"]      , _mute       , 1)
    gamethread.delayedname(1, 'blind_loop', _blind_loop)
    
    """ Make sure if XA is loaded late, add all players """
    for player in es.getUseridList():
        player_activate({'userid' : player})
        
def player_activate(ev): 
    userid = int(ev['userid']) 
    if userid in players: 
        del players[userid] 
    players[userid]                 = {} 
    players[userid]['gimped']       = 0 
    players[userid]['blind']        = 0 
    players[userid]['drugged']      = 0 
    players[userid]['firebombed']   = 0 
    players[userid]['freezebombed'] = 0 
    players[userid]['timebombed']   = 0 
    players[userid]['beaconed']     = 0 
    players[userid]['noclipped']    = 0
    gamethread.cancelDelayed('unmute_%s'%es.getplayersteamid(userid))

def player_disconnect(ev): 
    userid = int(ev['userid']) 
    if userid in players: 
        del players[userid]

    if userid in map(int, muted): 
        gamethread.delayedname(int(xa_adminmute_deletetime), 'unmute_%s'%ev['networkid'], _unmute, ev['networkid'])

def round_end(ev): 
    for userid in es.getUseridList(): 
        if not es.getplayerprop(userid, 'CBasePlayer.pl.deadflag'):
            if not players.has_key(userid):
                player_activate({'userid':userid})
            players[userid]['timebombed']   = 0 
            players[userid]['freezebombed'] = 0 
            players[userid]['firebombed']   = 0 
            players[userid]['noclipped']    = 0 
            players[userid]['beaconed']     = 0 
            players[userid]['drugged']      = 0 
            players[userid]['blind']        = 0 
            gamethread.cancelDelayed('beacon_%s'%userid) 
            gamethread.cancelDelayed('timebomb_%s'%userid) 
            gamethread.cancelDelayed('freezebomb_%s'%userid) 
            gamethread.cancelDelayed('firebomb_%s'%userid) 
            es.setplayerprop(userid, "CBaseEntity.movetype", 2)
            es.setplayerprop(userid, 'CBasePlayer.m_iDefaultFOV', 90)

def player_death(ev): 
    userid = int(ev['userid'])
    if not userid in players:
        players[userid] = {}
        players[userid]['gimped']   = 0 
    players[userid]['timebombed']   = 0 
    players[userid]['freezebombed'] = 0 
    players[userid]['firebombed']   = 0 
    players[userid]['noclipped']    = 0 
    players[userid]['beaconed']     = 0 
    players[userid]['drugged']      = 0 
    players[userid]['blind']        = 0 
    gamethread.cancelDelayed('beacon_%s'%userid) 
    gamethread.cancelDelayed('timebomb_%s'%userid) 
    gamethread.cancelDelayed('freezebomb_%s'%userid) 
    gamethread.cancelDelayed('firebomb_%s'%userid) 
    es.setplayerprop(userid, "CBaseEntity.movetype", 2)
    es.setplayerprop(userid, 'CBasePlayer.m_iDefaultFOV', 90)

def _blind(userid, adminid, args): 
    blind = players[userid]['blind'] 
    if str(xa_admingimp_anonymous) == "0": 
        tokens = {} 
        tokens['admin'] = es.getplayername(adminid) 
        tokens['user']  = es.getplayername(userid) 
        for player in playerlib.getPlayerList(): 
            tokens['state'] = xalanguage("blinded", lang=player.get("lang")) if not blind else xalanguage("unblinded", lang=player.get("lang")) 
            es.tell(int(player), xalanguage("admin state", tokens, player.get("lang"))) 
    players[userid]['blind'] = (1 if not blind else 0) 
    
def _blind_loop(): 
    for player in es.getUseridList(): 
        if players.has_key(player) and players[player]['blind']: 
            es.usermsg('create','admin_fade','Fade') 
            es.usermsg('write','short','admin_fade', 360)   # Frames to fade (60FPS = 6 seconds) 
            es.usermsg('write','short','admin_fade', 1000)  # Time to stay faded 
            es.usermsg('write','short','admin_fade', 2)     # 2 = fade in, 1 = fade out 
            es.usermsg('write','byte','admin_fade', 0)      # red 
            es.usermsg('write','byte','admin_fade', 0)      # green 
            es.usermsg('write','byte','admin_fade', 0)      # blue 
            es.usermsg('write','byte','admin_fade', 255)    # alpha 
            es.usermsg('send','admin_fade',player) 
            es.usermsg('delete','admin_fade') 
    gamethread.delayedname(1, 'blind_loop', _blind_loop) 
            
def _freeze(userid, adminid, args): 
    player = playerlib.getPlayer(userid) 
    if str(xa_adminfreeze_anonymous) == '0': 
        tokens = {} 
        tokens['admin']   = es.getplayername(adminid) 
        tokens['user']    = es.getplayername(userid) 
        for player in playerlib.getPlayerList(): 
            tokens['state']   = xalanguage("frozen", lang=player.get("lang")) if player.get('freeze') == '0' else xalanguage("defrosted", lang=player.get("lang")) 
            es.tell(int(player), xalanguage("admin state", tokens, player.get("lang")))
    if player.get('freeze') == '0':
        gamethread.queue(player.set, ('noclip', 1))
        gamethread.queue(player.set, ('freeze', 1))
    else:
        gamethread.queue(player.set, ('freeze', 0))

def _gimp(userid, adminid, args): 
    gimped = players[userid]['gimped'] 
    players[userid]['gimped'] = (1 if not gimped else 0) 
    if str(xa_admingimp_anonymous) == "0": 
        tokens = {} 
        tokens['admin'] = es.getplayername(adminid) 
        tokens['user']  = es.getplayername(userid) 
        for player in playerlib.getPlayerList(): 
            tokens['state'] = xalanguage("gimped", lang=player.get("lang")) if not gimped else xalanguage("ungimped", lang=player.get("lang")) 
            es.tell(int(player), xalanguage("admin state", tokens, player.get("lang"))) 
    
def _say_filter(userid, text, team):
    if userid in players:
        sayCommand = text.strip('"').split()
        if not sayCommand:
           return (0, "", 0)
        if not es.exists('saycommand', sayCommand[0]):
            if players[userid]['gimped']:
                text = getGimpPhrase()
                if text: 
                    return(userid, getGimpPhrase(), team)
                else:
                    return (userid, "I have been gimped", team)
    
            if userid in map(int, muted):
                es.tell(userid,'#multi', xalanguage("you are muted", lang=playerlib.getPlayer(userid).get("lang")))
                return (0, None, 0)

    return(userid, text, team)
es.addons.registerSayFilter(_say_filter)

def unload():
    for userid in es.getUseridList(): 
        if players.has_key(userid):
            gamethread.cancelDelayed('beacon_%s'%userid) 
            gamethread.cancelDelayed('timebomb_%s'%userid) 
            gamethread.cancelDelayed('freezebomb_%s'%userid) 
            gamethread.cancelDelayed('firebomb_%s'%userid)
            gamethread.cancelDelayed('unmute_%s'%es.getplayersteamid(userid))
            es.setplayerprop(userid, "CBaseEntity.movetype", 2)
            es.setplayerprop(userid, 'CBasePlayer.m_iDefaultFOV', 90)
    gamethread.cancelDelayed('remove_fire')
    gamethread.cancelDelayed('blind_loop')
    es.addons.unregisterSayFilter(_say_filter)
    # xaextendedpunishments.xapunishments.unregisterPunishment("punishment") 
    xaextendedpunishments.xapunishments.unregisterPunishment("blind") 
    xaextendedpunishments.xapunishments.unregisterPunishment("freeze") 
    xaextendedpunishments.xapunishments.unregisterPunishment("gimp") 
    xaextendedpunishments.xapunishments.unregisterPunishment("drug") 
    xaextendedpunishments.xapunishments.unregisterPunishment("beacon") 
    xaextendedpunishments.xapunishments.unregisterPunishment("noclip") 
    xaextendedpunishments.xapunishments.unregisterPunishment("freezebomb") 
    xaextendedpunishments.xapunishments.unregisterPunishment("timebomb") 
    xaextendedpunishments.xapunishments.unregisterPunishment("firebomb")
    
    if int(xa_adminmute_on):
        xaextendedpunishments.xapunishments.unregisterPunishment("mute")
        
    xaextendedpunishments.delRequirement('xapunishments')
    xaextendedpunishments.unregister()
    
def getGimpPhrase(): 
    if gimpphrases: 
        return random.choice(filter(lambda x: False if x == '' or x.startswith('//') else True, gimpphrases))

def _drug(userid, adminid, args): 
    drugged = players[userid]['drugged'] 
    players[userid]['drugged'] = (1 if not drugged else 0) 
    if str(xa_admindrug_anonymous) == "0": 
        tokens = {} 
        tokens['admin'] = es.getplayername(adminid) 
        tokens['user']  = es.getplayername(userid) 
        for player in playerlib.getPlayerList(): 
            tokens['state'] = xalanguage("drugged", lang=player.get("lang")) if not drugged else xalanguage("undrugged", lang=player.get("lang")) 
            es.tell(int(player), xalanguage("admin state", tokens, player.get("lang"))) 
        es.setplayerprop(userid, 'CBasePlayer.m_iDefaultFOV', 165 if not drugged else 90) 

def _beacon(userid, adminid, args): 
    beaconed = players[userid]['beaconed'] 
    if str(xa_adminbeacon_anonymous) == "0": 
        tokens = {} 
        tokens['admin'] = es.getplayername(adminid) 
        tokens['user']  = es.getplayername(userid) 
        for player in playerlib.getPlayerList(): 
            tokens['state'] = xalanguage("beaconed", lang=player.get("lang")) if not beaconed else xalanguage("unbeaconed", lang=player.get("lang")) 
            es.tell(int(player), xalanguage("admin state", tokens, player.get("lang"))) 
    if not beaconed: 
        players[userid]['beaconed'] = 1 
        _beacon_loop(userid) 
    else: 
        players[userid]['beaconed'] = 0 
        gamethread.cancelDelayed('beacon_%s'%userid) 
        
def _beacon_loop(userid):
    if userid in playerlib.getUseridList("#alive"):
        es.emitsound('player', userid, xa_adminbeacon_sound, '1.0', '0.7') 
        r, g, b, a = str(xa_adminbeacon_color).split() 
        location = es.getplayerlocation(userid) 
        effectlib.drawCircle(location, 150, steps=50, model="materials/sprites/laser.vmt", seconds=0.2, width=20, endwidth=10, red=r, green=g, blue=b, brightness = a, speed=70) 
        gamethread.delayedname(0.8, 'beacon_%s'%userid, _beacon_loop, userid)
    else:
        players[userid]['beaconed'] = 0 

def _noclip(userid, adminid, args): 
    noclipped = players[userid]['noclipped'] 
    if str(xa_adminnoclip_anonymous) == "0": 
        tokens = {} 
        tokens['admin'] = es.getplayername(adminid) 
        tokens['user']  = es.getplayername(userid) 
        for player in playerlib.getPlayerList(): 
            if not noclipped: 
                es.tell(int(player), xalanguage("noclip on", tokens, player.get("lang"))) 
            else: 
                es.tell(int(player), xalanguage("noclip off", tokens, player.get("lang"))) 
    if not noclipped: 
        players[userid]['noclipped'] = 1 
        es.setplayerprop(userid, "CBaseEntity.movetype", 8) 
    else: 
        players[userid]['noclipped'] = 0 
        es.setplayerprop(userid, "CBaseEntity.movetype", 2) 

def _freeze_bomb(userid, adminid, args): 
    freezebombed = players[userid]['freezebombed'] 
    if str(xa_admindrug_anonymous) == "0": 
        tokens = {} 
        tokens['admin']  = es.getplayername(adminid) 
        tokens['user']   = es.getplayername(userid) 
        for player in playerlib.getPlayerList(): 
            tokens['state'] = xalanguage("now", lang=player.get("lang")) if not freezebombed else xalanguage("no longer", lang=player.get("lang")) 
            tokens['bombtype'] = xalanguage("freezebomb", lang=player.get("lang")) 
            es.tell(int(player), xalanguage("bomb state", tokens, player.get("lang"))) 
    if not freezebombed: 
        _count_down(xa_admintimebomb_countdown, 'freezebomb', userid) 
        players[userid]['freezebombed'] = 1 
    else: 
        gamethread.cancelDelayed('freezebomb_%s'%userid) 
        players[userid]['freezebombed'] = 0 
            
def _fire_bomb(userid, adminid, args): 
    firebombed = players[userid]['firebombed'] 
    if str(xa_admindrug_anonymous) == "0": 
        tokens = {} 
        tokens['admin']  = es.getplayername(adminid) 
        tokens['user']   = es.getplayername(userid) 
        for player in playerlib.getPlayerList(): 
            tokens['state'] = xalanguage("now", lang=player.get("lang")) if not firebombed else xalanguage("no longer", lang=player.get("lang")) 
            tokens['bombtype'] = xalanguage("firebomb", lang=player.get("lang")) 
            es.tell(int(player), xalanguage("bomb state", tokens, player.get("lang"))) 
    if not firebombed: 
        _count_down(xa_admintimebomb_countdown, 'firebomb', userid) 
        players[userid]['firebombed'] = 1 
    else: 
        gamethread.cancelDelayed('firebomb_%s'%userid) 
        players[userid]['firebombed'] = 0 
            
def _time_bomb(userid, adminid, args): 
    timebombed = players[userid]['timebombed'] 
    if str(xa_admindrug_anonymous) == "0": 
        tokens = {} 
        tokens['admin']  = es.getplayername(adminid) 
        tokens['user']   = es.getplayername(userid) 
        for player in playerlib.getPlayerList(): 
            tokens['state'] = xalanguage("now", lang=player.get("lang")) if not timebombed else xalanguage("no longer", lang=player.get("lang")) 
            tokens['bombtype'] = xalanguage("timebomb", lang=player.get("lang")) 
            es.tell(int(player), xalanguage("bomb state", tokens, player.get("lang"))) 
    if not timebombed: 
        _count_down(xa_admintimebomb_countdown, 'timebomb', userid) 
        players[userid]['timebombed'] = 1 
    else: 
        gamethread.cancelDelayed('timebomb_%s'%userid) 
        players[userid]['timebombed'] = 0 

def _count_down(amount, bombType, userid): 
    if amount: 
        es.centermsg(amount) 
        amount -= 1 
        gamethread.delayedname(1, '%s_%s'%(bombType, userid), _count_down, (amount, bombType, userid)) 
        es.emitsound('player', userid, xa_adminbomb_sound, '1.0', '0.7') 
        r, g, b, a = str(xa_adminbomb_beaconcolor).split() 
        location = es.getplayerlocation(userid) 
        effectlib.drawCircle(location, 150, steps=50, model="materials/sprites/laser.vmt", seconds=0.2, width=20, endwidth=10, red=r, green=g, blue=b, brightness = a, speed=70) 
    elif bombType == "timebomb": 
        for index in es.createentitylist('env_explosion'): 
            es.server.cmd('es_xremove %s'%index) 
        es.server.cmd('es_xgive %s env_explosion'%userid) 
        es.server.cmd('es_xfire %s env_explosion addoutput "imagnitude 300"'%userid) 
        es.server.cmd('es_xfire %s env_explosion addoutput "iradiusoverride 600"'%userid) 
        es.setindexprop(es.ServerVar('eventscripts_lastgive'), 'CBaseEntity.m_hOwnerEntity', es.getplayerhandle(userid)) 
        es.server.cmd('es_xfire %s env_explosion explode'%userid) 
        es.server.cmd('es_xfire %s env_explosion kill'%userid) 
        players[userid]['timebombed'] = 0 
    elif bombType == "freezebomb": 
        x,y,z = es.getplayerlocation(userid) 
        for player in es.getUseridList(): 
            xx,yy,zz = es.getplayerlocation(player) 
            if (((xx - x) ** 2 + (yy - y) ** 2 + (zz-z) ** 2) ** 0.5) <= 300:
                player = playerlib.Player(userid)
                gamethread.queue(player.set, ('noclip', 1))
                gamethread.queue(player.set, ('freeze', 1))
        players[userid]['freezebombed'] = 0 
    elif bombType == "firebomb": 
        x,y,z = es.getplayerlocation(userid) 
        for player in es.getUseridList(): 
            xx,yy,zz = es.getplayerlocation(player) 
            if (((xx - x) ** 2 + (yy - y) ** 2 + (zz-z) ** 2) ** 0.5) <= 300: 
                es.server.cmd('es_xfire %s !self ignite'%player) 
                gamethread.delayedname(xa_adminfirebomb_duration, 'remove_fire', _extinguish, player) 
        players[userid]['firebombed'] = 0 
        
def _extinguish(userid): 
    napalmlist = es.createentitylist("entityflame") 
    handle = es.getplayerhandle(userid) 
    for flame_entity in napalmlist: 
        string = es.getindexprop(flame_entity, 'CEntityFlame.m_hEntAttached') 
        if string == handle: 
            es.setindexprop(flame_entity, 'CEntityFlame.m_flLifetime', 0) 
            break
            
def _rocket(userid, adminid, args):
    if str(xa_adminrocket_anonymous) == "0": 
        tokens = {} 
        tokens['admin']  = es.getplayername(adminid) 
        tokens['user']   = es.getplayername(userid) 
        for player in playerlib.getPlayerList():  
            es.tell(int(player), xalanguage("rocketed", tokens, player.get("lang"))) 
    es.emitsound('player', userid, 'weapons/rpg/rocketfire1.wav', '1.0', '0.4')
    
    es.usermsg('create', 'shake', 'Shake')
    es.usermsg('write', 'byte',  'shake', 0)
    es.usermsg('write', 'float', 'shake', 25)
    es.usermsg('write', 'float', 'shake', 1.0)
    es.usermsg('write', 'float', 'shake', 3)
    es.usermsg('send', 'shake', userid)
    es.usermsg('delete', 'shake')
    
    gamethread.delayed(0.5, es.emitsound, ('player', userid, 'ambient/fire/ignite.wav', '1.0', '0.4') )
    #playerlib.getPlayer(userid).set("freeze", 1)
    rocketEffectLoop(userid, 3.0)
    
def rocketEffectLoop(userid, time):
    """ A command to make some neat effects and push a player vertically... Made by bonbon <3 """
    if time >= 0:
        time -= 0.1
        loc = es.getplayerlocation(userid)
        if time < 2.5:
            effectlib.drawBox(loc, [loc[0] + 10, loc[1] + 10, loc[2]], "materials/sprites/laser.vmt", "materials/sprites/halo01.vmt", 0.2, 20, 20, 255, 0, 0, 255, 10, 0, 0, 0, 0)
            effectlib.drawBox(loc, [loc[0] - 10, loc[1] - 10, loc[2]], "materials/sprites/laser.vmt", "materials/sprites/halo01.vmt", 0.2, 20, 20, 255, 128, 0, 255, 10, 0, 0, 0, 0)
            effectlib.drawBox([loc[0] - 5, loc[1] - 5, loc[2]], [loc[0] + 5, loc[1] + 5, loc[2]], "materials/sprites/laser.vmt", "materials/sprites/halo01.vmt", 0.2, 20, 20, 0, 0, 255, 255, 10, 0, 0, 0, 0)
            if (time * 10) % 2:
                #es.setplayerprop(userid, 'CBasePlayer.localdata.m_vecBaseVelocity', '0,0,145')
                if es.exists('userid', userid): # stops the playerlib error if the player doesn't exist
                    playerlib.getPlayer(userid).set("push", (0, 145, True) )
                else:
                    return 
        gamethread.delayed(0.1, rocketEffectLoop, (userid, time) )
    else:
        es.server.queuecmd('es_give %s env_explosion' % userid)
        es.server.queuecmd('es_xfire %s env_explosion addoutput "iMagnitude 100"' % userid)
        es.server.queuecmd('es_xfire %s env_explosion explode' % userid)
        es.server.queuecmd('damage %s %s' % (userid, es.getplayerprop(userid, 'CBasePlayer.m_iHealth') ) )
        es.emitsound('player', userid, 'ambient/explosions/exp3.wav', '1.0', '0.4')
            
def _mute(userid, adminid, args):
    steamid = es.getplayersteamid(userid)
    if userid in muted:
        del muted[userid]
        status = 'unmuted'
    else:
        muted[userid] = steamid
        status = 'muted'
    if str(xa_adminmute_anonymous) == '0':
        tokens = {}
        tokens['admin']  = es.getplayername(adminid)
        tokens['user']   = es.getplayername(userid)
        for player in playerlib.getPlayerList('#human'):
            tokens['state'] = xalanguage(status, lang=player.get("lang"))
            es.tell(int(player), '#multi', xalanguage('admin state', tokens, player.get("lang")))
    
def _unmute(steamid):
    tUserid = None
    for userid in muted:
        if muted[userid] == steamid:
            tUserid = userid
    if tUserid:
        del muted[tUserid]
        
def tick():
    for player in muted:
        for listener in players:
            es.voicechat('nolisten', listener, player)
es.addons.registerTickListener(tick)