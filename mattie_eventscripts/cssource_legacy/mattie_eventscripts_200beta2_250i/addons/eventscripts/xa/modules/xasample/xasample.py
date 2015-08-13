import es
from xa import xa

#######################################
# ADDON INFORMATION
# This describes the XA module
info = es.AddonInfo()
# TODO: Change this to your module's data.  -- TODO
info.name           = "Sample"
info.version        = "0.1"
info.author         = "New Scripter"
info.basename       = "xasample"


#######################################
# MODULE SETUP
# Register the module
# this is a global reference to our module
# TODO: If possible, change all references of mymodule to your new module name
mymodule = xa.register(info.basename)


#######################################
# SERVER VARIABLES
# The list of our server variables
# TODO: Add your own variables              -- TODO
myvariable = mymodule.setting.createVariable('some_variable', 1, "Some variable (1=on, 0=off)")


#######################################
# GLOBALS
# Initialize our general global data here.
# Localization helper:
text = mymodule.language.getLanguage()


#######################################
# LOAD AND UNLOAD
# Formal system registration and unregistration
def load():
    # TODO: Register menu, say, client, or console commands.
    #                                       -- TODO


def unload():
    # Unregister the module
    mymodule.unregister()


#######################################
# MODULE FUNCTIONS
# Register your module's functions
