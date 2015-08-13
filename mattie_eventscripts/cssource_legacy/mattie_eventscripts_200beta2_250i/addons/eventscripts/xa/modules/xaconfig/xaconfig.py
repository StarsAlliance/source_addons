import es
import popuplib
import random
from xa import xa

info = es.AddonInfo()
info.name        = "Config"
info.version     = "0.1"
info.author      = "Hunter"
info.basename    = "xaconfig"

xaconfig = xa.register(info.basename)
lang = xaconfig.language.getLanguage()
menulist = []

def load():
    global menulist,mainmenu
    xacmd = xaconfig.addCommand('xa_config', _sendmain, 'change_config', 'ROOT')
    xacmd.register('say')  

    xaclientcmd = xaconfig.addCommand('setconfig', _inputbox_handle, 'change_config', 'ROOT', 'Set config')
    xaclientcmd.register('console')

    mainmenu = popuplib.easymenu('xamainconfigmenu',None,_mainmenu_select)
    mainmenu.settitle(lang['main config'])
    mainmenu.addoption('core', lang['core config'])
    mainmenu.addoption('module', lang['module config'])
    menulist.append(mainmenu)
    xaconfig.addMenu('xamainconfigmenu',lang['xa menu choice'],'xamainconfigmenu','change_config','ROOT')
	
def unload():
    global menulist
    for menu in menulist:
        if popuplib.exists(str(menu)): 
            popuplib.delete(str(menu))
    xaconfig.unregister()
    
def _moduleListMenu(userid):
    modulemenu = popuplib.easymenu('xalistmodulemenu_'+str(userid),None,_modulemenu_select)
    modulemenu.settitle(lang['module overview'])
    modulemenu.submenu(mainmenu)
    menulist.append(modulemenu)
    for module in sorted(xa.modules()):
        module = xa.find(module)
        if len(module.variables) > 0:
            modulemenu.addoption(str(module), xaconfig.language.createLanguageString(module.getAddonInfo().name))
    return modulemenu

def _variableListMenu(userid, module, parent):
    varlist = xaconfig.setting.getVariables(module)
    varmenu = popuplib.easymenu('xalistsettingmenu_'+str(userid)+'_'+str(module),None,_varmenu_select)
    varmenu.settitle(lang['module variables'])
    varmenu.submenu(parent)
    varmenu._xa = [module, parent]
    menulist.append(varmenu)
    for var in sorted(varlist):
        value = str(var)
        if len(value) > 10:
            value = value[0:10]
        varmenu.addoption(str(var.getName()), xaconfig.language.createLanguageString(str(var.getName())+' = '+str(value)))
    return varmenu

def _variableCoreListMenu(userid, parent):
    varlist = xa.corevars()
    varmenu = popuplib.easymenu('xalistsettingmenu_'+str(userid)+'_core',None,_varmenu_select)
    varmenu.settitle(lang['core variables'])
    varmenu.submenu(parent)
    varmenu._xa = ['core', parent]
    menulist.append(varmenu)
    for var in sorted(varlist):
        var._def = str(var)
        var._descr = 'Core variable'
        value = str(var)
        if len(value) > 10:
            value = value[0:10]
        varmenu.addoption(str(var.getName()), xaconfig.language.createLanguageString(str(var.getName())+' = '+str(value)))
    return varmenu

def _variableEditMenu(userid, module, variable, parent):
    if str(module) != 'core':
        descr = str(variable._descr)
        if len(descr) > 100:
            descr = descr[0:50] + '\n' + descr[50:50] + '\n' + descr[100:50]
        elif len(descr) > 50:
            descr = descr[0:50] + '\n' + descr[50:50]
    changesetting = popuplib.create('xachangesettingmenu_'+str(random.randint(1, 10))+'_'+str(userid)+'_'+variable.getName())
    changesetting.addline(lang('change setting'))
    changesetting.addlineAll('Name: '+variable.getName())
    changesetting.addlineAll('Value: '+str(variable))
    if str(module) != 'core':
        changesetting.addlineAll(descr)
        changesetting.addlineAll(' ')
        changesetting.addline(lang('variable warning'))
    changesetting.addlineAll('------------------------------------')
    changesetting.addline(popuplib.langstring('->1. ',lang['type value']))
    changesetting.addline(popuplib.langstring('->2. ',lang['default value']))
    changesetting.addlineAll('------------------------------------')
    if str(variable).isdigit():
        changesetting.addlineAll('->3. +1')
        changesetting.addlineAll('->4. -1')
        changesetting.addlineAll('->5. +10')
        changesetting.addlineAll('->6. -10')
        changesetting.addlineAll('->7. +100')
        changesetting.addlineAll('->8. -100')
        changesetting.addlineAll('------------------------------------')
        changesetting._xatype = 'int'
    elif str(variable).replace('.', '').isdigit():
        changesetting.addlineAll('->3. +0.1')
        changesetting.addlineAll('->4. -0.1')
        changesetting.addlineAll('->5. +1.0')
        changesetting.addlineAll('->6. -1.0')
        changesetting.addlineAll('->7. +10.0')
        changesetting.addlineAll('->8. -10.0')
        changesetting.addlineAll('------------------------------------')
        changesetting._xatype = 'float'
    else:
        changesetting._xatype = 'str'
    if str(module) != 'core':
        changesetting.addline(popuplib.langstring('->9. ',lang['save back']))
    changesetting.addline(popuplib.langstring('0. ',lang['just back']))
    changesetting.menuselect = _changesetting_select
    changesetting._xa = [module, variable, parent]
    menulist.append(changesetting)
    return changesetting

def _sendmain():
    userid = es.getcmduserid()
    if xaconfig.isUseridAuthorized(userid, 'change_config'):
        mainmenu.send(userid)
        
def _mainmenu_select(userid,choice,popupid):
    if choice == 'core':
        menu = _variableCoreListMenu(userid, popupid)
        menu.send(userid)
    elif choice == 'module':
        menu = _moduleListMenu(userid)
        menu.send(userid)

def _modulemenu_select(userid,choice,popupid):
    if xa.exists(choice):
        module = xa.find(choice)
        menu = _variableListMenu(userid, module, popupid)
        menu.send(userid)

def _varmenu_select(userid,choice,popupid):
    if es.exists('variable', choice):
        parentmenu = popuplib.find(popupid)
        parent = parentmenu._xa[0]
        if str(parent) != 'core':
            if xa.exists(parent) and choice in xa.find(parent).variables:
                var = xa.find(parent).variables[choice]
                menu = _variableEditMenu(userid, parent, var, popupid)
                menu.send(userid)
        else:
            for var in xa.corevars():
                if var.getName() == choice:
                    menu = _variableEditMenu(userid, parent, var, popupid)
                    menu.send(userid)

def _changesetting_select(userid,choice,popupid):
    menu = popuplib.find(popupid)
    module = menu._xa[0]
    variable = menu._xa[1]
    parent = menu._xa[2]
    if int(choice) == 1:
        _setconfig_handle(userid, module, variable, parent)
    elif int(choice) == 2:
        variable.set(variable._def)
        menu = _variableEditMenu(userid, module, variable, parent)
        menu.send(userid)
    elif (int(choice) > 2) and (int(choice) < 9):
        if menu._xatype == 'int':
            value = int(variable)
            if int(choice) == 3:
                variable.set(value+1)
            elif int(choice) == 4:
                variable.set(value-1)
            elif int(choice) == 5:
                variable.set(value+10)
            elif int(choice) == 6:
                variable.set(value-10)
            elif int(choice) == 7:
                variable.set(value+100)
            elif int(choice) == 8:
                variable.set(value-100)
            menu = _variableEditMenu(userid, module, variable, parent)
            menu.send(userid)
        elif menu._xatype == 'float':
            value = float(variable)
            if int(choice) == 3:
                variable.set(value+0.1)
            elif int(choice) == 4:
                variable.set(value-0.1)
            elif int(choice) == 5:
                variable.set(value+1.0)
            elif int(choice) == 6:
                variable.set(value-1.0)
            elif int(choice) == 7:
                variable.set(value+10.0)
            elif int(choice) == 8:
                variable.set(value-10.0)
            menu = _variableEditMenu(userid, module, variable, parent)
            menu.send(userid)
        else:
            popuplib.send(popupid, userid)
    elif int(choice) == 9:
        xaconfig.setting.writeConfiguration()
        parent = popuplib.find(parent)
        if str(module) != 'core':
            newparent = _variableListMenu(userid, module, str(parent._xa[1]))
        else:
            newparent = _variableCoreListMenu(userid, str(parent._xa[1]))
        newparent.send(userid)
    else:
        parent = popuplib.find(parent)
        if str(module) != 'core':
            newparent = _variableListMenu(userid, module, str(parent._xa[1]))
        else:
            newparent = _variableCoreListMenu(userid, str(parent._xa[1]))
        newparent.send(userid)
    
def _setconfig_handle(userid, module, var, parent):
    if xaconfig.isUseridAuthorized(userid, 'change_config'):
        es.escinputbox(30,userid,"Change '"+str(var.getName())+"' setting"+'\n \nCurrent value: '+str(var)+'\nDefault value: '+str(var._def)+'\n \n'+str(var._descr),'Type in the new value:','setconfig '+str(parent)+' '+str(module)+' '+str(var.getName()))

def _inputbox_handle():
    userid = es.getcmduserid()
    count = int(es.getargc())
    if count > 4:
        parent = es.getargv(1)
        if popuplib.exists(parent):
            module = es.getargv(2)
            if xa.exists(module):
                module = xa.find(module)
                varname = es.getargv(3)
                if module and varname in module.variables:
                    var = module.variables[varname]
                    i = 4
                    newvalue = ''
                    while i < count:
                        newvalue = newvalue+' '+es.getargv(i)
                        i = i + 1
                    newvalue = newvalue.strip()
                    var.set(newvalue)
                    es.esctextbox(10, userid, "Changed '"+str(varname)+"' setting", "Changed '%s' to '%s'\nThe variable menu is open again.\nPress [ESC] a second time." %(varname,newvalue))
                    menu = _variableEditMenu(userid, module, var, parent)
                    menu.send(userid)
    else:
        es.esctextbox(10, userid, "Invalid Entry", "<value>")
