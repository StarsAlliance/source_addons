import es
import playerlib
import gamethread
import os
from xa import xa

#plugin information
info = es.AddonInfo()
info.name       = "Reserve Slots"
info.version    = "1.2.4"
info.author     = "Errant"
info.basename   = "xareserveslots"


'''

--
Reserved slots - a full port of manis reserved slots (horrible though it is Smile) functionality for eXtendable Admin.
This module uses all the Mani configuration straight from the box.
However currently this feature does NOT support the redirect option. IF a server IP is set this is added to the kick message.
 -- 1.2.4 --
 * Fixed choosePlayer returning an integer rather than a playerlib instance if not overwritten
 -- 1.2.3 --
 * Fixed an error where "kickud" was an unkown local vairable
 -- 1.2.2 --
 * Fixed an error where player_activate was passing a string userid, not a playerlib
   instance 
 -- 1.2.1 --
 * Fixed small syntax error in logging.log()
 * Fixed call to an old method (in check_player) which changed name in 1.1.0 
 -- 1.2.0 --
 * Hunter converted this module to use the new api for xa methods
 -- 1.1.1 -- 
 * Mani file now loaded with xa.configparser (Yay Hunter)
 -- 1.1.0 --
 * [CHNG] Tweaked to use xa.configparser (plus custom method for the mani file)
 * [CHNG] Pulled a lot of the global vars out of methods
 * [CHNG] Renamed some methods for easier understanding
 * [+] Added a whole ream of comments
 * [+] Added soft redirect forwhen an IP is specified (thx to SD's xaredirect script for the ideas on how to do it)
 * [+] Auth load now use a try / except block.. just for cleanness in case at some poitn XA will load w/o an auth provider loaded
 * [-] Removed redundant call to .cfg files. All XA cfg is done "on the fly"
 -- 1.0.0 -- 
 * Added to the SVN
 -- OY4 --
 * [FIX] silly bug (my fault) where a text sting in the mani cfg was stripped of spaces.. duh!
 -- OY3 --
 * [FIX] reserved slot failing when a player joined
 * [FIX] a missing bracket
 * [TEST] getting it working some more
 -- OY2 --
 * [FIX] a load of dbg msgs
 * [+] cleaned the code slightly
 -- OY1  -- OY
 * [+] released

'''

# Register the module
xareserveslots = xa.register(info.basename)

# Get the lang file
text = xareserveslots.language.getLanguage()

# load the list of reserved players
if xa.isManiMode():
    xaReservedList = xareserveslots.configparser.getList("cfg/mani_admin_plugin/reserveslots.txt", True)
else:
    xaReservedList = None

if not xaReservedList:
    xaReservedList = xareserveslots.configparser.getList("reserved_slots_list.txt")
else:
    xaReservedList.extend(xareserveslots.configparser.getList("reserved_slots_list.txt"))

xareserveslots.registerCapability("use_slot", "ADMIN")

# kick delays list
kick_delays = []
'''
Internal  Methods
'''

def returnReservedStatus(x):
    '''
    Checks via various methods if the player x has a reserved slot
     - RETURNS False if they do have one (For playerlib purposes)
    '''
    if isinstance(x, str):
        x = playerlib.getPlayer(x)
    if xaReservedList:
        # if we have a list of reserved players then check x's steam id and return false if they are in the list
        if x.attributes['steamid'] in xaReservedList:
            return False

    if xa.isManiMode():
        # if we have mani mode on we can test for the "N" immunity for reserve slot kick immunity
        if xareserveslots.isUseridAuthorized(int(x), "n", "immunity"):
            return False
    # and finally check that they are not on the reserved list
    if xareserveslots.isUseridAuthorized(int(x), "use_slot"):
        return False

def cfg_vars():
    '''
    Register the cfg variables with xa
    '''
    vars = {
    "reserve_slots":{"val":"1", "desc":"Turn on reserve slots (1=On, 0=Off)"},
    "reserve_slots_kick_method":{"val":"0", "desc":"Reserve slots kick selection (1=By time connected, 0=By ping)"},
    "reserve_slots_redirect":{"val":"0", "desc":"Redirect people without reserved slots to an IP (will not redirect them but will give them the IP on kick)"},
    "reserve_slots_kick_message":{"val":"0", "desc":"A message to give to people when you kick them for using a reserved slot [0=use the ES language file]"},
    "reserve_slots_number_of_slots":{"val":"0", "desc":"The number of reserved slots on the server"},
    "reserve_slots_allow_slot_fill":{"val":"0", "desc":"Allow reserved slots to fill on the server [0=do not let them fill, 1=allow them to fill]"},
    }
    for x in vars:
        xareserveslots.setting.createVariable(x, vars[x]["val"], vars[x]["desc"])   
        
def check_player(userid):
    '''
    If there are too many players it checks if this new one has a reserved slot
    '''
    maxplayers = es.getmaxplayercount()
    pdiff = maxplayers - es.getplayercount()
    if pdiff <= int(xareserveslots.setting.getVariable("reserve_slots_number_of_slots")):
        # ok so there we are into the reserved slots...
        if returnReservedStatus(userid):
            # remember that ^^ returns true IF they do not have a reserve slot
            # The player is NOT allowed in a reserved slot so we kick them
            kickPlayer(playerlib.getPlayer(userid))
        else:
            # they are on the res list - so kick someone else??
            if int(xareserveslots.setting.getVariable("reserve_slots_allow_slot_fill")) == 0:
                #  we are not allowing the slots to fill so lets kick someone
                kickPlayer(chooseKick())
               
def kickPlayer(ulib):
    '''
    Kicks the player
     - If an IP is set in the cfg then it tries to soft redirect them
    '''
    uid = int(ulib) # we seemto need the uid alot so lets grab it here
    ip = str(xareserveslots.setting.getVariable("reserve_slots_redirect"))
    if ip != "0":
        # send them a dialogue box...
        msglib.VguiDialog(title=ip, time=15, mode=msglib.VguiMode.ASKCONNECT).send(uid)
        # but also set them up for a kick in 15 seconds if they dont comply
        kick_delays.append(uid)
        gamethread.delayedname(15, 'res_redirect_%s' % uid, ulib.kick, (text("ip_kick_message",{"ip":ip},ulib.get("lang"))))
    else:
        if str(xareserveslots.setting.getVariable("reserve_slots_kick_message")) == "0":
            # PLEASE use langlib :)
            msg = text("kick_message",None,ulib.get("lang"))
        else:
            msg = str(xareserveslots.setting.getVariable("reserve_slots_kick_message"))
        ulib.kick(msg)

    
def chooseKick():
    '''
    Chooses someone to kick, in the following order:
    1) Bots
    2) Either via Ping or by time (according to mani cfg)
    
     - Calls ChoosePlayer() method to return a player id if needed
    '''
    botlist = playerlib.getPlayerList("#bot")
    if len(botlist) == 1:   
        # we have to be careful here because of srcTV being in the bot list
        if botlist[0].attributes["steamid"] == "BOT":
            botlist[0]
        else:
            # aha it was  a srcTV....
            return ChoosePlayer()
    elif len(botlist) == 0:
        # just human players.. so
        return choosePlayer()
    else:
        # we have bots! so kick one
        for bot in botlist:
            if bot.attributes["steamid"] == "BOT":
                return bot
           
def choosePlayer():         
    '''
    Used by chooseKick() to determine a player to kick
    '''
    kicklist = playerlib.getPlayerList("#res")
    kickuid  = playerlib.getPlayer(es.getuserid()) # get a random player to return if none of the others return anything.
    if int(xareserveslots.setting.getVariable("reserve_slots_kick_method")) == 1:
        timelowest = None
        for id in kicklist:
            time = id.attributes["timeconnected"]   
            if timelowest is None or time < timelowest:
                timelowest = time
                kickuid = id
        return kickuid
    else:
        ping = -1
        for id in kicklist:
            pping = id.attributes["ping"]
            if pping > ping:
                ping = pping
                kickuid = id
        return kickuid
    return kickuid
                
'''
Events
'''
def load():
    #rslots = reservedSlots()
    # run the configuration variables
    cfg_vars()
    # register the playerlib player filter we have..
    playerlib.registerPlayerListFilter("res", returnReservedStatus)
    # And say were loaded!
    xareserveslots.logging.log("Loaded Reserve slots (mani clone) %s" % str(info.version))
    
    """ If XA has loaded whilst players are active, ensure they're not forgotten """
    es_map_start({})
    for player in map(str, es.getUseridList() ):
        player_activate({'userid':player})
 
def unload():
    for userid in es.getUseridList():
        gamethread.cancelDelayed('res_redirect_%s' % userid)
    xareserveslots.unregister()
   
def es_map_start(event_var):
    '''
    Reload the reserved lists on map start
    '''
    global xaReservedList
    # load the list of reserved players
    if xa.isManiMode():
        xaReservedList = xareserveslots.configparser.getList("cfg/mani_admin_plugin/reserveslots.txt", True)
    else:
        xaReservedList = None
    
    if not xaReservedList:
        xaReservedList = xareserveslots.configparser.getList("reserved_slots_list.txt")
    else:
        xaReservedList.extend(xareserveslots.configparser.getList("reserved_slots_list.txt"))
 
def player_activate(event_var):
    if xareserveslots.setting.getVariable("reserve_slots"):
        check_player(event_var["userid"])

def player_disconnect(event_var):
    '''
    Remove the players kick delays (cos it will cause errors!) if they leave
     - thx to SD's xaredirect for the idea
    '''
    global kick_delays
    userid = int(event_var['userid'])
    if userid in kick_delays:
        gamethread.cancelDelayed('res_redirect_%s' % userid)
        kick_delays.remove(userid)