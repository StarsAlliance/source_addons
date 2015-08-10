import es
import os
import time
import playerlib
from xa import xa

playertimes = {}
playerkills = {}
playerheads = {}
firstblood = False

#plugin information
info = es.AddonInfo()
info.name           = "Quake Sounds"
info.version        = "0.2"
info.author         = "Hunter"
info.basename       = "xaquakesounds"

xaquakesounds                       = xa.register(info.basename)
xalanguage                          = xaquakesounds.language.getLanguage()
xaplayerdata_quakesounds            = xaquakesounds.playerdata.createUserSetting('quakesounds')

if xa.isManiMode():
    xaquakesoundslist               = xaquakesounds.configparser.getAliasList('cfg/mani_admin_plugin/quakesoundlist.txt', True)
else:
    xaquakesoundslist               = xaquakesounds.configparser.getAliasList('quakesoundlist.txt')
if not xaquakesoundslist:
    raise ImportError('No quakesoundslist.txt found!')

quake_sounds                        = xaquakesounds.setting.createVariable('quake_sounds', '1', '0 = off, 1 = enable Quake Sounds')
quake_sounds_download               = xaquakesounds.setting.createVariable('quake_auto_download', '0', '0 = Don\'t auto download files to client, 1 = automatically download files to client')
quake_sounds_settings               = xaquakesounds.setting.createVariable('player_settings_quake', '1', '0 = player settings default to off, 1 = player settings default to on')
quake_kill_streak_mode              = xaquakesounds.setting.createVariable('quake_kill_streak_mode', '0', 'Reset kill streaks per round 1 = per round/death, 0 = per death')
quake_humiliation_mode              = xaquakesounds.setting.createVariable('quake_humiliation_mode', '1', '0 = off, 1 = all players hear it, 2 = players involved hear it, 3 = attacker hears it, 4 = victim hears it')
quake_humiliation_visual_mode       = xaquakesounds.setting.createVariable('quake_humiliation_visual_mode', '1', '0 = off, 1 = all players see it, 2 = players involved see it, 3 = attacker sees it, 4 = victim sees it')
quake_humiliation_weapon            = xaquakesounds.setting.createVariable('quake_humiliation_weapon', 'knife', 'Weapon that triggers the humiliation sound')
quake_humiliation_weapon2           = xaquakesounds.setting.createVariable('quake_humiliation_weapon2', '', 'Second weapon that triggers the humiliation sound')
quake_firstblood_mode               = xaquakesounds.setting.createVariable('quake_firstblood_mode', '1', '0 = off, 1 = all players hear it, 2 = players involved hear it, 3 = attacker hears it, 4 = victim hears it')
quake_firstblood_visual_mode        = xaquakesounds.setting.createVariable('quake_firstblood_visual_mode', '1', '0 = off, 1 = all players see it, 2 = players involved see it, 3 = attacker sees it, 4 = victim sees it')
quake_firstblood_reset_per_round    = xaquakesounds.setting.createVariable('quake_firstblood_reset_per_round', '1', 'CSS Only, 1 = reset per round, 0 = per map')
quake_headshot_mode                 = xaquakesounds.setting.createVariable('quake_headshot_mode', '1', '0 = off, 1 = all players hear it, 2 = players involved hear it, 3 = attacker hears it, 4 = victim hears it')
quake_headshot_visual_mode          = xaquakesounds.setting.createVariable('quake_headshot_visual_mode', '3', '0 = off, 1 = all players see it, 2 = players involved see it, 3 = attacker sees it, 4 = victim sees it')
quake_prepare_to_fight_mode         = xaquakesounds.setting.createVariable('quake_prepare_to_fight_mode', '0', '0 = off, 1 = all players hear it, 2 = players involved hear it, 3 = attacker hears it, 4 = victim hears it')
quake_prepare_to_fight_visual_mode  = xaquakesounds.setting.createVariable('quake_prepare_to_fight_visual_mode', '1', '0 = off, 1 = all players see it, 2 = players involved see it, 3 = attacker sees it, 4 = victim sees it')
quake_multi_kill_mode               = xaquakesounds.setting.createVariable('quake_multi_kill_mode', '0', '0 = off, 1 = all players hear it, 2 = players involved hear it, 3 = attacker hears it, 4 = victim hears it')
quake_multi_kill_visual_mode        = xaquakesounds.setting.createVariable('quake_multi_kill_visual_mode', '1', '0 = off, 1 = all players see it, 2 = players involved see it, 3 = attacker sees it, 4 = victim sees it')
quake_team_killer_mode              = xaquakesounds.setting.createVariable('quake_team_killer_mode', '1', '0 = off, 1 = all players hear it, 2 = players involved hear it, 3 = attacker hears it, 4 = victim hears it')
quake_team_killer_visual_mode       = xaquakesounds.setting.createVariable('quake_team_killer_visual_mode', '1', '0 = off, 1 = all players see it, 2 = players involved see it, 3 = attacker sees it, 4 = victim sees it')

xaquakekills = {}
xaquakekills['dominating'] = {}
xaquakekills['dominating']['mode']            = xaquakesounds.setting.createVariable('quake_dominating_mode', '0', '0 = off, 1 = all players hear it, 2 = players involved hear it, 3 = attacker hears it, 4 = victim hears it')
xaquakekills['dominating']['visual_mode']     = xaquakesounds.setting.createVariable('quake_dominating_visual_mode', '3', '0 = off, 1 = all players see it, 2 = players involved see it, 3 = attacker sees it, 4 = victim sees it')
xaquakekills['dominating']['trigger_count']   = xaquakesounds.setting.createVariable('quake_dominating_trigger_count', '4', 'Kills streak required to trigger sound')
xaquakekills['rampage'] = {}
xaquakekills['rampage']['mode']               = xaquakesounds.setting.createVariable('quake_rampage_mode', '0', '0 = off, 1 = all players hear it, 2 = players involved hear it, 3 = attacker hears it, 4 = victim hears it')
xaquakekills['rampage']['visual_mode']        = xaquakesounds.setting.createVariable('quake_rampage_visual_mode', '1', '0 = off, 1 = all players see it, 2 = players involved see it, 3 = attacker sees it, 4 = victim sees it')
xaquakekills['rampage']['trigger_count']      = xaquakesounds.setting.createVariable('quake_rampage_trigger_count', '6', 'Kills streak required to trigger sound')
xaquakekills['killingspree'] = {}
xaquakekills['killingspree']['mode']          = xaquakesounds.setting.createVariable('quake_killing_spree_mode', '0', '0 = off, 1 = all players hear it, 2 = players involved hear it, 3 = attacker hears it, 4 = victim hears it')
xaquakekills['killingspree']['visual_mode']   = xaquakesounds.setting.createVariable('quake_killing_spree_visual_mode', '3', '0 = off, 1 = all players see it, 2 = players involved see it, 3 = attacker sees it, 4 = victim sees it')
xaquakekills['killingspree']['trigger_count'] = xaquakesounds.setting.createVariable('quake_killing_spree_trigger_count', '8', 'Kills streak required to trigger sound')
xaquakekills['monsterkill'] = {}
xaquakekills['monsterkill']['mode']           = xaquakesounds.setting.createVariable('quake_monster_kill_mode', '0', '0 = off, 1 = all players hear it, 2 = players involved hear it, 3 = attacker hears it, 4 = victim hears it')
xaquakekills['monsterkill']['visual_mode']    = xaquakesounds.setting.createVariable('quake_monster_kill_visual_mode', '3', '0 = off, 1 = all players see it, 2 = players involved see it, 3 = attacker sees it, 4 = victim sees it')
xaquakekills['monsterkill']['trigger_count']  = xaquakesounds.setting.createVariable('quake_monster_kill_trigger_count', '10', 'Kills streak required to trigger sound')
xaquakekills['unstoppable'] = {}
xaquakekills['unstoppable']['mode']           = xaquakesounds.setting.createVariable('quake_unstoppable_mode', '0', '0 = off, 1 = all players hear it, 2 = players involved hear it, 3 = attacker hears it, 4 = victim hears it')
xaquakekills['unstoppable']['visual_mode']    = xaquakesounds.setting.createVariable('quake_unstoppable_visual_mode', '1', '0 = off, 1 = all players see it, 2 = players involved see it, 3 = attacker sees it, 4 = victim sees it')
xaquakekills['unstoppable']['trigger_count']  = xaquakesounds.setting.createVariable('quake_unstoppable_trigger_count', '12', 'Kills streak required to trigger sound')
xaquakekills['ultrakill'] = {}
xaquakekills['ultrakill']['mode']             = xaquakesounds.setting.createVariable('quake_ultra_kill_mode', '0', '0 = off, 1 = all players hear it, 2 = players involved hear it, 3 = attacker hears it, 4 = victim hears it')
xaquakekills['ultrakill']['visual_mode']      = xaquakesounds.setting.createVariable('quake_ultra_kill_visual_mode', '1', '0 = off, 1 = all players see it, 2 = players involved see it, 3 = attacker sees it, 4 = victim sees it')
xaquakekills['ultrakill']['trigger_count']    = xaquakesounds.setting.createVariable('quake_ultra_kill_trigger_count', '14', 'Kills streak required to trigger sound')
xaquakekills['godlike'] = {}
xaquakekills['godlike']['mode']               = xaquakesounds.setting.createVariable('quake_god_like_mode', '0', '0 = off, 1 = all players hear it, 2 = players involved hear it, 3 = attacker hears it, 4 = victim hears it')
xaquakekills['godlike']['visual_mode']        = xaquakesounds.setting.createVariable('quake_god_like_visual_mode', '1', '0 = off, 1 = all players see it, 2 = players involved see it, 3 = attacker sees it, 4 = victim sees it')
xaquakekills['godlike']['trigger_count']      = xaquakesounds.setting.createVariable('quake_god_like_trigger_count', '16', 'Kills streak required to trigger sound')
xaquakekills['wickedsick'] = {}
xaquakekills['wickedsick']['mode']            = xaquakesounds.setting.createVariable('quake_wicked_sick_mode', '0', '0 = off, 1 = all players hear it, 2 = players involved hear it, 3 = attacker hears it, 4 = victim hears it')
xaquakekills['wickedsick']['visual_mode']     = xaquakesounds.setting.createVariable('quake_wicked_sick_visual_mode', '1', '0 = off, 1 = all players see it, 2 = players involved see it, 3 = attacker sees it, 4 = victim sees it')
xaquakekills['wickedsick']['trigger_count']   = xaquakesounds.setting.createVariable('quake_wicked_sick_trigger_count', '18', 'Kills streak required to trigger sound')
xaquakekills['ludicrouskill'] = {}
xaquakekills['ludicrouskill']['mode']         = xaquakesounds.setting.createVariable('quake_ludicrous_kill_mode', '0', '0 = off, 1 = all players hear it, 2 = players involved hear it, 3 = attacker hears it, 4 = victim hears it')
xaquakekills['ludicrouskill']['visual_mode']  = xaquakesounds.setting.createVariable('quake_ludicrous_kill_visual_mode', '1', '0 = off, 1 = all players see it, 2 = players involved see it, 3 = attacker sees it, 4 = victim sees it')
xaquakekills['ludicrouskill']['trigger_count']= xaquakesounds.setting.createVariable('quake_ludicrous_kill_trigger_count', '20', 'Kills streak required to trigger sound')
xaquakekills['holyshit'] = {}
xaquakekills['holyshit']['mode']              = xaquakesounds.setting.createVariable('quake_holy_shit_mode', '0', '0 = off, 1 = all players hear it, 2 = players involved hear it, 3 = attacker hears it, 4 = victim hears it')
xaquakekills['holyshit']['visual_mode']       = xaquakesounds.setting.createVariable('quake_holy_shit_visual_mode', '1', '0 = off, 1 = all players see it, 2 = players involved see it, 3 = attacker sees it, 4 = victim sees it')
xaquakekills['holyshit']['trigger_count']     = xaquakesounds.setting.createVariable('quake_holy_shit_trigger_count', '24', 'Kills streak required to trigger sound')

def load():
    xaquakesounds.addRequirement("xasettings")
    xaquakesounds.xasettings.registerMethod("xaquakesounds", _switch_setting, xalanguage["quake sounds"])
    
    """ If XA is loaded whilst players are active, add them all """
    if str(es.ServerVar('eventscripts_currentmap')) != "":
        es_map_start({})
    for player in es.getUseridList():
        player_activate({'userid':player})

def unload():
    xaquakesounds.xasettings.unregister("xaquakesounds")
    xaquakesounds.delRequirement("xasettings")
    xaquakesounds.unregister()

def es_map_start(event_var):
    global firstblood, quake_sounds
    firstblood = True
    for userid in es.getUseridList():
        playerkills[userid] = 0
        playertimes[userid] = 0
        playerheads[userid] = False
    if len(xaquakesoundslist) > 0:
        if int(quake_sounds_download) == 1:
            for sound in xaquakesoundslist:
                es.stringtable('downloadables', 'sound/%s'%xaquakesoundslist[sound])
    else:
        quake_sounds.set('0')

def round_start(event_var):
    global firstblood
    if quake_firstblood_reset_per_round and int(quake_firstblood_reset_per_round) == 1:
        firstblood = True
    for userid in es.getUseridList():
        if (not userid in playerkills) or (int(quake_kill_streak_mode) == 1):
            playerkills[userid] = 0
    if quake_sounds and int(quake_sounds) == 1:
        _play_quakesound(xaquakesoundslist['prepare'], 'prepare', 0, 0, int(quake_prepare_to_fight_mode), int(quake_prepare_to_fight_visual_mode))

def player_activate(event_var):
    userid = int(event_var['userid'])
    playerkills[userid] = 0
    playertimes[userid] = 0
    playerheads[userid] = False
    if not xaplayerdata_quakesounds.exists(userid):
        xaplayerdata_quakesounds.set(userid, int(quake_sounds_settings))
    
def player_disconnect(event_var):
    userid = int(event_var['userid'])
    playerkills[userid] = 0
    playertimes[userid] = 0
    playerheads[userid] = False

def player_spawn(event_var):
    userid = int(event_var['userid'])
    playertimes[userid] = 0
    playerheads[userid] = False
    if not userid in playerkills:
        playerkills[userid] = 0
    if not xaplayerdata_quakesounds.exists(userid):
        xaplayerdata_quakesounds.set(userid, int(quake_sounds_settings))

def player_hurt(event_var):
    try:
        userid = int(event_var['userid'])
        attackerid = int(event_var['attacker'])
        hitgroup = int(event_var['hitgroup'])
        health = int(event_var['health'])
        if (userid > 0) and (attackerid > 0) and (hitgroup == 1) and (health == 0):
            playerheads[userid] = True
    except:
        pass

def player_death(event_var):
    global firstblood
    if quake_sounds and int(quake_sounds) == 1:
        userid = int(event_var['userid'])
        attackerid = int(event_var['attacker'])
        if userid > 0:
            playerkills[userid] = 0
        if attackerid > 0:
            if attackerid in playerkills:
                playerkills[attackerid] += 1
            else:
                playerkills[attackerid] = 1
            if attackerid in playertimes:
                lastkill = int(time.time()) - playertimes[attackerid]
                if lastkill < 2:
                    _play_quakesound(xaquakesoundslist['multikill'], 'multikill', userid, attackerid, int(quake_multi_kill_mode), int(quake_multi_kill_visual_mode))
                playertimes[attackerid] = int(time.time())
            else:
                playertimes[attackerid] = int(time.time())
        if (userid > 0) and (attackerid > 0) and (userid != attackerid):
            userteam = int(event_var['es_userteam'])
            attackerteam = int(event_var['es_attackerteam'])
            weapon = str(event_var['weapon'])
            try:
                if int(event_var['headshot']):
                    playerheads[userid] = True
            except:
                pass
            if (userteam == attackerteam):
                _play_quakesound(xaquakesoundslist['teamkiller'], 'teamkiller', userid, attackerid, int(quake_team_killer_mode), int(quake_team_killer_visual_mode))
            elif (weapon == str(quake_humiliation_weapon)) or (weapon == str(quake_humiliation_weapon2)):
                _play_quakesound(xaquakesoundslist['humiliation'], 'humiliation', userid, attackerid, int(quake_humiliation_mode), int(quake_humiliation_visual_mode))
            elif firstblood == True:
                firstblood = False
                if int(quake_firstblood_mode) >= 1:
                    _play_quakesound(xaquakesoundslist['firstblood'], 'firstblood', userid, attackerid, int(quake_firstblood_mode), int(quake_firstblood_visual_mode))
            elif playerheads[userid] == True:
                playerheads[userid] = False
                _play_quakesound(xaquakesoundslist['headshot'], 'headshot', userid, attackerid, int(quake_headshot_mode), int(quake_headshot_visual_mode))
            else:
                _prepare_killsound(userid, attackerid)
            
def _switch_setting(userid):
    if int(xaplayerdata_quakesounds.get(userid)) == 1:
        xaplayerdata_quakesounds.set(userid, 0)
        player = playerlib.getPlayer(userid)
        es.tell(userid, xalanguage('turn off', {}, player.get("lang")))
    else:
        xaplayerdata_quakesounds.set(userid, 1)
        player = playerlib.getPlayer(userid)
        es.tell(userid, xalanguage('turn on', {}, player.get("lang")))

def _prepare_killsound(userid, attackerid):
    killcount = int(playerkills[attackerid])
    for soundname in xaquakekills:
        triggercount = int(xaquakekills[soundname]['trigger_count'])
        if killcount == triggercount:
            _play_quakesound(xaquakesoundslist[soundname], soundname, userid, attackerid, int(xaquakekills[soundname]['mode']), int(xaquakekills[soundname]['visual_mode']))

def _play_quakesound(soundfile, soundname, userid, attackerid, mode, visual_mode):
    if mode == 0:
        useridlist_sound = []
    elif mode == 1:
        useridlist_sound = es.getUseridList()
    elif mode == 2:
        useridlist_sound = [userid, attackerid]
    elif mode == 3:
        useridlist_sound = [attackerid]
    elif mode == 4:
        useridlist_sound = [userid]
    else:
        useridlist_sound = es.getUseridList()
    if visual_mode == 0:
        useridlist_text = []
    elif visual_mode == 1:
        useridlist_text = es.getUseridList()
    elif visual_mode == 2:
        useridlist_text = [userid, attackerid]
    elif visual_mode == 3:
        useridlist_text = [attackerid]
    elif visual_mode == 4:
        useridlist_text = [userid]
    else:
        useridlist_text = es.getUseridList()
    if attackerid > 0:
        langdata = {"username":es.getplayername(attackerid)}
    else:
        langdata = {}
    for userid in useridlist_sound:
        if int(xaplayerdata_quakesounds.get(userid)) == 1:
            es.playsound(userid, soundfile, 1.0)
    for userid in useridlist_text:
        if int(xaplayerdata_quakesounds.get(userid)) == 1:
            player = playerlib.getPlayer(userid)
            soundtext = xalanguage(soundname, langdata, player.get("lang"))
            es.usermsg('create', 'centermsg', 'TextMsg')
            es.usermsg('write', 'byte', 'centermsg', '4')
            es.usermsg('write', 'string', 'centermsg', str(soundtext))
            es.usermsg('send', 'centermsg', str(userid))
            es.usermsg('delete', 'centermsg')
