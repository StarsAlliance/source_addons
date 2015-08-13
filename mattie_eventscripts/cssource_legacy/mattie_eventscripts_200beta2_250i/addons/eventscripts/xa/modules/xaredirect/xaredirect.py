# ./xa/modules/xaredirect/xaredirect.py


import es
import gamethread
import msglib
import playerlib
from xa import xa

#plugin information
info = es.AddonInfo() 
info.name     = "Redirect Users"
info.version  = "1.1" 
info.author   = "Unknown"
info.basename = "xaredirect"

#######################################
# MODULE SETUP
# Register the module
# this is a global reference to our module

xaredirect = xa.register(info.basename)


#######################################
# SERVER VARIABLES
# The list of our server variables

var_ip    = xaredirect.setting.createVariable('redirect_ip', '127.0.0.1:27015', 'IP players will be redirected to')
var_delay = xaredirect.setting.createVariable('redirect_delay', 15, 'Number of seconds to show redirect prompt')
var_kick  = xaredirect.setting.createVariable('redirect_kick', 0, '0 = do nothing when players choose not to be redirected, 1 = kick players who choose not to be redirected')
var_count = xaredirect.setting.createVariable('redirect_count', 0, 'Number of connected players required to automatically send redirect prompt, 0 = never automatically send redirect prompt')


#######################################
# GLOBALS
# Initialize our general global data here.

# Localization helper:
func_lang_text = xaredirect.language.getLanguage()

# Outstanding kick delays:
list_delays = []


#######################################
# LOAD AND UNLOAD
# Formal system registration and unregistration

def load():
    """
    Registers the xaredirect server, say, and client command
    """
    xaredirect.addCommand('xa_redirect', redirect_cmd, 'redirect_client', 'ADMIN').register(('server', 'say', 'console'))
    
    """ If XA is loaded whilst players are active, ensure they're not forgotten """
    for player in es.getUseridList():
        player_activate({'userid':player})


def unload():
    """
    Unregisters xaredirect with XA
    Calls es_map_start to clear delays
    """
    xaredirect.unregister()

    es_map_start({})


#######################################
# MODULE FUNCTIONS
# xaredirect module functions

def es_map_start(event_var):
    """Cancels outstanding delays and clears list_delays"""
    global list_delays

    for int_userid in list_delays:
       gamethread.cancelDelayed('xaredirect_%s' % int_userid)

    list_delays[:] = []


def player_activate(event_var):
    """Calls send_prompt if the player count is at the requisite number"""
    int_count_option = int(var_count)
    if int_count_option:
        if int_count_option <= es.getplayercount():
            send_prompt(int(event_var['userid']), str(var_ip), int(var_kick), float(var_delay))


def player_disconnect(event_var):
    """Cancels the delay if the client was redirected"""
    global list_delays

    int_userid = int(event_var['userid'])
    if int_userid in list_delays:
        gamethread.cancelDelayed('xaredirect_%s' % int_userid)
        list_delays.remove(int_userid)


def send_prompt(int_userid, str_ip, int_kick, float_delay):
    """
    Sends the redirect prompt
    Creates a delay for kicking the client
    """
    global list_delays

    msglib.VguiDialog(title=str_ip, time=float_delay, mode=msglib.VguiMode.ASKCONNECT).send(int_userid)

    if int_kick:
        if int_userid in list_delays:
            gamethread.cancelDelayed('xaredirect_%s' % int_userid)
        else:
            list_delays.append(int_userid)
        gamethread.delayedname(float_delay, 'xaredirect_%s' % int_userid, kick_player, (int_userid, str_ip))


def kick_player(int_userid, str_ip):
    """
    Kicks the client for not redirecting
    Does not kick clients who are authorized to redirect others
    """
    global list_delays

    if es.exists('userid', int_userid):
        if not xaredirect.isUseridAuthorized(int_userid, 'redirect_client'):
            player_kick = playerlib.getPlayer(int_userid)
            player_kick.kick(func_lang_text('kick', {'ip':str_ip}, player_kick.get('lang')))

    if int_userid in list_delays:
        list_delays.remove(int_userid)


def redirect_cmd():
    """
    redirect <userid/player name/"Steam ID"> ["IP"] [kick] [delay]
    Ensures a correct number of arguments were provided
    Ensures the specified player exists
    Retrieves the optional arguments while converting them to the desired type
    Calls send_prompt with the specified arguments
    """
    int_arg_count = es.getargc()
    int_cmd_userid = es.getcmduserid()

    if int_arg_count in (2, 3, 4, 5):
        str_player_arg = es.getargv(1)
        int_userid = es.getuserid(str_player_arg)

        if int_userid:
            list_args = [int_userid, str(var_ip), int(var_kick), float(var_delay)]
            dict_arg_types = {2:str, 3:int, 4:float}
            for int_x in range(2, int_arg_count):
                try:
                    list_args[int_x - 1] = dict_arg_types[int_x](es.getargv(int_x))
                except:
                    display_feedback(int_cmd_userid, 'invalid argument', {'arg':es.getargv(int_x), 'type':dict_arg_types[int_x].__name__})
                    return

            send_prompt(*list_args)

        else:
            display_feedback(int_cmd_userid, 'no player', {'player':str_player_arg})

    else:
        display_feedback(int_cmd_userid, 'syntax', {'syntax':'xaredirect <userid/player name/\"Steam ID\"> [\"IP\"] [kick] [delay]'})


def display_feedback(int_cmd_userid, str_text, dict_tokens):
    """Displays command feedback to the player or console"""
    if int_cmd_userid:
        es.tell(int_cmd_userid, func_lang_text(str_text, dict_tokens, playerlib.getPlayer(int_cmd_userid).get('lang')))

    else:
        es.dbgmsg(0, func_lang_text(str_text, dict_tokens))
