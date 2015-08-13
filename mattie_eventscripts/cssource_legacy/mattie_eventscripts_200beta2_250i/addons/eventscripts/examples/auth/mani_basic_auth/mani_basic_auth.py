# ./addons/eventscripts/examples/auth/mani_basic_auth/mani_basic_auth.py

import es
import keyvalues
import os
import services
import services.auth

import psyco
psyco.full()


class ManiAuthService(services.auth.AuthorizationService):
  clientspath = es.ServerVar('eventscripts_gamedir') + '/cfg/mani_admin_plugin/clients.txt'

  def __init__(self):
    self.defaultlevels = {}
    self.name = "mani_basic_auth"
    self.clients = {}
    self.refreshClients()

  def registerCapability(self, auth_capability, auth_recommendedlevel):
    self.defaultlevels[auth_capability] = int(auth_recommendedlevel)

  def isUseridAuthorized(self, auth_userid, auth_capability):
    user = self.getOfflineIdentifier(auth_userid)
    data = self.isIdAuthorized(user, auth_capability)
    return data

  def getOfflineIdentifier(self, auth_userid):
    s = es.getplayersteamid(int(auth_userid))
    if s is None:
      raise KeyError, 'Userid %s is not online.' % auth_userid
    return s

  def isIdAuthorized(self, auth_identifier, auth_capability):
    if auth_identifier is None:
      return False

    # if it's not registered, no way!
    if auth_capability not in self.defaultlevels:
      return False

    # If the client has the capability they are allowed
    if auth_identifier in self.clients and auth_capability in self.clients[auth_identifier]:
      return True

    level = self.defaultlevels[auth_capability]
    # Allow it if unrestricted
    if level >= self.UNRESTRICTED:
      return True

    # If they have to be identified, require that their steamid is ready.
    if level >= self.IDENTIFIED and str(auth_identifier) != "STEAM_ID_PENDING":
      return True

    # If they have to be an admin, check for the mani_flag_admin capability
    if level >= self.ADMIN and auth_identifier in self.clients and 'mani_flag_admin' in self.clients[auth_identifier]:
      return True

    # No way, Jose
    return False

  def refreshClients(self):
    # Get client list
    path = self._convertClientsFile(self.clientspath)
    clientdata = keyvalues.KeyValues('clients.txt')
    clientdata.load(path)
    os.remove(path)

    if 'players' not in clientdata:
      raise KeyError, 'clients.txt has no "players" section'
    self.clients.clear()

    # Parse the client data
    clientplayers = clientdata['players']
    for player in clientplayers:
      steamid = []
      flags   = []
      for attr in player:
        attr_name = attr.getName()
        # Snag SteamIDs for this player
        if attr_name == 'steam':
          player_steam = attr.getString()
          if player_steam:
            steamid += [player_steam]
          else:
            steamid += [x.getString() for x in attr]

        # Add the flags of groups this player belongs to
        elif attr_name in clientdata:
          group = clientdata[attr_name]
          player_group = attr.getString()
          if player_group:
            player_group = (attr,)
          else:
            player_group = attr
          for x in player_group:
            group_name = x.getString() if isinstance(player_group, tuple) else x.getName()
            for y in group:
              if y.getName() == group_name:
                flag_string = y.getString()
                if flag_string:
                  flags += y.getString().split()
                else:
                  for z in y:
                    if z.getName() == x.getString():
                      flags += z.getString().split()

        # Add individual flags
        elif attr_name == 'flags':
          player_flags = attr.getString()
          if not player_flags:
            player_flags = ' '.join([x.getString() for x in attr])
          flags += player_flags.split()

      # Put player in clients dictionary with respective flags
      if steamid and flags:
        # Making the flag list a set ensures each flag is only present once
        flagset = set(flags)
        # All flags are registered to capabilities at the ROOT level so admins aren't authed for flags they don't have
        for f in flagset:
          self.registerCapability('mani_flag_' + f, self.ROOT)
        for s in steamid:
          self.clients[s] = flagset

  @staticmethod
  def _convertClientsFile(path):
    """ Opens the original clients.txt, removes unicode characters, and saves the result as a new file """
    new_path = es.getAddonPath('examples/auth/mani_basic_auth') + '/clients.txt'
    nf = open(new_path, 'wb')
    of = open(path, 'rb')
    nf.write(filter(lambda x: ord(x) <= 127, of.read()))
    of.close()
    nf.close()
    return new_path

  @staticmethod
  def _makeList(value):
    return value if isinstance(value, list) else [value]


mani_auth = ManiAuthService()
services.register("auth", mani_auth)

def unload():
  services.unregister("auth")