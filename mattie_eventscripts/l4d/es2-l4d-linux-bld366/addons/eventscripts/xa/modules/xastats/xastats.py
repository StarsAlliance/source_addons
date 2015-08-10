import time
import os
from sqlite3 import dbapi2 as sqlite

import es
import playerlib
import popuplib
import weaponlib

from xa import xa

info = es.AddonInfo()
info.name     = "Stats Module"
info.version  = "1.0.0"
info.author   = "Carlsagan43 (Adminc) & Steven Hartin (freddukes)"
info.basename = "xastats"

xastats   = xa.register(info.basename)
directory = es.getGameName()

mani_string  = "steamid,address,lastconnected,rank,points,deaths,headshots,kills,suicides,teamkills,timeconnected,"
mani_string += "damage,hitgeneric,hithead,hitchest,hitstomach,hitleftarm,hitrigharm,hitleftleg,hitrightleg,ak47_kills,"
mani_string += "m4a1_kills,mp5navy_kills,awp_kills,usp_kills,deagle_kills,aug_kills,hegrenade_kills,xm1014_kills,"
mani_string += "knife_kills,g3sg1_kills,sg550_kills,galil_kills,m3_kills,scout_kills,sg552_kills,famas_kills,glock_kills,"
mani_string += "tmp_kills,ump45_kills,p90_kills,m249_kills,elite_kills,mac10_kills,fiveseven_kills,p228_kills,"
mani_string += "flashbang_kills,smokegrenade_kills,shotsfired,shotshit,bombsplanted,bombsdefused,hostagerescues,hostagetouches,"
mani_string += "hostagekills,bombsexploded,bombs_dropped_ignore,bombdefusalattempts,vip_escaped_ignore,vip_killed_ignore,"
mani_string += "ctwins,lost_as_ct_ignore,twins,lost_as_t_ignore,name"

stats_mode          = xastats.setting.createVariable('stats_calculate',                    3, "This defines how the stats are caclulated, 0 = by player kills, 1 = by player kill death ratio, 2 = by kills - deaths, 3 = by points")
stats_unique        = xastats.setting.createVariable('stats_unique',                       0, "Should players be remembered by steamid or by ip address, 0 = steamid, 1 = ip address. It would be best to use ip addresses when the server is on LAN mode")
stats_pdf           = xastats.setting.createVariable('stats_pdf',                          1, "Should the probability density function be used to tell players their chance of getting a high kill streak. If you don't know what this means, it's ok to just leave this alone. If you your server has limited CPU power, then turn this off")
stats_pdfthreshold  = xastats.setting.createVariable('stats_pdfthreshold',                 4, "If pdf is turned on, how many kills in a row should the player have before telling them their chance of getting that many kills. Set this higher if you feel that the players on your server regularly get more than 4 kills.")
stats_silent        = xastats.setting.createVariable('stats_silent',                       0, "When a player types !statsme, !session, or !rank, should other player see that the player typed it in? 0 = tell everyone, 1 = tell no one")
stats_publicrank    = xastats.setting.createVariable('stats_show_rank_to_all',             1, "This defines whether the command 'rank' is shown to all or not (1 = all players)")
stats_rankdays      = xastats.setting.createVariable('stats_delete_ranks_after_x_days',   21, "Number of days before a player's stats are removed")
stats_headshot      = xastats.setting.createVariable('stats_points_headshot_multiplier', 1.2, "This is the headshot multiplier. Set it to 1.0 if yout dont want players to get more points for getting headshots")
stats_killmult      = xastats.setting.createVariable('stats_points_multiplier',          5.0, "Kill multiplier. This is multiplied into the point the attacker gets for killing a player")
stats_deathmult     = xastats.setting.createVariable('stats_points_death_multiplier',    1.0, "Death multiplier. This is multiplied into the number of points the victim loses when he gets killed. Set this to 0.0 to turn off point loss")
stats_minkills      = xastats.setting.createVariable('stats_kills_minimum',               10, "Minimum number of kills needed to affect the victim's points. This helps keep new players from overly affecting the score of long time players")
stats_rankthreshold = xastats.setting.createVariable('stats_kills_required',              10, "Minimum Number of kills needed for the player to be ranked")
stats_poptime       = xastats.setting.createVariable('stats_top_display_time',            15, "Determines how long popups stay open in seconds")
stats_addonly       = xastats.setting.createVariable('stats_points_add_only',              0, "If set to 0 you lose points for being killed, if set to 1 you do not")
stats_startpoints   = xastats.setting.createVariable('stats_start_points',              1000, "The amount of points that a player starts off with")

bonusTable = {}
bonusTable['teamkill'] = xastats.setting.createVariable('stats_teamkill_bonus', -10, "The number of points a player will lose for teamkilling")
bonusTable['suicide']  = xastats.setting.createVariable('stats_suicide_bonus',   -5, "The number of points a player will lose for committing suicide. Note that this does not include players typing kill in console or admin slay")
if directory == "cstrike":
    bonusTable['hostagekill']       = xastats.setting.createVariable('stats_css_hostage_killed_bonus', -15, "How many points the player will lose for killing a hostage")
    bonusTable['hostagerescue']     = xastats.setting.createVariable('stats_css_hostage_rescued_bonus', 5, "How many points a player will gain for rescuing a hostage")
    bonusTable['bombplant']         = xastats.setting.createVariable('stats_css_bomb_planted_bonus', 10, "How many points a player will gain planting the bomb")
    bonusTable['bombdefuse']        = xastats.setting.createVariable('stats_css_bomb_defused_bonus', 10, "How many points a player will gain defusing the bomb")
    bonusTable['teamcteliminated']  = xastats.setting.createVariable('stats_css_t_eliminated_team_bonus', 2, "If Terrorists kill all CT, then all terrrorist will gain this many points")
    bonusTable['teamteliminated']   = xastats.setting.createVariable('stats_css_ct_eliminated_team_bonus', 2, "If CTs kill all Terrorists, then all CTs will gain this many points")
    bonusTable['teambombexplode']   = xastats.setting.createVariable('stats_css_t_target_bombed_team_bonus', 5, "If the bomb explodes, then All Terrorists will gain this many points")
    bonusTable['teambombdefuse']    = xastats.setting.createVariable('stats_css_ct_bomb_defused_team_bonus', 5, "If the bomb is defused, all CTs will gain this many points")
    bonusTable['teambombplant']     = xastats.setting.createVariable('stats_css_t_bomb_planted_team_bonus', 2, "If the bomb is planted, then All Terrorists will gain this many points")
    bonusTable['teamallhostages']   = xastats.setting.createVariable('stats_css_ct_all_hostages_rescued_team_bonus', 10, "If all hostages are rescued, all CTs will gain this many points")
    bonusTable['teamnohostages']    = xastats.setting.createVariable('stats_css_t_no_hostages_rescued_team_bonus', 0, "If Hostages are not rescued, then All Terrorists will gain this many points. Note: This does not stack with any other winning conditions")
    bonusTable['teamhostagekill']   = xastats.setting.createVariable('stats_css_ct_hostage_killed_team_bonus', 1, "If a player kills a hostage, everyone on his team will lose this many points")
    bonusTable['teamhostagerescue'] = xastats.setting.createVariable('stats_css_ct_hostage_rescued_team_bonus', 1, "If a single hostage is rescued, all CTs will gain this many points")
elif directory == "dod":
    bonusTable['teamblockcapture']  = xastats.setting.createVariable('stats_dods_block_capture', 4, "Points given to all players blocking the capture")
    bonusTable['teamcapturepoint']  = xastats.setting.createVariable('stats_dods_capture_point', 4, "Points given to all players that captured the point")
    bonusTable['teamroundwin']      = xastats.setting.createVariable('stats_dods_round_win_bonus', 4, "Points given to all players on winning team")



weaponTable = {}
if directory == "cstrike":
    weaponTable['weapon_ak47']         = xastats.setting.createVariable('stats_css_weapon_ak47',       1.0, "Weapon weight (1.0 default)")
    weaponTable['weapon_aug']          = xastats.setting.createVariable('stats_css_weapon_aug',        1.0, "Weapon weight (1.0 default)")
    weaponTable['weapon_awp']          = xastats.setting.createVariable('stats_css_weapon_awp',        1.0, "Weapon weight (1.0 default)")
    weaponTable['weapon_deagle']       = xastats.setting.createVariable('stats_css_weapon_deagle',     1.2, "Weapon weight (1.2 default)")
    weaponTable['weapon_elite']        = xastats.setting.createVariable('stats_css_weapon_elite',      1.4, "Weapon weight (1.4 default)")
    weaponTable['weapon_famas']        = xastats.setting.createVariable('stats_css_weapon_famas',      1.0, "Weapon weight (1.0 default)")
    weaponTable['weapon_fiveseven']    = xastats.setting.createVariable('stats_css_weapon_fiveseven',  1.5, "Weapon weight (1.5 default)")
    weaponTable['weapon_flashbang']    = xastats.setting.createVariable('stats_css_weapon_flashbang',  5.0, "Weapon weight (5.0 default)")
    weaponTable['weapon_g3sg1']        = xastats.setting.createVariable('stats_css_weapon_g3sg1',      0.8, "Weapon weight (0.8 default)")
    weaponTable['weapon_galil']        = xastats.setting.createVariable('stats_css_weapon_galil',      1.1, "Weapon weight (1.1 default)")
    weaponTable['weapon_glock']        = xastats.setting.createVariable('stats_css_weapon_glock',      1.4, "Weapon weight (1.4 default)")
    weaponTable['weapon_hegrenade']    = xastats.setting.createVariable('stats_css_weapon_hegrenade',  1.8, "Weapon weight (1.8 default)")
    weaponTable['weapon_knife']        = xastats.setting.createVariable('stats_css_weapon_knife',        2, "Weapon weight (2.0 default)")
    weaponTable['weapon_m249']         = xastats.setting.createVariable('stats_css_weapon_m249',       1.2, "Weapon weight (1.2 default)")
    weaponTable['weapon_m3']           = xastats.setting.createVariable('stats_css_weapon_m3',         1.2, "Weapon weight (1.2 default)")
    weaponTable['weapon_m4a1']         = xastats.setting.createVariable('stats_css_weapon_m4a1',         1, "Weapon weight (1.0 default)")
    weaponTable['weapon_mac10']        = xastats.setting.createVariable('stats_css_weapon_mac10',      1.5, "Weapon weight (1.5 default)")
    weaponTable['weapon_mp5navy']      = xastats.setting.createVariable('stats_css_weapon_mp5navy',    1.2, "Weapon weight (1.2 default)")
    weaponTable['weapon_p228']         = xastats.setting.createVariable('stats_css_weapon_p228',       1.5, "Weapon weight (1.5 default)")
    weaponTable['weapon_p90']          = xastats.setting.createVariable('stats_css_weapon_p90',        1.2, "Weapon weight (1.2 default)")
    weaponTable['weapon_scout']        = xastats.setting.createVariable('stats_css_weapon_scout',      1.1, "Weapon weight (1.1 default)")
    weaponTable['weapon_sg550']        = xastats.setting.createVariable('stats_css_weapon_sg550',      0.8, "Weapon weight (0.8 default)")
    weaponTable['weapon_sg552']        = xastats.setting.createVariable('stats_css_weapon_sg552',        1, "Weapon weight (1.0 default)")
    weaponTable['weapon_smokegrenade'] = xastats.setting.createVariable('stats_css_weapon_smokegrenade', 5, "Weapon weight (5.0 default)")
    weaponTable['weapon_tmp']          = xastats.setting.createVariable('stats_css_weapon_tmp',        1.5, "Weapon weight (1.5 default)")
    weaponTable['weapon_ump45']        = xastats.setting.createVariable('stats_css_weapon_ump45',      1.2, "Weapon weight (1.2 default)")
    weaponTable['weapon_usp']          = xastats.setting.createVariable('stats_css_weapon_usp',        1.4, "Weapon weight (1.4 default)")
    weaponTable['weapon_xm1014']       = xastats.setting.createVariable('stats_css_weapon_xm1014',     1.1, "Weapon weight (1.1 default)")
elif directory == "dod":
    weaponTable['weapon_30cal']        = xastats.setting.createVariable('stats_dods_weapon_30cal',        1.25, "Weapon weight (1.25 default)")
    weaponTable['weapon_amerknife']    = xastats.setting.createVariable('stats_dods_weapon_amerknife',       3, "Weapon weight (3.0 default)")
    weaponTable['weapon_bar']          = xastats.setting.createVariable('stats_dods_weapon_bar',           1.2, "Weapon weight (1.2 default)")
    weaponTable['weapon_bazooka']      = xastats.setting.createVariable('stats_dods_weapon_bazooka',      2.25, "Weapon weight (2.25 default)")
    weaponTable['weapon_c96']          = xastats.setting.createVariable('stats_dods_weapon_c96',           1.5, "Weapon weight (1.5 default)")
    weaponTable['weapon_colt']         = xastats.setting.createVariable('stats_dods_weapon_colt',          1.6, "Weapon weight (1.6 default)")
    weaponTable['weapon_frag_ger']     = xastats.setting.createVariable('stats_dods_weapon_frag_ger',        1, "Weapon weight (1.0 default)")
    weaponTable['weapon_frag_us']      = xastats.setting.createVariable('stats_dods_weapon_frag_us',         1, "Weapon weight (1.0 default)")
    weaponTable['weapon_garand']       = xastats.setting.createVariable('stats_dods_weapon_garand',        1.3, "Weapon weight (1.3 default)")
    weaponTable['weapon_k98']          = xastats.setting.createVariable('stats_dods_weapon_k98',           1.3, "Weapon weight (1.3 default)")
    weaponTable['weapon_k98_scoped']   = xastats.setting.createVariable('stats_dods_weapon_k98_scoped',    1.5, "Weapon weight (1.5 default)")
    weaponTable['weapon_m1carbine']    = xastats.setting.createVariable('stats_dods_weapon_m1carbine',     1.2, "Weapon weight (1.2 default)")
    weaponTable['weapon_mg42']         = xastats.setting.createVariable('stats_dods_weapon_mg42',          1.2, "Weapon weight (1.2 default)")
    weaponTable['weapon_mp40']         = xastats.setting.createVariable('stats_dods_weapon_mp40',         1.25, "Weapon weight (1.25 default)")
    weaponTable['weapon_mp44']         = xastats.setting.createVariable('stats_dods_weapon_mp44',         1.35, "Weapon weight (1.35 default)")
    weaponTable['weapon_p38']          = xastats.setting.createVariable('stats_dods_weapon_p38',           1.5, "Weapon weight (1.5 default)")
    weaponTable['weapon_pschreck']     = xastats.setting.createVariable('stats_dods_weapon_pschreck',     2.25, "Weapon weight (2.25 default)")
    weaponTable['weapon_punch']        = xastats.setting.createVariable('stats_dods_weapon_punch',           3, "Weapon weight (3.0 default)")
    weaponTable['weapon_riflegren_ger']= xastats.setting.createVariable('stats_dods_weapon_riflegren_ger', 1.3, "Weapon weight (1.3 default)")
    weaponTable['weapon_riflegren_us'] = xastats.setting.createVariable('stats_dods_weapon_riflegren_us',  1.3, "Weapon weight (1.3 default)")
    weaponTable['weapon_smoke_ger']    = xastats.setting.createVariable('stats_dods_weapon_smoke_ger',       5, "Weapon weight (5.0 default)")
    weaponTable['weapon_smoke_us']     = xastats.setting.createVariable('stats_dods_weapon_smoke_us',        5, "Weapon weight (5.0 default)")
    weaponTable['weapon_spade']        = xastats.setting.createVariable('stats_dods_weapon_spade',           3, "Weapon weight (3.0 default)")
    weaponTable['weapon_spring']       = xastats.setting.createVariable('stats_dods_weapon_spring',        1.5, "Weapon weight (1.5 default)")
    weaponTable['weapon_thompson']     = xastats.setting.createVariable('stats_dods_weapon_thompson',     1.25, "Weapon weight (1.25 default)")
for weapon in weaponlib.getWeaponNameList():
    if weapon not in weaponTable:
        weaponTable[weapon] = xastats.setting.createVariable('stats_%s_%s' % (directory, weapon), 1.0, "Weapon weight (1.0 default)")

weaponTable['prop_physics']     = xastats.setting.createVariable('stats_prop_physics',  1.2, "Barrel explosions/collisions weight (1.2 default)")
weaponTable['env_explosion']    = xastats.setting.createVariable('stats_env_explosion', 1.0, "Server created explosions weight (1.0 default)")

text = xastats.language.getLanguage()    
databaseLock = False
    
class ConnectionManager(object):
    def __init__(self, filePath):
        self.path       = filePath
        self.connection = sqlite.connect(filePath)
        self.cursor     = self.connection.cursor()
        self.cursor.execute("PRAGMA journal_mode=OFF")
        self.cursor.execute("""\
CREATE TABLE IF NOT EXISTS Stat (
    StatID INTEGER PRIMARY KEY AUTOINCREMENT ,
    UserID INTEGER,
    StatName VARCHAR(255),
    StatValue INTEGER
)""")
        self.cursor.execute("""\
CREATE TABLE IF NOT EXISTS User (
    UserID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    SteamID VARCHAR(30),
    Name VARCHAR(50)
)""")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS StatIndex ON Stat(UserID);")

    def addUser(self, steamid, name):
        """
        This function adds a user into the database with default values and 
        
        @Return - the userid
        """
        self.cursor.execute("INSERT INTO User (SteamID, Name) Values (?, ?)",
                            (steamid,
                            name )
                            )
        return self.cursor.lastrowid
    
    def addPlayerStat(self, userid, stat, value):
        self.cursor.execute("""INSERT INTO Stat (UserID, StatName, StatValue) VALUES
                                              (?, ?, ?)""",
                                              (userid,
                                               stat,
                                               value)
                                               )
    
    def fetchUserIDFromSteamID(self, steamid):
        self.cursor.execute("SELECT UserID FROM User WHERE SteamID=?", (steamid,) )
        return self.fetchone()
    
    def updateStatValue(self, UserID, StatName, StatValue):
        self.cursor.execute("UPDATE Stat SET StatValue=? WHERE UserID=? AND StatName=?",
                            (StatValue,
                            UserID,
                            StatName)
                            )
    
    def updateMultipleStatValues(self, UserID, StatValues):
        for statName, statValue in statValues.iteritems():
            self.updateStatValue(UseridID, StatName, StatValue)
            
    def fetchStatValue(self, UserID, StatName):
        self.cursor.execute("SELECT StatValue FROM Stat WHERE UserID=? AND StatName=?",
                                (UserID,
                                StatName)
                                )
        return self.fetchone()
    
    def fetchAllStatValues(self, UserID):
        self.cursor.execute("SELECT StatName, StatValue FROM Stat WHERE UserID=?",
                            (UserID,)
                            )
        return self.cursor.fetchall()
            
    def fetchone(self):
        result = self.cursor.fetchone()
        if hasattr(result, "__iter__"):
            if len(result) == 1:
                return result[0]
            return result
        else:
            return result
            
    def fetchall(self):
        results = []
        result  = self.cursor.fetchone()
        if not hasattr(result, "__iter__"):
            return self.fetchone()
        for tResult in result:
            if hasattr(tResult, "__iter__"):
                if len(tResult) == 1:
                    results.append(tResult[0])
                else:
                    results.append(tResult)
            else:
                results.append(tResult)
        return results
            
    def commit(self):
        global databaseLock
        if databaseLock is False:
            databaseLock = True
            self.connection.commit()
            databaseLock = False

class PlayerManager(object):
    def __init__(self):
        self.players = {}
        
    def __del__(self):
        for player in self.players.copy():
            self.removePlayer(player)
        
    def __getitem__(self, userid):
        userid = int(userid)
        if not userid in self.players:
            self.players[userid] = Player(userid)
        return self.players[userid]
        
    def __iter__(self):
        for player in self.players.itervalues():
            yield player
            
    def __contains__(self, userid):
        return self.players.__contains__(int(userid))
    
    def addPlayer(self, userid):
        userid = int(userid)
        if userid not in self.players:
            self.players[userid] = Player(userid)
    
    def removePlayer(self, userid):
        userid = int(userid)
        if userid in self.players:
            del self.players[userid]
        else:
            raise IndexError, "Userid %s cannot be removed from the stats player manager" % userid

class Player(object):
    def __init__(self, userid):
        self.userid            = int(userid)
        self.name              = es.getplayername(self.userid)
        self.steamid           = playerlib.uniqueid(self.userid)
        self.oldAttributes     = {}
        self.currentAttributes = {}
        self.dbUserid          = database.fetchUserIDFromSteamID(self.steamid)
        if self.dbUserid is None:
            self.dbUserid = database.addUser(self.steamid, self.name)
        else:
            self.refreshAttributes()
        
    def refreshAttributes(self):
        tempAttributes = database.fetchAllStatValues(self.dbUserid)
        if tempAttributes is not None:
            for name, value in tempAttributes:
                self.currentAttributes[name] = value
            self.oldAttributes  = self.currentAttributes.copy()
        xastats.logging.log("Refreshing player's stats from sqlite database", self.userid)
    
    def commitAttributes(self):
        for attribute, value in self.currentAttributes.iteritems():
            if attribute not in self.oldAttributes:
                database.addPlayerStat(self.dbUserid, attribute, value)
            elif value != self.oldAttributes[attribute]:
                database.updateStatValue(self.dbUserid, attribute, value)
        self.oldAttributes = self.currentAttributes.copy()
        xastats.logging.log("User %s [%s]: Committing player's stats to sqlite database" % (self.name, es.getplayersteamid(self.userid) ) )
        
    def __getitem__(self, item):
        if item in self.currentAttributes:
            return self.currentAttributes[item]
        raise KeyError, "Item %s cannot be found in the player container" % item
        
    def __setitem__(self, item, value):
        self.currentAttributes[item] = value
        
    def __contains__(self, item):
        return bool(item in self.currentAttributes)
        
    def __iter__(self):
        for item in self.currentAttributes.iterkeys():
            yield item
            
class SessionManager(object):
    sessions = {}
    
    def addSession(self, userid):
        userid = int(userid)
        self.sessions[userid] = Session(userid)
    
    def deleteSession(self, userid):
        userid = int(userid)
        if userid in self.sessions:
            del self.sessions[userid]
            
    def __getitem__(self, userid):
        if str(userid).isdigit():
            userid = int(userid)
            if not userid in self.sessions:
                self.sessions[userid] = Session(userid)
            return self.sessions[userid]
        raise KeyError, "Key %s does not exist in the session manager" % userid
        
    def __iter__(self):
        for session in self.sessions.itervalues():
            yield session
            
    def __contains__(self, userid):
        userid = int(userid)
        return bool(self.sessions.__contains__(userid))
    
class Session(object):
    def __init__(self, userid):
        self.userid     = int(userid)
        self.ignoreObjects = ("temp_killstreak", "joined")
        self.session    = {}
        
    def __getitem__(self, statType):
        if statType not in self.session:
            self.session[statType] = 0 
        return self.session[statType]
        
    def __setitem__(self, statType, value):
        if statType not in self.ignoreObjects:
            if statType in self.session:
                currentValue = self.session[statType]
            else:
                currentValue = 0
            if isinstance(value, int) or isinstance(value, float):
                if statType in players[self.userid]:
                    players[self.userid][statType] += value - currentValue
                else:
                    players[self.userid][statType] = value - currentValue
            else:
                players[self.userid][statType] = value
        self.session[statType] = value
        
    def __iter__(self):
        for item in self.session.iterkeys():
            yield item
        
class RankManager(object):
    def __init__(self):
        self.ranks = []
        self.size  = 0
        
    def __len__(self):
        return self.size
        
    def update(self):
        database.cursor.execute("SELECT u.SteamID FROM Stat s,User u WHERE s.StatName='points' AND s.UserID=u.UserID ORDER BY s.StatValue DESC")
        self.ranks = map(lambda x: x[0], database.cursor.fetchall() )
        self.size  = len(self.ranks)
        self.updateTopTen()
        xastats.logging.log("Updated all ranked positions")
        
    def updateTopTen(self):
        self.topTenStats = {}
        for index, SteamID in enumerate(self.getTopTen()):
            self.topTenStats[index + 1] = {}
            database.cursor.execute("SELECT Name FROM User WHERE SteamID=?", (SteamID,) )
            self.topTenStats[index + 1]['name'] = database.fetchone()
            
            database.cursor.execute("SELECT s.StatValue FROM Stat s, User u WHERE u.SteamID=? AND s.UserID=u.UserID AND s.StatName='kills'",
                                           (SteamID,) )
            self.topTenStats[index + 1]['kills'] = database.cursor.fetchone()[0]
            
            database.cursor.execute("SELECT s.StatValue FROM Stat s, User u WHERE u.SteamID=? AND s.UserID=u.UserID AND s.StatName='deaths'",
                                           (SteamID,) )
            self.topTenStats[index + 1]['deaths'] = database.cursor.fetchone()[0]
            
            database.cursor.execute("SELECT s.StatValue FROM Stat s, User u WHERE u.SteamID=? AND s.UserID=u.UserID AND s.StatName='points'",
                                           (SteamID,) )
            self.topTenStats[index + 1]['points'] = database.cursor.fetchone()[0]
        xastats.logging.log("Updated top 10 positions")  
    
    def getTopTenStats(self):
        return self.topTenStats          
        
    def getPosition(self, steamid):
        try:
            return self.ranks.index(steamid) + 1
        except ValueError:
            return -1
    
    def getRange(self, lower, upper):
        return self.ranks[lower:upper]
    
    def getTopTen(self):
        return self.ranks[:10]
    
###############
# Singletons
database = ConnectionManager( os.path.join(xa.coredir(), "data", "stats.sqlite") )
players  = PlayerManager()
sessions = SessionManager()
ranks    = RankManager()

def load():

    xastatsmenu = popuplib.easymenu('xastatsmenu', None, menuReader)
    xastatsmenu.settitle(text['menu'])
    xastatsmenu.addoption('resetplayer', text['resetplayer'])
    xastatsmenu.addoption('resetall',    text['resetall'])
    xastatsmenu.addoption('importmani',  text['importmani'])
    xastatsmenu.addoption('convertold',  text['convertold'])
    
    xastatsmenu = popuplib.easymenu('xastatmenu_public', None, resetPlayerStats)
    xastatsmenu.settitle(text['resetstats'])
    xastatsmenu.addoption('reset', text['resetpublic'])
    
    xastats.addMenu("xastatsmenu", text['menu'], 'xastatsmenu', 'manage_stats', 'ADMIN')
    xastats.addMenu('xastatmenu_public', text['resetstats'], 'xastatmenu_public', 'reset_stats', 'UNRESTRICTED')

    if (es.ServerVar('eventscripts_currentmap') != ""):
        ranks.update()

    for each in map(str, es.getUseridList()): # The session table is something we want to create rather than reload
        player_activate({'userid':each})

    xastats.addCommand('rank',      rankPlayer,  'stat_rank',     'UNRESTRICTED').register(('say', 'console')) 
    xastats.addCommand('session',   statPopup,   'stat_session',  'UNRESTRICTED').register(('say', 'console')) 
    xastats.addCommand('statsme',   statPopup,   'stat_statsme',  'UNRESTRICTED').register(('say', 'console'))
    xastats.addCommand('stats',     statPopup,   'stat_statsme',  'UNRESTRICTED').register(('say', 'console'))
    xastats.addCommand('top',       viewTop,     'stat_top',      'UNRESTRICTED').register(('say', 'console'))
    xastats.addCommand('hitboxme',  hitboxPopup, 'stat_hitboxme', 'UNRESTRICTED').register(('say', 'console'))
    xastats.addCommand('resetrank', resetPlayerStats, 'stat_reset', 'UNRESTRICTED').register(('say', 'console'))
    
def unload():
    # check we have commited and then 
    database.commit()
    database.cursor.close()
    database.connection.close()
    
    xastats.unregister()
    popuplib.delete("xastatsmenu")
    
def es_map_start(event_var):
    ranks.update()
    
    ignore = time.time() - float(stats_rankdays) * 86400
    
    database.cursor.execute("SELECT UserID From Stat WHERE StatName='lastconnected' AND StatValue < ?", (ignore,))
    UserIDs = map(lambda x: x[0], database.cursor.fetchall())
    for UserID in UserIDs:
        database.cursor.execute("DELETE FROM Stat WHERE UserID=?", (UserID,) )
        database.cursor.execute("DELETE FROM User WHERE UserID=?", (UserID,) )
    
def player_activate(event_var):
    userid = event_var['userid']
    if userid not in sessions:
        sessions.addSession(userid)
    if userid not in players:
        players.addPlayer(userid)
    sessions[userid]['joined'] = int(time.time())
    for statType in [
                    'kills', 
                    'deaths', 
                    'headshots', 
                    'shotshit',
                    'shotsfired',
                    'killstreak', 
                    'suicides', 
                    'damage', 
                    'teamkills', 
                    'twins', 
                    'ctwins', 
                    'trounds', 
                    'ctrounds', 
                    'hostagekills', 
                    'hostagerescues', 
                    'bombsplanted',
                    'bombsexploded', 
                    'bombsdefused'
                    ]:
        if statType not in players[userid]:
            players[userid][statType] = 0
    if 'points' not in players[userid]:
        players[userid]['points'] = int(stats_startpoints)
    
def player_disconnect(event_var):
    userid = event_var['userid']
    if userid in players:
        if 'timeconnected' not in players[userid]:
            players[userid]['timeconnected'] = int(time.time()) - sessions[userid]['joined']
        else:
            players[userid]['timeconnected'] += int(time.time()) - sessions[userid]['joined']
        players[userid]['lastconnected'] = int(time.time())
        players[userid].commitAttributes()
        sessions.deleteSession(userid)
        players.removePlayer(userid)
    
def player_death(event_var):
    victim       = event_var['userid']
    attacker     = event_var['attacker']
    victimteam   = event_var['es_userteam']
    attackerteam = event_var['es_attackerteam']
    weapon       = event_var['weapon']
    headshot     = event_var['headshot']
    
    if not headshot.isdigit():
        headshot = 0
    else:
        headshot = int(headshot)

    if attacker == victim: # they typed kill in console or the like
        return

    vsess = sessions[victim]
    
    if attacker == "0": # they committed suicide
        vsess["suicides"] += 1
        vsess["deaths"]   += 1
        vsess["points"]   += int(bonusTable["suicide"])
        
    else: # one player kills another
        asess = sessions[attacker] # only add attacker data once we know they exist

        if victimteam == attackerteam:  # We have a team killer
            asess["teamkills"]   += 1
            vsess["deaths"]      += 1
            asess["points"]      += int(bonusTable["teamkill"])
        else:
            # Lets first rack up all the kills 
            if headshot > 0:
                asess["headshots"] += 1
            asess["kills"]  += 1
            vsess["deaths"] += 1

            asess[weapon + "_kills"] += 1
            
            # check to see if we should do point calculations
            if int(stats_mode) == 3:
                vscore = vsess["points"]
                ascore = asess["points"]

                if headshot > 0:
                    headshot = stats_headshot
                else:
                    headshot = 1.0
                    
                if weapon in weaponTable:
                    vscoreDelta = 1.0 * vscore / ascore * float(weaponTable[weapon]) * float(headshot) * float(stats_deathmult)
                    ascoreDelta = 1.0 * vscore / ascore * float(weaponTable[weapon]) * float(headshot) * float(stats_killmult)
                
                    # lets update the player session.  Note that the socre 
                    # put here is only the score changes made during the session.
                    asess["points"] += int(ascoreDelta)
    
                    # only subtract player points if the killer has a few kills
                    if players[attacker]["kills"] > int(stats_minkills) and int(stats_addonly) == 0:
                        vsess["points"] -= int(vscoreDelta)

            vstat = players[victim]
            ## can we do PDF calculations?
            if int(stats_pdf) == 1:
            
                if "killdev" not in vstat:
                    vstat["killdev"] = 0
                if "kills" not in vstat:
                    vstat["kills"]   = 0
                    
                vstat["killdev"] += pow(vsess["temp_killstreak"], 2)

                if vsess["temp_killstreak"] >= int(stats_pdfthreshold): # should we player that he did well?
                    stddevtemp = vstat["killdev"]  * vstat["deaths"]
                    stddevtemp = stddevtemp - pow( vstat["kills"], 2)
                    if stddevtemp < 0: # this shouldn't happen, but if it does...
                        stddevtemp = 0
                        xastats.logging.log("***ERROR*** Standard Deviations gone horribly wrong!")
                    stddev = 1.0 / (vstat['deaths']) * pow(stddevtemp, 0.5) # we finally have the standard deviation


                        
                    if stddev != 0:
                        e = 2.7182818284590451 # im not importing the math module for a single constant
                        pi = 3.1415926535897931 # not for two either
                        exp = vsess["temp_killstreak"] - 1.0 * ( vstat["kills"] ) / ( vstat["deaths"] )
                        exp = -0.5 * pow(exp / stddev, 2) # dont worry about this.
                        pdf = pow(e, exp) / (stddev * pow(2 * pi , 0.5 )  )  * 100  # this is the probability that we have been looking for
                    else:
                        pdf = 100


                    es.tell(victim, "#multi",
                            "#defaultYou had a #green %0.1f%% #default chance of getting #green%i #defaultkills in a row." % 
                            (pdf,
                            vsess["temp_killstreak"]))
                    # Wow that took a while.  Hope you guys enjoy it!

            #lets finish the kill streak info
            if vsess["killstreak"] < vsess["temp_killstreak"]:
                vsess["killstreak"] = vsess["temp_killstreak"] # a new killstreak record
            vsess["temp_killstreak"] = 0
            asess["temp_killstreak"] += 1
            
def player_hurt(event_var):
    attacker = event_var['attacker']
    vteam    = event_var['es_userteam']
    ateam    = event_var['es_attackerteam']
    
    damage   = event_var["dmg_health"]
    if damage.isdigit():
        damage = int(damage)
    else:
        damage = event_var['damage']
        if damage.isdigit():
            damage = int(damage)
        else:
            damage = 0
            
    hitgroup = int(event_var["hitgroup"])

    if ateam == vteam: # no team damage
        return
    elif attacker == "0":
        return
    else:
        asess = sessions[attacker]
        asess["shotshit"] += 1
        asess["damage"]   += damage
        
        if hitgroup == 0:
            asess["hitgeneric"]
        elif hitgroup == 1:
            asess["hithead"]
        elif hitgroup == 2:
            asess["hitchest"]       
        elif hitgroup == 3:
            asess["hitstomach"]
        elif hitgroup == 4:
            asess["hitleftarm"]
        elif hitgroup == 5:
            asess["hitrightarm"]
        elif hitgroup == 6:
            asess["hitleftleg"]
        else:
            asess["hitrightleg"]
            
def weapon_fire(event_var):
    asess = sessions[event_var["userid"]]
    asess["shotsfired"] += 1
    
def round_end(event_var):  
    reason = event_var["reason"]
    
    for player in players:
        player.commitAttributes()
    database.commit()

    winner     = int(event_var["winner"])
    for each in es.getUseridList():
        tempSession = sessions[each]
        team        = es.getplayerteam(each)
        
        if team == 2:
            tempSession["trounds"]  += 1
        else:
            tempSession["ctrounds"] += 1
            
        if team == winner:
            if winner == 2:
                tempSession["twins"]  += 1
            else:
                tempSession["ctwins"] += 1    
            
            if reason == "9":    #all ct are dead
                tempSession["points"] += int(bonusTable["teamcteliminated"])
                
            elif reason == "13": # hostages not rescued
                tempSession["points"] += int(bonusTable["teamnohostages"])
                
            elif reason == "1":  #target bombed
                tempSession["points"] += int(bonusTable["teambombexplode"])
                
            elif reason == "8":  #all t are dead
                tempSession["points"] += int(bonusTable["teamteliminated"])
            
            elif reason == "11": # all hostages rescued
                tempSession["points"] += int(bonusTable["teamallhostages"])
                
            elif reason == "7":  # bomb defused
                tempSession["points"] += int(bonusTable["teambombdefuse"])       
                
def bomb_planted(event_var):
    tempSession = sessions[event_var['userid']]
    tempSession["bombsplanted"] += 1
    tempSession["points"] += int(bonusTable["bombplant"])
    for each in filter(lambda x: es.getplayerteam(x) == 2, es.getUseridList()):
        sessions[each]["points"] += int(bonusTable["teambombplant"])


def bomb_begindefuse(event_var):
    sessions[event_var["userid"]]["bombdefusalattempts"] += 1


def bomb_defused(event_var):
    tempSession = sessions[event_var["userid"]]
    tempSession["bombsdefused"] += 1
    tempSession["points"] += int(bonusTable["bombdefuse"])
    for each in filter(lambda x: es.getplayerteam(x) == 3, es.getUseridList()):
        sessions[each]["points"] += int(bonusTable["teambombdefuse"])

def bomb_exploded(event_var):
    sessions[event_var["userid"]]["bombsexploded"] += 1
    for each in filter(lambda x: es.getplayerteam(x) == 2, es.getUseridList()):
        sessions[each]["points"] += int(bonusTable["teambombexplode"])

def hostage_follows(event_var):
    sessions[event_var["userid"]]["hostagetouches"] += 1   

def hostage_rescued(event_var):
    if event_var['userid'] > 0:
        sessions[event_var['userid']]["hostagerescues"] += 1
        sessions[event_var['userid']]["points"] += int(bonusTable["hostagerescue"])
    for each in filter(lambda x: es.getplayerteam(x) == 3, es.getUseridList()):
        sessions[each]["points"] += int(bonusTable["teamhostagerescue"])

def hostage_killed(event_var):
    userid      = event_var['userid']
    tempSession = sessions[userid]
    tempSession["hostagekills"] += 1
    tempSession["points"] += int(bonusTable["hostagekill"])
    team = int(event_var['es_userteam'])
    for each in filter(lambda x: es.getplayerteam(x) == team, es.getUseridList()):
        sessions[each]["points"] -= abs(int(bonusTable["teamhostagekill"]))

def dod_axis_win(event_var):
    for each in (lambda x: es.getplayerteam(x) == 2, es.getUseridList()):
        sessions[each]["points"] -= abs(int(bonusTable["teamroundwin"]))

    round_end({'winner': '2', 'reason':'0', 'message':''})

def dod_allies_win(event_var):
    for each in (lambda x: es.getplayerteam(x) == 3, es.getUseridList()):
        sessions[each]["points"] -= abs(int(bonusTable["teamroundwin"]))

    round_end({'winner': '3', 'reason':'0', 'message':''})

def dod_bomb_exploded(event_var):
    global playerbomb
    userid = event_var['userid']
    sessions[userid]["bombsexploded"] += 1
    sessions[userid]["points"] += int(bonusTable["teambombexplode"])
    playerbomb = userid

def dod_bomb_defused(event_var):
    userid = event_var['userid']
    sessions[userid]["bombsdefused"] += 1
    sessions[userid]["points"] += int(bonusTable["bombdefuse"])

def dod_capture_blocked(event_var):
    global sessionTable, statTable
    sessions[event_var['userid']]["points"] += int(bonusTable["teamblockcapture"])

def dod_point_captured(event_var):
    if int(event_var['bomb']) == 1:
        if playerbomb:
            sessions[playerbomb]["points"] += int(bonusTable["teamcapturepoint"])
    else:
        for each in filter(lambda x: es.getplayerprop(x, "CDODPlayer.m_Shared.dodsharedlocaldata.m_iCPIndex") == int(event_var['cp']), es.getUseridList()):
            sessions[each]["points"] += int(bonusTable["teamcapturepoint"])
            
def menuReader(adminid, option, name):
    if option == "resetall":
        for each in es.getUseridList():
            players.removePlayer(each)
            sessions.deleteSession(each)
            
        database.cursor.execute("DROP TABLE Stat")
        database.cursor.execute("DROP TABLE User")
        database.commit()
        database.cursor.close()
        database.connection.close()
        database.__init__(os.path.join(xa.coredir(), "data", "stats.sqlite"))
        
        for each in es.getUseridList():
            player_activate({'userid':each})
            
        es.tell(adminid, "ALL PLAYER DATA DESTROYED")

    elif option == "importmani":
        filePath = os.path.join(xa.gamedir() + "cfg", "mani_admin_plugin", "data", "mani_ranks.txt")
        if os.path.isfile(filePath):
            if convertManiTable(filePath):
                es.tell(adminid, "ALL MANI STATS CONVERTED")
        else:
            es.tell(adminid, "There is no mani_ranks.txt in cfg/mani_admin_plugin/data")
        

    elif option == "resetplayer":
        popup = popuplib.easymenu('stats_adminplayer', None, resetPlayer)
        popup.settitle("Select Player")
        for userid in es.getUseridList():
            popup.addoption( userid, es.getplayername(userid) )
        popup.send(adminid)
        
    elif option == "convertold":
        filePath = os.path.join(xa.coredir(), "data", "stats.txt")
        if os.path.isfile(filePath):
            if convertOldStats(filePath):
                es.tell(adminid, "ALL STATS CONVERTED")
        else:
            es.tell(adminid, "There is no stats.txt in ../xa/data/")

def resetPlayer(adminid, option, name):
    steamid = es.getplayersteamid(option)
    userid  = players[option].dbUserid
    database.cursor.execute("DELETE FROM User WHERE SteamID=?", (steamid,) )
    database.cursor.execute("DELETE FROM Stat WHERE UserID=?", (userid,) )
    
    sessions.deleteSession(option)
    players.removePlayer(option)
    
    player_activate({'userid':option})
    es.tell(adminid, '#green', 'Players stats successfully removed!')
    
def resetPlayerStats(userid = None, choice = None, popupid = None):
    if userid is not None:
        userid = es.getcmduserid()
    steamid = es.getplayersteamid(userid)
    UserID  = players[userid].dbUserid
    database.cursor.execute("DELETE FROM User WHERE SteamID=?", (steamid,) )
    database.cursor.execute("DELETE FROM Stat WHERE UserID=?", (UserID,) )
    
    sessions.deleteSession(userid)
    players.removePlayer(userid)
    
    player_activate({'userid':userid})
    es.tell(userid, '#green', 'Stats successfully removed!')
    
def rankPlayer():
    userid = es.getcmduserid()
    if es.getargc() >= 2:
        userid = es.getuserid(es.getargs().split()[1:])
        if not es.exists('userid', userid):
            userid = es.getcmduserid()
    player = sessions[userid]
    name   = es.getplayername(userid)
    kills  = players[userid]["kills"]
    deaths = players[userid]["deaths"]
    points = players[userid]["points"]
    rank   = ranks.getPosition(es.getplayersteamid(userid))
    
    if deaths == 0:
        if kills == 0:
            kdr = 0.0
        else:
            kdr = kills
    elif kills == 0:
        kdr = 0.0
    else:
        kdr = kills / float(deaths)
    if int(stats_publicrank) == 1:
        if rank == -1:
            es.msg("Player %s is not yet ranked. Ranks are updated at map change." % (name) )
        else:
            es.msg("Player %s is ranked %i/%i with %i points, %i kills, %i deaths, kd ratio of %0.2f" % (name,
                                                                                                         rank,
                                                                                                         len(ranks),
                                                                                                         points,
                                                                                                         kills,
                                                                                                         deaths,
                                                                                                         kdr)   )
    else:
        if rank == -1:
            es.tell(userid, "%s is not yet ranked. Ranks are updated at map change." % (name) )
        else:
            es.tell(userid, "Player %s is ranked %i/%i with %i points, %i kills, %i deaths, kd ratio of %0.2f" % (name,
                                                                                                                  rank,
                                                                                                                  len(ranks),
                                                                                                                  points,
                                                                                                                  kills,
                                                                                                                  deaths,
                                                                                                                  kdr)   )


def statPopup():
    userid  = es.getcmduserid()
    steamid = es.getplayersteamid(userid)
    
    if es.getargv(0).lower() in ("session", "!session"):
        stat = False
    else:
        stat = True

    psess = sessions[userid]
    pstat = players[userid]

    if stat:
        timeConnected = 0
        if 'timeconnected' in pstat:
            timeconnected = pstat['timeconnected']
        timeonline = timestring( int(time.time()) - psess["joined"] + timeConnected )
        kills      = pstat["kills"]
        deaths     = pstat["deaths"]
        headshots  = pstat["headshots"]
        points     = pstat["points"]
        kdr        = getPercent(kills, deaths)
        killstreak = pstat["killstreak"]
        suicides   = pstat["suicides"]
        accuracy   = getPercent(pstat["shotshit"], pstat["shotsfired"]) * 100
        damage     = pstat["damage"]
        teamkills  = pstat["teamkills"]
        twins      = pstat["twins"]
        ctwins     = pstat["ctwins"]
        trounds    = pstat["trounds"]
        ctrounds   = pstat["ctrounds"]
        tpct       = getPercent(twins, trounds) * 100
        ctpct      = getPercent(ctwins, ctrounds) * 100
        rounds     = trounds + ctrounds

        hostagekills   = pstat["hostagekills"]
        hostagerescues = pstat["hostagerescues"]


        bombsplanted  = pstat["bombsplanted"]
        bombsexploded = pstat["bombsexploded"]
        bombsdefused  = pstat["bombsdefused"]
        sign = ""
    else:
        timeonline = timestring( int(time.time() ) -  psess["joined"] )
        kills      = psess["kills"]
        deaths     = psess["deaths"]
        headshots  = psess["headshots"]
        points     = psess["points"]
        if points < 0:
            sign = "-"
        else:
            sign = "+"
        kdr = getPercent(kills, deaths)
        
        killstreak = psess["killstreak"]
        
        suicides   = psess["suicides"]
        accuracy   = getPercent(psess["shotshit"], psess["shotsfired"]) * 100

        damage     = psess["damage"]
        
        teamkills  = psess["teamkills"]
        twins      = psess["twins"]
        ctwins     = psess["ctwins"]
        trounds    = psess["trounds"]
        ctrounds   = psess["ctrounds"]
        tpct       = getPercent(twins, trounds) * 100
        ctpct      = getPercent(ctwins, ctrounds) * 100
        rounds     = trounds + ctrounds

        hostagekills   = psess["hostagekills"]
        hostagerescues = psess["hostagerescues"]


        bombsplanted  = psess["bombsplanted"]
        bombsexploded = psess["bombsexploded"]
        bombsdefused  = psess["bombsdefused"]
        
    rank = ranks.getPosition(steamid)
    if rank == -1:
        place = ""
    else:
        place = "(%i/%i)" % (rank, len(ranks) )

    pop = popuplib.create('session_popup')
    pop.addline("Data for %s" % es.getplayername(userid) )
    
    pop.addline("----------------------------") 
    pop.addline("Points: %s%s %s" % (sign, points, place ))
    pop.addline("Kills: %s Deaths %s KDR %0.2f" % (kills, deaths, kdr) )
    pop.addline("Headshots: %s" % headshots)

    pop.addline("Killstreak: %i" % killstreak )
    pop.addline("Suicides: %i" % suicides )
    pop.addline("Time: %s" % timeonline )
    
    pop.addline("----------------------------")
    pop.addline("Accuracy: %0.2f Damage: %i Team Kills: %i" % (accuracy, damage, teamkills) )
    
    pop.addline("----------------------------")
    pop.addline("Bombs Planted: %i Exploded: %i Defused: %i" % (bombsplanted, bombsexploded, bombsdefused)  )
    
    pop.addline("----------------------------")
    pop.addline("Hostages Rescued: %i Killed: %i" % (hostagerescues, hostagekills) )
    
    pop.addline("----------------------------")
    pop.addline("Wins as T: %i/%i (%0.2f%%)" % (twins, trounds, tpct ) )
    pop.addline("Wins as CT: %i/%i (%0.2f%%)" % (ctwins, ctrounds, ctpct ) )
    pop.addline("Total Rounds: %i" % rounds)
    pop.addline("->2. Weapon Stats")
    if stat:
        pop.select(2, sendWeaponStats)
    else:
        pop.select(2, sendWeaponSession)
    pop.send(userid)

def sendWeaponStats(userid, choice, popupid):
    pop = popuplib.easymenu("weaponmenu", None, lambda x,y,z:None)
    pop.settitle("Weapon kills")
    player = players[userid]
    values = []
    for stat in player:
        if stat.endswith("_kills"):
            weapon = stat.rsplit("_", 1)[0]
            value  = player[stat]
            values.append((weapon, value))
    values.sort()
    for weapon, value in values:
        pop.addoption(None, "%s - %s kills" % (weapon, value), False)
    pop.send(userid)
    
def sendWeaponSession(userid, choice, popupid):
    pop = popuplib.easymenu("weaponmenu", None, lambda x,y,z:None)
    pop.settitle("Weapon kills this session")
    player = sessions[userid]
    values = []
    for stat in player:
        if stat.endswith("_kills"):
            weapon = stat.rsplit("_", 1)[0]
            value  = player[stat]
            values.append((weapon, value))
    values.sort()
    for weapon, value in values:
        pop.addoption(None, "%s - %s kills" % (weapon, value), False)
    pop.send(userid)
        
def viewTop():
    userid = str(es.getcmduserid() )
    pop = popuplib.create('session_popup')
    topTen = ranks.getTopTenStats()
    for index in topTen:
        cTop = topTen[index]
        kills, deaths, points, name = cTop['kills'], cTop['deaths'], cTop['points'], cTop['name']
        pop.addline("%s %s=%s KDR=%0.2f" % (index, name, points, (float(max(kills, 1)) / max(deaths, 1) ) ) )
                    
    pop.send(userid)

def hitboxPopup():

    userid = str(es.getcmduserid() )
    player = players[userid]
    length = 100.0

    name     = es.getplayername(userid)
    damage   = player["damage"]
    fired    = player["shotsfired"]
    hit      = player["shotshit"]
    generic  = player["hitgeneric"]
    head     = player["hithead"]
    chest    = player["hitchest"]
    stomach  = player["hitstomach"]
    leftarm  = player["hitleftarm"]
    rightarm = player["hitrightarm"]
    leftleg  = player["hitleftleg"]
    rightleg = player["hitrightleg"]

    accuracy = getPercent(hit, fired) * 100.0
    
    pop = popuplib.create('session_popup')
    pop.addline("Hitbox data for player %s" % name)
    pop.addline("Accuracy %0.2f Damage %i" % (accuracy, damage) )
    pop.addline("----------------------------")

    pop.addline("Body: %0.2f%%" % (getPercent(generic, hit) * 100) )
    pop.addline("%s" % ("|" * int(getPercent(generic, hit) * length ) ) )
    
    pop.addline("Head: %0.2f%%" % (getPercent(head, hit) * 100) )
    pop.addline("%s" % ("|" * int(getPercent(head, hit) * length ) ) )
    
    pop.addline("Chest: %0.2f%%" % (getPercent(chest, hit) * 100) )
    pop.addline("%s" % ("|" * int(getPercent(chest, hit) * length ) ) )
    
    pop.addline("Stomach: %0.2f%%" % (getPercent(stomach, hit) * 100) )
    pop.addline("%s" % ("|" * int(getPercent(stomach, hit) * length ) ) )

    pop.addline("Left Arm: %0.2f%%" % (getPercent(leftarm, hit) * 100) )
    pop.addline("%s" % ("|" * int(getPercent(leftarm, hit) * length ) ) )
    
    pop.addline("Right Arm: %0.2f%%" % (getPercent(rightarm, hit) * 100) )
    pop.addline("%s" % ("|" * int(getPercent(rightarm, hit) * length ) ) )
    
    pop.addline("Left Leg: %0.2f%%" % (getPercent(leftleg, hit) * 100) )
    pop.addline("%s" % ("|" * int(getPercent(leftleg, hit) * length ) ) )

    pop.addline("Right Leg: %0.2f%%" % (getPercent(rightleg, hit) * 100) )
    pop.addline("%s" % ("|" * int(getPercent(rightleg, hit) * length ) ) )
           
    pop.send(userid)
    
def timestring(sec): # this function take a number of seconds and turns it into time
    vals = time.gmtime(sec)
    if vals[1] - 1 == 0:
        months = ""
    else:
        months = "%im" % (vals[1] -1)
    if vals[2] - 1 == 0:
        days = ""
    else:
        days = "%id" % (vals[2] - 1)
    if vals[3] == 0:
        hours = ""
    else:
        hours = "%ih" % vals[3]
    if vals[4] == 0:
        minutes = ""
    else:
        minutes = "%im" % vals[4]
    seconds = "%is" % vals[5]

    fullstring = "%s %s %s %s %s" % (months, days, hours, minutes, seconds)

    return fullstring.strip()

def getPercent(top, bottom):
    top    = float(top)
    bottom = float(bottom)
    
    if bottom == 0.0:
        if top == 0.0:
            ratio = 0.0
        else:
            ratio = 1.0
    else:
        ratio = top / bottom
    return ratio
    
def convertManiTable(filePath):    
    database.execute("DROP TABLE Stat")
    database.execute("DROP TABLE User")
    database.commit()
    database.cursor.close()
    database.connection.close()
    database.__init__(os.path.join(xa.coredir(), "data", "stats.sqlite"))
    
    try:
       maniRawFile = open(filePath, "r")
       maniRawData = maniRawFile.read().split('\n')
       maniRawFile.close()
    except IOError:
        es.dbgmsg(0,  "***ERROR*** Unable to read from Mani File")
    
    ignore = time.time() - float(stats_rankdays) * 86400
    
    statNames = mani_string.split(',')
    for line in maniRawData:
        statValues    = line.split(',')
        if len(statvalues) != len(statNames):
            continue
        steamid       = statValues[0]
        lastConnected = float(statValues[2])
        if lastConnected < ignore:
            continue
        name          = statValues[-1]
        user = database.fetchUserIDFromSteamID(steamid)
        if user is None:
            user = database.addUser(steamid, name)
        for index, value in enumerate(statValues):
            if value.isdigit():
                value = int(value)
            try:
                value = int(float(value))
            except ValueError:
                pass
            database.addStat(user, statNames[index], value)
    
    database.commit()
    
    for player in es.getUseridList():
        sessions.deleteSession(player)
        players.removePlayer(player)
        player_activate({'userid':player})
    ranks.update()
    
    return True
    
def convertOldStats(filePath):
    database.cursor.execute("DROP TABLE Stat")
    database.cursor.execute("DROP TABLE User")
    database.commit()
    database.cursor.close()
    database.connection.close()
    database.__init__(os.path.join(xa.coredir(), "data", "stats.sqlite"))
        
    fileData = open(filePath, "r")
    lines    = fileData.read().split('\n')
    fileData.close()
    header   = lines.pop(0)
    header   = header.split(",")
    
    for attributeString in lines:
        attributeList = []
        attributes = attributeString.split(",")
        if len(attributes) != len(header):
            continue
        if "steamid" in header:
            steamid = attributes[header.index("steamid")]
        elif "address" in attributes:
            steamid = attributes[header.index("address")]
        else:
            continue
        name = attributes[-1]
        
        UserID = database.fetchUserIDFromSteamID(steamid)
        if UserID is None:
            UserID = database.addUser(steamid, name)
        
        for index, attribute in enumerate(attributes[:-1]):
            if attribute.isdigit():
                attribute = int(attribute)
            try:
                attribute = int(float(attribute))
            except ValueError:
                pass
            attributeList.append((UserID, header[index], attribute))
        
        database.cursor.executemany("INSERT INTO Stat (UserID, StatName, StatValue) VALUES (?, ?, ?)", attributeList)
    database.commit()
    for player in es.getUseridList():
        sessions.deleteSession(player)
        players.removePlayer(player)
        player_activate({'userid':player})
    ranks.update()
    
    return True
