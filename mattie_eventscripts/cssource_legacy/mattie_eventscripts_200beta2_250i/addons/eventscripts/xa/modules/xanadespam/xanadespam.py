# ./xa/modules/xanadespam/xanadespam.py

import es
import playerlib
from xa import xa

#plugin information
info = es.AddonInfo() 
info.name     = "Grenade Spam Prevention" 
info.version  = "1.2" 
info.author   = "Unknown"
info.basename = "xanadespam"

#######################################
# MODULE SETUP
# Register the module
# this is a global reference to our module
xanadespam = xa.register(info.basename)


#######################################
# SERVER VARIABLES
# The list of our server variables

punish_strip = xanadespam.setting.createVariable('nadespam_punishment_strip', 0, '0 = do not strip weapons as punishment, 1 = strip weapons as punishment')
punish_cash  = xanadespam.setting.createVariable('nadespam_punishment_cash', 0, '0 = do not remove cash as punishment, 1 = remove cash as punishment')
punish_slay  = xanadespam.setting.createVariable('nadespam_punishment_slay', 0, '0 = do not slay as punishment, 1 = slay as punishment')
punish_kick  = xanadespam.setting.createVariable('nadespam_punishment_kick', 0, '0 = do not kick as punishment, 1 = kick as punishment')

dict_grenade_limits = {'hegrenade':xanadespam.setting.createVariable('nadespam_limit_he', 1, 'Maximum number of HE grenades players may purchase per round'), 'flashbang':xanadespam.setting.createVariable('nadespam_limit_flashbang', 2, 'Maximum number of flashbangs players may purchase per round'), 'smokegrenade':xanadespam.setting.createVariable('nadespam_limit_smoke', 1, 'Maximum number of smoke grenades players may purchase per round')}


#######################################
# GLOBALS
# Initialize our general global data here.

dict_players = {} # Number of each type of grenade a player has purchased
dict_grenade_names = {'he':'hegrenade', 'fb':'flashbang', 'sg':'smokegrenade'}

# Localization helper:
func_lang_text = xanadespam.language.getLanguage()


#######################################
# LOAD AND UNLOAD
# Formal system registration and unregistration
def load():
    xanadespam.registerCapability('immune_nadespam', 'ADMIN', 'IMMUNITY')
    """ If XA is loaded late, ensure all userid's are inserted """
    for player in es.getUseridList():
        player_activate({'userid':player})

def unload():
    es.addons.unregisterClientCommandFilter(_cc_filter)

    # Unregister the module
    xanadespam.unregister()


#######################################
# MODULE FUNCTIONS
# Register your module's functions


def round_start(event_var):
    """Initializes dictionary with the number of grenades each player starts the round with."""
    global dict_players

    dict_players.clear()
    for player in playerlib.getPlayerList('#all'):
        dict_current_player = dict_players[int(player)] = {}
        for str_grenade in dict_grenade_names:
            dict_current_player[dict_grenade_names[str_grenade]] = player.get(str_grenade)
round_start({})


def player_activate(event_var):
    """Creates the player in the dictionary"""
    global dict_players
    dict_players[int(event_var['userid'])] = {'hegrenade':0, 'flashbang':0, 'smokegrenade':0}


def player_disconnect(event_var):
    """Removes the disconnecting player from the dictionary."""
    global dict_players

    userid = int(event_var['userid'])
    if dict_players.has_key(userid):
        del dict_players[userid]


def _cc_filter(userid, args):
    """Eats the client command if the player tries to buy more grenades than allowed."""
    global dict_players
    if not args:
        return True
    if args[0].lower() == 'buy' and len(args) > 1:
        item = args[1].lower().replace('weapon_', '')
        if dict_grenade_limits.has_key(item):
            count = dict_players[userid][item] = dict_players[userid][item] + 1
            if count > dict_grenade_limits[item] and not xanadespam.isUseridAuthorized(userid, 'immune_nadespam'):
                player = playerlib.getPlayer(userid)
                player_lang = player.get('lang')
                es.tell(userid, func_lang_text('limit %s' % item, {}, player_lang))

                if int(punish_strip):
                    es.server.queuecmd('es_xfire %s player_weaponstrip kill' % int_userid)
                    es.server.queuecmd('es_xgive %s player_weaponstrip' % int_userid)
                    es.server.queuecmd('es_xfire %s player_weaponstrip strip' % int_userid)

                if int(punish_cash):
                    player.set('cash', 0)

                if int(punish_slay):
                    player.kill()

                if int(punish_kick):
                    player.kick(func_lang_text('kick', {}, player_lang))

                return False
    return True

es.addons.registerClientCommandFilter(_cc_filter)
