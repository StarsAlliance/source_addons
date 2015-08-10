# ==============================================================================
#   IMPORTS
# ==============================================================================
# EventScripts Imports
import es
import playerlib
import xa

# Python imports
import os
import cPickle

# ==============================================================================
#   LOAD PLAYERDATA DICTIONARY OBJECT
# ==============================================================================

gPlayerData = {}
gPathDir    = os.path.join(str(es.getAddonPath('xa')).replace("\\", "/"), "data", "playerdata.db")
gOldPathDir = os.path.join(str(es.getAddonPath('xa')).replace("\\", "/"), "data", "playerdata.txt")
if os.path.exists(gPathDir):
    pathStream  = open(gPathDir, 'r')
    gPlayerData = cPickle.load(pathStream)
    pathStream.close()

# ==============================================================================
#   HELPER CLASSES
# ==============================================================================
class UserSetting(object):
    """
        UserSetting
        
        Module is stores per-steamid values for a particular module->setting.
    """
    def __init__(self, module, pref):
        # Create our setting object
        self.module  = str(module)
        self.name    = str(pref)
        
        # Does our module exist?
        if self.module in xa.gModules:
            # Add our module tree to the KeyValues tree
            if not self.module in gPlayerData:
                gPlayerData[self.module] = {}

            # Add our setting tree to the KeyValues tree
            if not self.name in gPlayerData[self.module]:
                gPlayerData[self.module][self.name] = {}

    def __str__(self):
        # Return a printable string
        return self.name

    def __repr__(self):
        # Return something that represents our object
        return 'UserSetting(%s)' % self.name

    def exists(self, userid):
        # Get the userid's uniqueid
        steamid = playerlib.uniqueid(userid, True)
        
        # Return if our user's setting has a value
        return steamid in gPlayerData[self.module][self.name]

    def set(self, userid, value):
        """
            Set the setting value for an individual player
        """
        # Get the userid's uniqueid
        steamid = playerlib.uniqueid(userid, True)
        
        # Set the user's setting to the new value
        gPlayerData[self.module][self.name][steamid] = value
        
        # Return if our user's setting has the new value
        return gPlayerData[self.module][self.name][steamid] == value
        
    def get(self, userid):
        """
            Get the set value for an individual player
        """
        # Check if our user's setting has a value
        if self.exists(userid):
            # Get the userid's uniqueid
            steamid = playerlib.uniqueid(userid, True)

            # Return the user's setting value
            return gPlayerData[self.module][self.name][steamid]
        return None

# ==============================================================================
#   MODULE API FUNCTIONS
# ==============================================================================
def createUserSetting(module, pref):
    """
        Create and return a new setting object for module/setting
        
        module: the name of the relevant module
        pref:   the name of your preference
    """
    return UserSetting(module, pref)

def saveUserSetting(module=None):
    """
        Save all user settings to disk
        
        module: (optional) specific module settings to save (currently unused!)
    """
    fileStream = open(gPathDir, 'w')
    cPickle.dump(gPlayerData, fileStream)
    fileStream.close()
    
def clearUsersSettings(module, value = None):
    """ 
        Clear all user settings for a specific player
    """
    if value == None:
        value = module
    if es.exists('userid', value):
        steamid = playerlib.uniqueid(value, True)
    else:
        steamid = value
    modulesToRemove = {}
    for module in gPlayerData:
        for name in gPlayerData[module]:
            if steamid in gPlayerData[module][name]:
                modulesToRemove[module] = name
    for module, name in modulesToRemove.iteritems():
        del gPlayerData[module][name][steamid]
    saveUserSetting()
    
def convertOldDatabase():
    """
        Converts old style keyvalue based databases (pre 1.1) to 1.1 style dict based database
    """
    import keyvalues
    oldPlayerSettings = keyvalues.KeyValues(name='playerdata.txt')
    oldPlayerSettings.load('%s/data/playerdata.txt' % es.getAddonPath('xa'))
    for moduleKeyValue in oldPlayerSettings:
        module = str(moduleKeyValue)
        gPlayerData[module] = {}
        for settingKeyValue in moduleKeyValue:
            setting = str(settingKeyValue)
            gPlayerData[module][setting] = {}
            for steamidKeyValue in settingKeyValue:
                steamid = str(steamidKeyValue)
                try:
                    gPlayerData[module][setting][steamid] = oldPlayerSettings[module][setting][steamid]
                except:
                    es.dbgmsg(0, "xa: playerdata - Error converting module %s, setting %s and steamid %s" % (module, setting, steamid) )
    saveUserSetting()
    
if os.path.exists(gOldPathDir):
    convertOldDatabase()
    os.remove(gOldPathDir)