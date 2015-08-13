import es
import time
import cfglib
import xa

import psyco
psyco.full()

###########################
#Module methods start here#
########################################################
# All methods that should be able to be called through #
# the API need to have "module" as first parameter     #
########################################################
def createVariable(module, variable, defaultvalue=0, description=""):
    if xa.exists(module):
        module = xa.find(module)
        variable = getVariableName(module, variable)
        if variable:
            module.variables[variable] = es.ServerVar(variable, defaultvalue, description)
            module.variables[variable]._def = defaultvalue
            module.variables[variable]._descr = description
            return module.variables[variable]
    return False

def deleteVariable(module, variable):
    if xa.exists(module):
        module = xa.find(module)
        variable = getVariableName(module, variable)
        if variable and getVariable(module, variable):
            es.set(variable, '', '')
            del module.variables[variable]

def getVariable(module, variable):
    if xa.exists(module):
        module = xa.find(module)
        variable = getVariableName(module, variable)
        if variable in module.variables:
            return module.variables[variable]
    return False

def getVariableName(module, variable = None):
    if str(variable).startswith('xa_'):
        variable = str(variable)[3:]
    if es.exists("variable", "mani_%s" % variable):
        variable = ("mani_%s" % variable)
    else:
        variable = ("xa_%s" % variable)
    return variable

def getVariables(module = None, submodule = None):
    varlist = []
    if submodule:
        module = submodule
    if xa.exists(module):
        module = xa.find(module)
        for variable in sorted(module.variables):
            varlist.append(module.variables[variable])
    else:
        for module in sorted(xa.modules()):
            module = xa.find(module)
            for variable in sorted(module.variables):
                varlist.append(module.variables[variable])
    return varlist
    
def writeConfiguration(module = None):
    config = cfglib.AddonCFG("%s/cfg/xamodules.cfg" % xa.gamedir())
    config.text('******************************')
    config.text('  XA Module Configuration', True)
    config.text('  Timestamp: %s' % time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))
    config.text('******************************')
    for module in sorted(xa.modules()):
        module = xa.find(module)
        if module.variables:
            config.text('')
            config.text('******************************')
            config.text('  Module: %s' % (module.name if module.name else module))
            config.text('******************************')
            for variable in sorted(module.variables):
                variable = module.variables[variable]
                if variable.getName().replace('_', '').isalnum():
                    config.cvar(variable.getName(), variable._def, variable._descr)
    config.write()

def executeConfiguration(module = None):
    config = cfglib.AddonCFG("%s/cfg/xamodules.cfg" % xa.gamedir())
    config.execute()
