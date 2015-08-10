# ./xa/modules/xaprefixexec/xaprefixexec.py

import es
import os
from xa import xa

"""
Executes ./cfg/xa/xaprefixexec/<map prefix>.cfg every map
"""

#plugin information
info = es.AddonInfo() 
info.name     = "Map Prefix cfg" 
info.version  = "1.1" 
info.author   = "Unknown"
info.basename = "xaprefixexec"

#######################################
# MODULE SETUP
# Register the module
# this is a global reference to our module
xaprefixexec = xa.register(info.basename)


#######################################
# GLOBALS
# Initialize our general global data here.

str_dir = None # Directory of the .cfg files


#######################################
# LOAD AND UNLOAD
# Formal system registration and unregistration

def load():
    """
    Ensures the .cfg directories exist
    Loads the path to the .cfg directory in str_dir
    """
    global str_dir

    # Ensures .cfg directories exist
    str_dir = xa.gamedir() + '/cfg/xa'
    _check_directory(str_dir)
    str_dir += '/prefixexec'
    _check_directory(str_dir)
    
    """ If XA is loaded whilst a map is loaded, run the map start event """
    mapName = str(es.ServerVar('eventscripts_currentmap'))
    if mapName != "":
        es_map_start({'mapname':mapName})


def unload():
    # Unregister the module
    xaprefixexec.unregister()


#######################################
# MODULE FUNCTIONS
# Register your module's functions

def es_map_start(event_var):
    """Executes ./cfg/xa/prefixexec/<map prefix>.cfg"""
    str_mapname = event_var['mapname']
    if '_' in str_mapname: # No prefix, no .cfg
        str_prefix = str_mapname.split('_')[0]
        if os.path.isfile(str_dir + '/%s.cfg' % str_prefix):
            es.server.queuecmd('es_xmexec xa/prefixexec/%s.cfg' % str_prefix)
            xaprefixexec.logging.log("xa/prefixexec/%s.cfg executed due to map prefix %s" % (str_prefix, str_prefix) )


def _check_directory(str_dir):
    """Creates the directory if it doesn't exist"""
    if not os.path.isdir(str_dir):
        os.mkdir(str_dir)
