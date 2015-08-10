import es 
import gamethread 
import playerlib
import time
from xa import xa 

#plugin information 
info = es.AddonInfo() 
info.name     = 'Spawn and Team protection' 
info.version  = '1.0.1' 
info.author   = 'Errant' 
info.basename = 'xaprotect' 

''' 
Provides basic spawn protection and damage reflection

== 1.0.2 ==
 - [FIX] bug fixes (module was still registering as xateamwound)
== 1.0.1 ==
 - [FIX] Problem where the player_team code tried to re-add players that had disconnected
== 1.0.0 ==
 - Released publicly
 - Name change to XAProtect
 - [+] Team kill protection
 - [FIX] Changed the protection levels from 5000 to 1124
== OY1 ==
 - [+] Added basic spawn protection (raised health)
 - [+] Added the ability to kill people who spawn kill
 - [+] Added reflect damage ability against team wounders
''' 

# register module with XA 
xaprotect = xa.register(info.basename) 

# Localization helper: 
#text = xaprotect.language.getLanguage() 

# make config vars 
protect_wound                     = xaprotect.setting.createVariable('protect_wound', 1, '1 = ON, 0 = OFF') 
protect_spawn_protection_time     = xaprotect.setting.createVariable('protect_spawn_protection_time', 3, 'The number of seconds to make people invulnerable at spawn (0 = OFF)') 
protect_spawn_protection_mode     = xaprotect.setting.createVariable('protect_spawn_protection_mode', 0, '(1 = Anytime players spawn, 0 = Only at round start)') 
protect_reflect_damage            = xaprotect.setting.createVariable('protect_reflect_damage', 0, '(0 = OFF, 1 = Reflect all damage, 2 = reflect some damage)') 
protect_reflect_damage_percentage = xaprotect.setting.createVariable('protect_reflect_damage_percentage', 10, '(0 to 10: the percentage of damage to reflect)') 
protect_spawn_slay                = xaprotect.setting.createVariable('protect_spawn_slay', 0, 'Slay spawn attackers(0=OFF, 1=ON)') 
protect_spawn_slay_time           = xaprotect.setting.createVariable('protect_spawn_slay_time', 3, '# of seconds after spawning an attacker is slayed for team attacking')    
protect_teamkill_slay             = xaprotect.setting.createVariable('protect_teamkill_slay', 0, 'Slay team killers(0=OFF, 1=ON)') 
protect_teamattack_slay           = xaprotect.setting.createVariable('protect_teamattack_slay', 0, 'Slay team attackers(0=OFF, 1=ON)') 

class twPlayer(object): 
    def __init__(self, userid): 
        # set up a player instance of playlib 
        self.uid = int(userid) 
        # some more stuff of use 
        self.plib = playerlib.getPlayer(self.uid) 
        self.steamid = es.getplayersteamid(self.uid) 
        # get some initial data 
        self.spawntime = False 

class twPHandler(object): 
    def __init__(self): 
        self.players = {} 
    def addPlayer(self, userid): 
        uid = int(userid) 
        self.players[uid] = twPlayer(uid) 
    def removePlayer(self, userid): 
        uid = int(userid) 
        if uid in self.players: 
            self.players.pop(uid, 0) 
    def protect(self, userid): 
        p = self.grab(userid) 
        if p: 
            p.set("health", 1124) 
    def unprotect(self, userid): 
        p = self.grab(userid) 
        if p: 
            p.set("health", 100) 
    def set(self, userid, setting, value): 
        p = self.grab(userid) 
        if p: 
            p.set(setting, value) 
    def getspawntime(self, userid): 
        uid = int(userid) 
        if uid in self.players: 
            return self.players[uid].spawntime 
        return False 
    def setspawntime(self, userid, value): 
        uid = int(userid) 
        if uid in self.players: 
            self.players[uid].spawntime = value 
    def get(self, userid, setting): 
        p = self.grab(userid) 
        if p: 
            return p.get(setting) 
        return False 
    def grab(self, userid): 
        uid = int(userid) 
        if uid in self.players: 
            return self.players[uid].plib 
        return False 
    def reflect(self, a, v, damage): 
        attacker = self.grab(a) 
        victim = self.grab(v) 
        if attacker.get("team") == victim.get("team"): 
            if protect_reflect_damage_percentage:
                multiplier = int(protect_reflect_damage_percentage)
            else:
                multiplier = 3
            if multiplier > 10: 
                multiplier = 10 
            elif multiplier < 0: 
                multiplier = 0 
            attacker.set("health", (((int(attacker.get("health")) - int(damage)) / 10) * multiplier)) 
    def team_killattack(self, a, v):  
        attacker = self.grab(a) 
        victim = self.grab(v) 
        if attacker.get("team") == victim.get("team"):
            attacker.kill()
            
# init player handler      
plist = twPHandler()

def unload():
    for userid in es.getUseridList(): 
        gamethread.cancelDelayed('unprotect_%s'%userid) 
    xaprotect.unregister()
    
def player_team(event_var): 
    if int(event_var["userid"]) not in plist.players and event_var["disconnect"] == "0": 
        plist.addPlayer(event_var["userid"]) 
    
    
def player_spawn(event_var): 
    ''' 
     = OY1 = 
     [+] Spawn protection (raises health for set # of seconds) 
    ''' 
    prtime = int(protect_spawn_protection_time)
    prmode = int(protect_spawn_protection_mode)
    if prtime and prtime > 0: 
        # initiate spawn protection 
        if prmode == 0 and roundstatus == 0: 
            # protect the player 
            plist.protect(event_var['userid']) 
            # after the set delay remove the "protection" 
            gamethread.delayedname(prtime, 'unprotect_%s'%event_var['userid'], plist.unprotect, (event_var['userid'])) 
        elif prmode == 0: 
            # protect the player 
            plist.protect(event_var['userid']) 
            # after the set delay remove the "protection" 
            gamethread.delayedname(prtime, 'unprotect_%s'%event_var['userid'], plist.unprotect, (event_var['userid'])) 

def player_hurt(event_var): 
    ''' 
    == OY1 == 
     [+] Added reflect damage 
     [+] Spawn slay protection 
    ''' 
    if protect_reflect_damage and int(protect_reflect_damage): 
        # were reflecting damage
        damage = event_var['damage'] if event_var['damage'] not in ("", "0") else event_var['dmg_health'] 
        plist.reflect(event_var["attacker"], event_var["userid"], damage)
        xaprotect.logging.log("has been reflected %s damage from user %s [%s] due to the player being protected" % (damage,  event_var['es_username'], event_var['es_steamid']), event_var['attacker'] ) 
    if protect_spawn_slay and protect_spawn_slay_time and int(protect_spawn_slay): 
        timelimit = plist.getspawntime(event_var["userid"]) + int(protect_spawn_slay_time) 
        if time.time() < timelimit: 
            # oops! kill them 
            plist.grab(event_var["attacker"]).kill()
            xaprotect.logging.log("has been slayed for spawn attacking", event_var['attacker']) 
    if protect_teamattack_slay and int(protect_teamattack_slay): 
        plist.team_killattack(event_var["attacker"], event_var["userid"])
        xaprotect.logging.log("has been slayed for team damaging", event_var['attacker'])
       
def player_death(event_var):
    '''
    == 1.0.0 ==
     [+] Team kill protect
    '''
    if protect_teamkill_slay and int(protect_teamkill_slay) and protect_teamattack_slay and not int(protect_teamattack_slay): 
        plist.team_killattack(event_var["attacker"], event_var["userid"])
        xaprotect.logging.log("has been slayed for team damaging", event_var['attacker'])
    
def round_start(event_var):  
    global roundstatus, round_start_time 
    roundstatus = 1 
    round_start_time = time.time() 

def round_end(event_var):  
    global roundstatus, round_start_time 
    roundstatus = 0 
  
def player_spawn(event_var):  
    plist.setspawntime(event_var["userid"], time.time()) 
    
def player_disconnect(event_var): 
    plist.removePlayer(event_var["userid"]) 


