# ./addons/eventscripts/examples/auth/ini_tree_auth/ini_tree_auth.py

import cfglib
import cmdlib
import es
import keyvalues
import os
import services
import services.auth


_gamedir = es.ServerVar('eventscripts_gamedir') # We use this variable a few times


class IniTreeAuth(services.auth.AuthorizationService):
   """ Primary class that determines authorization """
   clients_path = _gamedir + '/cfg/mani_admin_plugin/clients.txt'
   auth_path    = es.getAddonPath('examples/auth/ini_tree_auth') + '/'
   name = 'ini_tree_auth'

   def __init__(self):
      # Create ini
      ini_path = _gamedir + '/cfg/ini_tree_auth.ini'
      ini = cfglib.AddonINI(ini_path)
      ini.unrepr = False # Quotes around strings in this case would be confusing since we only use = True or = False
      ini.indent_type = '    ' # Indention makes the ini much easier to read

      # Some comments and groups we need to enforce
      ini.setInitialComments(['./cfg/ini_tree_auth.ini', 'Use the space below to add players to ini_tree_auth', 'For more information see: http://www.eventscripts.com/pages/ini_tree_auth'])
      ini.addGroup('ROOT')
      ini.setGroupComments('ROOT', ['This group is usually reserved for server owners as players at level will be authorized for everything.'])
      ini.addGroup('ADMIN')
      ini.setGroupComments('ADMIN', ['This group is for players who should be allowed to use admin commands (kick, ban, etc.)'])
      ini.addGroup('POWERUSER')
      ini.setGroupComments('POWERUSER', ['This group is for players who should receive some special privileges (clan members, etc.)'])
      ini.addGroup('NOGROUP')
      ini.setGroupComments('NOGROUP', ['This group is for players who are authorized only for specific capabilities'])

      # If the file doesn't exist we give admin power to STEAM_ID_LAN
      if not os.path.isfile(ini_path):
         ini['ADMIN']['STEAM_ID_LAN'] = {}

      # Write any changes we made
      ini.write()
      self.ini_file = ini

      # Get client groups and capabilities from the ini
      self.capabilities = {}

      # Store each client's group by offline identifier
      self.clients = {}
      for group in ini:
         inigroup = ini[group]
         for steamid in inigroup:
            for s in inigroup[steamid]:
               # Register Mani flags they are available without being registered
               if s.startswith('mani_flag_'):
                  self.capabilities[s] = 'ROOT'
                  self.clients[steamid] = 'ROOT'
               else:
                  self.clients[steamid] = group.upper()

      cmdlib.registerServerCommand('initreeauth_importmani', self._importManiClients,
       'This command imports clients from ./cfg/mani_admin_plugin/clients.txt into ini_tree_auth.')

   def registerCapability(self, auth_capability, auth_recommendedlevel):
      self.capabilities[auth_capability] = auth_recommendedlevel

   def isUseridAuthorized(self, auth_userid, auth_capability):
      return self.isIdAuthorized(self.getOfflineIdentifier(auth_userid), auth_capability)

   def getOfflineIdentifier(self, auth_userid):
      s = es.getplayersteamid(int(auth_userid))
      if s is None:
         raise KeyError, 'Userid %s is not online.' % auth_userid
      return s

   def isIdAuthorized(self, auth_identifier, auth_capability):
      # No capability, no authorization
      if auth_capability not in self.capabilities:
         return False

      # If capability is unresitricted we allow anyone
      if self.capabilities[auth_capability] == self.UNRESTRICTED:
         return True

      # If capability only requires a valid SteamID we just have to test the identifier against STEAM_ID_PENDING
      if self.capabilities[auth_capability] == self.IDENTIFIED and auth_identifier != 'STEAM_ID_PENDING':
         return True

      # If identifier is not found, no authorization
      if auth_identifier not in self.clients:
         return False

      # If the client has the specific capabiltity they are authorized
      capability_dict = self.ini_file[self.clients[auth_identifier]][auth_identifier]
      if auth_capability in capability_dict:
         # If the capability is explicitly denied the player is not authorized
         if capability_dict[auth_capability].lower() in ('false', '0'):
            return False
         return True

      # Authorize clients who get the capability due to group level
      if (self.clients[auth_identifier] in ('ROOT', 'ADMIN', 'POWERUSER', 'IDENTIFIED', 'UNRESTRICTED') and
       self.__getattribute__(self.clients[auth_identifier]) <= self.capabilities[auth_capability]):
         return True

      # No more options for auth so the player is not authorized
      return False

   def _importManiClients(self, args):
      # No clients, nothing to import
      if not os.path.isfile(self.clients_path):
         raise IOError, 'ini_tree_auth: Cannot find ./cfg/mani_admin_plugin/clients.txt to import Mani clients'

      """ Gather the contents of Mani's clients.txt"""
      # Remove Unicode characters from clients.txt
      nf = open(self.auth_path + 'clients.txt', 'wb')
      of = open(self.clients_path, 'rb')
      nf.write(filter(lambda x: ord(x) <= 127, of.read()))
      of.close()
      nf.close()

      # Load the new clients.txt and then remove it
      clientdata = keyvalues.KeyValues('clients.txt')
      clientdata.load(self.auth_path + 'clients.txt')
      os.remove(self.auth_path + 'clients.txt')

      if 'players' not in clientdata:
         raise KeyError, 'clients.txt has no "players" section'

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
               ini_tree_auth.registerCapability('mani_flag_' + f, self.ROOT)
            for s in steamid:
               group = 'ADMIN' if 'admin' in flagset else 'POWERUSER'
               for f in flagset:
                  if s not in self.ini_file[group]:
                     self.ini_file[group][s] = {}
                  self.ini_file[group][s]['mani_flag_' + f] = 'True'

      # Write the newly imported clients to the ini
      self.ini_file.write()

# Register IniAuth with services as the auth provider
ini_tree_auth = IniTreeAuth()
services.register("auth", ini_tree_auth)


def unload():
  services.unregister("auth")
  cmdlib.unregisterServerCommand('initreeauth_importmani')