# ./xa/modules/xatimeleft/xatimeleft.py

import es
import time
from xa import xa

#plugin information
info = es.AddonInfo()
info.name       = "Timeleft"
info.version    = "1.2"
info.author     = "Unknown"
info.basename   = "xatimeleft"

#######################################
# MODULE SETUP
# Register the module
# this is a global reference to your module
xatimeleft = xa.register(info.basename)


startTime          = 0
playersConnected   = False
reset              = True

def load():
    """ Initialize and register the module with XA Core """
    xatimeleft.addCommand('timeleft', timeleft_cmd, 'display_timeleft', 'UNRESTRICTED').register(('console', 'say'))
    
    """ If XA loads late, then send es_map_start event to load the start time """
    if str(es.ServerVar('eventscripts_currentmap')) != "":
        es_map_start({})


def es_map_start(event_var):
    """ Called when the map starts. Reset the start time and players connected """
    global startTime
    global playersConnected
    startTime = time.time()
    playersConnected = bool(es.getUseridList())
    
def round_end(event_var):
    """
    If the round ends with reason 16 it means the round is restarting. This resets
    the timer, so we should make sure our timer resets too.
    """
    global reset
    if event_var['reason'] == "16":
        reset = True

def player_connect(event_var):
    """
    When a player activates the event player_connect for the first time, Valve
    reset the map timer so we need to ensure that the timer is correct. We also
    need to add 1 to the startTime as for some reason it takes a second longer
    for the server to recognise the event.
    """
    global playersConnected
    global startTime
    if playersConnected is False:
        startTime = (time.time() - 1)
        playersConnected = True
      
def round_start(event_var):
    """
    When a new round starts, check to see if the previous round ended due to a
    round restart. If so, then reset the start timer.
    """
    global reset
    global startTime
    if reset:
        reset = False
        startTime = time.time()

def unload():
    """ Unregister itself from xa core when unloaded """
    xatimeleft.unregister()


def timeleft_cmd():
    """ 
    Called when the 'timeleft' chat command is run. Tell the user the time
    remaining
    """
    userid = es.getcmduserid()
    xatimeleft.logging.log('xatimeleft request by %s (%s)' % (es.getplayersteamid(userid), es.getplayername(userid)))
    timeLeft = getTimeLeft()
    if timeLeft > -1:
        if timeLeft:
            es.tell(userid, 'Time left in map: %.0f:%02d' % divmod(timeLeft, 60) )
        else:
            es.tell(userid, 'This is the last round')
    else:
        es.tell(userid, 'No map time limit')
      
def getTimeLeft(moduleInstance = None):
    """ A function to return the amount of time left on the server in seconds """
    maptime = float(es.ServerVar('mp_timelimit')) * 60
    if maptime:
        timeLeft = maptime - (time.time() - startTime)
        if timeLeft < 0:
            timeLeft = 0
        return timeLeft
    return -1