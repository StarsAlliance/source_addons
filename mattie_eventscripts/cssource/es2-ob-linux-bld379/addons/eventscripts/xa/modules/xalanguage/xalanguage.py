import es
import os
import cfglib
import popuplib
import playerlib
import langlib
import random
from xa import xa

info = es.AddonInfo()
info.name        = "Language Management"
info.version     = "0.1"
info.author      = "Hunter"
info.basename    = "xalanguage"

xalanguage = xa.register(info.basename)
xalang = xalanguage.language.getLanguage()
langlist = {}
menulist = []

def load():
    global menulist,mainmenu
    xaclientcmd = xalanguage.addCommand('setlanguage', _inputbox_handle, 'change_language', 'ROOT', 'Set language')
    xaclientcmd.register('console')

    mainmenu = popuplib.easymenu('xamainlanguagemenu',None,_mainmenu_select)
    mainmenu.settitle(xalang['main language'])
    mainmenu.addoption('module', xalang['module language'])
    menulist.append(mainmenu)
    xalanguage.addMenu('xamainlanguagemenu',xalang['xa menu choice'],'xamainlanguagemenu','change_language','ROOT')

def unload():
    global menulist
    for menu in menulist:
        if popuplib.exists(str(menu)): 
            popuplib.delete(str(menu))
    xalanguage.unregister()
    
def _moduleListMenu(userid):
    modulemenu = popuplib.easymenu('xalistmodulemenu_'+str(userid),None,_modulemenu_select)
    modulemenu.settitle(xalang['module overview'])
    modulemenu.submenu(mainmenu)
    menulist.append(modulemenu)
    for module in sorted(xa.modules()):
        module = xa.find(module)
        if os.path.exists("%s/modules/%s/strings.ini" % (xa.coredir(), module)):
            modulemenu.addoption(str(module), xalanguage.language.createLanguageString(module.getAddonInfo().name))
    return modulemenu

def _stringListMenu(userid, module, parent):
    keylist = langlist[str(module)]
    keymenu = popuplib.easymenu('xaliststringmenu_'+str(userid)+'_'+str(module),None,_keymenu_select)
    keymenu.settitle(xalang['module strings'])
    keymenu.submenu(parent)
    keymenu._xa = [module, parent]
    menulist.append(keymenu)
    for key in keylist:
        keymenu.addoption(str(key), keylist[key])
    return keymenu

def _stringEditMenu(userid, module, key, parent):
    keylist = langlist[str(module)]
    changestring = popuplib.easymenu('xachangestringmenu_'+str(random.randint(1, 10))+'_'+str(userid)+'_'+str(key).lower(),None,_changestring_select)
    changestring.settitle(xalang['change language'])
    changestring.submenu(parent)
    changestring.c_exitformat = '0. '+xalang('just back', playerlib.getPlayer(userid).get('lang'))
    changestring._xa = [module, key, parent]
    menulist.append(changestring)
    for ll in langlib.getLanguages():
        lang = langlib.getLangAbbreviation(ll)
        changestring.addoption(str(lang), xalanguage.language.createLanguageString('%s = %s' % (lang, keylist(key, {}, lang))))
    return changestring

def _sendmain():
    userid = es.getcmduserid()
    if xalanguage.isUseridAuthorized(userid, 'change_config'):
        mainmenu.send(userid)

def _mainmenu_select(userid,choice,popupid):
    if choice == 'module':
        menu = _moduleListMenu(userid)
        menu.send(userid)

def _modulemenu_select(userid,choice,popupid):
    if xa.exists(choice):
        module = xa.find(choice)
        try:
            langlist[str(module)] = module.language.getLanguage()
            menu = _stringListMenu(userid, module, popupid)
            menu.send(userid)
        except IOError:
            popuplib.send(popupid)

def _keymenu_select(userid,choice,popupid):
    parentmenu = popuplib.find(popupid)
    parent = parentmenu._xa[0]
    if xa.exists(parent) and choice in xa.language.getLanguage(parent):
        menu = _stringEditMenu(userid, parent, choice, popupid)
        menu.send(userid)

def _changestring_select(userid,choice,popupid):
    menu = popuplib.find(popupid)
    if menu:
        _setconfig_handle(userid, menu._xa[0], menu._xa[1], str(choice), menu._xa[2])
    
def _setconfig_handle(userid, module, key, lang, parent):
    if xalanguage.isUseridAuthorized(userid, 'change_language'):
        keylist = langlist[str(module)]
        es.escinputbox(30,userid,"Change '"+str(keylist(key, lang))+"' string",'Type in the new string:','setlanguage '+str(parent)+' '+str(module)+' '+str(lang)+' '+str(key).replace(' ', '+'))
        es.tell(userid, '#green', xalang('press esc', playerlib.getPlayer(userid).get('lang')))

def _inputbox_handle():
    userid = es.getcmduserid()
    count = int(es.getargc())
    if count > 5:
        parent = es.getargv(1)
        if popuplib.exists(parent):
            module = es.getargv(2)
            if xa.exists(module):
                module = xa.find(module)
                keylist = langlist[str(module)]
                lang = es.getargv(3)
                key = es.getargv(4)
                if not key in keylist:
                    key = es.getargv(4).replace('+', ' ')
                if module and lang and key in keylist:
                    i = 5
                    newvalue = ''
                    while i < count:
                        newvalue = newvalue+' '+es.getargv(i)
                        i = i + 1
                    newvalue = newvalue.strip()
                    if newvalue:
                        language = cfglib.AddonINI("%s/modules/%s/strings.custom.ini" % (xa.coredir(), module))
                        language.addValueToGroup(key, lang, newvalue, True)
                        language.write()
                        es.tell(userid, '#green', xalang('string warning', playerlib.getPlayer(userid).get('lang')))
                    else:
                        newvalue = langlist[str(module)](key, lang)
                    try:
                        langlist[str(module)] = module.language.getLanguage()
                    except IOError:
                        pass
                    es.esctextbox(10, userid, "Changed '"+str(keylist(key, lang))+"' string", "Changed '%s' to '%s'\nThe language menu is open again.\nPress [ESC] a second time." %(keylist(key, lang),newvalue))
                    menu = _stringEditMenu(userid, module, key, parent)
                    menu.send(userid)
    else:
        es.esctextbox(10, userid, "Invalid Entry", "<string>")
