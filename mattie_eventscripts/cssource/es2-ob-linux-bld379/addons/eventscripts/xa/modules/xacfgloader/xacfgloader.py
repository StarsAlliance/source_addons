import es
import popuplib
import playerlib
import cfglib
from xa import xa

import os

#plugin information
info = es.AddonInfo()
info.name           = "XA CFG Loader"
info.version        = "1"
info.author         = "Errant"
info.basename       = "xacfgloader"



xacfgl               = xa.register(info.basename)
xalanguage           = xacfgl.language.getLanguage()


cfg_dir = "%s/cfg" % es.ServerVar("eventscripts_gamedir")

def load():
    menu = _create_menu()
    xacfgl.addMenu('xacfgloader_menu', xalanguage['cfgloader_title'], 'xacfgloader_menu', 'xa_cfgloader', 'ADMIN')
    
def _create_menu():
    if popuplib.exists('xacfgloader_menu'):
        popuplib.delete('xacfgloader_menu')
    menu = popuplib.easymenu("xacfgloader_menu", "_unused", _select_cfg)
    menu.addoption('reload','Reload CFG Files',lang="en")
    for file in [f for f in os.listdir(cfg_dir) if os.path.isfile(os.path.join(cfg_dir, f)) and f.endswith('.cfg')]:
        menu.addoption(file,file,lang="en")
    menu.settitle(xalanguage['menu_title'])
    menu.setdescription(xalanguage['menu_description'])
    return menu
    
def _select_cfg(userid, choice, name):
    if choice == "reload": 
        es.tell(userid,xalanguage("cfgs reloaded", {}, playerlib.Player(userid).get("lang")))
    elif os.path.isfile(os.path.join(cfg_dir, choice)):
        cfglib.AddonCFG(os.path.join(cfg_dir, choice)).execute()
        es.tell(userid,xalanguage("cfg executed", {'file':choice}, playerlib.Player(userid).get("lang")))
        xacfgl.logging.log("Loaded config %s" % choice, userid, True)
    else:
        es.tell(userid,xalanguage("unrecognised", {'file':choice}, playerlib.Player(userid).get("lang")))
    menu = _create_menu()
    menu.send(userid)
        