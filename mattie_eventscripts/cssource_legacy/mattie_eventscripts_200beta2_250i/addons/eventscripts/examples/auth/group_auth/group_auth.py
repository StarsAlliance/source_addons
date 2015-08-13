import es
import services
import services.auth

class GroupAuthService(services.auth.AuthorizationService):
    def __init__(self):
        self.name = 'group_auth'
   
    def registerCapability(self, auth_capability, auth_recommendedlevel):
        if isinstance(auth_recommendedlevel, str):
            level = cap_level(auth_recommendedlevel)
        else:
            level = int(auth_recommendedlevel)
        sql = "INSERT OR IGNORE INTO Caps (CName, CDefaultLevel) VALUES ('%s', %d);" %(auth_capability, level)
        es.sql('query', 'group_auth', sql)
        return
   
    def isUseridAuthorized(self, auth_userid, auth_capability):
        user = self.getOfflineIdentifier(auth_userid)
        data = self.isIdAuthorized(user, auth_capability)
        return data
   
    def getOfflineIdentifier(self, auth_userid):
        s = es.getplayersteamid(int(auth_userid))
        if s is None:
            raise KeyError, "The userid is not online."
        return s
   
    def isIdAuthorized(self, auth_identifier, auth_capability):
        if not auth_identifier:
            auth_identifier = 'STEAM_ID_PENDING'
        if auth_identifier == 'STEAM_ID_PENDING':
            check = self.check_id(auth_identifier, auth_capability)
        else:
            test = self.check_exists(auth_identifier)
            if test:
                check = self.check_id(auth_identifier, auth_capability)
            else:
                check = self.check_nogroup(auth_capability)
        if check:
            es.log('group_auth: ' + auth_identifier + ' was permitted ' + auth_capability)
            return True
        else:
            es.log('group_auth: ' + auth_identifier + ' was forbidden ' + auth_capability)
            return False
   
    def check_id(self, auth_identifier, auth_capability):
        sql = "SELECT COUNT(vwCombined.UId) as cp FROM vwCombined WHERE (Reviewed AND CName='%s' AND SteamId='%s');" %(auth_capability, auth_identifier)
        query = int(es.sql('queryvalue', 'group_auth', sql))
        if query:
            return True
        else:
            sql = "SELECT COUNT(vwPlayersGroups.GId) as pg FROM vwPlayersGroups WHERE SteamId='%s' AND GId in (SELECT GId from Caps, Groups where Not Reviewed AND CName='%s' AND GDefaultLevel<=CDefaultLevel);" %(auth_identifier, auth_capability)
            query = int(es.sql('queryvalue', 'group_auth', sql))
            if query:
                return True
            else:
                return False
   
    def check_nogroup(self, auth_capability):
        sql = "SELECT COUNT(vwCapsGroups.GId) as gc FROM vwCapsGroups WHERE (Reviewed AND CName='%s' AND GroupName='IdentifiedPlayers');" %(auth_capability)
        query = int(es.sql('queryvalue', 'group_auth', sql))
        if query:
            return True
        else:
            sql = "SELECT COUNT(GId) as cg from Caps, Groups where Not Reviewed AND CName='%s' AND GroupName='IdentifiedPlayers' AND GDefaultLevel<=CDefaultLevel;" %(auth_capability)
            query = int(es.sql('queryvalue', 'group_auth', sql))
            if query:
                return True
            else:
                return False
   
    def check_exists(self, auth_identifier):
        sql = "SELECT COUNT(UId) as cp FROM Players WHERE SteamId='%s';" %(auth_identifier)
        query = int(es.sql('queryvalue', 'group_auth', sql))
        if query:
            return True
        else:
            return False

group_auth = GroupAuthService()

def load():
    global gCommands
    services.register("auth", group_auth)
    gCommands = {'group_create':group_create, 'group_delete':group_delete, 'power_create':power_create, 'power_give':power_give, 'power_revoke':power_revoke, 'power_delete':power_delete, 'user_create':user_create, 'user_join':user_join, 'user_leave':user_leave, 'user_delete':user_delete}
    es.regcmd('gauth', 'examples/auth/group_auth/command_extra', 'Create groups, players, etc, via the group_auth script addon.')
    es.sql('open','group_auth','|examples/auth/group_auth')
    test = es.sql('queryvalue', 'group_auth', "SELECT COUNT(name) as num FROM sqlite_master WHERE type='table';")
    if not int(test): init_db()

def init_db():
    #Used to create the defaults if you delete DB.
    es.sql('query', 'group_auth', "CREATE TABLE [Caps] ([CId] INTEGER  PRIMARY KEY AUTOINCREMENT NOT NULL,[CName] VARCHAR(30)  UNIQUE NOT NULL,[CDefaultLevel] INTEGER  NULL,[Reviewed] BOOLEAN DEFAULT '''0''' NOT NULL);")
    es.sql('query', 'group_auth', "CREATE TABLE [GroupCaps] ([GId] INTEGER  NOT NULL,[CId] INTEGER  NOT NULL,PRIMARY KEY(Cid, Gid));")
    es.sql('query', 'group_auth', "CREATE TABLE [Groups] ([GId] INTEGER  PRIMARY KEY AUTOINCREMENT NOT NULL,[GroupName] VARCHAR(30)  UNIQUE NULL,[GDefaultLevel] INTEGER DEFAULT '''''''256''''''' NULL);")
    es.sql('query', 'group_auth', "CREATE TABLE [Players] ([Uid] INTEGER  PRIMARY KEY AUTOINCREMENT NOT NULL,[Name] VARCHAR(100)  UNIQUE NOT NULL,[SteamId] VARCHAR(30)  NULL,[Comments] TEXT  NULL);")
    es.sql('query', 'group_auth', "CREATE TABLE [PlayersGroups] ([UId] INTEGER  NOT NULL,[GId] INTEGER  NOT NULL,PRIMARY KEY(Uid, Gid));")
    es.sql('query', 'group_auth', "CREATE INDEX [IDX_PLAYERS_STEAMID] ON [Players]([SteamId]  DESC,[Name]  DESC);")
    es.sql('query', 'group_auth', "CREATE VIEW [vwCapsGroups] AS SELECT Caps.*, Groups.* FROM Caps, GroupCaps, Groups WHERE Groups.GId=GroupCaps.GId AND GroupCaps.CId=Caps.CId;")
    es.sql('query', 'group_auth', "CREATE VIEW [vwCombined] AS SELECT Caps.*, Players.*, Groups.* FROM Caps, GroupCaps, Groups, Players, PlayersGroups WHERE Players.Uid=PlayersGroups.Uid AND PlayersGroups.GId=Groups.GId AND Groups.GId=GroupCaps.GId AND GroupCaps.CId=Caps.CId;")
    es.sql('query', 'group_auth', "CREATE VIEW [vwPlayersGroups] AS SELECT Players.*, Groups.* FROM Groups, Players, PlayersGroups WHERE Players.Uid=PlayersGroups.Uid AND PlayersGroups.GId=Groups.GId;")
    user_create(['user', 'create', 'UNKNOWN','STEAM_ID_PENDING'])
    group_create(['group', 'create', 'UnidentifiedPlayers', '#UNRESTRICTED'])
    user_join(['user', 'join', 'UNKNOWN', 'UnidentifiedPlayers'])
    group_create(['group', 'create', 'IdentifiedPlayers', '#IDENTIFIED'])

def unload():
    es.sql('close', 'group_auth', '|examples/auth/group_auth')
    services.unregister("auth")

def cap_level(auth_capability):
    try:
        level = int(auth_capability)
    except ValueError:
        auth_capability = auth_capability.lower()
        if auth_capability == '#root':
            level = group_auth.ROOT
        elif auth_capability == '#admin':
            level = group_auth.ADMIN
        elif auth_capability == '#poweruser':
            level = group_auth.POWERUSER
        elif auth_capability == '#identified':
            level = group_auth.IDENTIFIED
        elif auth_capability == '#unrestricted':
            level = group_auth.UNRESTRICTED
        else:
            level = None
    return level
   
def command_extra():
    args = []
    for i in range(1,es.getargc()):
        args.append(es.getargv(i))
    func = '%s_%s' %(args[0],args[1])
    if func in gCommands:
        gCommands[func](args)
    else:
        es.dbgmsg(0,'[group_auth] Unknown command: '+args[0]+' '+args[1])

def group_create(args):
    if isinstance(args[3], str):
        level = cap_level(args[3])
    else:
        level = int(args[3])
    sql = "INSERT OR IGNORE INTO Groups ('GroupName', 'GDefaultLevel') VALUES ('%s', %d);" %(args[2],level)
    es.sql('query', 'group_auth', sql)

def group_delete(args):
    sql = "DELETE FROM GroupCaps WHERE GId in (SELECT GId FROM Groups WHERE Groups.GroupName='%s');DELETE FROM PlayersGroups WHERE GId in (SELECT GId FROM Groups WHERE Groups.GroupName='%s');DELETE FROM Groups WHERE GroupName='%s';" %(args[2],args[2],args[2])
    es.sql('query', 'group_auth', sql)

def power_create(args):
    if isinstance(args[3], str):
        level = cap_level(args[3])
    else:
        level = int(args[3])
    group_auth.registerCapability(args[2],level)

def power_give(args):
    sql = "INSERT OR IGNORE INTO GroupCaps (GId, CId) VALUES ((Select GId FROM Groups WHERE GroupName='%s'), (Select CId FROM Caps WHERE CName='%s'));" %(args[3],args[2])
    es.sql('query', 'group_auth', sql)
    sql = "UPDATE Caps SET Reviewed=1 WHERE Cid =(Select CId FROM Caps WHERE CName='%s');" % args[2]
    es.sql('query', 'group_auth', sql)

def power_revoke(args):
    sql = "DELETE FROM GroupCaps WHERE GId=(Select GId FROM Groups WHERE GroupName='%s') AND CId=(Select CId FROM Caps WHERE CName='%s');" %(args[3],args[2])
    es.sql('query', 'group_auth', sql)

def power_delete(args):
    sql = "DELETE FROM GroupCaps WHERE CId in (SELECT CId FROM Caps WHERE CName='%s');DELETE FROM Caps WHERE CName='%s';" %(args[2],args[2])
    es.sql('query', 'group_auth', sql)

def user_create(args):
    sql = "INSERT OR IGNORE INTO Players (Name, SteamId) VALUES ('%s', '%s');" %(args[2],args[3])
    es.sql('query', 'group_auth', sql)

def user_join(args):
    sql = "INSERT OR IGNORE INTO PlayersGroups (UId, GId) VALUES ((Select Uid FROM Players WHERE Name='%s'), (Select GId FROM Groups WHERE GroupName='%s'));" %(args[2],args[3])
    es.sql('query', 'group_auth', sql)

def user_leave(args):
    sql = "DELETE FROM PlayersGroups WHERE GId=(Select GId FROM Groups WHERE GroupName='%s') AND UId=(Select Uid FROM Players WHERE Name='%s');" %(args[3],args[2])
    es.sql('query', 'group_auth', sql)

def user_delete(args):
    sql = "DELETE FROM PlayersGroups WHERE UId in (SELECT Uid FROM Players WHERE Name='%s');DELETE FROM Players WHERE Name='%s';" %(args[2],args[2])
    es.sql('query', 'group_auth', sql)