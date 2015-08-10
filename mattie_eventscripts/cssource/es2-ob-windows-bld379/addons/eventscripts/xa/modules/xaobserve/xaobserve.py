# ./xa/modules/xaobserve/xaobserve.py

"""
TODO: Allow admin-view with mp_forcecamera
"""

import es
import gamethread
import playerlib
import random
from xa import xa

#plugin information
info = es.AddonInfo() 
info.name     = "Observe" 
info.version  = "1.1" 
info.author   = "Unknown"
info.basename = "xaobserve"

#######################################
# MODULE SETUP
# Register the module
# this is a global reference to our module

xaobserve = xa.register('xaobserve')


#######################################
# SERVER VARIABLES
# The list of our server variables

allow_chase = xaobserve.setting.createVariable('observe_allow_chase', 1, 'xaobserve: 0 = only allow first-person view for dead players, 1 = allow frist-person or chase-cam view for dead players')
spec_delay  = xaobserve.setting.createVariable('observe_spec_delay',  3, 'xaobserve: Number of seconds after death a player can be spectated')


#######################################
# GLOBALS
# We initialize our general global data here.

# Module globals
delays       = []
dead_players = {}
team_handles = {2:[], 3:[]}


#######################################
# LOAD AND UNLOAD
# Formal system registration and unregistration

def load():
    """
    Logs the module load with XA
    Registers the "observe_opponent" ability with the authorization service
    """
    xaobserve.registerCapability('observe_opponent', 'ADMIN')
    
    round_start({})


def unload():
    """
    Unregisters the module with XA
    Cancels outstanding delays and unregisters client command filter
    """
    # Unregister the module
    xaobserve.unregister()

    cancel_delays()


#######################################
# MODULE FUNCTIONS
# xaobserver module functions

def round_start(event_var):
    """
    Cancels outstanding delays and unregisters client command filter
    Refreshes the dictionary of living player handles
    """
    global team_handles

    cancel_delays()

    team_handles = {2:[], 3:[]}
    for userid in es.getUseridList():
        add_player_handle(userid, es.getplayerteam(userid))


def player_spawn(event_var):
    """Ensures the player's handle is in the dictionary of living player handles and not in the dictionary of dead players"""
    if not es.getplayerprop(event_var['userid'], 'CBasePlayer.pl.deadflag'):
        add_player_handle(int(event_var['userid']), int(event_var['es_userteam']))


def player_death(event_var):
    """
    Removes the dead player's handle from the dictionary of living player handles
    Registers client command filter if this is the first unauthorized dead player
    Adds the player to the dictionary of dead players to monitor if the player is not authorized to observe opponents
    """
    userid = int(event_var['userid'])
    team   = int(event_var['es_userteam']) if event_var['es_userteam'] else 0
    handle = es.getplayerhandle(userid)

    if team in team_handles:
        for loop_userid in dead_players:
            if dead_players[loop_userid] == handle:
                gamethread.delayedname(float(spec_delay), 'xaobserve_%s' % loop_userid, end_spec_delay, loop_userid)
                if loop_userid not in delays:
                    delays.append(loop_userid)

        if handle in team_handles[team]:
            team_handles[team].remove(handle)

    if not xaobserve.isUseridAuthorized(userid, 'observe_opponent') and event_var['es_steamid'] <> 'BOT':
        if not dead_players:
            es.addons.registerClientCommandFilter(client_command_filter)

        dead_players[userid] = -1
        gamethread.delayedname(float(spec_delay), 'xaobserve_%s' % userid, end_spec_delay, (userid, True) )
        if userid not in delays:
            delays.append(userid)


def player_disconnect(event_var):
    """
    Cancels any delays for the disconnecting player
    Removes the disconnecting player from the dictionary of unauthorized dead players
    """
    userid = int(event_var['userid'])
    if userid in delays:
        gamethread.cancelDelayed('xaobserve_%s' % userid)
        delays.remove(userid)

    if userid in dead_players:
        del dead_players[userid]
        if not dead_players:
            es.addons.unregisterClientCommandFilter(client_command_filter)


def client_command_filter(userid, args):
    """
    Checks all non-admin dead players for spectating an opponent
    """
    team = es.getplayerteam(userid)
    if userid not in dead_players or not args or team not in (2, 3):
        return True

    if userid in delays:
        gamethread.cancelDelayed('xaobserve_%s' % userid)
        delays.remove(userid)

    if len(args):
        if args[0] == 'spec_mode':
            if es.getplayerprop(userid, 'CBasePlayer.m_iObserverMode') == 3 and int(allow_chase):
                es.setplayerprop(userid, 'CBasePlayer.m_iObserverMode', 4)
            else:
                es.setplayerprop(userid, 'CBasePlayer.m_iObserverMode', 3)
            return False
    
        elif args[0] == 'spec_next' and team_handles[team]:
            target_handle = es.getplayerprop(userid, 'CBasePlayer.m_hObserverTarget')
            if target_handle in team_handles[team]:
                target_index = team_handles[team].index(target_handle) + 1
                if target_index >= len(team_handles[team]):
                    target_index = 0
                dead_players[userid] = team_handles[team][target_index]
            else:
                dead_players[userid] = team_handles[team][0]
            es.setplayerprop(userid, 'CBasePlayer.m_hObserverTarget', dead_players[userid])
            return False
    
        elif args[0] == 'spec_prev' and team_handles[team]:
            target_handle = es.getplayerprop(userid, 'CBasePlayer.m_hObserverTarget')
            if target_handle in team_handles[team]:
                target_index = team_handles[team].index(target_handle) - 1
                if target_index < 0:
                    target_index = len(team_handles[team]) - 1
                dead_players[userid] = team_handles[team][target_index]
            else:
                dead_players[userid] = team_handles[team][0]
            es.setplayerprop(userid, 'CBasePlayer.m_hObserverTarget', dead_players[userid])
            return False

    return True


def end_spec_delay(userid, set_mode=False):
    """
    Removes the delay from the list of delays
    Forces the client to spectate a teammate
    """
    if userid in delays:
        delays.remove(userid)

    if set_mode:
        client_command_filter(userid, ['spec_mode'])
    client_command_filter(userid, ['spec_next'])


def add_player_handle(userid, team):
    """Adds the player's handle to the dictionary of player handles according to team"""
    if team in (2, 3):
        handle = es.getplayerhandle(userid)
        if handle not in team_handles[team]:
            team_handles[team].append(handle)

    if playerlib.getPlayer(userid).get('isdead'):
        dead_players[userid] = -1
        end_spec_delay(userid)

    elif userid in dead_players:
        del dead_players[userid]


def cancel_delays():
    """
    Cancels delays for dead players
    Unregisters client command filter
    """
    for userid in delays:
        gamethread.cancelDelayed('xaobserve_%s' % userid)

    if dead_players:
        es.addons.unregisterClientCommandFilter(client_command_filter)
        dead_players.clear()