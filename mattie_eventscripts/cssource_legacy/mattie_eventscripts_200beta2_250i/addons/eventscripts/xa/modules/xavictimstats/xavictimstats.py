import es
import playerlib
import popuplib
import gamethread
from xa import xa

info = es.AddonInfo()
info.name       = 'Victim Stats'
info.version    = '4.2'
info.author     = 'Satoon101'
info.basename   = 'xavictimstats'

xavictimstats = xa.register(info.basename)
xavictimstats.addRequirement('xasettings')
victimstats_setting = xavictimstats.playerdata.createUserSetting('victimstats_setting')
victimstats_timeout_death = xavictimstats.setting.createVariable('victimstats_timeout_death', 15, 'Time till gui closes with inaction after player_death')
victimstats_timeout_round = xavictimstats.setting.createVariable('victimstats_timeout_round', 10, 'Time till gui closes with inaction after round_end or when using victimstats_command command')
victimstats_distance = xavictimstats.setting.createVariable('victimstats_distance', 3, 'When displaying distance, which system to use \n// 1 = Imperial (Feet), 2 = Metric (Meters), 3 = Both / Off is not an option')
victimstats_default = xavictimstats.setting.createVariable('victimstats_default', 5, 'Stats Display user default\n// 0 = Off, 1 = Text:Hitbox, 2 = Text:No Hitbox, 3 = GUI:Hitbox, 4 = GUI:No Hitbox, 5 = GUI: Menu')
victimstats_command = xavictimstats.setting.createVariable('victimstats_command', '', 'Set to command for displaying current stats while alive (LEAVE BLANK to disable)')

xalang = xavictimstats.language.getLanguage()

xavictimstats_menu = {0:'Off',1:'Text: Hitgroups',2:'Text: No Hitgroups',3:'GUI: Hitgroups',4:'GUI: No Hitgroups',5:'GUI: Menu'}
hitgroups = {1:'Head',2:'Chest',3:'Stomach',4:'Left Arm',5:'Right Arm',6:'Left Leg',7:'Right Leg'}

PlayerList = {}

class Player:
    def __init__(self, userid):
        self.userid = str(userid)
        if not victimstats_setting.exists(userid):
            self.setting = int(victimstats_default)
            xavictimstats.playerdata.saveUserSetting()
        else:
            self.setting = victimstats_setting.get(userid)
        self.lang = playerlib.getPlayer(self.userid).lang
        self.TakenPlayers = {}
        self.GivenPlayers = {}
        self.KilledPlayers = {}
    
    def set(self, setting):
        self.setting = setting
        victimstats_setting.set(self.userid,setting)
        xavictimstats.playerdata.saveUserSetting()

    def damageTaken(self, attackername, dmg_health, hitgroup):
        if not attackername in self.TakenPlayers:
            self.TakenPlayers[attackername] = DamageRecord(dmg_health,hitgroup)
        else:
            self.TakenPlayers[attackername].addDamage(dmg_health,hitgroup)
    
    def damageGiven(self, username, dmg_health, hitgroup):
        if username in self.KilledPlayers:
            self.KilledPlayers[username].addDamage(dmg_health,hitgroup)
            return
        if not username in self.GivenPlayers:
            self.GivenPlayers[username] = DamageRecord(dmg_health,hitgroup)
        else:
            self.GivenPlayers[username].addDamage(dmg_health,hitgroup)
    
    def playerKilled(self, username, weapon, headshot, distance):
        if not username in self.KilledPlayers:
            self.KilledPlayers[username] = KillRecord(distance, weapon, headshot)
        else:
            self.KilledPlayers[username].addKill(distance, weapon, headshot)
        if username in self.GivenPlayers:
            self.KilledPlayers[username].swapDamage(self.userid,username)
            del self.GivenPlayers[username]
    
    def sendStats(self,args=()):
        if not (self.TakenPlayers or self.GivenPlayers or self.KilledPlayers): return
        self.Data = {}
        self.Totals = {}
        if self.TakenPlayers:
            type = 'Attacker' if self.setting in [1,2] else 'Attackers'
            self.createdata(type,self.TakenPlayers)
        if self.GivenPlayers:
            self.createdata('Wounded',self.GivenPlayers)
        if self.KilledPlayers:
            self.createdata('Killed',self.KilledPlayers)
        if args:
            type = xalang(args[0],self.lang)
            killer = '%s %s'%(type,xalang('HeadShot',{},self.lang)) if args[1] else type
            self.Data['Killer'] = [xalang('%sText'%args[0],{'killertype':killer,'name':args[2],'weapon':args[3],'distance':args[4],'health':args[5]},self.lang)]
        if self.setting in [1,2]:
            for x in ['Attacker','Wounded','Killed','Killer']:
                if x in self.Data:
                    for y in self.Data[x]:
                        es.tell(self.userid,'#multi',y)
            return
        time = victimstats_timeout_death if 'Killer' in self.Data else victimstats_timeout_round
        if self.setting in [3,4]:
            user_popup = popuplib.create('user_popup')
            number = 0
            for x in ['Attackers','Wounded','Killed','Killer']:
                if not x in self.Data: continue
                number += 1
                if x != 'Killer':
                    user_popup.addline('->%s. %s'%(number,xalang(x,self.lang)))
                    for y in self.Data[x]:
                        user_popup.addline(gui2(y,x))
                else:
                    for y in self.Data[x]:
                        user_popup.addline('->%s. %s'%(number,gui(y)))
            user_popup.timeout('view',time)
            user_popup.send(self.userid)
        if self.setting == 5:
            main_popup = popuplib.create('%sMain'%self.userid)
            take_popup = popuplib.create('%sAttacker'%self.userid)
            give_popup = popuplib.create('%sWounded'%self.userid)
            kill_popup = popuplib.create('%sKilled'%self.userid)
            types = {1:{'name':'Attackers','popup':take_popup},2:{'name':'Wounded','popup':give_popup},3:{'name':'Killed','popup':kill_popup},4:{'name':'Main','popup':main_popup}}
            for x in types:
                popupid = types[x]['popup']
                popupid.timeout('view',time)
                name = types[x]['name']
                if name != 'Main':
                    if name in self.Data:
                        enemies = len(self.Data[name])
                        enemytype = 'enemy' if enemies == 1 else 'enemies'
                        hits = self.Totals[name].hits
                        hittype = 'hit' if hits == 1 else 'hits'
                        kills = self.Totals[name].kills
                        killtype = 'kill' if kills == 1 else 'kills'
                        type = 'Gui%sPlus'%name if name == 'Killed' and kills > enemies else 'Gui%s'%name
                        text = xalang(type,{'total_enemies':enemies,'enemies':xalang(enemytype,self.lang),'total_kills':kills,'killtype':xalang(killtype,self.lang),'total_dmg':self.Totals[name].damage,'total_hits':hits,'hittype':xalang(hittype,self.lang)},self.lang)
                    else:
                        text = xalang('No%s'%name,{},self.lang)
                    main_popup.addline(text)
                    main_popup.addline(' ')
                    popupid.addline(text)
                    if name in self.Data:
                        for y in self.Data[name]:
                            popupid.addline(gui2(y,name))
                    popupid.addline(' ')
                if 'Killer' in self.Data:
                    for y in self.Data['Killer']:
                        popupid.addline(gui(y))
                        popupid.addline(' ')
                for y in types:
                    z = types[y]['name']
                    if not name in [z,'Main']:
                        popupid.addline('->%s. %s'%(y,xalang(z,self.lang)))
                    types[y]['popup'].submenu(x,popupid)
            main_popup.send(self.userid)
    
    def createdata(self, type, statsPlayers):
        self.Data[type] = []
        stats = self.TakenPlayers if type in ['Attacker','Attackers'] else self.GivenPlayers
        stats = self.KilledPlayers if type == 'Killed' else stats
        addtype = xalang(type,self.lang)
        for name in stats:
            player = stats[name]
            if self.setting == 5:
                if not type in self.Totals:
                    self.Totals[type] = dataTotals(player.hits,player.damage,player.kills)
                else:
                    self.Totals[type].addTotals(player.hits,player.damage,player.kills)
            hittype = 'hit' if player.hits == 1 else 'hits'
            if type == 'Killed' and player.kills >= 1:
                """ 
                Killer Jason mac10 @ 1.26m (3.69ft) still has 8 hp left
                Killed <name> <weapoN> @ <distance> <feet> 
                """
                text = xalang('KillsText',{'type':addtype,'name':name,'damage':player.damage,'hits':player.hits,'hittype':hittype},self.lang)
                newtext = xalang("WeaponText", {"text":text, "weapon":player.weapon,"distance":player.distance}, self.lang)
                text = gui2(newtext, addtype) if self.setting > 2 else newtext
                if self.setting in [1,3,5]:
                    sort = sorted(player.hitgroup)
                    text = '%s, %s: %s'%(text,xalang(hitgroups[sort[0]],self.lang),player.hitgroup[sort[0]])
                    for x in range(1,len(player.hitgroup)):
                        text = '%s - %s: %s'%(text,xalang(hitgroups[sort[x]],self.lang),player.hitgroup[sort[x]])
            else:
                newtype = '%s %s'%(addtype,xalang('HeadShot',{},self.lang)) if type == 'Killed' and player.headshot else addtype
                text = xalang('MainText',{'type':newtype,'name':name,'damage':player.damage,'hits':player.hits,'hittype':hittype},self.lang)
                newtext = xalang('WeaponText',{'text':text,'weapon':player.weapon,'distance':player.distance},self.lang) if type == 'Killed' else text
                text = gui2(newtext,addtype) if self.setting > 2 else newtext
                if self.setting in [1,3,5]:
                    sort = sorted(player.hitgroup)
                    text = '%s, %s: %s'%(text,xalang(hitgroups[sort[0]],self.lang),player.hitgroup[sort[0]])
                    for x in range(1,len(player.hitgroup)):
                        text = '%s - %s: %s'%(text,xalang(hitgroups[sort[x]],self.lang),player.hitgroup[sort[x]])
            self.Data[type].append(text)

class DamageRecord:
    def __init__(self, dmg_health, hitgroup):
        self.damage = dmg_health
        self.hits = 1
        self.hitgroup = {hitgroup:1}
        self.kills = 0
    
    def addDamage(self, dmg_health, hitgroup):
        self.damage += dmg_health
        self.hits += 1
        if not hitgroup in self.hitgroup:
            self.hitgroup[hitgroup] = 1
        else:
            self.hitgroup[hitgroup] += 1

class KillRecord:
    def __init__(self, distance, weapon, headshot):
        self.distance = distance
        self.weapon = weapon
        self.headshot = headshot
        self.kills = 1
    
    def addKill(self, distance, weapon, headshot):
        self.distance = distance
        self.weapon = weapon
        self.headshot = headshot
        self.kills += 1
    
    def addDamage(self, dmg_health, hitgroup):
        self.damage += dmg_health
        self.hits += 1
        if not hitgroup in self.hitgroup:
            self.hitgroup[hitgroup] = 1
        else:
            self.hitgroup[hitgroup] += 1
    
    def swapDamage(self, userid, name):
        given = PlayerList[userid].GivenPlayers[name]
        self.damage = given.damage
        self.hits = given.hits
        self.hitgroup = {}
        for hitgroup in given.hitgroup:
            self.hitgroup[hitgroup] = given.hitgroup[hitgroup]

class dataTotals:
    def __init__(self,hits,damage,kills):
        self.hits = hits
        self.damage = damage
        self.kills = kills
    
    def addTotals(self,hits,damage,kills):
        self.hits += hits
        self.damage += damage
        self.kills += kills


def load():
    global gui, gui2
    gui = lambda x: x.replace('#green','').replace('#default','').replace('#lightgreen','')
    gui2 = lambda x,y: gui(x.replace('#lightgreen%s'%y,'   '))
    xavictimstats.xasettings.registerMethod(xavictimstats, sendmenu, xalang['Victim Stats Options'])
    xavictimstatscommand = xavictimstats.addCommand('xa_victimstatssetting', sendmenu, 'victimstats_settingtings', 'UNRESTRICTED')
    xavictimstatscommand.register(['console', 'server'])

    if str(victimstats_command):
        xavictimstatssaycommand = xavictimstats.addCommand(str(victimstats_command), display, 'victim_stats', 'UNRESTRICTED', 'Send player stats while alive')
        xavictimstatssaycommand.register(['say'])

    for userid in playerlib.getUseridList('#human'):
        gamethread.queue(default, str(userid))

def es_map_start(ev):
    for userid in playerlib.getUseridList('#human'):
        default(str(userid))

def player_activate(ev):
    if ev['es_steamid'] == 'BOT': return
    default(str(ev['userid']))

def default(userid):
    PlayerList[userid] = Player(userid)

def player_disconnect(ev):
    userid = str(ev['userid'])
    if userid in PlayerList:
        del PlayerList[userid]

def player_spawn(ev):
    default(str(ev['userid']))

def player_hurt(ev):
    if not ev['es_attackerteam']: return
    team = int(ev['es_attackerteam'])
    userteam = int(ev['es_userteam'])
    usersteam = ev['es_steamid']
    steam = ev['es_attackersteamid']
    if userteam == team or not team in [2,3] or steam == usersteam == 'BOT': return
    userid = ev['userid']
    attacker = ev['attacker']
    dmg_health = int(ev['dmg_health'])
    group = int(ev['hitgroup'])
    hitgroup = 2 if not group else group
    if usersteam != 'BOT':
        victim = PlayerList[userid]
        if victim.setting:
            victim.damageTaken(ev['es_attackername'],dmg_health,hitgroup)
    if steam == 'BOT': return
    shooter = PlayerList[attacker]
    if shooter.setting:
        shooter.damageGiven(ev['es_username'],dmg_health,hitgroup)

def player_death(ev):
    usersteam = ev['es_steamid']
    steam = ev['es_attackersteamid']
    if steam == usersteam == 'BOT': return
    userid = ev['userid']
    attacker = ev['attacker']
    if attacker != userid and attacker.isdigit() and int(attacker):
        headshot = int(ev['headshot'])
        weapon = ev['weapon']
        team = int(ev['es_attackerteam'])
        userteam = int(ev['es_userteam'])
        killtype = 'Killer' if not userteam == team else 'TeamKilled'
        killtype = 'Suicide' if userid in ['0',attacker] else killtype
        distance = playerlib.getPlayer(userid).get('distance',attacker) if userid != attacker else 0
        feet = '%0.2fft'%(distance * 0.0375)
        meters = '%0.2fm'%(distance * 0.01278)
        dist = feet if victimstats_distance == 1 else meters
        dist = str('%s (%s)'%(meters,feet)) if victimstats_distance == 3 else dist
        if usersteam != 'BOT':
            victim = PlayerList[userid]
            if victim.setting:
                victim.sendStats((killtype,headshot,ev['es_attackername'],weapon,dist,ev['es_attackerhealth']))
        if steam == 'BOT': return
        killer = PlayerList[attacker]
        if killer.setting and userteam != team in [2,3]:
            killer.playerKilled(ev['es_username'],weapon,headshot,dist)

def round_end(ev):
    for userid in playerlib.getUseridList('#alive,#human'):
        player = PlayerList[str(userid)]
        if player.setting:
            player.sendStats()

def display():
    player = PlayerList[str(es.getcmduserid())]
    if player.setting:
        player.sendStats()

def sendmenu(userid = False):
    userid = es.getcmduserid()
    player = PlayerList[str(userid)]
    userlang = player.lang
    victimstatsmenu = popuplib.easymenu('victimstatsmenu','victimstatsmenu_choice',select)
    victimstatsmenu.settitle(xalang('Victim Stats Options',{},userlang))
    for x in xavictimstats_menu:
        y = xavictimstats_menu[x]
        z = xalang(y,userlang)
        z = '%s    [%s]'%(z,xalang('current',{},userlang)) if x == player.setting else z
        victimstatsmenu.addoption(x, z)
    victimstatsmenu.send(userid)

def select(userid, choice, popupid):
    type = xavictimstats_menu[choice]
    player = PlayerList[str(userid)]
    userlang = player.lang
    msg = 'Changed to' if choice != player.setting else 'Left as'
    es.tell(userid,'#multi',xalang(msg,{'setting':type},userlang))
    if choice != player.setting:
        player.set(choice)

def unload():
    xavictimstats.unregister()
