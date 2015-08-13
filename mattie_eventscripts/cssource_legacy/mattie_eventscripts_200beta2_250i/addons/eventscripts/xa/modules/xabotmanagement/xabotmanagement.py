import es
import popuplib
import playerlib
from xa import xa

#plugin information
info = es.AddonInfo()
info.name           = "Bot Management"
info.version        = "0.1.1"
info.author         = "GODJonez"
info.basename       = "xabotmanagement"

xabotmanagement     = xa.register(info.basename)
xalanguage          = xabotmanagement.language.getLanguage()

xabmmenu = None
menu_display = {
    'state': False,
    'displays': {},
    }
menu_actions = {}

def load():
    '''
Load Function for Bot Management in XA
Called automatically when loading this script
    '''
    global xabmmenu
    xabmmenu = popuplib.easymenu("xabotmanagementmenu", None, _select_action)
    xabmmenu.settitle(xalanguage["bot management"])
    xabotmanagement.addMenu("xabotmanagementmenu", xalanguage["manage bots"], "xabotmanagementmenu", "manage_bots", "ADMIN")
    
    xabmmenu.prepuser = _menu_update_display
    
    registerDisplay('quota', _display_quota)
    registerDisplay('difficulty', _display_difficulty)
    
    registerAction("add_auto", xalanguage["add bot"], _action_add_auto)
    registerAction("add_2", xalanguage["add 2"], _action_add_2)
    registerAction("add_3", xalanguage["add 3"], _action_add_3)
    registerAction("remove", xalanguage["remove bot"], _action_remove)
    registerAction("kick_all", xalanguage["kick all"], _action_kick_all)
    registerAction("kill_all", xalanguage["kill all"], _action_kill_all)
    registerAction("difficulty-", xalanguage["easier bots"], _action_difficulty_down)
    registerAction("difficulty+", xalanguage["harder bots"], _action_difficulty_up)


def unload():
    '''
Unload Function for Bot Management in XA
Called automatically when unloading this script
    '''
    global xabmmenu
    for d in menu_display['displays'].keys():
        unRegisterDisplay(d)
    for a in menu_actions.keys():
        unRegisterAction(a)
    xabmmenu.delete()
    xabmmenu = None
    
    xabotmanagement.unregister()
    

def registerDisplay(identifier, updater):
    '''
Registers a new function to update status in bot menu

    identifier = unique name to identify this object
    updater    = a method that returns a dict-like object with strings
                 to include in display, it is called as updater()
    '''
    if not identifier in menu_display:
        menu_display['displays'][identifier] = {
            'updater': updater,
            'laststate': None,
            }
        menu_display['state'] = True
        return True
    else:
        return False

def unRegisterDisplay(identifier):
    '''
Unregisters previously registered display object by identifier
    '''
    if identifier in menu_display:
        del menu_display['displays'][identifier]
        menu_display['state'] = True
        return True
    else:
        return False

def registerAction(identifier, text, method):
    '''
Registers a new bot management action to be included in the menu

    identifier = unique name to identify this action
    text       = preferably multi-language dict-like object holding the
                 text to be shown in the menu
    method     = method to be called when this action is selected
                 it is called with method(userid, popupid)
                 return True if the menu is to stay up
    '''
    if not identifier in menu_actions:
        if callable(method):
            menu_actions[identifier] = method
            try:
                xabmmenu.setoption(identifier, text, 1)
            except IndexError:
                xabmmenu.addoption(identifier, text)
            return True
    return False

def unRegisterAction(identifier):
    '''
Unregisters a bot management action based on the identifier
    '''
    if identifier in menu_actions:
        del menu_actions[identifier]
        xabmmenu.setoption(identifier, state=0)
        return True
    else:
        return False

def _select_action(userid, choice, popupid):
    '''
Private method that is executed when the admin chooses an action from the menu
    '''
    if choice in menu_actions:
        resend = menu_actions[choice](userid, popupid)
        if resend:
            xabmmenu.send(userid)

def _menu_update_display(userid, popupid):
    '''
Private method that is called by popuplib to update the display line
    '''
    newdesc = {}
    dostate = menu_display['state']
    for d in menu_display['displays']:
        newstuff = menu_display['displays'][d]['updater']()
        if newstuff != menu_display['displays'][d]['laststate']:
            dostate = True
        menu_display['displays'][d]['laststate'] = newstuff
        newdesc = _superconcat(newdesc, newstuff, " | ")
    if dostate:
        xabmmenu.setdescription(newdesc)
        xabmmenu.recache(userid)


def _superconcat(older, newer, sep, override=True):
    '''
Concates older and newer dict type objects using separator sep
    '''
    tbr = {}
    for key in newer:
        if key in older:
            tbr[key] = older[key] + sep + newer[key]
        elif override:
            tbr[key] = newer[key]
    return tbr


# FROM HERE ON ARE THE BUILT-IN PROVIDED DISPLAYS AND ACTIONS

def _display_quota():
    '''
Returns current bot quota for display
    '''
    bq = str(es.ServerVar('bot_quota'))
    return popuplib.langstring('', xalanguage['display_quota'], ': '+bq)

def _display_difficulty():
    '''
Returns current bot difficulty
    '''
    dif = int(es.ServerVar('bot_difficulty'))
    ls = xalanguage["difficulty %d"%dif]
    return _superconcat(xalanguage["display_difficulty"], ls, ": ", False)


def _action_add_auto(userid, popupid):
    '''
Adds a bot with team auto-assign
    '''
    cvar = es.ServerVar('bot_join_team')
    old = str(cvar).upper()
    cvar.set('ANY')
    es.server.queuecmd('bot_add')
    if old != 'ANY':
        cvar.set(old)
    return True

def _action_add_2(userid, popupid):
    '''
Adds a bot to team 2
    '''
    es.server.queuecmd('bot_add_t')
    return True

def _action_add_3(userid, popupid):
    '''
Adds a bot to team 3
    '''
    es.server.queuecmd('bot_add_ct')
    return True

def _action_kick_all(userid, popupid):
    '''
Kicks all bots
    '''
    es.server.queuecmd('bot_kick')
    return True

def _action_remove(userid, popupid):
    '''
Removes one bot, trying to conserve team balance
    '''
    if int(es.ServerVar('bot_quota')):
        if int(es.getplayercount(2)) > int(es.getplayercount(3)):
            prefteam = 2
        else:
            prefteam = 3
        
        botlist = playerlib.getPlayerList('#bot')
        currentbot = None
        currentlevel = 0
        for botid in botlist:
            level = 1
            if int(botid.get('teamid')) == prefteam:
                level += 4
            if int(botid.get('isdead')) == 1:
                level += 2
            if level == 7:
                # max level, we found our bot >:)
                es.server.queuecmd('bot_kick '+botid.get('name'))
                return True
            if level > currentlevel:
                currentbot = botid
                currentlevel = level
        if currentbot:
            # we found at least one bot...
            es.server.queuecmd('bot_kick '+currentbot.get('name'))
            return True
    # TODO: Insert a message here telling that no bots on server
    # message string: remove_no_bots
    return True


def _action_kill_all(userid, popupid):
    '''
Kills all bots
    '''
    es.server.queuecmd('bot_kill')
    return False

def _action_difficulty_down(userid, popupid):
    '''
Makes bots easier
    '''
    cvar = es.ServerVar('bot_difficulty')
    if int(cvar) > 0:
        cvar.set(int(cvar)-1)
    return True

def _action_difficulty_up(userid, popupid):
    '''
Makes bots harder
    '''
    cvar = es.ServerVar('bot_difficulty')
    if int(cvar) < 3:
        cvar.set(int(cvar)+1)
    return True
