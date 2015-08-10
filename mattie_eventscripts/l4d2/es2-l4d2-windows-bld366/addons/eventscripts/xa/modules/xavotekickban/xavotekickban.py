from math import ceil

import es
import gamethread
import popuplib
import playerlib

from xa import xa

targets = {}
userids = {}

xavotekickban = xa.register('xavotekickban')
xalanguage 	  = xavotekickban.language.getLanguage()

minKickPlayers = xavotekickban.setting.createVariable("votekick_minplayers", 3, "Minimum players on the server before votekick is enabled")
minBanPlayers  = xavotekickban.setting.createVariable("voteban_minplayers",  5, "Minimum players on the server before voteban is enabled")
kickPercentage = xavotekickban.setting.createVariable("votekick_percentage", 40, "The percentage of players on the server who need to type this to kick a player")
banPercentage  = xavotekickban.setting.createVariable("voteban_percentage",  51, "The percentage of players on the server who need to type this to ban a player")
banEnable  = xavotekickban.setting.createVariable("enable_voteban",      1, "Whether or not players are allowed to voteban players")
banTime    = xavotekickban.setting.createVariable("voteban_time",        0, "The time in minutes a player is banned for (0 = permanent ban)")
notify     = xavotekickban.setting.createVariable("votekickban_announce",   1, "Whether or not players are notified about vote kicking / banning when they spawn")

def load():
    """
    Executed when the module loads. Register server command and ensure that
    everything is registered
    """
    xavotekickban.addCommand('votekick', voteKick, "votekick", "UNRESTRICTED", "Vote Kick", True).register(('say', 'console'))
    gamethread.delayed(0, delayVoteBanEnableCheck)
    
    if str(es.ServerVar("eventscripts_currentmap")):
        """ Loaded halfway through a map, ensure all players are registered """
        for player in es.getUseridList():
            event_var = {}
            event_var['userid']  = str(player)
            event_var['es_username'] = es.getplayername(player)
            event_var['es_steamid'] = es.getplayersteamid(player)
            player_activate(event_var)
            
def delayVoteBanEnableCheck():
    """
    This is a function to execute after a certain time delay as we need to ensure
    that the configuration file has been executed before we attempt to register
    the command
    """
    if int(banEnable):
        xavotekickban.addCommand('voteban', voteBan, "voteban", "UNRESTRICTED", "Vote Ban", True).register(('say', 'console'))
            
def unload():
    """
    Executed when the module is unloaded. Unregister this module from the main
    package instance
    """
    xavotekickban.unregister()

def player_activate(event_var):
    """
    Executes when a player is activated on the server. Initialize the dictioanry
    instances
    
    @PARAM event_var - an automatically passed event instance
    """
    steamid = event_var['es_steamid']
    userid  = event_var['userid']
    gamethread.cancelDelayed("xa_votekickban_remove_%s" % steamid)
    if steamid not in targets:
        targets[steamid] = {}
        targets[steamid]["kicks"] = 0
        targets[steamid]["bans"]  = 0
    userids[userid] = {}
    userids[userid]["kicks"] = []
    userids[userid]["bans"]  = []
    
def player_disconnect(event_var):
    """
    Executed when a player is disconnected from the server. Remove their instance
    after 10 minutes so that they can't simply retry. This will be known as the
    cooldown timer.
    
    @PARAM event_var - an automatically passed event instance
    """
    steamid = event_var['networkid']
    userid  = event_var['userid']
    gamethread.delayedname(600, "xa_votekickban_remove_%s" % steamid, removePlayer, steamid)
    
    """ Remove the kicks from the people they have vote kicked """
    if userid in userids:
        for kickRemovePlayer in userids[userid]["kicks"]:
            steamid = es.getplayersteamid(kickRemovePlayer)
            if steamid in targets:
                targets[steamid]["kicks"] -= 1
    
        """ Remove the bans from the people they have vote banned """        
        for banRemovePlayer in userids[userid]["bans"]:
            steamid = es.getplayersteamid(banRemovePlayer)
            if steamid in targets:
                targets[steamid]["bans"] -= 1 
    
def voteKick():
    """
    Executed when a player types 'votekick' in either console or chat. Build
    a popup of all the valid players they can kick.
    """
    userid = str(es.getcmduserid())
    if es.getplayercount() >= minKickPlayers:
        """ There are enough players to run the command """
        myPopupInstance = popuplib.easymenu("xa_votekick_%s" % userid, "_popup_choice", voteKickCheck)
        myPopupInstance.settitle("Select a player to kick")
        for player in es.getUseridList():
            """ Loop through all the players in the server """
            if str(player) != userid:
                """ The current iteration is not equal to the user who executed the command """
                myPopupInstance.addoption(player, es.getplayername(player), bool( player not in userids[userid]["kicks"] ) )
        myPopupInstance.send(userid)
    else:
        """ There are not enough players, notify the user """
        es.tell(userid, '#green', xalanguage("not enough players", {}, playerlib.getPlayer(userid).get("lang") ) )
    
def voteKickCheck(userid, choice, popupid):
    """
    Executed when a player has chosen another to vote kick. Get the steamid
    of the victim, and check for the amount of kicks needed. Kick the player
    if their are enough votes
    """
    userid = str(userid)
    if not es.exists('userid', choice):
        """ Something went wrong, the user no longer exists, return early """
        return
    steamid = es.getplayersteamid(choice)
    if userid not in userids or steamid not in targets:
        """ One of the instances weren't avaiable, return early """
        return
    xavotekickban.logging.log("has voted to kick user %s [%s]" % (es.getplayername(choice), es.getplayersteamid(choice) ), userid )
    userids[userid]["kicks"].append(choice)
    targets[steamid]["kicks"] += 1
    
    kicksRemaining = getKicksRemaining(steamid)
    
    if kicksRemaining == 0:
        """ There has been enough kicks passed, kick the player. """
        removePlayer(steamid)
        es.server.queuecmd('kickid %s "You have been votekicked from the server"' % choice)
        tokens = {}
        tokens['name'] = es.getplayername(choice)
        for player in playerlib.getPlayerList('#all'):
            es.tell(int(player), '#multi', xalanguage('player kicked', tokens, player.get("lang") ) )
        xavotekickban.logging.log("has been vote kicked" % choice)
    else:
        tokens = {}
        tokens['name']   = es.getplayername(choice)
        tokens['amount'] = kicksRemaining
        for player in playerlib.getPlayerList("#all"):
            es.tell( int(player), '#multi', xalanguage('player votes kicked', tokens, player.get("lang") ) )
        xavotekickban.logging.log("needs %s more votes till they are kicked" % kicksRemaining, choice)
        
def voteBan():
    """
    Executed when a player types 'voteban' in either console or chat. Build
    a popup of all the valid players they can ban.
    """
    userid = str(es.getcmduserid())
    if es.getplayercount() >= minBanPlayers:
        """ There are enough players to run the command """
        myPopupInstance = popuplib.easymenu("xa_voteban_%s" % userid, "_popup_choice", voteBanCheck)
        myPopupInstance.settitle("Select a player to ban")
        for player in es.getUseridList():
            """ Loop through all the players in the server """
            if str(player) != userid:
                """ The current iteration is not equal to the user who executed the command """
                myPopupInstance.addoption(player, es.getplayername(player), bool( player not in userids[userid]["bans"] ) )
        myPopupInstance.send(userid)
    else:
        """ There are not enough players, notify the user """
        es.tell(userid, '#green', xalanguage("not enough players", {}, playerlib.getPlayer(userid).get("lang") ) )
    
def voteBanCheck(userid, choice, popupid):
    """
    Executed when a player has chosen another to vote ban. Get the steamid
    of the victim, and check for the amount of bans needed. Ban the player
    if their are enough votes
    """
    userid = str(userid)
    if not es.exists('userid', choice):
        """ Something went wrong, the user no longer exists, return early """
        return
    steamid = es.getplayersteamid(choice)
    if userid not in userids or steamid not in targets:
        """ One of the instances weren't avaiable, return early """
        return
        
    xavotekickban.logging.log("has voted to ban user %s [%s]" % (es.getplayername(choice), es.getplayersteamid(choice) ), userid )
    userids[userid]["bans"].append(choice)
    targets[steamid]["bans"] += 1
    bansRemaining = getBansRemaining(steamid)
    if bansRemaining == 0:
        """ There has been enough kicks passed, kick the player. """
        removePlayer(steamid)
        es.server.queuecmd('banid %s %s;writeid;kickid %s "You have been banned"' % (banTime, choice, choice) )
        tokens = {}
        tokens['name'] = es.getplayername(choice)
        for player in playerlib.getPlayerList('#all'):
            es.tell(int(player), '#multi', xalanguage('player banned', tokens, player.get("lang") ) )
        xavotekickban.logging.log("has been vote banned", choice)
    else:
        tokens = {}
        tokens['name']   = es.getplayername(choice)
        tokens['amount'] = bansRemaining
        for player in playerlib.getPlayerList("#all"):
            es.tell( int(player), '#multi', xalanguage('player votes banned', tokens, player.get("lang") ) )
        xavotekickban.logging.log("needs %s more votes till they are banned" % bansRemaining, choice)
    
def removePlayer(steamid):
    """
    Executed when we want to remove a players dictionary instance.
    
    @PARAM steamid - the steamid of the player we wish to remove
    """
    if steamid in targets:
        del targets[steamid]

def getKicksRemaining(steamid):
    """
    Returns the amount of votes needed till a player is kicked
    
    @PARAM steamid - the steamid of the user wishing to check if we should kick them
    @RETURN integer - amount of votes needed to kick
    """
    players = es.getplayercount()
    if steamid not in targets:
        return None
    if players >= minKickPlayers:
        kickAmount = targets[steamid]["kicks"]
        amountNeeded = players * kickPercentage / 100.
        if kickAmount >= amountNeeded:
            return 0
        return ceil(amountNeeded - kickAmount)
    return None
    
def getBansRemaining(steamid):
    """
    Returns the amount of votes needed till a player is banned
    
    @PARAM steamid - the steamid of the user wishing to check if we should ban them
    @RETURN integer - amount of votes needed to ban
    """
    players = es.getplayercount()
    if steamid not in targets:
        return None
    if players >= minBanPlayers:
        banAmount    = targets[steamid]["bans"]
        amountNeeded = players * banPercentage / 100.
        if banAmount >= amountNeeded:
            return 0
        return ceil(amountNeeded - banAmount) 
    return None