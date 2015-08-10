# ==============================================================================
#   IMPORTS
# ==============================================================================

# Python Imports
import os
import shutil
import hotshot.stats
import time
import cPickle

# EventScripts Imports
import es
import services
import gamethread
import playerlib
import popuplib
import keymenulib
import settinglib
import keyvalues
import cmdlib
import cfglib

# ==============================================================================
#   ADDON REGISTRATION
# ==============================================================================

# Version info
__version__ = '1.1.0.560'
es.ServerVar('eventscripts_xa', __version__, 'eXtensible Admin').makepublic()
es.dbgmsg(0, '[eXtensible Admin] Version: %s' % __version__)
es.dbgmsg(0, '[eXtensible Admin] Begin loading...')

# Register with EventScripts
info = es.AddonInfo()
info.name       = 'eXtensible Admin'
info.version    = __version__
info.url        = 'http://forums.mattie.info/cs/forums/viewforum.php?f=97'
info.basename   = 'xa'
info.author     = 'EventScripts Developers'

# ==============================================================================
#   LOAD XA LIBRARIES
# ==============================================================================

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

# ==============================================================================
#   GLOBALS
# ==============================================================================

# Imported libraries
gImportLibraries = dir()

# Core variables
gCoreVariables = {}
gCoreVariables['log']           = es.ServerVar('xa_log',            0,      'Activates the module logging')
gCoreVariables['debug']         = es.ServerVar('xa_debug',          0,      'Activates the module/library debugging')
gCoreVariables['debugprofile']  = es.ServerVar('xa_debugprofile',   0,      'Activates the module/library profiling')
gCoreVariables['manimode']      = es.ServerVar('xa_manimode',       0,      'Is Mani compatibility mode active?')
gCoreVariables['manimode_cmd']  = es.ServerVar('xa_manimode_command',       0,      'Admin console command to register when mani compatibility is on')
gCoreVariables['sayprefix']     = es.ServerVar('xa_sayprefix',      '!',    'Say command prefix')
gCoreVariables['setting_expiry_days'] = es.ServerVar('xa_setting_expiry_days',      14,    'Amount of days before settings are removed') 

# Main menu and command instance
gMainConfig = None
gMainMenu = {}
gMainCommand = None

# Module dict
gModules = {}
gModulesLoading = False

# game name
currentGame = es.getGameName()

# ==============================================================================
#   HELPER CLASSES
# ==============================================================================

class Admin_libfunc(object):
    """
    This class is to be used as a wrapper for a function in a library. It will
    allow us to simulate a call to a library function passing the module as the
    first parameter. This allows us to access library functions through the
    Admin Module instance we are given from xa.register().
    
    This basically allows us to call:
    
    xamodule_instance.xa_library.<function>(<args>, <keywords>)
    
    This instance will make the <function>(<args>, <kw>) callable.
    """
    def __init__(self, gLib, gFunc, gModule):
        """
        Default constructor, initialise all variables
        
        @param gLib module The instance of an import to the library where the function is held
        @param gFunc function The function's address we wish to execute
        @param gModule Admin_module The instance to a registered XA Module calling the libary
        """
        self._xalib = gLib
        self._xamod = gModule
        self._xalibfunc = gFunc
        
        # Number of function calls
        self._xalibfunccalls = 0
        
        # Statistics for functions calls
        self._xalibfuncstats = {'calls':0, 'times':0}
        
        
        
    def __call__(self, *args, **kw):
        """
        Executed when this instance is treated as a function and called. This
        is the magic of this instance and will perceive the interface of a function.
        As we are simulating a function, just execute the intended function passing
        the arguments and keywords. The main objective of this is to hook the
        function calling so we can add some debugging to it.
        
        @param args tuple A list of arguments in the correct order
        @param kw dict A list of named arguments
        """
        # Let's call our lib function, increase counter
        self._xalibfunccalls += 1
        
        # Is debugging or profiling enabled?
        if int(gCoreVariables['debug']) >= 1 or int(gCoreVariables['debugprofile']) > 0:
            # Let's profile our function to collect statistics
            fn = '%s/xa.prof' % coredir()
            
            # Create hotshot Profile object
            pr = hotshot.Profile(fn)
            
            # Run the function using the Profiler
            re = pr.runcall(self._xalibfunc, *(self._xamod,)+args, **kw)
            
            # Close the Profiler
            pr.close()
            
            # Load the generated statistic
            st = hotshot.stats.load(fn)
            st.strip_dirs()
            
            # Sort the statistic
            st.sort_stats('time', 'calls')
            
            # How much should we debug to the console?
            if int(gCoreVariables['debug']) >= 2:
                es.dbgmsg(0, '--------------------')
                es.dbgmsg(0, ('Admin_libfunc %d: __call__(%s.%s [%s], %s, %s)' % (self._xalibfunccalls, str(self._xalib.__name__), str(self._xalibfunc.__name__), str(self._xamod), args, kw)))
                es.dbgmsg(0, ('Admin_libfunc %d: Profile Statistics' % (self._xalibfunccalls)))
                st.print_stats(20)
                es.dbgmsg(0, '--------------------')
                
            elif int(gCoreVariables['debug']) == 1:
                es.dbgmsg(0, ('Admin_libfunc %d: __call__(%s.%s [%s], %s, %s)' % (self._xalibfunccalls, str(self._xalib.__name__), str(self._xalibfunc.__name__), str(self._xamod), args, kw)))
                es.dbgmsg(0, ('Admin_libfunc %d: %d calls in %f CPU seconds' % (self._xalibfunccalls, st.total_calls, st.total_tt)))
            
            # Should we increate the statistic counters?
            if int(gCoreVariables['debugprofile']) > 0:
                self._xalibfuncstats['calls'] += st.total_calls
                self._xalibfuncstats['times'] += st.total_tt
                
            # Does our statistic file still exist?
            if os.path.exists(fn):
                # Delete the statistic file
                os.unlink(fn)
            
            # Return the functions result
            return re

        else:
            # Just call our function and return it's result
            return self._xalibfunc(self._xamod, *args, **kw)

class Admin_lib(object):
    """
    This class has a purpose to imitate a library. The reason we have this as
    an instance is so we can create our own call structure to known libraries in
    our custom directories by using the module instance. An example of how we
    use this is:
    
    xa_module_instance.<library>
    
    This will enable us to import funtions from libraries directly from the
    "../xa/" directory without any imports at all.
    """
    def __init__(self, gLib, gModule):
        """
        Default constructor, initialise variables. Called when we create an
        instance.
        
        @param gLib module A library module returned by an __import__ statement
                           to the place where this library represents
        @param gModule Admin_module The XA Admin Module calling this library
        """
        self._xalib = gLib
        self._xamod = gModule
        
        # Number of library function requests
        self._xalibcalls = 0
        
        # References to function wrappers
        self._xalibfuncs = {}        
        
    def __getattr__(self, name):
        """
        Executed when an unknown attribute is read from this instance. We will
        use this to simulate a function call from the libary instance.
        
        @param name string The name of the 'function' in the libary we want to call
        @return Admin_libfunc A function type object which imitates a library function
        """
        # Let's fetch our function from the library, increase counter
        self._xalibcalls += 1
        
        # Is debugging enabled?
        if int(gCoreVariables['debug']) >= 2:
            es.dbgmsg(0, ('Admin_lib %d: __getattr__(%s [%s], %s)' % (self._xalibcalls, str(self._xalib.__name__), str(self._xamod), name)))
        
        # Does the function exist in the library and is it public?
        if self._xalib.__dict__.has_key(name) and not name.startswith('_'):
            # Didn't we already find the function before?
            if not name in self._xalibfuncs:
                self._xalibfuncs[name] = Admin_libfunc(self._xalib, self._xalib.__dict__[name], self._xamod)
                
            # Return the function wrapper reference
            return self._xalibfuncs[name]
            
        else:
            # Raise an error, the function does not exist
            raise AttributeError("%s is not a callable function in the %s library" % (name, self._xalib) )

# ==============================================================================
#   CORE CLASSES
# ==============================================================================

class Admin_module(object):
    """
    This class is used to hold all information needed by an XA module. There will
    be one instance for each loaded module, and it will be returned by xa.register().
    This module will hold key API structures for the module, and any libary
    will be accessed through this instance. It is the string which ties the main
    XA and the module itself together.
    """
    def __init__(self, gModule):
        """
        Defualt constructor, initialise variables. Called automatically when a
        new instance is created, CANNOT return anything.
        
        @param gModule string The base name of the module this represents
        """
        
        # XA core reference
        self._xa = None
        
        # XA module reference
        self._xamod = None
        
        # XA libraries references
        self._xalibs = {}
        
        # Module name
        self.name = gModule
        
        # Module commands
        self.subCommands = {}
        
        # Module menus inside the main menu
        self.subMenus = {}
        
        # Custom permissions owned by this module
        self.customPermissions = {}
        
        # Other modules which require this module
        self.requiredFrom = []
        
        # This module requires other modules
        self.requiredList = []
        
        # Number of other modules which require this module
        self.required = 0
        
        # Variables created by this module
        self.variables = {}
    
        # Commands created by this module
        self.commands = {}
        
        # Find the XA core reference
        self.getCore()
        
    def __str__(self):
        """
        Executed automatically when a string cast is attempting on this instance.
        Return the name of the module it represents so we can use it in string
        concatenation and other string casting methods such as str().
        
        @return string The name of the module this represents
        """
        # Module name
        return self.name
        
    def __repr__(self):
        """
        Executed automatically when we wan't to know how Python represents this
        instance. Return a string which simulates this as an instance and the
        data it contains.
        
        @return string A string representation of how Python represents this instance.
        """
        return "Admin_module(%s)" % repr(self.name)
        
    def __getattr__(self, name):
        """
        Executed automatically when we attempt to access an attribute which 
        cannot be found in the instances global dictionary. In this case, we can
        assume that we are attempting to access a library due to the API dependencies
        of XA and the acceptance of accessing libraries through this instance.
        We need to check if this is an imported library / module, if so, return
        an Admin_lib instance to it, otherwise, raise an AttributeError which
        would have normally have been raised but with a more relevant and
        helpful message.
        
        @param name string The name of the attribute as a string we're attempting to access
        @return Admin_lib An object to a representation of the intended imported library
        """
        
        # Find the module reference
        self.getModule()
        
        if (name in gImportLibraries) and (name in self._xa.__dict__):
            """ See if the requested library is in the imported library list """
            if name not in self._xalibs:
                self._xalibs[name] = Admin_lib(self._xa.__dict__[name], self)
            return self._xalibs[name]
        
        
        elif (name in gModules) and (name in self.requiredList):
            """ Test to see if the requested library is an XA module """
            for mod in es.addons.getAddonList():
                if mod.__name__ == 'xa.modules.%s.%s' % (name, name):
                    if name not in self._xalibs:
                        self._xalibs[name] = Admin_lib(mod, self)
                    return self._xalibs[name]
                    
            """ The module was not found in the loaded addon list """
            raise AttributeError, "XA Module %s is currently not loaded or does not exist" % name
        
        elif (name in self._xamod.__dict__):
            """ See if the attribute exists in the global scope of this module """
            return Admin_lib(self._xamod, self).__getattr__(name)
        else:
            raise AttributeError("Library %s cannot be found, please ensure the library exists" % name)

    def getAddonInfo(self):
        """
        Gets the information of an addon via the registered es.AddonInfo instance
        which should be assigned for each module.
        
        @return es.AddonInfo|None The Information of the loaded addon, otherwise None
        """
        self.getModule()
        
        """ Loop through all global items to see if there is an es.AddonInfo instance inside """
        for item in self._xamod.__dict__:
            if isinstance(self._xamod.__dict__[item], es.AddonInfo):
                return self._xamod.__dict__[item]
        return None
                
    def getCore(self):
        """
        This finds the XA core (this module) and stores the module type in our
        own instance. Maybe we could make a static instance and assign directly
        so the class has a static variable, not an inherited copy?
        
        @return module The module instance of this loaded file. 
        """
        if not self._xa:
            for mod in es.addons.getAddonList():
                if mod.__name__ == 'xa.xa':
                    self._xa = mod
                    
        return self._xa
        
    def getModule(self):
        """
        This finds the Module reference (the module this instance represents) and
        stores the module type in our own instance. This enables us to have an
        __import__ instance of the module this instance represents.
        
        @return module The module of the XA module this instance represents
        """
        if not self._xamod:
            for mod in es.addons.getAddonList():
                if mod.__name__ == 'xa.modules.%s.%s'%(self.name, self.name):
                    self._xamod = mod
        
        return self._xamod
        
    def delete(self):
        """
        @depricated
        
        A wrapper to unregister the XA module this instance represents. Execute
        the unregister function.
        
        Depricated, only use to keep backwards compatibility
        """
        unregister(self.name)
        
    def unregister(self):
        """
        Used to execute the unregister function. This will unregister the module
        this instance represents. Should be called whenever the addon is unloaded.
        Used as a wrapper so we can unload the XA module directly from the instance 
        rather than the imported XA module (this file's global scope).
        """
        unregister(self.name)
        
    def unload(self):
        """
        Used to unload the module that this instance represents. Call the global
        xa_unload() function passing this module's name as a parameter. Used as
        a wrapper so we can unload the XA module directly from the instance rather
        than the imported XA module (this file's global scope).
        """
        xa_unload(self.name)
        
    def addRequirement(self, gModuleList):
        """
        Add a requirement for the module to work. Requirements are a list of
        other known XA modules which MUST be loaded to ensure that the module
        this instance represents works correctly.
        
        @param tuple|list|string gModuleList A list of modules which are required by this module
        """
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
        """
        Remove requirements for this module to work. This should generally be
        called on unload before the module is unregistered.
        
        @param tuple|list|string gModuleList A list of modules which are no longer required by this module 
        """
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
                
    def addCommand(self, command, block, perm=None, permlvl=None, descr='eXtensible Admin command', mani=False):
        """
        Register a command to be used. A command will execute a Python function
        whenever it is called. 
        
        @param string command The command as a string which will execute the block
        @param function block The Python function which will be executed on command call
        @param optional string perm The permission of the command. This will be used in permission based auth as flags.
        @param optional string permlvl The recommended auth level of the command. Should be in form of cmdlib.permisionlevels
        @param optional string descr A description of the command
        @param optional boolean mani Whether or not this should be registered as a mani command
        @return Admin_command An instance which represents a cmdlib type object for the command. 
        """
        self.subCommands[command] = Admin_command(command, block, perm, permlvl, descr, mani)
        return self.subCommands[command]
        
    def delCommand(self, command):
        """
        Remove a command from the list of commands registered by this module
        instnace. Ensure that all command types are unregistered when this
        command is deleted.
        
        @param string command The name of the command to be deleted from this instance
        """
        if (command in self.subCommands):
            if self.subCommands[command]:
                self.subCommands[command].unregister(['server','console','say'])
                self.subCommands[command] = None
                del self.subCommands[command]
                
    def isCommand(self, command):
        """
        Test to see if a command has already been created
        
        @param string command The name of the command to test
        @return boolean Whether or not the command is registered
        """
        return (command in self.subCommands)
        
    def findCommand(self, command):
        """
        Retrieve the Admin_command object from the list of contained commands.
        
        @param string command The name of the string to retrieve the command object from
        @return Admin_command|None The command object which represents the command
        """
        if (command in self.subCommands):
            return self.subCommands[command]
        return None
            
    def addMenu(self, menu, display, menuname, perm=None, permlvl=None):
        """
        Registers and adds a new popup to the main XA menu. This will allow us
        to display sub items from the main menu. This will be built specifically
        for each individual admin, so permission based authorizations will work.
        
        @param string menu Unique identifier to identify the menu. Why not use menuname?
        @param string display Popup title, must be multilingual to display correctly.
        @param string menuname Name of the popuplib identifier to create a link between the menus.
        @param string perm Name of the permission which will be used to see if an admin is authorized to view the menu.
        @param string permlvl Name of the recommended authority level to use.
        @return Admin_menu An instance representing a linked popuplib sub menu for the popuplib identifier.
        """
        self.subMenus[menu] = Admin_menu(menu, display, menuname, perm, permlvl)
        return self.subMenus[menu]
        
    def delMenu(self, menu):
        """
        Removes and unregisters the menu from the saved instances.
        
        @param string menu Unique identifier to identify popup submenu.
        """
        if (menu in self.subMenus):
            if self.subMenus[menu]:
                self.subMenus[menu].unregister()
                del self.subMenus[menu]
                
    def isMenu(self, menu):
        """
        Test to see if a menu has already been created/registered.
        
        @param string menu Unique identifier to see which menu we are testing
        @return boolean Whether or not the menu has already been created/registered.
        """
        return (menu in self.subMenus)
        
    def findMenu(self, menu):
        """
        Retrieve thse menu instance from the given identifier.
        
        @param string menu Unique identifier of popup instance to retrieve
        @return Admin_menu Instance representing the popup of the unique identifier
        """
        if (menu in self.subMenus):
            return self.subMenus[menu]
        return None
            
    def registerCapability(self, auth_capability, auth_recommendedlevel, auth_type='ADMIN'):
        """
        Register a capability so that we can have permission based actions. This
        is for a more precise way of managing actions rather than having commands
        do it automatically for you.
        
        @param string auth_capability The permission name which will be used as a flag
        @param string auth_recommendedlevel The recommended level of the permission
        @param string auth_type The authorization type of the permission, why not use auth_recommendedlevel? 
        @return services.auth.AuthorizationService The current loaded authorization service instance
        """
        self.customPermissions[auth_capability] = {'level':str(auth_recommendedlevel).upper(), 'type':str(auth_type).upper()}
        return registerCapability(auth_capability, getLevel(auth_recommendedlevel))
        
    def isUseridAuthorized(self, auth_userid, auth_capability):
        """
        Used as a short wrapper so we can access this functionality without going
        through the global XA module import. Test to see if a user is authorized
        to execute a certain permission.
        
        @param int|string auth_userid The userid to test for authority
        @param string auth_capability The capability to test for validity
        @return boolean Whether or not the user is authorized to execute the capability
        """
        return isUseridAuthorized(auth_userid, auth_capability)
        
    def information(self, listlevel):
        """
        Send information about this class to the console to be logged. This should
        display instance unique information for debugging and logging purposes.
        
        @param int listlevel The level of detail to provide when logging
                    Level 1: Requirements and variable
                    Level 2: Libraries and function call information
        """
        if listlevel >= 1:
            es.dbgmsg(0, ' ')
        es.dbgmsg(0, self.name)
        if listlevel >= 1:
            """ Display information about this instance and requirements """
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
        if listlevel >= 2:
            """ Display information about all the library and function calls """
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

class Admin_command(object):
    """
    This class is used to register a command so we can use chat / console / server
    commands. It's a way to manage customized cmdlib items to make the API more
    friendly and familiar to the XA theme.
    """
    def __init__(self, gCommand, gBlock, gPerm=None, gPermLevel=None, gDescription='eXtensible Admin command', gManiComp=False):
        """
        Default constructor, initialise all properties of the instnace.
        
        @param string gCommand The command name string which will be used to execute the function
        @param function gBlock The Python block to be executed upon command notify
        @param string gPerm The name of the permission (if any) to use for the command
        @param string gPermLevel The recommended permission level of te command (if any)
        @param string gDescription A short description of the command and what it does / how to use it
        @param boolean gManiComp Create a mani command as well?
        """
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
        """
        Executed automatically when this instance is cast to a string. Ensure that
        we return a string object which can identify the command in string
        manipulation such as string concatenation.
        
        @return string The name of the command.
        """
        return self.name
        
    def __repr__(self):
        """
        Executed automatically when we want to show a string representation of
        how this instance will be handled in Python. Return a string representation
        containing specific instance information.
        
        @return string The string representation of how Python uses this instance
        """
        registers = []
        if self.server:
            registers.append("server")
        if self.console:
            registers.append("console")
        if self.say:
            registers.append("say")
        if self.chat:
            registers.append("chat")
        if registers:
            return "Admin_command(%s, %s)" % (self.name, ", ".join(registers) )
        return "Admin_command(%s)" % self.name 
        
    def register(self, gList):
        """
        Register the command with cmdlib so the commands are actually enabled and
        working on the server. Even though we have created an instance, the
        commands will not take effect until they have been registered.
        
        @param string|iterable gList A list of types of commands to register
                    Types:
                    ------------------------------------------------------------ 
                    server  - Server command, can be called via RCON or via es.server.cmd() calls
                    chat    - Say command, text will NOT be killed
                    say     - Say command, text WILL be killed
                    console - Client console command, easy to bind keys to etc 
        """
        
        """ Ensure we have a list rather than a single string item """
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
        """
        Unregister commands, this should be called on unload so that it clears
        up any register commands.
        
        @param string|iterable gList A list of types of commands to unregister
                    Types:
                    ------------------------------------------------------------ 
                    server  - Server command, can be called via RCON or via es.server.cmd() calls
                    chat    - Say command, text will NOT be killed
                    say     - Say command, text WILL be killed
                    console - Client console command, easy to bind keys to etc  
        """
        
        """ Ensure we have a list rather than a single string item """
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
        """
        This function attempts to execute the relative function via several
        methods. First we shall attempt to execute the registered method passing
        userid and args parmaeters; if that fails, just try without any parameters.
        If that still fails, just execute an ESS block.
        
        @param int userid The ID of the person who executed the command
        @param mixed args A list of arguments following the original command 
        """
        try:
            self.block(userid, args)
        except TypeError:
            try:
                self.block()
            except TypeError:
                es.doblock(self.block)
                
    def incomingServer(self, args):
        """
        Executed when this registered server command has been executed. Execute
        the registered block with "0" as the userid so it looks as though the
        "World" executed it.
        
        @param mixed args A mixture of additional arguments
        """
        if self.server:
            self.callBlock(0, args)
            
    def incomingConsole(self, userid, args):
        """
        Executed when a console command is used from a client. Execute the
        registered method passing the userid and args
        
        @param int userid The userid of the person who executed the command
        @param mixed args Any additional arguments
        """
        if self.console:
            self.callBlock(userid, args)
            
    def incomingSay(self, userid, args):
        """
        Executed when a say command is used from a client. Execute the
        registered method passing the userid and args
        
        @param int userid The userid of the person who executed the command
        @param mixed args Any additional arguments
        """
        if self.say:
            self.callBlock(userid, args)
            
    def incomingChat(self, userid, message, teamonly):
        """
        The say filter we registered to pick up any chat commands. We will test
        to see if the command is equal to any commands, if so, send the method
        with the rest of the text split by a space delimiter.
        
        @param int userid The ID of the user who executed the command
        @param string message The text which was said
        @param boolean teamonly Whether or not this was said as team only chat
        @return (int, string, boolean) The modified text of the say filter
        """
        if self.chat:
            output = message
            if output[0] == output[-1:] == '"':
                output = output[1:-1]
            command = output.split(' ')[0]
            if command.startswith('ma_'):
                command = 'xa_'+command[3:]
            elif command.startswith(str(gCoreVariables['sayprefix'])):
                command = 'xa_'+command[len(str(gCoreVariables['sayprefix'])):]
            if command == self.name and not self.permission or isUseridAuthorized(userid, self.permission):
                self.callBlock(userid, cmdlib.cmd_manager.CMDArgs(output.split(' ')[1:] if len(output.split(' ')) > 1 else []))
        return (userid, message, teamonly)
        
    def information(self, listlevel):
        """
        A function to provide debug information to the server console in the form
        of es debug messages. Print any important information.
        
        @param int listlevel The level of information to print
                    0 - Just the command name
                    1 - Any registered properties with this instance
        """
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
            es.dbgmsg(0, '  Capability:   '+str(self.permission))
            es.dbgmsg(0, '  Level:        '+str(self.permissionlevel))
            es.dbgmsg(0, '  Description:  '+str(self.descr))

class Admin_menu(object):
    """
    This object is used to replicate and represent a sub menu for a user's
    main XA menu. This should be used whenever we create a new submenu directly
    from themain XA menu. Ensure that permissions etc are set. We use our own
    custom object so we can have it very specific to our needs and remove the
    complex parts from the user's. 
    """
    def __init__(self, gMenu, gDisplay, gMenuName, gPerm=None, gPermLevel=None):
        """
        Default constructor, ensure that all properties and instance values
        are assigned correctly.
        
        @param string gMenu A unique identifier to specify the menu
        @param string gDisplay A title of the popup option, this should be multi-lingual
        @param string gMenuName The name of the popuplib identifier
        @param string gPerm The permission required to have access to this option
        @param string gPermlevel The recommended level for the permission
        """
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
        if self.permission and self.permissionlevel:
            registerCapability(self.permission, getLevel(self.permissionlevel))
        self.addBackButton()
        
    def __str__(self):
        """
        Executed automatally when string casting occurs. Return a string object
        which can be used in a string manipulation conversion. In this case we
        shall return the unique identifier.
        
        @return string The unique identifier of the object
        """
        return self.name
        
    def __repr__(self):
        """
        Executed automatically when we want to show a string representation of
        how this instance will be handled in Python. Return a string representation
        containing specific instance information.
        
        @return string The string representation of how Python uses this instance
        """
        return "Admin_menu(%s, %s)" % (self.name, self.menutype) 
        
    def unregister(self):
        """
        Unassign the menu object so that the object no longer exists and hopefully
        the deconstructors can clean up the object themselves.
        """
        self.menuobj = None
        
    def setDisplay(self, display):
        """
        Reassign the display to a new value. This should be a multi-lingual text
        so it displays in all languages.
        
        @param string display The title of the option
        """
        self.display = display
        
    def setMenu(self, menu):
        """
        Reassigns the menu object so that the sub menu points to a new object.
        
        @param string menu Either the identifier for a popup, keymenu or setting menu.
        """
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
        """
        Ensures that a back button is present on the current menuobject
        
        @return Whether or not the back button was successfully added.
        """
        isInstance = False
        try:
            isInstance = isinstance(self.menuobj, popuplib.Popup_easymenu)
        except AttributeError:
            isInstance = isinstance(self.menuobj, popuplib.Easymenu)
        if isInstance:
            """ The menu object is a popup menu, alter the sub menu. """
            self.menuobj.menuselect = sendMenu
            self.menuobj.c_exitformat = '0. Back'
        elif isinstance(self.menuobj, keymenulib.Keymenu_keymenu):
            """ The menu object is a key menu, alter the sub menu. """
            try:
                self.menuobj.popup.menuselect = sendMenu
                self.menuobj.popup.c_exitformat = '0. Back'
            except:
                return False ## keymenulib was probably changed, don't worry, no back button then
        return True
        
    def information(self, listlevel):
        """
        A function to provide debug information to the server console in the form
        of es debug messages. Print any important information.
        
        @param int listlevel The level of information to print
                    0 - Just the menu name
                    1 - Any registered properties with this instance
        """
        if listlevel >= 1:
            es.dbgmsg(0, ' ')
        es.dbgmsg(0, self.name)
        if listlevel >= 1:
            es.dbgmsg(0, '  Display:      '+str(self.display))
            es.dbgmsg(0, '  Menuname:     '+str(self.menu))
            es.dbgmsg(0, '  Menutype:     '+str(self.menutype))
            es.dbgmsg(0, '  Capability:   '+str(self.permission))
            es.dbgmsg(0, '  Level:        '+str(self.permissionlevel))

class Admin_mani(object):
    """
    This class is here to encapsulate all of Mani Admin conversion properties
    in one place so we can easily manage the execution of Mani Admin settings.
    This should be used as a singleton, so only one instance should be created.
    """
    def __init__(self):
        """
        Default constructor, ensure that we assign default variables and set up
        important engine settings.
        """
        self.admincmd = Admin_command(gCoreVariables['manimode_cmd'], sendMenu)
        self.admincmd.register(['console'])
        self.config = configparser.getList(self, 'addons/eventscripts/xa/static/maniconfig.txt', True)
        self.permissions = configparser.getKeyList(self, 'addons/eventscripts/xa/static/manipermission.txt', True)

    def loadVariables(self):
        """
        Register all default mani admin Server Variables so that we can alter
        them in a .CFG file.
        """
        if self.config:
            for line in self.config:
                linelist = map(str, line.strip().split('|', 2))
                es.ServerVar(linelist[0], linelist[1], linelist[2])
        else:
            raise IOError, 'Could not find xa/static/maniconfig.txt!'

    def hookAuthProvider(self):
        """
        Hook the auth provider's isIdAuthorized function so we can change what
        occurs before we attempt to see if a person is authorized. Save the old
        authorization function in a different value so we still have access
        to the underlying functionality of that object.
        """
        if self.permissions:
            auth = services.use('auth')
            if auth.name in ('group_auth', 'basic_auth', 'mani_basic_auth', 'ini_tree_auth'):
                es.dbgmsg(0, '[eXtensible Admin] We will be converting capabilities to Mani flags')
                self.isIdAuthorized = auth.isIdAuthorized
                auth.isIdAuthorized = self.hookIsIdAuthorized
                es.dbgmsg(0, '[eXtensible Admin] Finished Mani setup for Mani flags based Auth')
        else:
            raise IOError, 'Could not find xa/static/manipermission.txt!'

    def hookIsIdAuthorized(self, auth_identifier, auth_capability):
        """
        This hook occurrs before we attempt to see if a userid is authorized.
        We need to alter the auth_identifier to change it from a mani_admin flag
        so that the mani_admin flags equals our custom permissions so mani_admin
        flags can be used instead of the full text meaning.
        
        @param int auth_identifier The id of the user we are testing for access
        @param string auth_capability The flag / permission that we are testing for
        @return boolean Whether or not the user is allowed to execute that permission. 
        """
        if self.permissions:
            if auth_capability in self.permissions['adminflags']:
                return self.isIdAuthorized(auth_identifier, auth_capability) or self.isIdAuthorized(auth_identifier, 'mani_flag_%s'%self.permissions['adminflags'][auth_capability])
            else:
                return self.isIdAuthorized(auth_identifier, auth_capability)
        else:
            raise IOError, 'Could not find xa/static/manipermission.txt!'

# ==============================================================================
#   MODULE API FUNCTIONS
# ==============================================================================

def xa_load(pModuleid):
    """
    Loads a module if loading is enabled. This is just a wrapper for es.load()
    or es_xload in autoexec.cfg.
    
    @param string pModuleid Name of the XA module 
    """
    if gModulesLoading:
        es.server.cmd('es_xload xa/modules/%s' % pModuleid)

def xa_unload(pModuleid):
    """
    Unloads a module if loading is enabled. This is just a wrapper for es.unload()
    or es_xunload in autoexec.cfg.
    
    @param string pModuleid Name of the XA module 
    """
    if gModulesLoading:
        es.server.cmd('es_xunload xa/modules/%s' % pModuleid)

def xa_reload(pModuleid):
    """
    Reloads a module if loading is enabled. This is just a wrapper for es.reload()
    or es_xreload in autoexec.cfg.
    
    @param string pModuleid Name of the XA module 
    """
    if gModulesLoading:
        es.server.cmd('es_xunload xa/modules/%s' % pModuleid)
        es.server.queuecmd('es_xload xa/modules/%s' % pModuleid)

def xa_runconfig():
    """
    Runs XA configuration file. This will load all the configurations and alter
    the global ServerVariable values.
    """
    setting.executeConfiguration(None)

def debug(dbglvl, message):
    """
    Debugs a message to console. This sends a message to the console and also
    adds a line to the log file if sv_log is enabled.
    
    @param int dblvl The level of the debug required to have this message logged
    @param string message The text which will be logged if dbglvl passes 
    """
    if int(gCoreVariables['debug']) >= dbglvl:
        es.dbgmsg(0, message)

def register(pModuleid, gameSupport = None):
    """
    Registers a new module with XA. This should be used for every XA module.
    The return instance will provide a way to interact with XA itself. It is
    the link between the XA core and the module itself.
    
    @param string pModuleid The name of the XA module which needs to be regisitered
    @param optional mixed gameSupport A list of games which this module is supported by
    @return Admin_module A module instance which represents this module name.
    """
    gModules[pModuleid] = Admin_module(pModuleid)
    es.dbgmsg(1, '[eXtensible Admin] Registered module "%s"' % gModules[pModuleid].name)
    
    if gameSupport is not None and not hasattr(gameSupport, "__iter__"):
        """ If game support is not itterable, convert to tuple so we can use __contains__ """
        gameSupport = (gameSupport, )
        
    if gameSupport and currentGame not in gameSupport:
        es.dbgmsg(1, '[eXtensible Admin] Module "%s" is not supported for this game and will be disabled' % gModules[pModuleid].name)
        # delay unload to ensure it has loaded correctly
        gamethread.delayed(1, xa_unload, (pModuleid,))
    return gModules[pModuleid]

def unregister(pModuleid):
    """
    Unregisters the module from XA. This removes the link between the core API
    and the module. Make sure that we unregister all the command and menus so
    we clear up everything by default.
    
    @param string pModuleid The name of the module to unregister
    """
    if exists(pModuleid):
        """ The module is registered and can be unregistered """
        module = find(pModuleid)
        if module.required:
            """ The module is required by other modules, unload them first. """
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
        for command in module.subCommands.copy():
            module.delCommand(command)
        for menu in module.subMenus.copy():
            module.delMenu(menu)
        es.dbgmsg(1, '[eXtensible Admin] Unregistered module "%s"' % module.name)
        del gModules[module.name]

def modules():
    """
    @returns list The list of registered modules
    """
    return gModules.keys()
    
def corevars():
    """
    @returns list The core server variables
    """
    return gCoreVariables.values()

def exists(pModuleid):
    """
    Checks if the module is registered with XA Core.
    
    @param string pModuleid The name of the module to check for existance
    @return boolean Whether or not the module is currently registered 
    """
    return str(pModuleid) in modules()

def find(pModuleid):
    """
    Retrieves the class instance of the Admin_module from the global dictionary
    
    @param string pModuleid The identifier of the module we wish to get the instance of
    @return Admin_module The instancewhich represents the module
    """
    if exists(pModuleid):
        return gModules[str(pModuleid)]
    return None

def isRequired(pModuleid):
    """
    Checks if the module is required by other modules.
    
    @param string pModuleid The name of the module to check for requirements
    @return boolean Whether or not the module is required by other modules
    """
    if exists(pModuleid):
        return bool(find(pModuleid).required)
    return False

def findMenu(pModuleid, pMenuid):
    """
    Returns the class instance a menu in the named module
    
    @param string pModuleid The module where the menu is registered
    @param string pMenuid The menu which is registered in the module
    @return Admin_menu The class instance of the menu inside the module
    """
    if exists(pModuleid):
        if pMenuid in find(pModuleid).subMenus:
            return find(pModuleid).subMenus[pMenuid]
    return None

def findCommand(pModuleid, pCommandid):
    """
    Returns the class instance a menu in the named module
    
    @param string pModuleid The module where the command is registered
    @param string pCommandid The command which is registered in the module
    @return Admin_command The class instance of the command inside the module
    """
    if exists(pModuleid):
        if pCommandid in find(pModuleid).subCommands:
            return find(pModuleid).subCommands[pCommandid]
    return None

def isManiMode():
    """
    Checks if Mani mode is enabled or not.
    
    @return boolean Whether or not mani mode is currently active.
    """
    return bool(int(gCoreVariables['manimode']))

def getLevel(auth_capability):
    """
    Converts the string capability into the integral power value, e.g. ADMIN => 1
    
    @param string auth_capability The string capability name
    @returns int The auth provider level
    """
    return cmdlib.permissionToInteger(auth_capability)

def registerCapability(auth_capability, auth_recommendedlevel):
    """
    Registers an auth capability with the recommended level. This will make it
    so we can test for user's authorization.
    
    @param string auth_capability The capability power
    @param string auth_recommendedlevel The recommended level for the power of the auth
    @return services.auth.AuthorizationService The current loaded authorization service instance 
    """
    return services.use('auth').registerCapability(auth_capability, getLevel(auth_recommendedlevel))

def isUseridAuthorized(auth_userid, auth_capability):
    """
    Checks if a userid is authorized or not for a particular capability.
    
    @param int|string auth_userid The ID of the user we wish to test for authorization
    @param string auth_capability The capability we wish to test for
    """
    return services.use('auth').isUseridAuthorized(auth_userid, auth_capability)

def sendMenu(userid=None, choice=10, name=None):
    """
    Shows the main menu to the specified player. We need to build a new menu
    and reload the permissions to ensure that each menu is individual to each
    player so custom permissions mean custom menus.
    
    @param int userid The ID of the user who we wish to send the popup to
    @param int choice The choice of the last menu item which was chosen
    @param string name The name of the last popup which was executed by the user
    """
    if choice != 10:
        return None
    if userid:
        userid = int(userid)
    elif es.getcmduserid():
        userid = int(es.getcmduserid())
    if userid and (es.exists('userid', userid)):
        """ Build the menu unique to the user """
        gMainMenu[userid] = popuplib.easymenu('xa_%s'%userid, None, incomingMenu)
        gMainMenu[userid].settitle(language.createLanguageString(None, 'eXtensible Admin'))
        gMainMenu[userid].vguititle = 'eXtensible Admin'
        for module in modules():
            module = find(module)
            for page in module.subMenus:
                if module.subMenus[page] and not module.subMenus[page].permission or isUseridAuthorized(userid, module.subMenus[page].permission):
                    gMainMenu[userid].addoption(page, module.subMenus[page].display, 1)
        if popuplib.active(userid)['name'] == gMainMenu[userid].name or popuplib.isqueued(gMainMenu[userid].name, userid):
            gMainMenu[userid].update(userid)
        else:
            gMainMenu[userid].send(userid)

def incomingMenu(userid, choice, name):
    """
    Executed when a person has chosen an option from the main page. Loop through
    all registered modules and check which sub menu we want to open.
    
    @param int userid The ID of the user that chose the option
    @param string choice The choice that was selected from the main menu
    @param string name The name of the popup which was used to get here
    """
    for module in modules():
        module = find(module)
        if choice in module.subMenus:
            if module.subMenus[choice] and not module.subMenus[choice].permission or isUseridAuthorized(userid, module.subMenus[choice].permission):
                module.subMenus[choice].menuobj.send(userid)

def addondir():
    """
    @return string The directory of the ../addons/ folder.
    """
    return str(es.ServerVar('eventscripts_addondir')).replace("\\", "/")

def gamedir():
    """
    @return string The directory of the ../<game dir>/ folder, e.g. ../cstrike/.
    """
    return str(es.ServerVar('eventscripts_gamedir')).replace("\\", "/")

def coredir():
    """
    @return string The directory of the ../addons/xa/ folder (this addon).
    """
    return str(es.getAddonPath('xa')).replace("\\", "/")

def moduledir(pModuleid):
    """
    @return string The XA modules directory of the ../addons/xa/modules/ folder.
    """
    return str('%smodules/%s' % (es.getAddonPath('xa'), pModuleid)).replace("\\", "/")

def copytree(src, dst, counter=0):
    """
    Modified Python 2.6 shutil.copytree method that ignores existing files. This
    copies over files and folders from one place to another but will not 
    overwrite any current files / folders.
    
    @param string src The source of the copy tree
    @param string dst The destination of the copy tree
    @param int counter The amount of files which have currently been moved
    @return int The amount of files which have been moved
    """
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
    except:
        pass # can't copy file access times on Windows
    return counter

# ==============================================================================
#   GAME EVENTS
# ==============================================================================
def load():
    """
    Executed when this addon loads. We need to ensure that we set up everything
    here. We need to register the main menus and commands, then load all the
    other XA modules followed by executing the main configuration files.
    """
    global gMainConfig
    global gMainMenu
    global gMainCommand
    global gModulesLoading
    global gSettingExpireManager
    global gSettingPath
    
    es.dbgmsg(0, '[eXtensible Admin] Second loading part...')
    if not services.isRegistered('auth'):
        """ No authorization services is loaded, load a default one (mani basic auth) """
        es.dbgmsg(0, '[eXtensible Admin] WARNING! Auth Provider required!')
        es.dbgmsg(0, '[eXtensible Admin] Loading Mani Basic Auth...')
        es.load('examples/auth/mani_basic_auth')
        
    """ Register default commands """
    gMainCommand = Admin_command('xa', command)
    gMainCommand.register(['server', 'console', 'say'])
    gModulesLoading = False
    
    """ Merge default configs for first time set up """
    es.dbgmsg(0, '[eXtensible Admin] Merging default configuration...')
    gCopiedFiles = copytree('%s/cfg/xa/_defaults' % gamedir(), '%s/cfg' % gamedir())
    es.dbgmsg(0, '[eXtensible Admin] Number of files copied = %d' % gCopiedFiles)
    
    """ Execute the default config which will load the modules """
    es.dbgmsg(0, '[eXtensible Admin] Executing xa.cfg...')
    gMainConfig = cfglib.AddonCFG('%s/cfg/xa.cfg' % gamedir())
    gMainConfig.execute()
    
    """ Check for mani admin set up """
    es.dbgmsg(0, '[eXtensible Admin] Mani mode enabled = %s' % isManiMode())
    gModulesLoading = True
    if isManiMode():
        """ Mani mode is active, assign the singelton and execute mani settings """
        ma = Admin_mani()
        es.dbgmsg(0, '[eXtensible Admin] Executing mani_server.cfg...')
        ma.loadVariables()
        es.server.cmd('es_xmexec mani_server.cfg')
        ma.hookAuthProvider()
    
    """ Executing and updating the main configurations """    
    es.dbgmsg(0, '[eXtensible Admin] Third loading part...')
    es.dbgmsg(0, '[eXtensible Admin] Executing xa.cfg...')
    gMainConfig.execute()
    es.dbgmsg(0, '[eXtensible Admin] Executing xamodules.cfg...')
    setting.executeConfiguration(None)
    es.dbgmsg(0, '[eXtensible Admin] Updating xamodules.cfg...')
    setting.writeConfiguration(None)
    
    """ Remove any expired settings so we clear up old unused data """
    es.dbgmsg(0, '[eXtensible Admin] Removing any expired settings')
    gSettingExpireManager = {}
    gSettingPath = os.path.join(coredir(), "data", "settings_expire.db")
    if os.path.exists(gSettingPath):
        pathStream = open(gSettingPath, 'r')
        gSettingExpireManager = cPickle.load(pathStream)
        pathStream.close()
        if es.ServerVar('eventscripts_currentmap') != "":
            checkExpiredSettings()
    es.dbgmsg(0, '[eXtensible Admin] Finished loading')

def unload():
    """
    Executed when this module is unloaded. Ensure that we clear up everything
    and unload all other dependancies.
    """
    global gMainMenu
    global gMainCommand
    es.dbgmsg(0, '[eXtensible Admin] Begin unloading...')
    
    """ Unload all sub modules """
    for module in sorted(gModules.values(), lambda x, y: cmp(x.required, y.required)*-1):
        for command in module.subCommands:
            module.subCommands[command].unregister(['console', 'say'])
        for menu in module.subMenus:
            module.subMenus[menu].unregister()
        es.dbgmsg(0, '[eXtensible Admin] Unloading module "%s"' % module.name)
        module.unload()
        
    """ Delete all the main menus which aren't cleared up by deconstructors of XA modules """
    for menu in gMainMenu:
        if popuplib.exists(str(menu)):
            menu.delete()
            
    """ Remove the main command  """
    if gMainCommand:
        gMainCommand.unregister(['server', 'console', 'say'])
        del gMainCommand
    es.dbgmsg(0, '[eXtensible Admin] Finished unloading sequence')
    es.dbgmsg(0, '[eXtensible Admin] Modules will now unregister themself...')

# ==============================================================================
#    Expire Settings Manage
# ==============================================================================

def es_map_start(event_var):
    """
    Executed when the map loads. Check for any expired settings
    
    @param SourceEventVariables event_var An instance containing access to event variables
    """
    checkExpiredSettings()
    
def player_activate(event_var):
    """
    Executed when a player is activated on the server. Add them to the setting
    expire manager and update their last connected times, then save the global
    database.
    
    @param SourceEventVariables event_var An instance containing access to event variables
    """
    gSettingExpireManager[playerlib.uniqueid(event_var['userid'], True)] = time.time()
    saveSettingExpiredManager()

def checkExpiredSettings():
    """
    This function iterates through the global setting expire manager dictionary
    and tests everybodies last active time to the current time. If the time since
    last connection is greater than the setting decided to clear, then we shall
    remove any inactive people. Finally save the database to commit changes.
    """
    steamidsToRemove = []
    for steamid, lastConnected in gSettingExpireManager.iteritems():
        if (time.time() - lastConnected) / 86400 >= gCoreVariables['setting_expiry_days']:
            steamidsToRemove.append(steamid)
    for steamid in steamidsToRemove:
        del gSettingExpireManager[steamid]
        playerdata.clearUsersSettings(steamid)
    saveSettingExpiredManager()

def saveSettingExpiredManager():
    """
    Commits the database to file so it saves any alterations to disk to be loaded
    next time we load the file.
    """
    fileStream = open(gSettingPath, 'w')
    cPickle.dump(gSettingExpireManager, fileStream)
    fileStream.close()

# ==============================================================================
#   SERVER COMMANDS
# ==============================================================================

def command(userid, args):
    """
    This is the global xa command. We want to test for the first argument as
    any sub commands. The reason we shall do this is that we only need to
    register 1 command, and we also have more control about how we sub categorize
    things etc.
    
    @param int userid The ID of the user (if any) who executed the command
    @param mixed args Any additional arguments
    """
    if userid > 0:
        return sendMenu()
    else:
        argc = len(args)
        subcmd = (args[0].lower() if argc else None)
        seccmd = (args[1] if argc > 1 else None)
        
    if subcmd == 'load':
        """ Load another module, pass the third argument as the module id """
        if seccmd:
            xa_load(seccmd)
        else:
            es.dbgmsg(0, 'Syntax: xa load <module-name>')
            
    elif subcmd == 'unload':
        """ Unload another module, pass the third argument as the module id """
        if seccmd:
            xa_unload(seccmd)
        else:
            es.dbgmsg(0, 'Syntax: xa unload <module-name>')
            
    elif subcmd == 'reload':
        """ Reloads another module, pass the third argument as the module id """
        if seccmd:
            xa_reload(seccmd)
        else:
            es.dbgmsg(0, 'Syntax: xa reload <module-name>')
            
    elif subcmd == 'send':
        """ Sends the XA menu to a user, pass the third argument as the User ID """
        if seccmd:
            sendMenu(seccmd)
        else:
            es.dbgmsg(0, 'Syntax: xa send <userid>')
            
    elif subcmd == 'help':
        """
        Requested help, send the description about any additional arguments. Loop
        through all loaded modules to see if any of the arguments are any of the
        loaded variables, commands or modules. If so, send the description about
        that object. Otherwise, send them a global list of ommands and variables.
        """
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
        """
        Requested permissions, print out a list of permissions in alphabetical
        order and sorted so they are arranged.
        """
        permissions = []
        if seccmd:
            userid = int(es.getuserid(seccmd))
        else:
            userid = None
        if userid:
            permissions.append(['Module', 'Capability', 'Level', 'Type', 'Name', 'Granted'])
        else:
            permissions.append(['Module', 'Capability', 'Level', 'Type', 'Name'])
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
        es.dbgmsg(0,'---------- List of capabilities:')
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
        """
        Send stats about amount of calls for modules in console. 
        """
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
        """
        Print a list of loaded modules in console and details about them.
        """
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
            es.dbgmsg(0, 'For more details, supply list level (0-2):')
            es.dbgmsg(0, 'Syntax: xa module list [level]')
        es.dbgmsg(0,'----------')
        
    elif subcmd == 'info':
        """
        Prints out information for a particular module in console.
        """
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
