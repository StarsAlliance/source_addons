import es 
import votelib 
import popuplib 
import playerlib 
import gamethread 
import time
import os
import random
from xa import xa

vote_list      = {}
vote_admins    = {}
vote_players   = {}
multi_map      = []
previousMaps   = []
round_count    = {}
change_map     = None
startTime      = time.time()

info                = es.AddonInfo() 
info.name           = "Vote" 
info.version        = "0.9" 
info.author         = "freddukes" 
info.basename       = "xavote"

xavote     = xa.register(info.basename)

vote_timer       = xavote.setting.createVariable('vote_timer',       30,                                "How long in seconds that a vote will last for."      ) 
vote_start_sound = xavote.setting.createVariable("vote_start_sound", "ambient/machines/teleport4.wav",  "The sound that will be played when a vote is started") 
vote_end_sound   = xavote.setting.createVariable("vote_end_sound",   "ambient/alarms/warningbell1.wav", "The sound that will be played when a vote is ended"  )
vote_map_file    = xavote.setting.createVariable("vote_map_file" ,   "maplist.txt",                     "The map file for all of your votes from ../<directory>/\n// e.g, from ../cstrike/"  )

end_of_map_vote             = xavote.setting.createVariable('end_of_map_vote',             1,   'Whether or not you wish to enable automatic end of map voting.\n// 0 = disabled\n// 1 = enabled')
amount_of_maps              = xavote.setting.createVariable('amount_of_maps',              8,   'Amount of maps to be inside the end of map vote')
ignore_last_map_amount      = xavote.setting.createVariable('ignore_last_map_amount',      3,   'The number of previous maps played to be ignored from the random vote')
time_before_end_of_map_vote = xavote.setting.createVariable('time_before_end_of_map_vote', 180, 'Amount of seconds before the end of the map that the vote will appear.\n// If you do not wish to use this feature use a value of 0')
rounds_before_mp_winlimit   = xavote.setting.createVariable('rounds_before_mp_winlimit',   2,   'Amount of rounds before mp_winlimit that the vote will appear.\n// If you do not wish to use this feature use a value of 0')
rounds_before_mp_maxrounds  = xavote.setting.createVariable('rounds_before_mp_maxrounds',  3,   'Amount of rounds before mp_maxrounds that the vote will appear.\n// If you do not wish to use this feature use a value of 0')

xalanguage = xavote.language.getLanguage()

if xa.isManiMode(): 
    xavotelist     = xavote.configparser.getList('cfg/mani_admin_plugin/votequestionlist.txt', True)
    xavoterconlist = xavote.configparser.getList('cfg/mani_admin_plugin/voterconlist.txt',     True) 
else: 
    xavotelist     = xavote.configparser.getList('votequestionlist.txt')
    xavoterconlist = xavote.configparser.getList('voterconlist.txt')
    
def load():
    global vote_list
    xavotemenu = popuplib.easymenu("xavotemenu", "_vote_type", voteOption)
    xavotemenu.settitle(xalanguage["select vote"])
    xavote.addMenu("xavotemenu", xalanguage["vote"], "xavotemenu", "start_vote", "ADMIN")
    
    registerVoteMenu("create"  , xalanguage["create vote"]  , customVote, serverCmdFunction = customVoteCommand)
    xavote.addCommand("xa_set_title",   customVoteTitle,     "set_a_title",     "ADMIN").register("console") 
    xavote.addCommand("xa_set_options", customVoteQuestions, "set_vote_option", "ADMIN").register("console")
    
    submenus = []
    if xavoterconlist:
        for line in xavoterconlist: 
            if not line.startswith('//') and line != '': 
                line = line.split('"')
                title = line[1]
                question = line[3]
                command = line[4]
                command = command.split('//')
                command = command[0]
                vote_list[title] = {}
                vote_list[title]['question'] = question
                vote_list[title]['command']  = command
                vote_list[title]['type']     = 'rcon'
                submenus.append(title)
    registerVoteMenu("rcon"    , xalanguage["rcon vote"]    , rconVote  , submenus, rconCommand)
    
    submenus = []
    if xavotelist:
        for line in xavotelist:
            if not line.startswith('//') and line != '' : 
                line = line.split('"') 
                title = line[1] 
                question = line[3]
                vote_list[title] = {}
                vote_list[title]['question'] = question
                vote_list[title]['type']     = 'question'
                submenus.append(title)
    registerVoteMenu("question", xalanguage["question vote"], questionVote, submenus, questionCommand)
    
    mypopup = popuplib.create("multimapaccept")
    a = mypopup.addline
    a('Would you like to start the map')
    a('        vote now?              ')
    a('-------------------------------')
    a('->1. No, add more maps')
    a('->2. Yes, start the vote now')
    a('-------------------------------')
    a('0. Cancel')
    mypopup.menuselect = MultiMapConfirm
    registerVoteMenu("multimap", xalanguage["build multi map"], MultiMap, serverCmdFunction= MultiMapCommand)
    
    registerVoteMenu("random", xalanguage["random map vote"], RandomMapVote, serverCmdFunction= RandomCommand)
    
    registerVoteMenu("stopvotes", xalanguage["stop votes"], StopVotes, serverCmdFunction=StopVotesCommand)
    
    """ If XA loads late, then ensure all users are added to the dictionary. """
    for player in map(str, es.getUseridList() ):
        player_activate({'userid':player})
    if str(es.ServerVar('eventscripts_currentmap')) != "":
        es_map_start({'mapname':str(es.ServerVar('eventscripts_currentmap'))})

def unload():
    gamethread.cancelDelayed('vote_endmap')
    gamethread.cancelDelayed('votemap_timer')
    xavote.unregister()

#################################
# EVENTS
def player_activate(event_var): 
    vote_players[event_var['userid']] = {'stopped':0, 'reason':None} 

def player_disconnect(event_var): 
    if vote_players.has_key(event_var['userid']):
        del vote_players[event_var['userid']] 
        
def round_end(event_var):
    if change_map == 2:
        EndMap()
    elif not change_map:
        round_count['round_counting'] += 1
        winlimit = int(es.ServerVar('mp_winlimit')) - int(rounds_before_mp_winlimit)
        roundlimit = int(es.ServerVar('mp_maxrounds')) - int(rounds_before_mp_maxrounds)
        if event_var['winner'] == '2':
            round_count['t_wins'] += 1
        elif event_var['winner'] == '3':
            round_count['c_wins'] += 1
        if (round_count['round_counting'] >= roundlimit) and roundlimit > 0:
            EndOfMapVote()
        elif (round_count['c_wins'] >= winlimit or round_count['t_wins'] >= winlimit) and winlimit > 0:
            EndOfMapVote()
            
def server_cvar(event_var):
    if event_var['cvarname'] == "mp_timelimit" and startTime is not None and int(time_before_end_of_map_vote):
        gamethread.cancelDelayed('votemap_timer')
        delay = es.ServerVar('mp_timelimit') * 60 - int(time_before_end_of_map_vote) - (time.time() - startTime)
        if delay:
            gamethread.delayedname(delay, 'votemap_timer', EndOfMapVote)
        else:
            EndOfMapVote()
        
def es_map_start(event_var):
    global map_list
    global startTime
    global round_count
    mapfilename = str(es.ServerVar('eventscripts_gamedir')).replace('\\','/') + '/' + str(vote_map_file)
    if os.path.exists(mapfilename):    
      map_file       = open(mapfilename, 'r')
      map_list       = filter(lambda x: False if x == '' or x.startswith('//') else os.path.isfile(str(es.ServerVar('eventscripts_gamedir')).replace('\\','/') + '/maps/%s.bsp'%x), map(lambda x: x.replace('\n',''), map_file.readlines()))
      map_file.close()
    else:
      es.dbgmsg(0, "xavote.py: Note: Cannot find maplist file '"+mapfilename+"'")
    
    gamethread.cancelDelayed('votemap_timer')
    round_count = {}
    round_count['round_counting'] = 0
    round_count['t_wins']     = 0
    round_count['c_wins']     = 0
    round_count['frag_kills'] = 0
    startTime = time.time()
    if int(time_before_end_of_map_vote):
        gamethread.delayed(10, DelayTimer)
    previousMaps.append(event_var['mapname'])
    if len(previousMaps) and len(previousMaps) > int(ignore_last_map_amount):
        previousMaps.remove(previousMaps[0])
#
#################################
    
def voteCmd():
    command   = es.getargv(0).replace('xa_','').replace('vote','')
    args      = []
    argLength = es.getargc()
    tempCount = 0
    while tempCount < argLength:
        tempCount += 1
        args.append(es.getargv(tempCount))
    if '' in args:
        args.remove('')
    commandFunction = vote_list[command]['commandFunction']
    if callable(commandFunction):
        if args:
            commandFunction(args)
        else:
            commandFunction()
    
def registerVoteMenu(shortName, displayName, returnFunction, submenus=[], serverCmdFunction=None, permission='ADMIN'):
    if not vote_list.has_key(shortName):
        vote_list[shortName] = {}
        if serverCmdFunction:
            vote_list[shortName]['commandFunction'] = serverCmdFunction 
            xavote.addCommand('xa_' + shortName + 'vote', voteCmd, 'vote_commands', permission).register(('server', 'console'))
        vote_list[shortName]['display']  = displayName
        vote_list[shortName]['function'] = returnFunction
        vote_list[shortName]['type']     = 'mainmenu'
        votemenu = popuplib.find("xavotemenu")
        votemenu.addoption(shortName, displayName)
        if submenus:
            vote_list[shortName]['type'] = 'submenu'
            myPopup = popuplib.easymenu(shortName, 'vote_choice', returnMenu)
            for submenu in submenus:
                vote_list[submenu]['function'] = returnFunction
                myPopup.addoption(submenu, submenu)
            myPopup.settitle(displayName)
            myPopup.submenu(10, "xavotemenu")
        
def voteOption(userid, choice, popupid):
    if not vote_list.has_key(choice): 
        return
    if vote_list[choice]['type'] == 'submenu':
        if popuplib.exists(choice):
            popuplib.send(choice, userid)
    elif callable(vote_list[choice]['function']):
            vote_list[choice]['function'](userid, choice)
        
def returnMenu(userid, choice, popupid):
    function = vote_list[choice]['function']
    if callable(function):
        xavote.logging.log("Admin "+ es.getplayername(userid)+ " selected vote " + str(choice))
        function(userid, choice)
    else:
        es.dbgmsg(0, "xavote.py: Cannot find method '"+str(function)+"'!")
        
def customVote(userid, choice):
    lang = playerlib.getPlayer(userid).get("lang")
    es.escinputbox(30, userid, xalanguage("select vote title", lang=lang), xalanguage("select vote title", lang=lang), 'xa_set_title') 
    es.tell(userid, '#green',  xalanguage("escape prompt", lang=lang)) 
    
def customVoteTitle():
    userid = es.getcmduserid()
    title  = es.getargs()
    lang   = playerlib.getPlayer(userid).get("lang")
    es.escinputbox(30, userid, xalanguage("vote options", lang=lang), xalanguage("select vote options", lang=lang), 'xa_set_options %s ^^^'%title) 
    
def customVoteQuestions():
    userid    = es.getcmduserid()
    title     = str(es.getargs()).split('^^^')[0].strip()
    questions = str(es.getargs()).split('^^^')[1].split(',')
    myvote = Vote(str(userid))
    myvote.CreateVote(title)
    for question in questions:
        myvote.AddOption(question.strip())
    myvote.StartVote()
    
def customVoteCommand(args):
    title     = args[0].strip()
    questions = args[1].split(',')
    myvote = Vote(title)
    myvote.CreateVote(title)
    for question in questions:
        myvote.AddOption(question.strip())
    myvote.StartVote()
    
def rconVote(userid, vote):
    myvote = Vote(vote)
    myvote.CreateVote(vote_list[vote]['question'], vote_list[vote]['command'])
    myvote.AddOption("Yes", True)
    myvote.AddOption("No")
    myvote.StartVote()
    
def rconCommand(args):
    question = args[0]
    command  = args[1]
    myvote = Vote(question)
    myvote.CreateVote(question, command)
    myvote.AddOption("Yes", True)
    myvote.AddOption("No")
    myvote.StartVote()
        
def questionVote(userid, vote):
    myvote = Vote(vote)
    myvote.CreateVote(vote_list[vote]['question'])
    myvote.AddOption("Yes")
    myvote.AddOption("No")
    myvote.StartVote()
    
def questionCommand(args):
    question = args[0]
    myvote = Vote(question)
    myvote.CreateVote(question)
    myvote.AddOption("Yes")
    myvote.AddOption("No")
    myvote.StartVote()
        
def MultiMap(userid, vote):
    ReBuildMultiMapMenu()
    popuplib.send("multimap", userid)
        
def ReBuildMultiMapMenu():
    submenus = []
    for x,y,z in os.walk(str(es.ServerVar('eventscripts_gamedir')).replace('\\','/') + '/maps'):
        for mymap in filter(lambda x: x.endswith('.bsp'), z): 
            mymap = mymap.replace('.bsp','')
            submenus.append(mymap)    
    vote_list["multimap"]['type'] = 'submenu'
    myPopup = popuplib.easymenu("multimap", 'vote_choice', MultiMapSubmit)
    for submenu in submenus:
        if submenu not in multi_map:
            myPopup.addoption(submenu, submenu)
        else:
            myPopup.addoption(submenu, '+ ' + submenu)
    myPopup.settitle(xalanguage["build multi map"])
    myPopup.submenu(10, "xavotemenu")
        
def MultiMapSubmit(userid, vote, popupid):
    if vote not in multi_map:
        multi_map.append(vote)
    else:
        multi_map.remove(vote)
    popuplib.send("multimapaccept", userid)
        
def MultiMapConfirm(userid, choice, popupid):
    if choice == 1:
        ReBuildMultiMapMenu()
        popuplib.send("multimap", userid)
    elif choice == 2:
        ChangeMapBuild(StartMultiMap, userid)        

def StartMultiMap(userid, choice, popupid):
    global change_map
    global multi_map
    change_map = int(choice)
    myvote = Vote("multimap")
    myvote.CreateVote("Please select a map", MultiMapWin)
    for mymap in multi_map:
        myvote.AddOption(mymap, True)
    multi_map = []
    myvote.StartVote()
        
def MultiMapWin(args):
    winner = args['winner']
    es.set('eventscripts_nextmapoverride', winner)
    if change_map == 1:
        EndMap()
    
def MultiMapCommand(args):
    global change_map
    global multi_map
    multi_map = args[0].split(',')
    change_map = int(args[1].replace('immediately','1').replace('round_end','2').replace('map_end','3'))
    myvote = Vote("multimap")
    myvote.CreateVote("Please select a map", MultiMapWin)
    for mymap in multi_map:
        myvote.AddOption(mymap.strip(), True)
    myvote.StartVote()
    
def RandomMapVote(userid, vote):
    ChangeMapBuild(StartRandomMapVote, userid)

def StartRandomMapVote(userid, choice, popupid):
    global change_map
    change_map = int(choice)
    mypopup  = popuplib.easymenu("randmapamount", "_popup_choice", RandomMapVoteAmountSelection)
    submenus = []
    temp_index = 1
    amount = len(map_list)
    while temp_index <= amount:
        mypopup.addoption(temp_index, '[%s]'%temp_index)
        temp_index += 1
    mypopup.settitle("Select the amount of maps you want")
    mypopup.send(userid)
    
def RandomMapVoteAmountSelection(userid, choice, popupid):
    vote = Vote("randommap")
    vote.CreateVote("Please select a map", RandomMapWin)
    random_list = []
    copyOfMapList = map_list[:]
    if not copyOfMapList:
        return
    while choice:
        choice -= 1
        random_map = random.choice(copyOfMapList)
        copyOfMapList.remove(random_map)
        random_list.append(random_map)
    random_list.sort()
    for random_map in random_list:
        vote.AddOption(random_map, True)
    vote.StartVote()
    
def RandomMapWin(args):
    winner = args['winner']
    es.set('eventscripts_nextmapoverride', winner)
    if change_map == 1:
        EndMap()
    
def RandomCommand(args):
    global change_map
    vote = Vote("randommap")
    vote.CreateVote("Please select a map", RandomMapWin)
    maplist = filter(lambda x: False if x in args else True, map_list)
    if not maplist:
        return
    random_list = []
    choice = int(args[0])
    change_map = int(args[1].replace('immediately','1').replace('round_end','2').replace('map_end','3'))
    while choice:
        choice -= 1
        random_map = random.choice(maplist)
        maplist.remove(random_map)
        random_list.append(random_map)
    random_list.sort()
    for random_map in random_list:
        vote.AddOption(random_map, True)
    vote.StartVote()
    
def DelayTimer():
    gamethread.cancelDelayed('votemap_timer')
    delay = int(es.ServerVar('mp_timelimit')) * 60 - int(time_before_end_of_map_vote) - 10
    gamethread.delayedname(delay, 'votemap_timer', EndOfMapVote)
    
def EndOfMapVote():
    if not change_map and int(end_of_map_vote):
        string = ""
        for ignoremap in previousMaps:
            string += (ignoremap + " ")
        string = string[:-1]
        if string:
            es.server.queuecmd('xa_randomvote %s 3 %s' % (amount_of_maps, string))
        else:
            es.server.queuecmd('xa_randomvote %s 3' % amount_of_maps)
    
def EndMap( APIAccessorModule = None ):
    global change_map
    change_map = None
    winner = es.ServerVar('eventscripts_nextmapoverride')
    userid = es.getuserid()
    if not userid:
        return
    es.server.queuecmd('nextlevel %s'%winner)
    es.server.queuecmd('es_give %s game_end'%userid)
    es.server.queuecmd('es_fire %s game_end EndGame'%userid)
       
def ChangeMapBuild(function, userid):
    mypopup = popuplib.create("mapchange")
    a = mypopup.addline
    a('When should the map change?')
    a('-------------------------------')
    a('->1. Immediately')
    a('->2. End of the round')
    a('->3. End of the map')
    a('-------------------------------')
    a('0. Cancel')
    mypopup.menuselect = function
    mypopup.send(userid)
        
def StopVotes(userid, vote):
    for voteInstance in voteInstances:
        voteInstances[voteInstance].Stop()
    
def StopVotesCommand(args):
    stopVotes(None, None)
        
class VoteManager(object):
    def __init__(self, name):
        self.options   = {}
        self.display   = None
        self.vote      = None
        self.option    = None
        self.shortName = name
        
    def CreateVote(self, question, command=None):
        self.vote      = votelib.create(self.shortName, self._Win, self._Message)
        self.option    = command
        self.vote.setquestion(question)
        
    def AddOption(self, option, winner = False):
        self.vote.addoption(option)
        self.options[option] = {'votes':0,'winner':winner}
        
    def StartVote(self):
        self.vote.showmenu = False
        self.vote.start(float(vote_timer))
        self.display = HudHint(self.options, self.shortName)
        for player in vote_players:
            if not es.exists('userid', player):
                continue
            if not vote_players[player]['stopped']: 
                popuplib.send("vote_" + self.shortName , player) 
            elif vote_players[player]['reason']: 
                tokens = {} 
                tokens['reason'] = vote_players[player]['reason'] 
                es.tell(player, '#green', xalanguage("stopped vote", tokens, playerlib.getPlayer(player).get("lang"))) 
        es.cexec_all('playgamesound ' + str(vote_start_sound) )
        self.display.Start()
        
    def Stop(self):
        self.vote.stop(True)
        
    def _Message(self, userid, votename, optionid, option):
        tokens = {} 
        tokens['username'] = es.getplayername(userid) 
        tokens['option']   = str(option) 
        for player in playerlib.getPlayerList(): 
            es.tell(int(player),'#multi', xalanguage("vote message", tokens, player.get("lang")))
        self.display.ChangeDict(option, 1)
        
    def _Win(self, popupid, optionid, choice, winner_votes, winner_percent, total_votes, was_tied, was_canceled):
        self.display.Stop()
        es.cexec_all('playgamesound', str(vote_end_sound) )
        if not was_tied or was_canceled:
            if choice != "0" and winner_votes:
                if self.option and self.options[choice]['winner']:
                    if isinstance(self.option, str):
                        es.server.cmd(self.option)
                    elif callable(self.option):
                        self.params = {}
                        self.params['winner']      = choice
                        self.params['votes']       = winner_votes
                        self.params['percent']     = winner_percent
                        self.params['total votes'] = total_votes
                        self.option(self.params)
                tokens = {}
                tokens['winner']     = choice 
                tokens['votes']      = winner_votes 
                tokens['totalvotes'] = total_votes
                tokens['percent']    = winner_percent
                
                for player in playerlib.getPlayerList("#human"): 
                    es.tell(int(player),'#multi',xalanguage("vote win",tokens, player.get("lang")))
            else:
                for player in playerlib.getPlayerList("#human"): 
                    es.tell(int(player),'#green',xalanguage("vote no voters", {}, player.get("lang")))
             
        elif was_tied and not was_canceled:
            for player in playerlib.getPlayerList("#human"): 
                es.tell(int(player),'#green',xalanguage("vote tie", player.get("lang")))
            possibilities = []
            maxAmount = 0
            for possibility in self.display.SortDict():
                amount = self.display.votes[possibility]['votes'] 
                if amount < maxAmount:
                    break
                maxAmount = amount
                possibilities.append(possibility)
            winner = random.choice(possibilities)
            tokens = {}
            tokens['winner'] = winner
            for player in playerlib.getPlayerList("#human"): 
                es.tell(int(player),'#multi',xalanguage("random win", tokens, player.get("lang")))
            if self.option and self.options[winner]['winner']:
                if isinstance(self.option, str):
                    es.server.cmd(self.option)
                elif callable(self.option):
                    self.params = {}
                    self.params['winner']      = winner
                    self.params['votes']       = winner_votes
                    self.params['percent']     = winner_percent
                    self.params['total votes'] = total_votes
                    self.option(self.params)
        else: 
            for player in playerlib.getPlayerList("#human"): 
                es.tell(int(player), '#green', xalanguage("vote canceled", player.get("lang") ) )

""" Acessor functions which allows others to start votes etc """    

voteInstances = {}            
def Vote( APIAccessorFunctionTest, shortNameTest = None ):
    if not isinstance(APIAccessorFunctionTest, str):
        shortName = shortNameTest
    else:
        shortName = APIAccessorFunctionTest
    if shortName not in voteInstances:
        voteInstances[shortName] = VoteManager(shortName)
    return voteInstances[shortName]

def CreateVote( APIAccessorFunctionTest, shortNameTest, questionTest = None, commandTest = None):
    if not isinstance(APIAccessorFunctionTest, str):
        shortName = shortNameTest
        question  = questionTest
        command   = commandTest
    else:
        shortName = APIAccessorFunctionTest
        question  = shortNameTest
        command   = questionTest
    myVote = FindVote(shortName)
    if myVote:
        myVote.CreateVote(question, command)
        
def StartVote( APIAccessorFunctionTest, shortNameTest = None):
    if not isinstance(APIAccessorFunctionTest, str):
        shortName = shortNameTest
    else:
        shortName = APIAccessorFunction
    myVote = FindVote(shortName)
    if myVote:
        myVote.StartVote()

def FindVote( APIAccessorFunctionTest, shortNameTest = None):
    if not isinstance(APIAccessorFunctionTest, str):
        shortName = shortNameTest
    else:
        shortName = APIAccessorFunction
    if shortName in voteInstances:
        return voteInstances[shortName]
    return None
    
def StopVote( APIAccessorFunctionTest, shortNameTest = None ):
    if not isinstance(APIAccessorFunctionTest, str):
        shortName = shortNameTest
    else:
        shortName = APIAccessorFunctionTest
    myVote = FindVote(shortName)
    if myVote:
        myVote.stop()
        
def AddOption( APIAccessorFunctionTest, shortNameTest, optionTest = None, winnerTest = None):
    if not isinstance(APIAccessorFunctionTest, str):
        shortName = shortNameTest
        option    = optionTest
        winner    = winnerTest if winnerTest else False
    else:
        shortName = APIAccessorFunctionTest
        option    = shortNameTest
        winner    = optionTest if optionTest else False
    myVote = FindVote(shortName)
    if myVote:
        myVote.AddOption(option, winner)

class HudHint(object):
    def __init__(self, votes, uniquename):
        self.running = False
        self.votes = votes
        self.name = uniquename
        
    def Start(self):
        self.starttime = time.time()
        if not self.running:
            self.running = True
            self.Loop()
        
    def Loop(self):
        time_left = int(self.starttime - time.time() + float(vote_timer) )
        if time_left < 0:
            time_left = 0
        SortedVotes = self.SortDict()
        es.usermsg("create", self.name, "HintText") 
        es.usermsg("write" , "short"  , self.name, -1) 
        format = "Vote Counter: (%ss)\n-----------------------\n"%time_left
        for index in range(min(2, len(SortedVotes))): 
            option = SortedVotes[index] 
            format = format + option + " - Votes: " + str(self.votes[option]['votes']) + "\n" 
        es.usermsg("write", "string", self.name, format)
        for player in es.getUseridList(): 
            es.usermsg("send", self.name, player, 0) 
        es.usermsg("delete", self.name)
        gamethread.delayedname(1, self.name, self.Loop) 
        
    def SortDict(self):
        return sorted(self.votes, lambda x,y : -1 if self.votes[x]['votes'] > self.votes[y]['votes'] else 0 if self.votes[x]['votes'] == self.votes[y]['votes'] else 1)
        
    def ChangeDict(self, vote, amount):
        self.votes[vote]['votes'] += amount
        gamethread.cancelDelayed(self.name)
        self.Loop()
    
    def Stop(self):
        if self.running:
            self.running = False
            gamethread.cancelDelayed(self.name)
            
def getGlobalVariable( APIAccessorFunctionTest, variableNameTest=None ):
    if not isinstance(APIAccessorFunctionTest, str):
        variableName = variableNameTest
    else:
        variableName = APIAccessorFunctionTest
    if variableName not in globals().keys():
        raise AttributeError, "Variable name %s is not inside xavote" % variableName
        return 0
    return globals()[variableName]
