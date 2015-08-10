""" Eventscripts Libary Imports """
import es
import playerlib
import popuplib
import gamethread

""" Import engine files """
import random
import time
import os

""" Import eXtensible Admin """
from xa import xa

info = es.AddonInfo() 
info.name       = "Rock the Vote" 
info.version    = "0.02" 
info.author     = "[#OMEGA] - K2" 
info.basename   = "xarockthevote" 

''' 
Credits: 

me (obviously)  

Changelog:

Version 0.02

It is now usig xavote to manage the votes.
Fixed lots of small bugs.

Version 0.01: 

-release 

ToDo: 

-Add option in admin menu to cancel RTV 
-Option & command for refreshing variables 
-Admin & Server command to cancel RTV 
-Output to server console (logging excluded) 
-mapchange protection 
-find a better way to open the mapfiles 
-german translation of strings.ini (0.02) 

Notes: 

''' 

xartv = xa.register(info.basename) 

vote_req_time       = xartv.setting.createVariable('vote_time_before_rock_the_vote',           120, "Time before rockthevote can be started after a new map starts in seconds")  
vote_maps           = xartv.setting.createVariable('vote_rock_the_vote_number_of_maps',          6, "Number of random maps chosen from the votelist after nominations have been taken into account.")
vote_req_p          = xartv.setting.createVariable('vote_vote_rock_the_vote_threshold_percent', 60, "Percentage of players on server required to type rockthevote before it starts (min 1, max 100)") 
vote_req_min        = xartv.setting.createVariable('vote_rock_the_vote_threshold_minimum',       4, "Minimum number of players required to type rockthevote before it starts")

if int(vote_req_min) < 1:
    vote_req_min = 4
     
if not 1 < int(vote_req_p) < 100: 
    vote_req_p = 60
     
if int(vote_maps) < 1:
    vote_maps = 6 

###############
### GLOBALS ###
###############
votes_in       = 0 
vote_req_total = 0 
allowVoting    = True
players        = {} 
nominations    = []
map_start_time = time.time()
lang           = xartv.language.getLanguage() 

def load():
    """ Called on load. Register itself with the XA API """
    global nomination_popup 
    
    xartv.addRequirement("xavote")
    
    xartv.addCommand('rtv',         rtv,      'use_rtv', 'UNRESTRICTED').register(('say', 'console')) 
    xartv.addCommand('rockthevote', rtv,      'use_rtv', 'UNRESTRICTED').register(('say', 'console')) 
    xartv.addCommand('nominate',    nominate, 'use_rtv', 'UNRESTRICTED').register(('say', 'console'))

def unload():
    """ Called on unload. Remove itself from the XA API """
    xartv.delRequirement("xavote") 
    xartv.unregister()

def entry(steamid):
    """ Make sure a player exists before try reading from the dictionary """ 
    if steamid not in players: 
        players[steamid] = [False, False]
        
def loadPopups():
    nomination_popup = popuplib.easymenu('nomination_menu', None, nomination_result) 
    nomination_popup.settitle(lang['choose_map']) 
    maps = read_mapfile()
    for mapName in maps: 
        nomination_popup.addoption(mapName, xartv.language.createLanguageString(mapName))
    
#####################
### USER COMMANDS ###
#####################
    
def nominate():
    """ Executed when a user types 'nominate' in chat """
    userid = es.getcmduserid() 
    if allowVoting: 
        steamid = es.getplayersteamid(userid) 
        entry(steamid) 
        if not players[steamid][1]: 
            popuplib.send("nomination_menu", userid) 
        else:
            es.tell(userid, '#multi', lang('1nominate', lang=playerlib.getPlayer(userid).get('lang') ) )
    else:
        es.tell(userid, '#multi', lang('no_nominate', lang=playerlib.getPlayer(userid).get('lang') ) )

def nomination_result(userid, choice, popupname):
    """ Append the nomination to the nomination list """
    if allowVoting:
        steamid = es.getplayersteamid(userid)
        players[steamid][1] = True
        if choice not in nominations:
            nominations.append(choice)
        xartv.logging.log("has nominated map %s for Rock The Vote" % choice, userid )            
        tokens = {}
        tokens['player']  = es.getplayername(userid)
        tokens['mapname'] = choice 
        for user in es.getUseridList():
            es.tell(user, '#multi', lang('nominated', tokens, playerlib.getPlayer(user).get('lang') ) )
    else:
        es.tell(userid, '#multi', lang('no_nominate', lang=playerlib.getPlayer(userid).get('lang') ) )
    
def rtv():
    """ Executed when a user types 'rtv' in chat """
    global votes_in
    global vote_req_total
     
    userid  = es.getcmduserid() 
    steamid = es.getplayersteamid(userid) 
    entry(steamid) 
    if not players[steamid][0]:
        
        if (time.time() - map_start_time) < float(vote_req_time):
            tokens = {}
            tokens['time'] = int(float(vote_req_time) - int( time.time() - map_start_time ) ) 
            es.tell(userid, '#multi', lang('map_time', tokens, playerlib.getPlayer(userid).get('lang') ) )
            xartv.logging.log("has been denied the right to RTV as not enough time in the map has passed", userid ) 
        else: 
            if allowVoting:
                players[steamid][0] = True
                vote_req_total = int( round(vote_req_p / 100. * len(playerlib.getPlayerList("#human") ) ) )
                if not votes_in: 
                    name = es.getplayername(userid) 
                    for user in es.getUseridList(): 
                        tokens = {}
                        tokens['player'] = es.getplayername(user)
                        es.tell(user, '#multi', lang('player_started', tokens, playerlib.getPlayer(user).get('lang') ) ) 
                        popuplib.unsend("nomination_menu", user)
                votes_in += 1
                xartv.logging.log("has rocked the vote, %s votes in" % votes_in, userid )
                
                if votes_in >= int(vote_req_min): 
                    if votes_in >= vote_req_total:
                        xartv.logging.log("Rock the vote has passed, starting the vote") 
                        rtv_init() 
                    else: 
                        name   = es.getplayername(userid)
                        tokens = {}
                        tokens['player'] = name
                        tokens['votes']  = vote_req_total - votes_in
                        xartv.logging.log("%s votes still needed to rock the vote" % (vote_req_total - votes_in) ) 
                        for user in es.getUseridList():
                            es.tell(user, '#multi', lang('req', tokens ,playerlib.getPlayer(user).get('lang') ) ) 
                else: 
                    name   = es.getplayername(userid)
                    tokens = {}
                    tokens['player'] = name
                    tokens['votes']  = int(vote_req_min) - votes_in
                    for user in es.getUseridList(): 
                        es.tell(user, '#multi', lang('req', tokens, playerlib.getPlayer(user).get('lang') ) ) 
            else: 
                es.tell(userid, '#multi', lang('started', lang=playerlib.getPlayer(userid).get('lang') ) ) 
    else:
        xartv.logging.log("has attempted to RTV more than once", userid) 
        es.tell(userid, '#multi', lang('1vote', lang=playerlib.getPlayer(userid).get('lang') ) ) 

############################
### END OF USER COMMANDS ###
############################

#######################
### VOTE MANAGEMENT ###
#######################

def rtv_init():
    """ Called when there has been enough "RTV's" to execute the vote """
    global allowVoting
    allowVoting = False
    maps = read_mapfile()
     
    """ Checks for the number of maps to be included """ 
    if len(nominations) >= int(vote_maps): 
        random_maps = nominations
        xartv.logging.log("Number of maps to be included in rtv is too high - using all maps.")
    else:
        random_maps = []
        for x in xrange(0, min( len(nominations), int(vote_maps) ) ):
            random.shuffle(nominations)
            random_maps.append( nominations.pop(0) )
        maps = filter(lambda x: x not in random_maps, maps)
        while len(random_maps) < vote_maps and maps:
            random.shuffle( maps )
            random_maps.append( maps.pop(0) )

    random_maps = sorted(random_maps)
    
    """ Create a vote """
    myVote = xartv.xavote.Vote("rockthevote")
    myVote.CreateVote("Choose a map:", vote_win)
    for mapName in random_maps: 
        myVote.AddOption(mapName, True) 
    myVote.StartVote() 

def vote_win(args):
    """ Called when a winner has been chosen. """
    xartv.logging.log('Rock the vote has won, changing map to %s...' % args['winner']) 
    players.clear()
    winner = args['winner']
    es.set('eventscripts_nextmapoverride', winner)
    xartv.xavote.EndMap()     
    
def read_mapfile(): 
    """ Return the global map list in xavote """ 
    return sorted(xartv.xavote.getGlobalVariable("map_list"))
    
##############
### Events ###
##############

def es_map_start(event_var):
    """ Executed when the map starts """
    global map_start_time
    global allowVoting
    global votes_in
    map_start_time = time.time()
    allowVoting    = True
    votes_in       = 0
    for steamid in players:
        players[steamid] = [False, False]
    gamethread.delayed(1, loadPopups)