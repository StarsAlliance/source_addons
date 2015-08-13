import es
import playerlib
import keyvalues
import xa

import psyco
psyco.full()

gSettingFile = "%s/data/playerdata.txt" % es.getAddonPath('xa')
gKeyValues = keyvalues.KeyValues(name="playerdata.txt")
gKeyValues.load(gSettingFile)

###########################
#Module methods start here#
########################################################
# All methods that should be able to be called through #
# the API need to have "module" as first parameter     #
########################################################
class UserSetting(object):
    def __init__(self, module, pref):
        self.module = str(module)
        self.name = str(pref)
        if self.module in xa.gModules:
            if not self.module in gKeyValues:
                gKeyValues[self.module] = keyvalues.KeyValues(name=self.module)
            if not self.name in gKeyValues[self.module]:
                gKeyValues[self.module][self.name] = keyvalues.KeyValues(name=self.name)
    def __str__(self):
        return self.name        
    def exists(self, userid):
        if es.exists("userid", userid):
            steamid = playerlib.uniqueid(userid, True)
            if steamid in gKeyValues[self.module][self.name]:
                return True
            else:
                return False
        else:
            return False
    def set(self, userid, value):
        if es.exists("userid", userid):
            steamid = playerlib.uniqueid(userid, True)
            gKeyValues[self.module][self.name][steamid] = value
            if gKeyValues[self.module][self.name][steamid] == value:
                return True
            else:
                return False
        else:
            return False
    def get(self, userid):
        if es.exists("userid", userid):
            steamid = playerlib.uniqueid(userid, True)
            if steamid in gKeyValues[self.module][self.name]:
                return gKeyValues[self.module][self.name][steamid]
            else:
                return False
        else:
            return False

def createUserSetting(module, pref):
    return UserSetting(module, pref)

def saveUserSetting(module = None):
    gKeyValues.save(gSettingFile)
