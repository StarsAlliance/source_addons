#import EventScripts
import es

#begin loading
es.dbgmsg(0, '[eXtensible Admin] Begin loading...')

#import custom stuff
import os
import shutil
import hotshot.stats
import services
import gamethread
import playerlib
import popuplib
import keymenulib
import settinglib
import keyvalues
import cmdlib

#import libraries
import configparser
reload(configparser)
import language
reload(language)
import logging
reload(logging)
import playerdata
reload(playerdata)
import setting
reload(setting)

#plugin information
info = es.AddonInfo()
info.name = 'eXtensible Admin EventScripts Python addon'
info.version = '1.0.0.399'
info.author = 'EventScripts Developers'
info.url = 'http://forums.mattie.info/cs/forums/viewforum.php?f=97'
info.description = 'eXtensible Admin EventScripts Python addon'
info.basename = 'xa'

##################### ######################################################
#Variables Section# # PLEASE KEEP IN MIND THAT THOSE VARIABLES ARE PRIVATE #
##################### ######################################################
##public server variable
es.ServerVar('eventscripts_xa', str(info.version), 'eXtensible Admin Version').makepublic()
##generate import dict
gImportLibraries = dir()
## list of core variables
gCoreVariables = {}
gCoreVariables['log']           = es.ServerVar('xa_log', 0, 'Activates the module logging')
gCoreVariables['debug']         = es.ServerVar('xa_debug', 0, 'Activates the module/library debugging')
gCoreVariables['debugprofile']  = es.ServerVar('xa_debugprofile', 0, 'Activates the module/library profiling')
gCoreVariables['manimode']      = es.ServerVar('xa_manimode', 0, 'Is Mani compatibility mode active?')
gCoreVariables['sayprefix']     = es.ServerVar('xa_sayprefix', '!', 'Say command prefix')
## gMainMenu/gMainCommand holds XAs main menu/main command
gMainMenu = {}
gMainCommand = None
## gModules holds all the modules
gModules = {}
gModulesLoading = False

#################### ######################################################
#Core Class Section# # PLEASE KEEP IN MIND THAT THOSE CLASSES ARE PRIVATE #
#################### ######################################################
## Library API
# Admin_libfunc is a 'fake' method class used for the lib API
class Admin_libfunc(object):
    def __init__(self, gLib, gFunc, gModule):
        self._xalib = gLib
        self._xalibfunc = gFunc
        self._xalibfunccalls = 0
        self._xalibfuncstats = {'calls':0, 'times':0}
        self._xamod = gModule
    def __call__(self, *args, **kw):
        self._xalibfunccalls += 1
        if int(gCoreVariables['debug']) >= 1 or int(gCoreVariables['debugprofile']) > 0: #check debug here to be faster
            fn = '%s/xa.prof' % coredir()
            pr = hotshot.Profile(fn)
            re = pr.runcall(self._xalibfunc, *(self._xamod,)+args, **kw)
            pr.close()
            st = hotshot.stats.load(fn)
            st.strip_dirs()
            st.sort_stats('time', 'calls')
            if int(gCoreVariables['debug']) >= 2:
                es.dbgmsg(0, '--------------------')
                es.dbgmsg(0, ('Admin_libfunc %d: __call__(%s.%s [%s], %s, %s)' % (self._xalibfunccalls, str(self._xalib.__name__), str(self._xalibfunc.__name__), str(self._xamod), args, kw)))
                es.dbgmsg(0, ('Admin_libfunc %d: Profile Statistics' % (self._xalibfunccalls)))
                st.print_stats(20)
                es.dbgmsg(0, '--------------------')
            elif int(gCoreVariables['debug']) == 1:
                es.dbgmsg(0, ('Admin_libfunc %d: __call__(%s.%s [%s], %s, %s)' % (self._xalibfunccalls, str(self._xalib.__name__), str(self._xalibfunc.__name__), str(self._xamod), args, kw)))
                es.dbgmsg(0, ('Admin_libfunc %d: %d calls in %f CPU seconds' % (self._xalibfunccalls, st.total_calls, st.total_tt)))
            if int(gCoreVariables['debugprofile']) > 0:
                self._xalibfuncstats['calls'] += st.total_calls
                self._xalibfuncstats['times'] += st.total_tt
            if os.path.exists(fn):
                os.unlink(fn)
            return re
        else:
            return self._xalibfunc(self._xamod, *args, **kw)

# Admin_lib is a 'fake' library class used for the lib API
class Admin_lib(object):
    def __init__(self, gLib, gModule):
        self._xalib = gLib
        self._xalibcalls = 0
        self._xalibfuncs = {}
        self._xamod = gModule
    def __getattr__(self, name):
        self._xalibcalls += 1
        if int(gCoreVariables['debug']) >= 2: #check debug here to be faster
            es.dbgmsg(0, ('Admin_lib %d: __getattr__(%s [%s], %s)' % (self._xalibcalls, str(self._xalib.__name__), str(self._xamod), name)))
        if self._xalib.__dict__.has_key(name) and not name.startswith('_'):
            if not name in self._xalibfuncs:
                self._xalibfuncs[name] = Admin_libfunc(self._xalib, self._xalib.__dict__[name], self._xamod)
            return self._xalibfuncs[name]
        else:
            raise AttributeError, name

## Core
# Admin_module is the module class
class Admin_module(object):
    def __init__(self, gModule):
        #initialization of the module
        self._xa = None
        self._xamod = None
        self._xalibs = {}
        self.name = gModule
        self.allowAutoUnload = True
        self.subCommands = {}
        self.subMenus = {}
        self.customPermissions = {}
        self.requiredFrom = []
        self.requiredList = []
        self.required = 0
        self.variables = {}
        self.getCore()
    def __str__(self):
        return self.name
    def __getattr__(self, name):
        self.getModule()
        if (name in gImportLibraries) and (self._xa.__dict__.has_key(name)):
            if not name in self._xalibs:
                self._xalibs[name] = Admin_lib(self._xa.__dict__[name], self)
            return self._xalibs[name]
        elif (name in gModules) and (name in self.requiredList):
            for mod in es.addons.getAddonList():
                if mod.__name__ == 'xa.modules.%s.%s'%(name, name):
                    if not name in self._xalibs:
                        self._xalibs[name] = Admin_lib(mod, self)
                    return self._xalibs[name]
            raise AttributeError, name
        elif (self._xamod.__dict__.has_key(name)):
            return Admin_lib(self._xamod, self).__getattr__(name)
        else:
            raise AttributeError, name
    def getAddonInfo(self):
        self.getModule()
        for item in self._xamod.__dict__:
            if isinstance(self._xamod.__dict__[item], es.AddonInfo):
                return self._xamod.__dict__[item]
    def getCore(self):
        if not self._xa:
            for mod in es.addons.getAddonList():
                if mod.__name__ == 'xa.xa':
                    self._xa = mod
        return self._xa
    def getModule(self):
        if not self._xamod:
            for mod in es.addons.getAddonList():
                if mod.__name__ == 'xa.modules.%s.%s'%(self.name, self.name):
                    self._xamod = mod
        return self._xamod
    def delete(self):
        unregister(self.name)
    def unregister(self):
        unregister(self.name)
    def addRequirement(self, gModuleList):
        if isinstance(gModuleList, str):
            addlist = [gModuleList]
        else:
            addlist = list(gModuleList)
        for module in addlist:
            if module in modules():
                module = find(module)
                module.required += 1
                module.requiredFrom.append(self.name)
                self.requiredList.append(module.name)
    def delRequirement(self, gModuleList):
        if isinstance(gModuleList, str):
            dellist = [gModuleList]
        else:
            dellist = list(gModuleList)
        for module in dellist:
            if exists(module) and (module in self.requiredList):
                module = find(module)
                module.required -= 1
                module.requiredFrom.remove(self.name)
                self.requiredList.remove(module.name)
    def addCommand(self, command, block, perm, permlvl, descr='eXtensible Admin command', mani=False):
        #create new menu
        self.subCommands[command] = Admin_command(command, block, perm, permlvl, descr, mani)
        return self.subCommands[command]
    def delCommand(self, command):
        #delete a menu
        if (command in self.subCommands):
            if self.subCommands[command]:
                self.subCommands[command].unregister(['server','console','say'])
                self.subCommands[command] = None
    def isCommand(self, command):
        if (command in self.subCommands):
            return True
        return False
    def findCommand(self, command):
        if (command in self.subCommands):
            return self.subCommands[command]
    def addMenu(self, menu, display, menuname, perm, permlvl):
        #create new menu
        self.subMenus[menu] = Admin_menu(menu, display, menuname, perm, permlvl)
        return self.subMenus[menu]
    def delMenu(self, menu):
        #delete a menu
        if (menu in self.subMenus):
            if self.subMenus[menu]:
                self.subMenus[menu].unregister()
                self.subMenus[menu] = None
    def isMenu(self, menu):
        if (menu in self.subMenus):
            return True
        return False
    def findMenu(self, menu):
        if (menu in self.subMenus):
            return self.subMenus[menu]
    def registerCapability(self, auth_capability, auth_recommendedlevel, auth_type='ADMIN'):
        self.customPermissions[auth_capability] = {'level':str(auth_recommendedlevel).upper(), 'type':str(auth_type).upper()}
        return registerCapability(auth_capability, getLevel(auth_recommendedlevel))
    def isUseridAuthorized(self, auth_userid, auth_capability):
        return isUseridAuthorized(auth_userid, auth_capability)
    def information(self, listlevel):
        if listlevel >= 1:
            es.dbgmsg(0, ' ')
        es.dbgmsg(0, self.name)
        if listlevel >= 1:
            es.dbgmsg(0, '  Auto-Unload:  '+str(self.allowAutoUnload))
        if listlevel >= 2:
            es.dbgmsg(0, '  Required by:  '+str(len(self.requiredFrom)))
            for module in self.requiredFrom:
                es.dbgmsg(0,'    '+module)
            es.dbgmsg(0, '  Requires:     '+str(len(self.requiredList)))
            for module in self.requiredList:
                es.dbgmsg(0,'    '+module)
            es.dbgmsg(0, '  ')
            es.dbgmsg(0, '  Variables:    '+str(len(self.variables)))
            for var in self.variables:
                es.dbgmsg(0,'    '+var)
        if listlevel >= 3:
            es.dbgmsg(0, '  ')
            es.dbgmsg(0, '  Libs & Funcs: '+str(len(self._xalibs)))
            for lib in self._xalibs:
                es.dbgmsg(0,'    '+lib+' ['+str(self._xalibs[lib]._xalibcalls)+' calls]')
                for func in self._xalibs[lib]._xalibfuncs:
                    if self._xalibs[lib]._xalibfuncs[func]._xalibfuncstats['calls'] > 0:
                        es.dbgmsg(0,'        '+func+' ['+str(self._xalibs[lib]._xalibfuncs[func]._xalibfunccalls)+' calls, '+str(self._xalibs[lib]._xalibfuncs[func]._xalibfuncstats['calls'])+' subcalls, '+str(self._xalibs[lib]._xalibfuncs[func]._xalibfuncstats['times'])+' CPU seconds]')
                    else:
                        es.dbgmsg(0,'        '+func+' ['+str(self._xalibs[lib]._xalibfuncs[func]._xalibfunccalls)+' calls]')
            es.dbgmsg(0, '  -------------')

# Admin_command is the clientcmd class
class Admin_command(object):
    def __init__(self, gCommand, gBlock, gPerm, gPermLevel, gDescription='eXtensible Admin command', gManiComp=False):
        #initialization of the module
        self.name = gCommand
        self.block = gBlock
        self.permission = gPerm
        self.permissionlevel = gPermLevel
        self.manicomp = gManiComp
        self.descr = gDescription
        self.server = False
        self.console = False
        self.say = False
        self.chat = False
    def __str__(self):
        return self.name
    def register(self, gList):
        if isinstance(gList, str):
            cmdlist = [gList]
        else:
            cmdlist = list(gList)
        if 'server' in cmdlist and not self.server:
            if self.manicomp and isManiMode() and self.name.startswith('xa_'):
                cmdlib.registerServerCommand('ma_'+self.name[3:], self.incomingServer, self.descr)
            cmdlib.registerServerCommand(self.name, self.incomingServer, self.descr)
            self.server = True
        if 'console' in cmdlist and not self.console:
            if self.manicomp and isManiMode() and self.name.startswith('xa_'):
                cmdlib.registerClientCommand('ma_'+self.name[3:], self.incomingConsole, self.descr, self.permission, self.permissionlevel)
            cmdlib.registerClientCommand(self.name, self.incomingConsole, self.descr, self.permission, self.permissionlevel)
            self.console = True
        if 'say' in cmdlist and not self.say:
            if self.name.startswith('xa_'):
                cmdlib.registerSayCommand(str(gCoreVariables['sayprefix'])+self.name[3:], self.incomingSay, self.descr, self.permission, self.permissionlevel)
            cmdlib.registerSayCommand(self.name, self.incomingSay, self.descr, self.permission, self.permissionlevel)
            self.say = True
        if 'chat' in cmdlist and not self.chat:
            if not self.incomingChat in es.addons.SayListeners:
                es.addons.registerSayFilter(self.incomingChat)
            self.chat = True
    def unregister(self, gList):
        if isinstance(gList, str):
            cmdlist = [gList]
        else:
            cmdlist = list(gList)
        if 'server' in cmdlist and self.server:
            if self.name.startswith('xa_'):
                cmdlib.unregisterServerCommand('ma_'+self.name[3:])
            cmdlib.unregisterServerCommand(self.name)
            self.server = False
        if 'console' in cmdlist and self.console:
            if self.name.startswith('xa_'):
                cmdlib.unregisterClientCommand('ma_'+self.name[3:])
            cmdlib.unregisterClientCommand(self.name)
            self.console = False
        if 'say' in cmdlist and self.say:
            if self.name.startswith('xa_'):
                cmdlib.unregisterSayCommand(str(gCoreVariables['sayprefix'])+self.name[3:])
            cmdlib.unregisterSayCommand(self.name)
            self.say = False
        if 'chat' in cmdlist and self.chat:
            if self.incomingChat in es.addons.SayListeners:
                es.addons.unregisterSayFilter(self.incomingChat)
            self.chat = False
    def callBlock(self, userid, args):
        try:
            self.block(userid, args)
        except TypeError:
            try:
                self.block()
            except TypeError:
                es.doblock(self.block)
    def incomingServer(self, args):
        if self.server:
            self.callBlock(0, args)
    def incomingConsole(self, userid, args):
        if self.console:
            self.callBlock(userid, args)
    def incomingSay(self, userid, args):
        if self.say:
            self.callBlock(userid, args)
    def incomingChat(self, userid, message, teamonly):
        if self.chat:
            output = message
            if output[0] == output[-1:] == '"':
                output = output[1:-1]
            command = output.split(' ')[0]
            if command.startswith('ma_'):
                command = 'xa_'+command[3:]
            elif command.startswith(str(gCoreVariables['sayprefix'])):
                command = 'xa_'+command[len(str(gCoreVariables['sayprefix'])):]
            if command == self.name and services.use('auth').isUseridAuthorized(userid, self.permission):
                self.callBlock(userid, cmdlib.cmd_manager.CMDArgs(output.split(' ')[1:] if len(output.split(' ')) > 1 else []))
        return (userid, message, teamonly)
    def information(self, listlevel):
        if listlevel >= 1:
            es.dbgmsg(0, ' ')
        es.dbgmsg(0, self.name)
        if listlevel >= 1:
            es.dbgmsg(0, '  Block:        '+str(self.block))
            es.dbgmsg(0, '  Server cmd:   '+str(self.server))
            es.dbgmsg(0, '  Console cmd:  '+str(self.console))
            es.dbgmsg(0, '  Say cmd:      '+str(self.say))
            es.dbgmsg(0, '  Chat cmd:     '+str(self.chat))
            es.dbgmsg(0, '  Mani cmd:     '+str(self.manicomp))
            es.dbgmsg(0, '  Permission:   '+str(self.permission))
            es.dbgmsg(0, '  Perm-level:   '+str(self.permissionlevel))
            es.dbgmsg(0, '  Description:  '+str(self.descr))

# Admin_menu is the clientcmd class
class Admin_menu(object):
    def __init__(self, gMenu, gDisplay, gMenuName, gPerm, gPermLevel):
        #initialization of the module
        self.name = gMenu
        self.display = gDisplay
        self.menu = gMenuName
        self.menutype = ''
        self.menuobj = None
        self.permission = gPerm
        self.permissionlevel = gPermLevel
        if popuplib.exists(self.menu):
            self.menutype = 'popup'
            self.menuobj = popuplib.find(self.menu)
        elif keymenulib.exists(self.menu):
            self.menutype = 'keymenu'
            self.menuobj = keymenulib.find(self.menu)
        elif settinglib.exists(self.menu):
            self.menutype = 'setting'
            self.menuobj = settinglib.find(self.menu)
        services.use('auth').registerCapability(self.permission, getLevel(self.permissionlevel))
        self.addBackButton()
    def __str__(self):
        return self.name
    def unregister(self):
        self.menuobj = None
    def setDisplay(self, display):
        self.display = display
    def setMenu(self, menu):
        if popuplib.exists(menu):
            self.menu = menu
            self.menutype = 'popup'
            self.menuobj = popuplib.find(self.menu)
        elif keymenulib.exists(menu):
            self.menu = menu
            self.menutype = 'keymenu'
            self.menuobj = keymenulib.find(self.menu)
        elif settinglib.exists(menu):
            self.menu = menu
            self.menutype = 'setting'
            self.menuobj = settinglib.find(self.menu)
        else:
            return False
        return self.addBackButton()
    def addBackButton(self):
        if isinstance(self.menuobj, popuplib.Popup_easymenu):
            self.menuobj.menuselect = sendMenu
            self.menuobj.c_exitformat = '0. Back'
        elif isinstance(self.menuobj, keymenulib.Keymenu_keymenu):
            try:
                self.menuobj.popup.menuselect = sendMenu
                self.menuobj.popup.c_exitformat = '0. Back'
            except:
                return False ## keymenulib was probably changed, don't worry, no back button then
        return True
    def information(self, listlevel):
        if listlevel >= 1:
            es.dbgmsg(0, ' ')
        es.dbgmsg(0, self.name)
        if listlevel >= 1:
            es.dbgmsg(0, '  Display:      '+str(self.display))
            es.dbgmsg(0, '  Menuname:     '+str(self.menu))
            es.dbgmsg(0, '  Menutype:     '+str(self.menutype))
            es.dbgmsg(0, '  Permission:   '+str(self.permission))
            es.dbgmsg(0, '  Perm-level:   '+str(self.permissionlevel))

# Admin_mani is the Mani compatibility helper class
class Admin_mani(object):
    def __init__(self):
        self.admincmd = Admin_command('admin', sendMenu, 'xa_menu', 'ADMIN')
        self.admincmd.register(['console'])

    def loadModules(self):
        module = configparser.getList(self, 'addons/eventscripts/xa/static/manimodule.txt', True)
        if module:
            for line in module:
                linelist = map(str, line.strip().split('|', 3))
                if linelist[0] == '*':
                    xa_load(linelist[1])
                else:
                    variable = es.ServerVar(linelist[0], 0)
                    if linelist[2] == str(variable) or linelist[2] == '*':
                        xa_load(linelist[1])
                    elif linelist[3] != str(variable) or linelist[3] == '*':
                        xa_load(linelist[1])
        else:
            raise IOError, 'Could not find xa/static/manimodule.txt!'

    def loadVariables(self):
        config = configparser.getList(self, 'addons/eventscripts/xa/static/maniconfig.txt', True)
        if config:
            for line in config:
                linelist = map(str, line.strip().split('|', 2))
                es.ServerVar(linelist[0], linelist[1], linelist[2])
        else:
            raise IOError, 'Could not find xa/static/maniconfig.txt!'

    def convertClients(self):
        permissions = configparser.getKeyList(self, 'addons/eventscripts/xa/static/manipermission.txt', True)
        if not permissions:
            raise IOError, 'Could not find xa/static/manipermission.txt!'

        auth = services.use('auth')
        if not auth.name in ('group_auth', 'basic_auth'):
            return False

        clients = configparser.getKeyList(self, 'cfg/mani_admin_plugin/clients.txt', True)
        if not clients:
            return False

        if not 'players' in clients:
            clients['players'] = keyvalues.KeyValues(name='players')
        if not 'admingroups' in clients:
            clients['admingroups'] = keyvalues.KeyValues(name='admingroups')
        if not 'immunitygroups' in clients:
            clients['immunitygroups'] = keyvalues.KeyValues(name='immunitygroups')

        if auth.name == 'basic_auth':
            es.dbgmsg(0, '[eXtensible Admin] Converting clients.txt to Basic Auth')
            adminlist = str(es.ServerVar('BASIC_AUTH_ADMIN_LIST'))
            for client in clients['players']:
                if 'steam' in clients['players'][str(client)]:
                    if not clients['players'][str(client)]['steam'] in adminlist.split(';'):
                        adminlist += ';' + str(clients['players'][str(client)]['steam'])
                        es.dbgmsg(0, ('[eXtensible Admin] Added Admin: %s [%s]' % (str(client), str(clients['players'][str(client)]['steam']))))
            es.dbgmsg(0, '[eXtensible Admin] Finished Mani setup for Basic Auth')        
        elif auth.name == 'group_auth':
            es.dbgmsg(0, '[eXtensible Admin] Converting clients.txt to Group Auth')
            permcache = []
            commandqueue = []
            adminflags = {}
            immunityflags = {}
            if int(es.ServerVar('mani_reverse_admin_flags')):
                for module in sorted(modules()):
                    module = find(module)
                    for command in sorted(module.subCommands):
                        adminflags[str(module.subCommands[command].permission)] = 'ADMIN'
                    for menu in module.subMenus:
                        adminflags[str(module.subMenus[menu].permission)] = 'ADMIN'
                    for custom in module.customPermissions:
                        if module.customPermissions[str(custom)]['type'] == 'ADMIN':
                            adminflags[str(custom)] = 'ADMIN'
            if int(es.ServerVar('mani_reverse_immunity_flags')):
                for module in sorted(modules()):
                    module = find(module)
                    for custom in module.customPermissions:
                        if module.customPermissions[str(custom)]['type'] == 'IMMUNITY':
                            immunityflags[str(custom)] = 'ADMIN'
            for perm in permissions['adminflags']:
                if not str(perm) in adminflags:
                    adminflags[str(perm)] = permissions['adminflags'][str(perm)]
            for perm in permissions['immunityflags']:
                if not str(perm) in immunityflags:
                    immunityflags[str(perm)] = permissions['immunityflags'][str(perm)]
            for group in clients['admingroups']:
                if 'ADMIN' in clients['admingroups'][str(group)].upper().split(' '):
                    commandqueue.append('gauth group delete "Mani_%s"' % (str(group).replace(' ', '_')))
                    commandqueue.append('gauth group create "Mani_%s" %d' % (str(group).replace(' ', '_'), int(es.ServerVar('AUTHSERVICE_UNRESTRICTED'))))
                    if int(es.ServerVar('mani_reverse_admin_flags')):
                        for perm in adminflags:
                            if (adminflags[str(perm)] in clients['admingroups'][str(group)].split(' ')) or (str(adminflags[str(perm)]).upper() == 'ADMIN'):
                                if not str(perm) in permcache:
                                    permcache.append(str(perm))
                                    commandqueue.append('gauth power create "%s" %s' % (str(perm), str(es.ServerVar('AUTHSERVICE_ADMIN'))))
                                commandqueue.append('gauth power give "%s" "Mani_%s"' % (str(perm), str(group).replace(' ', '_')))
                    else:
                        for perm in adminflags:
                            if (not adminflags[str(perm)] in clients['admingroups'][str(group)].split(' ')) or (str(adminflags[str(perm)]).upper() == 'ADMIN'):
                                if not str(perm) in permcache:
                                    permcache.append(str(perm))
                                    commandqueue.append('gauth power create "%s" %s' % (str(perm), str(es.ServerVar('AUTHSERVICE_ADMIN'))))
                                commandqueue.append('gauth power give "%s" "Mani_%s"' % (str(perm), str(group).replace(' ', '_')))
            for group in clients['immunitygroups']:
                if 'IMMUNITY' in clients['immunitygroups'][str(group)].upper().split(' '):
                    commandqueue.append('gauth group delete "Mani_%s"' % (str(group).replace(' ', '_')))
                    commandqueue.append('gauth group create "Mani_%s" %d' % (str(group).replace(' ', '_'), int(es.ServerVar('AUTHSERVICE_UNRESTRICTED'))))
                    if int(es.ServerVar('mani_reverse_immunity_flags')):
                        for perm in immunityflags:
                            if (immunityflags[str(perm)] in clients['immunitygroups'][str(group)].split(' ')) or (str(immunityflags[str(perm)]).upper() == 'IMMUNITY'):
                                if not str(perm) in permcache:
                                    permcache.append(str(perm))
                                    commandqueue.append('gauth power create "%s" %s' % (str(perm), str(es.ServerVar('AUTHSERVICE_ADMIN'))))
                                commandqueue.append('gauth power give "%s" "Mani_%s"' % (str(perm), str(group).replace(' ', '_')))
                    else:
                        for perm in immunityflags:
                            if (not immunityflags[str(perm)] in clients['immunitygroups'][str(group)].split(' ')) or (str(immunityflags[str(perm)]).upper() == 'IMMUNITY'):
                                if not str(perm) in permcache:
                                    permcache.append(str(perm))
                                    commandqueue.append('gauth power create "%s" %s' % (str(perm), str(es.ServerVar('AUTHSERVICE_ADMIN'))))
                                commandqueue.append('gauth power give "%s" "Mani_%s"' % (str(perm), str(group).replace(' ', '_')))
            for client in clients['players']:
                if 'steam' in clients['players'][str(client)]:
                    commandqueue.append('gauth user create "%s" "%s"' % (str(client), str(clients['players'][str(client)]['steam'])))
                    es.dbgmsg(0, ('[eXtensible Admin] Added Client: %s [%s]' % (str(client), str(clients['players'][str(client)]['steam']))))
                    if 'admingroups' in clients['players'][str(client)]:
                        for group in clients['players'][str(client)]['admingroups'].split(';'):
                            commandqueue.append('gauth user join "%s" "Mani_%s"' % (str(client), str(group).replace(' ', '_')))
                    if 'immunitygroups' in clients['players'][str(client)]:
                        for group in clients['players'][str(client)]['immunitygroups'].split(';'):
                            commandqueue.append('gauth user join "%s" "Mani_%s"' % (str(client), str(group).replace(' ', '_')))
            for cmd in commandqueue:
                es.server.cmd(cmd)
            es.dbgmsg(0, '[eXtensible Admin] Finished Mani setup for Group Auth')

###########################
#Module methods start here#
###########################
def xa_load(pModuleid):
    """Loads a module"""
    if gModulesLoading:
        es.load('xa/modules/%s' % pModuleid)

def xa_unload(pModuleid):
    """Unloads a module"""
    if gModulesLoading:
        es.unload('xa/modules/%s' % pModuleid)

def xa_reload(pModuleid):
    """Reloads a module"""
    if gModulesLoading:
        gamethread.delayed(0.1, xa_unload, (pModuleid,))
        gamethread.delayed(0.5, xa_load, (pModuleid,))

def xa_runconfig():
    """Runs XA's configuration file"""
    setting.executeConfiguration()

def xa_exec(pModuleid = None): # be backwards compatible, but just execute general module config
    """Runs XA's configuration file"""
    xa_runconfig()

def debug(dbglvl, message):
    """Debugs a message"""
    if int(gCoreVariables['debug']) >= dbglvl:
        es.dbgmsg(0, message)

def register(pModuleid):
    """Registers a new module with XA"""
    gModules[pModuleid] = Admin_module(pModuleid)
    es.dbgmsg(0, '[eXtensible Admin] Registered module "%s"' % gModules[pModuleid].name)
    return gModules[pModuleid]

def unregister(pModuleid):
    """Unregisters the module from XA"""
    if exists(pModuleid):
        module = find(pModuleid)
        if module.required:
            es.dbgmsg(0, '[eXtensible Admin] ***********************************')
            es.dbgmsg(0, '[eXtensible Admin] WARNING! Module "%s" is required!' % module.name)
            for submodule in module.requiredFrom:
                submodule = find(submodule)
                if submodule.name in modules():
                    es.dbgmsg(0, '[eXtensible Admin] Required by "%s"' % submodule.name)
                else:
                    module.required -= 1
                    module.requiredFrom.remove(submodule.name)
            es.dbgmsg(0, '[eXtensible Admin] ***********************************')
        for submodule in module.requiredList:
            if submodule in modules():
                submodule = find(submodule)
                submodule.required -= 1
                submodule.requiredFrom.remove(module.name)
                module.required -= 1
                module.requiredList.remove(submodule.name)
        for command in module.subCommands:
            module.delCommand(command)
        for menu in module.subMenus:
            module.delMenu(menu)
        es.dbgmsg(0, '[eXtensible Admin] Unregistered module "%s"' % module.name)
        del gModules[module.name]

def modules():
    """Returns the list of registered modules"""
    return gModules.keys()
    
def corevars():
    """Returns the list of core server variables"""
    return gCoreVariables.values()

def exists(pModuleid):
    """Checks if the module is registered with XA Core"""
    return (str(pModuleid) in modules())

def find(pModuleid):
    """Returns the class instance of the named module"""
    if exists(pModuleid):
        return gModules[str(pModuleid)]

def isRequired(pModuleid):
    """Checks if the module is required by other modules"""
    if exists(pModuleid):
        return bool(find(pModuleid).required)

def findMenu(pModuleid, pMenuid):
    """Returns the class instance a menu in the named module"""
    if exists(pModuleid):
        if pMenuid in find(pModuleid).subMenus:
            return find(pModuleid).subMenus[pMenuid]

def findCommand(pModuleid, pCommandid):
    """Returns the class instance a command in the named module"""
    if exists(pModuleid):
        if pCommandid in find(pModuleid).subCommands:
            return find(pModuleid).subCommands[pCommandid]

def isManiMode():
    """Checks if Mani mode is enabled"""
    return bool(int(gCoreVariables['manimode']))

def getLevel(auth_capability):
    """Returns the Auth Provider level by name"""
    return cmdlib.permissionToInteger(auth_capability)

def registerCapability(auth_capability, auth_recommendedlevel):
    """Registers an auth capability with the recommended level"""
    return services.use('auth').registerCapability(auth_capability, getLevel(auth_recommendedlevel))

def isUseridAuthorized(auth_userid, auth_capability):
    """Checks if a userid is authorized or not"""
    return services.use('auth').isUseridAuthorized(auth_userid, auth_capability)

def sendMenu(userid=None, choice=10, name=None):
    """Shows the main menu to the specified player"""
    if choice != 10:
        return None
    if userid:
        userid = int(userid)
    elif es.getcmduserid():
        userid = int(es.getcmduserid())
    if userid and (es.exists('userid', userid)):
        gMainMenu[userid] = popuplib.easymenu('_xa_mainmenu_'+str(userid), None, incomingMenu)
        gMainMenu[userid].settitle(language.createLanguageString('eXtensible Admin'))
        gMainMenu[userid].vguititle = 'eXtensible Admin'
        for module in modules():
            module = find(module)
            for page in module.subMenus:
                if module.subMenus[page] and services.use('auth').isUseridAuthorized(userid, module.subMenus[page].permission):
                    gMainMenu[userid].addoption(page, module.subMenus[page].display, 1)
        if popuplib.isqueued(gMainMenu[userid].name, userid):
            gMainMenu[userid].update(userid)
        else:
            gMainMenu[userid].send(userid)

def incomingMenu(userid, choice, name):
    for module in modules():
        module = find(module)
        if choice in module.subMenus:
            if module.subMenus[choice] and services.use('auth').isUseridAuthorized(userid, module.subMenus[choice].permission):
                module.subMenus[choice].menuobj.send(userid)

def addondir():
    return str(es.ServerVar('eventscripts_addondir')).replace("\\", "/")

def gamedir():
    return str(es.ServerVar('eventscripts_gamedir')).replace("\\", "/")

def coredir():
    return str(es.getAddonPath('xa')).replace("\\", "/")

def moduledir(pModuleid):
    return str('%smodules/%s' % (es.getAddonPath('xa'), pModuleid)).replace("\\", "/")

def copytree(src, dst, counter=0):
    # modified Python 2.6 shutil.copytree method that ignores existing files
    if not os.path.exists(dst):
        os.makedirs(dst)
    for name in os.listdir(src):
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        if os.path.isdir(srcname):
            counter += copytree(srcname, dstname, counter)
        elif not os.path.exists(dstname):
            shutil.copy2(srcname, dstname)
            counter += 1
    try:
        shutil.copystat(src, dst)
    except WindowsError:
        # can't copy file access times on Windows
        pass
    return counter

###########################################
#EventScripts events and blocks start here#
###########################################

def load():
    global gMainMenu, gMainCommand, gModulesLoading
    es.dbgmsg(0, '[eXtensible Admin] Second loading part...')
    if not services.isRegistered('auth'):
        es.dbgmsg(0, '[eXtensible Admin] WARNING! Auth Provider required!')
        es.dbgmsg(0, '[eXtensible Admin] Loading Basic Auth...')
        es.load('examples/auth/basic_auth')
    gMainCommand = Admin_command('xa', command, 'xa_menu', 'UNRESTRICTED')
    gMainCommand.register(['server', 'console', 'say'])
    gModulesLoading = False
    es.dbgmsg(0, '[eXtensible Admin] Merging default configuration...')
    gCopiedFiles = copytree('%s/cfg/xa/_defaults' % gamedir(), '%s/cfg' % gamedir())
    es.dbgmsg(0, '[eXtensible Admin] Number of files copied = %d' % gCopiedFiles)
    es.dbgmsg(0, '[eXtensible Admin] Executing xa.cfg...')
    es.server.cmd('es_xmexec xa.cfg')
    es.dbgmsg(0, '[eXtensible Admin] Mani mode enabled = %s' % isManiMode())
    gModulesLoading = True
    if isManiMode():
        ma = Admin_mani()
        es.dbgmsg(0, '[eXtensible Admin] Executing mani_server.cfg...')
        ma.loadVariables()
        es.server.cmd('es_xmexec mani_server.cfg')
        ma.loadModules()
        ma.convertClients()
    es.dbgmsg(0, '[eXtensible Admin] Third loading part...')
    es.dbgmsg(0, '[eXtensible Admin] Executing xa.cfg...')
    es.server.cmd('es_xmexec xa.cfg')
    es.dbgmsg(0, '[eXtensible Admin] Executing xamodules.cfg...')
    setting.executeConfiguration()
    es.dbgmsg(0, '[eXtensible Admin] Updating xamodules.cfg...')
    setting.writeConfiguration()
    es.dbgmsg(0, '[eXtensible Admin] Finished loading')

def unload():
    global gMainMenu, gMainCommand
    es.dbgmsg(0, '[eXtensible Admin] Begin unloading...')
    for module in sorted(gModules.values(), lambda x, y: cmp(x.required, y.required)*-1):
        if module.allowAutoUnload:
            for command in module.subCommands:
                module.subCommands[command].unregister(['console', 'say'])
            for menu in module.subMenus:
                module.subMenus[menu].unregister()
            es.dbgmsg(0, '[eXtensible Admin] Unloading module "%s"' % module.name)
            es.unload('xa/modules/'+module.name)
    for menu in gMainMenu:
        if popuplib.exists(str(menu)):
            menu.delete()
    if gMainCommand:
        gMainCommand.unregister(['server', 'console', 'say'])
        del gMainCommand
    es.dbgmsg(0, '[eXtensible Admin] Finished unloading sequence')
    es.dbgmsg(0, '[eXtensible Admin] Modules will now unregister themself...')

def command(userid, args):
    if userid > 0:
        return sendMenu()
    else:
        argc = len(args)
        subcmd = (args[0].lower() if argc else None)
        seccmd = (args[1] if argc > 1 else None)
    if subcmd == 'load':
        if seccmd:
            xa_load(seccmd)
        else:
            es.dbgmsg(0, 'Syntax: xa load <module-name>')
    elif subcmd == 'unload':
        if seccmd:
            xa_unload(seccmd)
        else:
            es.dbgmsg(0, 'Syntax: xa unload <module-name>')
    elif subcmd == 'reload':
        if seccmd:
            xa_reload(seccmd)
        else:
            es.dbgmsg(0, 'Syntax: xa reload <module-name>')
    elif subcmd == 'send':
        if seccmd:
            sendMenu(seccmd)
        else:
            es.dbgmsg(0, 'Syntax: xa send <userid>')
    elif subcmd == 'help':
        helplist = {}
        if exists(seccmd):
            module = find(seccmd)
            for command in sorted(module.subCommands):
                helplist[command] = ['cmd', str(module.subCommands[command].permission), str(module.subCommands[command].descr)]
            for variable in sorted(module.variables):
                helplist[variable] = ['var', str(module.variables[variable]), str(module.variables[variable]._def), str(module.variables[variable]._descr)]
        else:
            for module in sorted(modules()):
                module = find(module)
                for command in sorted(module.subCommands):
                    helplist[command] = ['cmd', str(module.subCommands[command].permission), str(module.subCommands[command].descr)]
                for variable in sorted(module.variables):
                    helplist[variable] = ['var', str(module.variables[variable]), str(module.variables[variable]._def), str(module.variables[variable]._descr)]
        es.dbgmsg(0,'---------- List of commands and variables:')
        for helpindex in sorted(helplist):
            helpline = helplist[helpindex]
            if helpline[0] == 'cmd':
                es.dbgmsg(0,('%-*s'%(40, helpindex))+' : '+('%-*s'%(8, 'cmd'))+' : '+('%-*s'%(16, helpline[1]))+' : '+helpline[2])
            elif helpline[0] == 'var':
                es.dbgmsg(0,('%-*s'%(40, helpindex))+' : '+('%-*s'%(8, helpline[1]))+' : '+('%-*s'%(16, helpline[2]))+' : '+helpline[3])
        es.dbgmsg(0,'----------')
        es.dbgmsg(0, 'Syntax: xa help [module]')
    elif subcmd == 'permissions':
        permissions = []
        if seccmd:
            userid = int(es.getuserid(seccmd))
        else:
            userid = None
        if userid:
            permissions.append(['Module', 'Permission', 'Level', 'Type', 'Name', 'Granted'])
        else:
            permissions.append(['Module', 'Permission', 'Level', 'Type', 'Name'])
        for module in sorted(modules()):
            module = find(module)
            if userid:
                for command in sorted(module.subCommands):
                    permissions.append([str(module.name), str(module.subCommands[command].permission), str(module.subCommands[command].permissionlevel), 'command', str(module.subCommands[command].name), module.isUseridAuthorized(userid, str(module.subCommands[command].permission))])
                for menu in module.subMenus:
                    permissions.append([str(module.name), str(module.subMenus[menu].permission), str(module.subMenus[menu].permissionlevel), 'menu', str(module.subMenus[menu].name), module.isUseridAuthorized(userid, str(module.subMenus[menu].permission))])
                for custom in module.customPermissions:
                    permissions.append([str(module.name), str(custom), str(module.customPermissions[custom]['level']), 'custom', str(module.customPermissions[custom]['type']), module.isUseridAuthorized(userid, str(custom))])
            else:
                for command in sorted(module.subCommands):
                    permissions.append([str(module.name), str(module.subCommands[command].permission), str(module.subCommands[command].permissionlevel), 'command', str(module.subCommands[command].name)])
                for menu in module.subMenus:
                    permissions.append([str(module.name), str(module.subMenus[menu].permission), str(module.subMenus[menu].permissionlevel), 'menu', str(module.subMenus[menu].name)])
                for custom in module.customPermissions:
                    permissions.append([str(module.name), str(custom), str(module.customPermissions[custom]['level']), 'custom', str(module.customPermissions[custom]['type'])])
        es.dbgmsg(0,'---------- List of permissions:')
        for perm in permissions:
            if userid:
                if not perm[5] == 'Granted':
                    if perm[5]:
                        granted = 'Yes'
                    else:
                        granted = 'No'
                else:
                    granted = perm[5]
                es.dbgmsg(0,('%-*s'%(18, perm[0]))+' '+('%-*s'%(20, perm[1]))+' '+('%-*s'%(8, '['+perm[2]+']'))+' '+('%-*s'%(10, perm[3]))+' '+('%-*s'%(15, perm[4]))+' '+granted)
            else:
                es.dbgmsg(0,('%-*s'%(18, perm[0]))+' '+('%-*s'%(20, perm[1]))+' '+('%-*s'%(8, '['+perm[2]+']'))+' '+('%-*s'%(10, perm[3]))+' '+perm[4])
        es.dbgmsg(0,'----------')
        es.dbgmsg(0, 'Syntax: xa permissions [user]')
    elif subcmd == 'stats':
        statistics = []
        for module in sorted(modules()):
            module = find(module)
            xlibs = xfuncs = xcalls = xsubcalls = xseconds = 0
            for lib in module._xalibs:
                xlibs += 1
                for func in module._xalibs[lib]._xalibfuncs:
                    xfuncs += 1
                    xcalls += module._xalibs[lib]._xalibfuncs[func]._xalibfunccalls
                    xsubcalls += module._xalibs[lib]._xalibfuncs[func]._xalibfuncstats['calls']
                    xseconds += module._xalibs[lib]._xalibfuncs[func]._xalibfuncstats['times']
            statistics.append([str(module.name), xlibs, xfuncs, xcalls, xsubcalls, xseconds])
        es.dbgmsg(0,'---------- List of statistics:')
        if seccmd and seccmd.isdigit():
            sortkey = int(seccmd)
        else:
            sortkey = 5
        if int(gCoreVariables['debugprofile']) > 0:
            sortkey = min(5, sortkey)
        else:
            sortkey = min(3, sortkey)
        sortkey = max(0, sortkey)
        statistics = sorted(statistics, cmp=lambda x,y: cmp(x[sortkey], y[sortkey]))
        statistics.append(['Module', 'Libraries', 'Functions', 'Calls', 'SubCalls', 'CPU seconds'])
        if int(gCoreVariables['debugprofile']) > 0:
            for stat in reversed(statistics):
                es.dbgmsg(0,('%-*s'%(18, stat[0]))+' '+('%-*s'%(10, str(stat[1])))+' '+('%-*s'%(10, str(stat[2])))+' '+('%-*s'%(10, str(stat[3])))+' '+('%-*s'%(10, str(stat[4])))+' '+str(stat[5]))
        else:
            for stat in reversed(statistics):
                es.dbgmsg(0,('%-*s'%(18, stat[0]))+' '+('%-*s'%(10, str(stat[1])))+' '+('%-*s'%(10, str(stat[2])))+' '+str(stat[3]))
        es.dbgmsg(0,'----------')
        es.dbgmsg(0, 'Syntax: xa stats [sort-column]')
    elif subcmd == 'list':
        es.dbgmsg(0,'---------- List of modules:')
        if seccmd and seccmd.isdigit():
            listlevel = int(seccmd)
        else:
            listlevel = 0
        for module in modules():
            module = find(module)
            module.information(listlevel)
        if argc == 2:
            es.dbgmsg(0, ' ')
            es.dbgmsg(0, 'For more details, supply list level (0-3):')
            es.dbgmsg(0, 'Syntax: xa module list [level]')
        es.dbgmsg(0,'----------')
    elif subcmd == 'info':
        if argc >= 2:
            if argc >= 3 and args[2].isdigit():
                listlevel = int(args[2])
            else:
                listlevel = 2
            if exists(seccmd):
                module = find(seccmd)
                module.information(listlevel)
        else:
            es.dbgmsg(0, 'Syntax: xa module info <module-name> [level]')
    else:
        es.dbgmsg(0,'Invalid xa subcommand, see http://python.eventscripts.com/pages/XA for help')
