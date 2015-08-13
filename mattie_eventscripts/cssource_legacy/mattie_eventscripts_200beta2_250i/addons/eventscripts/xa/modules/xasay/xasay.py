import es
import playerlib
from xa import xa


#######################################
# ADDON INFORMATION
# This describes the XA module
info = es.AddonInfo()
info.name           = "Say"
info.version        = "0.2"
info.author         = "Mattie"
info.basename       = "xasay"


#######################################
# MODULE SETUP
# Register the module
# this is a global reference to your module
xasay = xa.register(info.basename)


#######################################
# SERVER VARIABLES
# The list of our my server variables
say_admin_prefix = xasay.setting.createVariable('say_admin_prefix', '@', "Prefix for admin chat")
say_admin_soundfile = xasay.setting.createVariable('say_admin_soundfile', 'ui/buttonclick.wav', "Determines the sound played with an admin say.")
# normal admin say
# normal

#######################################
# GLOBALS
# Initialize our general global data here.
# Localization helper:
text = xasay.language.getLanguage()
tree = None

#######################################
# LOAD AND UNLOAD
# Formal system registration and unregistration
def load():
    global tree, auth
    tree = PrefixCompletionTree()
    if not saywatcher in es.addons.SayListeners:
        es.addons.registerSayFilter(saywatcher)

    playerlib.registerPlayerListFilter("admin_say", admin_say_filter)
    xasay.registerSayPrefix(str(say_admin_prefix), _admin_say, "admin_say", "ADMIN")
    # ..
    # ..


def unload():
    if saywatcher in es.addons.SayListeners:
        es.addons.unregisterSayFilter(saywatcher)
    playerlib.unregisterPlayerListFilter("#admin_say")
    # Unregister the module
    xasay.unregister()


#######################################
# CLASSES
# Below are the classes needed for this module

    
#######################################
# MODULE FUNCTIONS
# Register your

def saywatcher(userid, message, teamonly):
  global tree
  output = message
  # strip quotes if at beginning and end of string
  if output[0] == output[-1:] == '"':
      output = output[1:-1]
  # search for the prefix in our prefix tree
  word, func, cap = tree.find(output, False)
  if func:
    text = output[len(word):]
    # we need check if they're authorized for a protected prefix
    if cap:
      if xasay.isUseridAuthorized(userid, cap):
        return func(userid, text, teamonly)
      else:
        # unauthorized, just do nothing
        return (userid, message, teamonly)
    else:
        # no capability required, just do it
        return func(userid, text, teamonly)
  else:
    # no prefix, just do nothing
    return (userid, message, teamonly)

# function to allow people to register their own say filter replacements
def registerSayPrefix(module, prefix, command, capability=None, defaultlevel=None):
  '''
  Allows you to register a prefix string for say commands and a callback.
  Callbacks functions much match a normal say filter. For example:
    def my_admin_say(userid, message, teamonly):
  and it must return a 3-piece tuple of the same order:
    return (userid, message, teamonly)
  If userid 0 is provided as part of the return, the say text will be eaten.
  If you provide a capability the filter requires the user be authorized
  for that capability.
  If you provide a defaultlevel and capability, this command will register
  that capability with the auth service.
  '''
  if defaultlevel and capability:
    xasay.registerCapability(capability, defaultlevel)
  tree.insert(prefix, command, capability)

# player filter for those with the permissions for admin_say
def admin_say_filter(x):
    if xasay.isUseridAuthorized(int(x), "admin_say"):
      return True
    return False

def play_admin_say_sound(userid=None):
  '''
  Used to play the admin message sound for everyone to hear.
  '''
  if str(say_admin_soundfile):
    if userid:
      es.playsound(userid, str(say_admin_soundfile), 1)
    else:
      for p in playerlib.getPlayerList():
        es.playsound(int(p), str(say_admin_soundfile), 1)

def _admin_say(userid, message, teamonly):
  tokens = {}
  tokens['username'] = es.getplayername(userid)
  tokens['message']   = message
  if teamonly:
    admins = playerlib.getPlayerList("#admin_say")
    for j in admins:
      #  "#green[Admin Only]#lightgreen $username: #default$message" % (es.getplayername(userid), message)
      es.tell(int(j), "#multi", text("admin only message", tokens))
      play_admin_say_sound(int(j))
  else:
    es.msg("#multi", text("admin say message", tokens))
    play_admin_say_sound()
  # kill the message
  return (0, "", 0)

# ignore everything below this line for now.
class Node:
    def __init__(self, char):
        self.children = {}
        self.char     = char
        self.word     = None
        self.func     = None
        self.capability = None

class PrefixCompletionTree:
    def __init__(self, case_sensitive = True):
        self.root           = Node("0")

    ## Inserts the given string into the tree.
    def insert(self, string, command, capabilitystring):
        path = string

        # Walk through all chars and add each into the tree.
        node = self.root
        for char in path:
            node = self._insert(node, char)
        node.word = string
        node.func = command
        node.capability = capabilitystring

    # Inserts the given char at the given root position.
    # If root is None a new node is returned.
    # Returns the newly inserted node.
    def _insert(self, root, char):
        if not root:
            raise AssertionError
        if not char:
            raise AssertionError
        if not root.children.has_key(char):
            root.children[char] = Node(char)
        return root.children[char]

    ## Finds the given string in the tree.
    ## If exact_match is True (default):
    ##    This function returns the given string if a match
    ##    was found, None otherwise.
    ## If exact_match is False:
    ##    This function returns the given string if an exact match was found.
    ##    Otherwise, it returns a string that starts with the given string.
    ##    If multiple strings start with the given string, this function
    ##    returns the first one alphabetically.
    def find(self, string, exact_match = True):
        if string == None or string == "":
            raise AssertionError

        path = str.lower(string)

        # Ascend up the tree until we find a match or a leaf.
        node = self.root
        for char in path:
            if not node.children.has_key(char):
                # if we're at the end of a prefix, return that
                if node.word is not None:
                  return (node.word, node.func, node.capability)
                else:
                  return (None, None, None)
            node = node.children[char]

        # Now that we point to the node that corresponds with the string,
        # check whether it is in exact match.
        if node.word == string:
            return (string, node.func, node.capability)
        if exact_match == True:
            return (None, None, None)

        # Ascend up the tree until a complete word is found.
        while node.word == None:
            keys = node.children.keys()
            keys.sort()
            node = node.children[keys[0]]
        return (node.word, node.func, node.capability)

