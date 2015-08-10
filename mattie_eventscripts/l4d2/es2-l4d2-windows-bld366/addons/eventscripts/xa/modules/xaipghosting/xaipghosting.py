# es imports
import es
import playerlib
import repeat
import usermsg
# xa imports
from xa import xa 

#plugin information
info = es.AddonInfo()
info.name       = "IP Ghosting"
info.version    = "1.3.2"
info.author     = "Errant"
info.basename   = "xaipghosting"

'''
==  IP Ghosting - A full port of mani's fuctionality to blind IP ghosters  ==
 
-- About --

 - Supports the original mani cfg variable (to turn it on and off bascially)
 - Does NOT currently support (as mani did) disabling votekick and voteban functionality for ghosters - mostly as there is no XA Vote module yet!
 
-- Version log --
 #    |  Type  | Date       |  Change log
OY1   | [BETA] | 15/09/2007 |  Working Standalone version
1.0   | [FULL] | 08/10/2007 |  Converted to work within XA, added multi-lingual functionality
1.0.1 | [FULL] | 15/11/2007 | [FIX] r_screenoverlay requires a cheat - changed to use 1 1sec repeated fade via usermsg.fade (works v well - thx to Mattie for the idea)
1.1.0 | [FULL] | 21/01/2008 | Changed to using a class for the blind, fixed a few idiot errors and cleaned things up a bit. Added a cvar to show the version publicly. Added logging of the blind
1.1.1 | [FULL] | 21/01/2008 | Lots of silly fixes (thx mattie) - and fixed a repeat problem that stopped it working
1.2.0 | [FULL] | 04/02/2008 | Added option to blind spectators who are IP ghosting, Added catchem for players leaving the server, Reworked some of the methods in a minor way.
1.3.0 | [FULL] | 08/02/2008 | Added a console command for when auto blinding is turned off 
1.3.1 | [FULL] | 16/02/2008 | Fixed a bunch of minor errors in player_team, commented out global variable
1.3.2 | [FULL] | 13/05/2008 | Fixed typo in player_team method/event
1.3.1 | [FULL] | 22/02/2009 | Fixed a chance where a key error could happen when a player would be checked before added to the dictionary.
--Future--
 #  |  Status       | Desc

1.5 | [UNSTARTED]   | Add other features, provide admin notification / features, add further config options
'''

# the dictionary to track blinded players
blinded = {}
# same idea but for spectators
spec_blinded = {}

# Register the module
ghosting = xa.register(info.basename) 

# Grab the languages file using the XA langlib wrapper
text = ghosting.language.getLanguage()

# Public variable for version
#es.ServerVar("xa_blind_ip_ghosters_ver",str(info.version), "Blind IP Ghosters, version").makepublic()

'''
Internal classes
'''
class Player(playerlib.Player):
    '''
    Extends playerlib.Player to provide special functions
    '''
    def blind(self):
        '''
        The actual blind
        '''
        usermsg.fade(self.userid,2,500,1000,0,0,0,255)
    def tell_blinded(self):
        '''
        Used to tell the player they were blinded
        '''
        # And tell them about it
        es.tell(int(self.userid), text("blind_message",None,self.get("lang")))
        es.tell(int(self.userid), text("blind_message",None,self.get("lang")))
        es.tell(int(self.userid), text("blind_message",None,self.get("lang")))
        
'''
Internal methods
'''
def repeat_fade(x):
    '''
    Method to handle the fading. Is run every second by the repeat xaip. 
    The fade is set to fade out so on round end you get a nice fade out effect for the player
    '''
    for uid in blinded:
        blinded[uid].blind()
        
def repeat_fade(x):
    '''
    As above but for the spectators dict
    '''
    for uid in spec_blinded:
        spec_blinded[uid].blind()

def blindplayer(uid):
    '''
    - Starts the fade repeat if it isn't already running
    - Fades out the player
    - Tell them 3 times they have been blinded
    '''
    global blinded
    if repeat.status("xaip") == 0:
        a = repeat.create("xaip", repeat_fade)
        a.start(1,0)
    # do the initial fade 
    blinded[uid] = Player(uid)
    blinded[uid].blind()
    # tell them
    blinded[uid].tell_blinded()
    # log that they were blinded
    ghosting.logging.log("blinded for ghosting", uid)
                
def blindplayer_spec(uid):
    '''
    As above but for the spectator Dict
    '''
    global spec_blinded
    if repeat.status("xaip_spec") == 0:
        a = repeat.create("xaip_spec", repeat_fade_spec)
        a.start(1,0)
    # do the initial fade 
    spec_blinded[uid] = Player(uid)
    spec_blinded[uid].blind()
    # tell them
    spec_blinded[uid].tell_blinded()
    # log that they were blinded
    ghosting.logging.log("blinded for ghosting", uid)
    

def checkplayer(uid):
    '''
    Checks if a player is ghosting and blinds them if so (does not test bots)
    '''
    if not es.isbot(uid):
        if str(uid).isdigit():
            uid = int(uid)
        else:
            return False
        plist = es.createplayerlist()
        if uid not in plist:
            return False
        uip   = plist[uid]["address"]   
        for userid in plist:
            if not userid == int(uid) and plist[userid]["address"]== uip: 
                return True
    return False
    
def remove_from_spec(uid):
    '''
    Removes the user from the spec dict and stops the repeat if the dict is empty
    '''
    global spec_blinded
    spec_blinded.pop(uid)
    if len(spec_blinded) < 1:
        # no one IP ghosting as spec so kill the repeat
        if repeat.status("xaip_spec") > 0:
            r = repeat.find("xaip_spec")
            r.stop()
            r.delete()
                
def blind_con_com():
    '''
    Allows admins to blind via a console command
    '''
    if es.getargc() > 1:
        id = es.getuserid(es.getargv(1))
        admin = playerlib.getPlayer(es.getcmduserid())
        if id > 0:
            target = playerlib.getPlayer(id)
            if ghosting.setting.getVariable('blind_ghosters') == "0":
                # can only use this if auto blinding is OFF
                if checkplayer(int(target)):
                    es.msg("#green %s blinded %s till the end of the round for ghosting" % (admin.attributes["name"], target.attributes["name"]))
                    ghosting.logging.log("blinded user %s [%s] for ghosting" % (es.getplayername(id), es.getplayersteamid(id)), int(admin), True)
                    blindplayer(str(target))
                else:
                    es.tell(int(admin), "#green %s was not IP ghosting" % (target.attributes["name"]))
            else:
                es.tell(int(admin), "#green XA will blind %s automatically if they are IP ghosting" % (target.attributes["name"]))
        else:
            es.tell(int(admin), "#green Player %s could not be found" % (str(es.getargv(1))))
    else:
        es.dbgmsg(0, "Syntax: xa_blind_ghoster <steamid|userid> - blinds ghosting players till the end of the round")
'''
Events
'''
def load():
    # sort the variable registration
    ghosting.setting.createVariable('blind_ghosters', '1', "Blind IP Ghosters when they die (1=On, 0=Off)") 
    # Option to blind people who are speccing
    ghosting.setting.createVariable('blind_ghosters_when_spectating', '1', "Blind IP Ghosters when they are spectating (1=On, 0=Off)") 
    # create the console command
    ghosting.addCommand('xa_blind_ghoster',blind_con_com,'blind_ghoster','ADMIN').register(('console','say'))

def player_death(event_var):
    global blinded
    '''
    If player is IP ghosting add them to the list! And if the repeat is not fired yet then do that too!
    '''
    if ghosting.setting.getVariable('blind_ghosters') != "0" and checkplayer(event_var['userid']):
        blindplayer(event_var['userid'])
        

def round_end(event_var):
    '''
    On the round end delete the keys from our dict of ghosters and also end the repeat to minimize server load
    '''
    global blinded
    if repeat.status("xaip") > 0:
        r = repeat.find("xaip")
        r.stop()
        r.delete()
    blinded = {}
    
def player_team(event_var):
    '''
    Blinds a ghoster when they switch to Spec.. and removes them again when they go back to playing.
    '''
    if not int(event_var['disconnect']):
        if ghosting.setting.getVariable('blind_ghosters_when_spectator') != "0" and checkplayer(event_var['userid']) and int(event_var['team']) == 1:
            blindplayer_spec(event_var['userid'])
        if int(event_var['team']) > 1 and  event_var["userid"] in spec_blinded:
            # check they are not on the list and remove them
            remove_from_spec(event_var['userid'])
        
def player_disconnect(event_var):
    '''
    When a player disconnects remove them fro mthe dictionaries (to avoid errors)
    '''
    if event_var["userid"] in blinded:
        # player is currently beign blinded
        blinded.pop(event_var["userid"])
    if event_var["userid"] in spec_blinded:
        # player is currently beign blinded
        remove_from_spec(event_var['userid'])
            
def unload():
    # Unregister the module
    ghosting.unregister()
