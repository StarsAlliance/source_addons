# ==============================================================================
#   IMPORTS
# ==============================================================================
# Python Imports
import time

# EventScripts Imports
import es
import cfglib
import xa

# ==============================================================================
#   HELPER CLASSES
# ==============================================================================
class Command(object):
    def __init__(self, commandName, description, usage):
        self.name           = commandName
        self.description    = description
        self.usage          = usage

# ==============================================================================
#   MODULE API FUNCTIONS
# ==============================================================================
def createVariable(module, variable, defaultvalue=0, description=''):
    """
        Create a server variable
        
        module:         module name (usually automatically provided)
        variable:       the name of the cvar
        defaultvalue:   default value
        description:    text description of the cvar
        
        return:         (bool) true (false if module does not exist)
    """
    # Does the module exist?
    if xa.exists(module):
        # Find the module instance
        module = xa.find(module)
        
        # Get the variable name
        variable = getVariableName(module, variable)
        
        # Did we get a valid variable name?
        if variable:
            # Setup the variable
            module.variables[variable] = es.ServerVar(variable, defaultvalue, description)
            module.variables[variable]._def = defaultvalue
            module.variables[variable]._descr = description
            
            # Return our new variable instance
            return module.variables[variable]
    
    # Fallback, variable creation failed
    return False
    
def createCommandSpace(module, command, usage='', description=''):
    """
        Create a server command section in the cfg
        
        module:         module name (usually automatically provided)
        command:        the command
        usage:          usually a longer section of text describing usage
        description:    text description of the command
        
        return:         (bool) true (false if module does not exist)
    """
    # ensure the module exists
    if xa.exists(module):
        # Find the module instance
        module = xa.find(module)
        
        # Store the command instance into the module's command attribute 
        module.commands[command] = Command(command, description, usage)
        return True
    return False

def deleteVariable(module, variable):
    """
        Delete a variable
        
        module:         module name (usually automatically provided)
        variable:       the name of the cvar to delete
        
        return:         (bool) true (false if variable/module does not exist)
    """
    # Does the module exist?
    if xa.exists(module):
        # Find the module instance
        module = xa.find(module)
        
        # Get the variable name
        variable = getVariableName(module, variable)
        
        # Did we get a valid variable name and does the variable exist?
        if variable and getVariable(module, variable):
            # Reset the variable
            es.set(variable, '', '')
            
            # Remove the variable from our module
            del module.variables[variable]
            
            return True
    return False

def getVariable(module, variable):
    """
        Retrieve a ServerVar reference to variable
        
        module:         module name (usually automatically provided)
        variable:       the name of the cvar to retrieve
        
        return:         ServerVar instance (False if no variable or module)
    """
    # Does the module exist?
    if xa.exists(module):
        # Find the module instance
        module = xa.find(module)
        
        # Get the variable name
        variable = getVariableName(module, variable)
        
        # Did we get a valid variable name and is the variable assigned to our module?
        if variable in module.variables:
            # Return our existing variable instance
            return module.variables[variable]

    # Fallback, couldn't find variable instance
    return False

def getVariableName(module, variable):
    """
        Retrieve the name of a variable that XA registered (with the xa_ prefix)
        
        module:         module name (usually automatically provided)
        variable:       the name of the cvar name to retrieve
        
        return:         str variable name
    
    """
    # xa_ prefix should not be used inside variable names
    if str(variable).startswith('xa_'):
        variable = str(variable)[3:]
    
    # Is there a Mani version of our variable?
    if es.exists('variable', 'mani_%s' % variable):
        # Return the Mani version of our variable
        return 'mani_%s' % variable
    
    # Return the XA version of our variable
    return 'xa_%s' % variable

def getVariables(module, submodule = None):
    """
        Retrieve a list of the variables registered to a module
        
        module:         module name (usually automatically provided)
        submodule:      used to specify another module to retrieve variables from
        
        return:         list of ServerVar instances
        
        Because of how this is used you usually call:
          <xa instance>.settings.getVariables()
        to retrieve your own module's variables. And:
          <xa instance>.settings.getVariables("othermodule")
        to retrieve another modules variables.
    
    """
    # Return variable
    varlist = []
    
    # Do we want to get the list of another module?
    if submodule:
        module = submodule
    
    # Does our module exist?
    if xa.exists(module):
        # Find the module instance
        module = xa.find(module)
        
        # Fill our variable list
        for variable in sorted(module.variables):
            varlist.append(module.variables[variable])
        
    else:
        # No, we just return a variable list of all modules
        for module in sorted(xa.modules()):
            # Find the module instance
            module = xa.find(module)
            
            # Fill our variable list
            for variable in sorted(module.variables):
                varlist.append(module.variables[variable])
    
    # Return our variable list
    return varlist

def writeConfiguration(module):
    """
        Uses Cfglib to write module configuration to disk
        
        module:         module name (usually automatically provided)
        
        return:         nothing
        
    """
    # Write our configuration to disk using cfglib
    config = cfglib.AddonCFG('%s/cfg/xamodules.cfg' % xa.gamedir())
    config.text('******************************')
    config.text('  XA Module Configuration', True)
    config.text('  Timestamp: %s' % time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime()))
    config.text('******************************')
    
    # Loop through all modules
    for module in sorted(xa.modules()):
        # Find the module instance
        module = xa.find(module)
        
        # Does the module have variables?
        if module.variables:
            # Add the module to the AddonCFG instance
            config.text('')
            config.text('******************************')
            config.text('  Module: %s' % (module.name if module.name else module))
            config.text('******************************')
            
            # Loop through all variables of the module
            for variable in sorted(module.variables):
                # Get the variable instance
                variable = module.variables[variable]
                
                # Is this a valid variable name?
                if variable.getName().replace('_', '').isalnum():
                    # Add our variable to the AddonCFG instance
                    config.cvar(variable.getName(), variable._def, variable._descr)
            
            # Loop through all commands of the module
            for command in sorted(module.commands):
                config.text('')
                config.text(module.commands[command].usage)
                config.text(module.commands[command].description)
                config.text("Insert commands below the lines")
                config.text('-' * 77)
                config.command(command)
                config.text('-' * 77)
    
    # Finally write the file to disk
    config.write()

def executeConfiguration(module):
    """
        Uses Cfglib to execute a modules cfg file
        
        module:         module name (usually automatically provided)
        
        return:         nothing

    """
    # Execute our configuration using cfglib
    config = cfglib.AddonCFG('%s/cfg/xamodules.cfg' % xa.gamedir())
    config.execute()
