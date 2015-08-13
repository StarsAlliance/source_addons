import es
import services
import services.auth

def load():
  authlist = es.ServerVar("BASIC_AUTH_ADMIN_LIST", defaultvalue="STEAM_ID_LAN;",description="List of administrators for basic_auth")
  basic_auth = BasicAuthService(authlist)
  services.register("auth", basic_auth)

def unload():
  services.unregister("auth")

class BasicAuthService(services.auth.AuthorizationService):
  def __init__(self, variable):
    self.defaultlevels = {}
    self.adminlist = variable
    self.name = "basic_auth"
    
  def registerCapability(self, auth_capability, auth_recommendedlevel):
    self.defaultlevels[auth_capability] = int(auth_recommendedlevel)
    return
    
  def isUseridAuthorized(self, auth_userid, auth_capability):
    user = self.getOfflineIdentifier(auth_userid)
    data = self.isIdAuthorized(user, auth_capability)
    return data
    
  def getOfflineIdentifier(self, auth_userid):
    s = es.getplayersteamid(int(auth_userid))
    if s is None:
      raise KeyError, "The userid is not online."
    return s
  
  def isIdAuthorized(self, auth_identifier, auth_capability):

    if auth_identifier is None:
      return False

    # Admins always win
    if auth_identifier in str(self.adminlist):
      return True

    # if it's not registered, no way!
    if not self.defaultlevels.has_key(auth_capability):
      return False
      
    level = self.defaultlevels[auth_capability]
    # Allow it if unrestricted
    if  level >= self.UNRESTRICTED:
      return True
      
    # If they have to be identified, require that their steamid is ready.
    if level >= self.IDENTIFIED and str(auth_identifier) != "STEAM_ID_PENDING":
      return True 

    # No way, Jose
    return False
    
