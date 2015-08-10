import es
import playerlib
import popuplib
from xa import xa

#plugin information
info = es.AddonInfo()
info.name           = "Settings"
info.version        = "0.1"
info.author         = "Hunter"
info.basename       = "xasettings"

setting_object = {}

xasettings                  = xa.register(info.basename)
xalanguage                  = xasettings.language.getLanguage()

def load():
    #Load Function for Player Settings for XA.    
    xasettingmenu = popuplib.easymenu("xasettingmenu", "_tempcore", _select_setting)
    xasettingmenu.settitle(xalanguage["player settings"])
    xasettings.addMenu("xasettingmenu", xalanguage["player settings"], "xasettingmenu", "change_playersetting", "UNRESTRICTED")
    xacommand = xasettings.addCommand("settings", _send_menu, "change_playersetting", "UNRESTRICTED")
    xacommand.register(["console","say"])

def unload():
    popuplib.delete("xasettingmenu")
    xasettings.unregister()
    
def _send_menu():
    userid = es.getcmduserid()
    for setting in setting_object:
        setting_object[setting].rebuild(userid) # TODO: finish rebuild methods later
    xasettingmenu = popuplib.find("xasettingmenu")
    xasettingmenu.recache(userid)
    xasettingmenu.send(userid)

def _select_setting(userid, choice, name):
    if choice in setting_object:
        setting_object[choice].use(userid, name)

class SettingMenu(object):
    def __init__(self, setting, menu, texts):
        self.name = str(setting)
        self.texts = dict(texts)
        if popuplib.exists(menu):
            self.menu = menu
            self.menutype = "popup"
            self.menuobj = popuplib.find(self.menu)
        elif keymenulib.exists(menu):
            self.menu = menu
            self.menutype = "keymenu"
            self.menuobj = keymenulib.find(self.menu)
        elif settinglib.exists(menu):
            self.menu = menu
            self.menutype = "setting"
            self.menuobj = settinglib.find(self.menu)
        xasettingmenu = popuplib.find("xasettingmenu")
        xasettingmenu.addoption(setting, self.texts)
    def use(self, userid, popup):
        self.menu.send(userid)
    def rebuild(self, userid):
        pass
        
class SettingMethod(object):
    def __init__(self, setting, method, texts):
        self.name = str(setting)
        self.texts = dict(texts)
        self.method = method
        xasettingmenu = popuplib.find("xasettingmenu")
        xasettingmenu.addoption(setting, self.texts)
    def use(self, userid, popup):
        if callable(self.method):
            self.method(userid)
        else:
            es.set("_xa_userid", str(userid))
            es.doblock(self.method)
    def rebuild(self, userid):
        pass
        
def registerSubmenu(module, setting, menu, texts):
    if not setting in setting_object:
        setting_object[setting] = SettingMenu(setting, menu, texts)

def registerMethod(module, setting, method, texts):
    if not setting in setting_object:
        setting_object[setting] = SettingMethod(setting, method, texts)

def unregister(module, setting):
    if setting in setting_object:
        del setting_object[setting]
