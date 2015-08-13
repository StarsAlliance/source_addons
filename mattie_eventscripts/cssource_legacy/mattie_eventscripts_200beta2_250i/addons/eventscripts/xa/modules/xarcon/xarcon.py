# ./xa/modules/xarcon/xarcon.py

import es
from xa import xa

#plugin information
info = es.AddonInfo() 
info.name     = "Admin rcon" 
info.version  = "1.0" 
info.author   = "McFly"
info.basename = "xarcon"

#######################################
# MODULE SETUP
# Register the module
# this is a global reference to our module
xarcon = xa.register(info.basename)


#######################################
# GLOBALS
# We initialize our general global data here.

list_round_rcon = []
list_map_rcon = []


#######################################
# LOAD AND UNLOAD
# Formal system registration and unregistration
def load():
    """Registers the xarcon commands"""
    xarcon.addCommand('xa_rcon', rcon_cmd, 'use_rcon', 'ROOT', "Appends the command to the end of the queue of server commands to execute").register(('say', 'console'))
    xarcon.addCommand('xa_rcon_round', rcon_round_cmd, 'use_rcon', 'ROOT', "Appends the command to the end of the queue of server commands to execute next round").register(('say', 'console'))
    xarcon.addCommand('xa_rcon_map', rcon_map_cmd, 'use_rcon', 'ROOT', "Appends the command to the end of the queue of server commands to execute next map").register(('say', 'console'))


def unload():
    """Unregisters the module with XA"""
    xarcon.unregister()


#######################################
# MODULE FUNCTIONS
# Register your module's functions

def es_map_start(event_var):
    """Executes all xarcon_map commands"""
    global list_map_rcon

    for str_item in list_map_rcon:
        es.server.queuecmd(str_item)
    list_map_rcon[:] = []


def round_start(event_var):
    """Executes all xarcon_round commands"""
    global list_round_rcon

    for str_item in list_round_rcon:
        es.server.queuecmd(str_item)
    list_round_rcon[:] = []


def rcon_cmd():
    """Appends the command to the end of the queue of server commands to execute"""
    es.server.queuecmd(es.getargs())


def rcon_round_cmd():
    """Appends the command to the end of the queue of server commands to execute next round"""
    list_round_rcon.append(es.getargs())


def rcon_map_cmd():
    """Appends the command to the end of the queue of server commands to execute next map"""
    list_map_rcon.append(es.getargs())
