# ./xa/modules/xarestrict/xarestrict.py


import es
import gamethread
import langlib
import os.path
import playerlib
import random
from xa import xa

#plugin information
info = es.AddonInfo()
info.name       = "Restrict Weapons"
info.version    = "1.3"
info.author     = "Unknown"
info.basename   = "xarestrict"

#######################################
# MODULE SETUP
# Register the module
# this is a global reference to our module
xarestrict     = xa.register(info.basename)


#######################################
# SERVER VARIABLES
# The list of our server variables

repickup      = xarestrict.setting.createVariable('restrict_restrict_repickup', '2', 'Number of seconds a weapon will be unavaible for pickup after a restricted player attempts to pick the weapon up')
removebanned  = xarestrict.setting.createVariable('restrict_restrict_removebanned', 1, '0 = no change, 1 = when a player picks up a weapon both team are restricted from the weapon is removed')
cvar_announce = xarestrict.setting.createVariable('restrict_announce', 0, '0 = no change, 1 = players receive a console message when they try to pick up a restricted weapon, 2 = players receive a chat area message when they try to pick up a restricted weapon')


#######################################
# GLOBALS
# Initialize our general global data here.
# Localization helper:
lang_text = xarestrict.language.getLanguage()


###


def getGameData():
   """Returns the eye angle property based on game"""
   game_data = {'cs':('CCSPlayer.m_angEyeAngles[%s]', {'t':2, 'ct':3}, {'deagle':('#all', '#secondary', '#pistol'), 'ak47':('#all', '#primary', '#rifle'), 'scout':('#all', '#primary', '#rifle', '#sniper'), 'aug':('#all', '#primary', '#rifle'), 'g3sg1':('#all', '#primary', '#rifle', '#sniper'), 'galil':('#all', '#primary', '#rifle'), 'famas':('#all', '#primary', '#rifle'), 'm4a1':('#all', '#primary', '#rifle'), 'sg552':('#all', '#primary', '#rifle'), 'sg550':('#all', '#primary', '#rifle', '#sniper'), 'm249':('#all', '#primary'), 'awp':('#all', '#primary', '#rifle', '#sniper'), 'tmp':('#all', '#primary', '#smg'), 'mp5navy':('#all', '#primary', '#smg'), 'glock':('#all', '#secondary', '#pistol'), 'elite':('#all', '#secondary', '#pistol'), 'm3':('#all', '#primary', '#shotgun'), 'xm1014':('#all', '#primary', '#shotgun'), 'usp':('#all', '#secondary', '#pistol'), 'mac10':('#all', '#primary', '#smg'), 'ump45':('#all', '#primary', '#smg'), 'p228':('#all', '#secondary', '#pistol'), 'fiveseven':('#all', '#secondary', '#pistol'), 'p90':('#all', '#primary', '#smg'), 'knife':('#all', '#knife'), 'hegrenade':('#all', '#grenade'), 'flashbang':('#all', '#grenade'), 'smokegrenade':('#all', '#grenade'), 'c4':()}), 'dod':('CDODPlayer.m_angEyeAngles[%s]', {'a':2, 'x':3}, {'30cal':('#all', '#machinegun', '#primary'), 'amerhand':('#all', '#hand'), 'bar':('#all', '#machinegun', '#primary'), 'bazooka':('#all', '#bazooka', '#primary'), 'basebomb':(), 'c96':('#all', '#smg', '#primary'), 'colt':('#all', '#pistol', '#secondary'), 'frag_us':('#all', '#grenade'), 'frag_ger':('#all', '#grenade'), 'garand':('#all', '#rifle', '#primary'), 'k98':('#all', '#rifle', '#primary'), 'k98s':('#all', '#rifle', '#sniper', '#primary'), 'm1carb':('#all', '#rifle', '#primary'), 'mg42':('#all', '#machinegun', '#primary'), 'mp40':('#all', '#smg', '#primary'), 'mp44':('#all', '#smg', '#primary'), 'p38':('#all', '#pistol', '#secondary'), 'punch_ger':('#all', '#grenade'), 'punch_us':('#all', '#grenade'), 'pschreck':('#all', '#bazooka', '#primary'), 'riflegren_ger':('#all', '#grenade'), 'riflegren_us':('#all', '#grenade'), 'smoke_ger':('#all', '#grenade'), 'smoke_us':('#all', '#grenade'), 'spade':('#all', '#hand'), 'spring':('#all', '#rifle', '#sniper', '#primary'), 'stick':('#all', '#grenage'), 'thompson':('#all', '#smg', '#primary')}), 'hl2dm':('CHL2MP_Player.m_angEyeAngles[%s]', {'r':2, 'c':3}, {'357':('#all', '#pistol'), 'alyxgun':('#all', '#pistol'), 'annabelle':('#all', '#shotgun'), 'ar2':('#all', '#smg'), 'brickbat':('#all', '#tool'), 'bugbait':('#all', '#tool'), 'citizenpackage':('#all', '#tool'), 'citizensuitcase':('#all', '#tool'), 'crossbow':('#all', '#sniper'), 'crowbar':('#all', '#hand'), 'extinguisher':('#all', '#tool'), 'frag':('#all', '#grenade'), 'physcannon':('#all', '#tool'), 'physgun':('#all', '#tool'), 'pistol':('#all', '#pistol'), 'rpg':('#all', '#rpg'), 'shotgun':('#all', '#shotgun'),  'slam':('#all', '#hand'), 'smg1':('#all', '#smg'), 'stunstick':('#all', '#hand')})}
   gamename  = es.getgame()

   if game_data.has_key(gamename): return game_data[gamename]

   searchnames = {'Day of Defeat':'dod', 'Deathmatch':'hl2dm'}
   for game in filter(lambda x: x in gamename, searchnames): return game_data[game]

   return game_data['cs']

eyeangle_prop, acceptable_teams, weapon_tags = getGameData()


###


class RestrictedTeam:
   teamnum      = 0
   restrictions = set()
   
   def __init__(self, teamnum):
      self.teamnum      = teamnum
      self.restrictions = set()

   def addRestriction(self, weapon):
      """
      Adds the weapon to the set of restricted weapons
      Calls the removeWeapon function on the RestrictedPlayer instance for each player on the restricted team
      """
      weapon = weapon.replace('weapon_', '')
      if weapon in self.restrictions: return

      self.restrictions.add(weapon)

      for userid in filter(lambda x: es.getplayerteam(x) == self.teamnum if not es.getplayerprop(x, 'CBasePlayer.pl.deadflag') else False, es.getUseridList()):
         getPlayer(userid).removeWeapon(weapon)
      xarestrict.logging.log("Weapon %s has been restricted for team %s" % (weapon, self.teamnum) )

   def removeRestriction(self, weapon):
      """Removes the weapon from the set of restricted weapons"""
      self.restrictions = self.restrictions.difference((weapon.replace('weapon_', ''),))
      xarestrict.logging.log("Weapon %s has been unrestricted for team %s" % (weapon, self.teamnum) )

   def isRestricted(self, weapon):
      """Returns True if the weapon is restricted otherwise returns False"""
      return weapon in self.restrictions

   def joiningPlayer(self, userid):
      """Removes any restricted weapons from the player joining the team"""
      player = getPlayer(userid)

      for weapon in self.restrictions:
         player.removeWeapon(weapon)


restrictedteams = {}


def getTeam(team):
   """Returns a RestrictedTeam instance based on team number"""
   global restrictedteams

   team = int(team)
   if not restrictedteams.has_key(team):
      restrictedteams[team] = RestrictedTeam(team)

   return restrictedteams[team]


def clearTeamRestrictions():
   """Clears the RestrictedTeam instances"""
   restrictedteams.clear()


###


class RestrictedPlayer:
   userid       = 0
   handle       = 0
   restrictions = set()

   def __init__(self, userid):
      self.userid       = userid
      self.handle       = es.getplayerhandle(userid)
      self.restrictions = set()

   def addRestriction(self, weapon):
      """
      Adds the weapon to the set of restricted weapons
      """
      weapon = weapon.replace('weapon_', '')
      if weapon in self.restrictions: return

      self.restrictions.add(weapon)

      self.removeWeapon(weapon)
      xarestrict.logging.log("Weapon %s has been restricted for user %s" % (weapon, es.getplayername(self.userid) ) )

   def removeRestriction(self, weapon):
      """
      Removes the weapon from the set of restricted weapons
      """
      weapon = weapon.replace('weapon_', '')
      if weapon not in self.restrictions: return

      self.restrictions.remove(weapon)
      xarestrict.logging.log("Weapon %s has been unrestricted for user %s" % (weapon, es.getplayername(self.userid) ) )

   def isRestricted(self, weapon):
      """Returns True if the weapon is restricted otherwise returns False"""
      return weapon in self.restrictions or getTeam(es.getplayerteam(self.userid)).isRestricted(weapon)

   def itemPickup(self, weapon):
      """Calls removeWeapon if the picked up weapon is restricted"""
      weapon = weapon.replace('weapon_', '')

      if self.isRestricted(weapon):
         self.removeWeapon(weapon)
   
   def removeWeapon(self, weapon):
      """
      Executes "lastinv" on the client if the weapon to remove is the player's active weapon
      Removes the weapon by index
      Creates a new weapon at the player's feet if necessary
      Announces the restricted pickup
      """
      longname = 'weapon_' + weapon
      xarestrict.logging.log("Weapon %s has been removed from user %s" % (weapon, es.getplayername(self.userid) ) )
      if es.createplayerlist(self.userid)[self.userid]['weapon'] == longname:
         es.cexec(self.userid, 'lastinv')

      for index in es.createentitylist(longname):
         if es.getindexprop(x, 'CBaseEntity.m_hOwnerEntity') <> self.handle: continue

         gamethread.delayedname(0.2, 'saferemove_%s'%index, saferemove, index)

         if (getTeam(2).isRestricted(weapon) and getTeam(3).isRestricted(weapon)) if int(removebanned) else False:
            lastgive = -1

         else:
            eye_angles = tuple(es.getplayerprop(self.userid, eyeangle_prop % x) for x in range(3))
            es.server.cmd('es_xsetang %s 90 0 0' % self.userid)

            es.server.cmd('es_xentcreate %s %s' % (self.userid, longname))
            lastgive = int(es.ServerVar('eventscripts_lastgive'))
            setNPCWeapon(longname)

            es.server.cmd('es_xsetang %s %s %s %s' % ((self.userid,) + eye_angles))

         self.announceRestrictedPickup(weapon, lastgive)

         break

   def announceRestrictedPickup(self, weapon, lastgive=-1):
      """
      Announces to the player the weapon is restricted
      """
      announce = int(cvar_announce)
      if announce == 2:
         es.tell(self.userid, '#multi', lang_text('restricted pick up', {'weapon':weapon}, playerlib.getPlayer(self.userid).get('lang')))
      elif announce:
         es.cexec(self.userid, 'echo ' + self.__removeTags(lang_text('restricted pick up', {'weapon':weapon}, playerlib.getPlayer(self.userid).get('lang'))))

   def __removeTags(self, text):
      """Removes #lightgreen, #green and #default tags from text"""
      return text.replace('#lightgreen', '').replace('#green', '').replace('#default', '')


restrictedplayers = {}


def getPlayer(userid):
   """Returns a RestrictedPlayer instance based on userid"""
   global restrictedplayers

   userid = int(userid)
   if not restrictedplayers.has_key(userid):
      restrictedplayers[userid] = RestrictedPlayer(userid)

   return restrictedplayers[userid]


def removePlayer(userid):
   """Removes RestrictedPlayer instance based on userid"""
   global restrictedplayers

   userid = int(userid)
   if restrictedplayers.has_key(userid):
      del restrictedplayers[userid]


def clearPlayers():
   """Clears RestrictedPlayer instances""" 
   restrictedplayers.clear()


###


class NPCWeapon:
   name        = ''
   activedelay = False

   def __init__(self, name):
      self.name = name

   def createDelay(self):
      """
      Designates all weapons of the desired type as "reserved for NPC"
      """
      self.removeDelay()

      userid = es.getuserid()
      if userid:
         es.server.cmd('es_xfire %s %s addoutput \"spawnflags 2\"' % (userid, self.name))

         self.activedelay = True
         gamethread.delayedname(repickup, 'xarestrict_weapon_%s' % self.name, self._endDelay)
   
   def removeDelay(self):
      """Removes the delay for this NPC weapon"""
      if self.activedelay:
         gamethread.cancelDelayed('xarestrict_weapon_%s' % self.name)

         self._endDelay()

   def _endDelay(self):
      """Marks the weapons as available for player pickup"""
      self.activedelay = False

      userid = es.getuserid()
      if userid:
         es.server.cmd('es_xfire %s %s addoutput \"spawnflags 0\"' % (userid, self.name))


npcweapons = {}


def setNPCWeapon(name):
   """Calls createDelay on a NPCWeapon instance based on weapon name"""
   global npcweapons

   if not npcweapons.has_key(name):
      npcweapons[name] = NPCWeapon(name)

   npcweapons[name].createDelay()


def clearNPCWeapons():
   """
   Calls removeDelay on each NPCWeapon instance
   Clears all NPCWeapon instances
   """
   for name in npcweapons:
      npcweapons[name].removeDelay()

   npcweapons.clear()


###


def getPlayerList(players):
   """Returns a set of RestrictedPlayer or RestrictedTeam instances based on userid or team tag"""
   if isinstance(players, str):
      if players.startswith('@'):
         if players[1:] == 'all':
            players = (getTeam(2), getTeam(3))
         elif acceptable_teams.has_key(players[1:]):
            players = (getTeam(acceptable_teams[players[1:]]),)
         else:
            #bugfix: echo to users console (useful message)
            usermsg.echo("#all",'xarestrict error: invalid tag \"%s\" [command accepts @all, @ct, @t]' % players)
            raise ValueError, 'Invalid team tag \"%s\"' % players

      elif players.startswith('#'):
         if players[1:] == 'all':
            players = es.getUseridList()
         elif acceptable_teams.has_key(players[1:]):
            team    = acceptable_teams[players[1:]]
            players = filter(lambda x: es.getplayerteam(x) == team, es.getUseridList())
         else:
            #bugfix: echo to users console (useful message)
            usermsg.echo("#all",'xarestrict error: invalid tag \"%s\" [command accepts #all, #ct, #t]' % players)
            raise ValueError, 'Invalid team tag \"%s\"' % players

         players = map(getPlayer, players)

      else:
         userid = es.getuserid(players)
         if not userid:
            #bugfix: echo to users console (useful message)
            usermsg.echo("#all",'xarestrict error: invalid player \"%s\" [command accepts partial username, userid or steamid]' % players)
            raise ValueError, 'Invalid player \"%s\"' % players

         players = (getPlayer(userid),)

   elif isinstance(players, (int, float)):
      players = (getPlayer(players),)

   return players


def getWeaponList(weapons):
   """Returns a set of weapons based on weapon name or tag"""
   weaponlist = set()
   for weapon in (weapons,) if isinstance(weapons, str) else weapons:
      if weapon.startswith('#'):
         filtered = filter(lambda x: weapon in weapon_tags[x], weapon_tags)
         if not filtered:
            raise ValueError, 'Invalid weapon type \"%s\"' % weapon

         weaponlist = weaponlist.union(filtered)

      elif weapon_tags.has_key(weapon.replace('weapon_', '')):
         weaponlist = weaponlist.union((weapon,))

      else:
         raise ValueError, 'Invalid weapon or weapon type \"%s\"' % weapon

   return weaponlist


###


def load():
    """ If XA loads late, then call map start by default to reset everythin """
    if (str(es.ServerVar('eventscripts_currentmap')) != ""):
        es_map_start({})

def es_map_start(event_var):
   clearTeamRestrictions()
   clearPlayers()
   clearNPCWeapons()


def round_start(event_var):
   clearNPCWeapons()


def dod_round_start(event_var):
   clearNPCWeapons()


def item_pickup(event_var):
   getPlayer(event_var['userid']).itemPickup(event_var['item'])


def player_team(event_var):
   getTeam(event_var['team']).joiningPlayer(event_var['userid'])


def player_disconnect(event_var):
   removePlayer(event_var['userid'])


def unload():
   """Unregisters the client comand filter"""
   clearNPCWeapons()

   es.addons.unregisterClientCommandFilter(_buy_restrict)

   xarestrict.unregister()


###


def _buy_restrict(userid, args):
   """Client command filter to prevent players from buying restricted weapons"""
   if not args:
      return True
   if args[0].lower() == 'buy' and len(args) > 1:
      player = getPlayer(userid)
      weapon = args[1].lower().replace('weapon_', '')
      if player.isRestricted(weapon):
         xarestrict.logging.log("has been denied the right to buy weapon %s due to restrictions" % weapon, userid)
         player.announceRestrictedPickup(weapon)
         return False

   return True
es.addons.registerClientCommandFilter(_buy_restrict)


###


def saferemove_cmd():
   """
   xa_restrict_saferemove <index>
   """
   if es.getargc() == 2:
      saferemove(es.getargv(1))

   else:
      es.dbgmsg(0, 'Syntax: xa_restrict_saferemove <index>')
xarestrict.addCommand('xa_restrict_saferemove', saferemove_cmd, 'restrict_weapon', 'ADMIN').register('server')


def saferemove(arg_index):
   """Ensures the entity at index arg_index exists before it is removed"""
   if es.createentitylist(arg_index).has_key(int(arg_index)):
      es.server.cmd('es_xremove %s' % arg_index)


###


def removeidle_cmd():
   """
   xa_restrict_removeidle [weapon 1] [weapon 2] ... [weapon n]
   """
   arg_count = es.getargc()
   if arg_count > 1:
      weapons = getWeaponList([es.getargv(x).lower() for x in range(1, arg_count)])
      if not weapons: raise IndexError, 'Invalid weapon list'

      removeidle(weapons)

   else:
      removeidle()
xarestrict.addCommand('xa_restrict_removeidle', removeidle_cmd, 'restrict_weapon', 'ADMIN').register('server')


def removeidle(arg_weapons='#all'):
   """Removes idle weapons of the desired type"""
   arg_weapons = getWeaponList(arg_weapons)
   if not arg_weapons: raise IndexError, 'Invalid weapon list'

   for weapon in arg_weapons:
      for index in filter(lambda x: es.getindexprop(x, 'CBaseEntity.m_hOwnerEntity') == -1, es.createentitylist('weapon_' + weapon)):
         es.server.cmd('es_xremove %s' % index)


###


def xarestrict_cmd():
   """
   xa_restrict <player/team> <weapon 1> [weapon 2] ... [weapon n]
   xa_unrestrict <player/team> <weapon 1> [weapon 2] ... [weapon n]
   """
   arg_count    = es.getargc()
   command_name = es.getargv(0).lower()
   func_command = restrict if command_name == 'xa_restrict' else unrestrict

   if arg_count > 2:
      func_command(es.getargv(1).lower(), [es.getargv(x).lower() for x in range(2, arg_count)])

   else:
      es.dbgmsg(0, 'Syntax: %s <player/team> <weapon 1> [weapon 2] ... [weapon n]' % command_name)
xarestrict.addCommand('xa_restrict', xarestrict_cmd, 'restrict_weapon', 'ADMIN').register(('server', 'say', 'console'))
xarestrict.addCommand('xa_unrestrict', xarestrict_cmd, 'restrict_weapon', 'ADMIN').register(('server', 'say', 'console'))


def restrict(arg_players, arg_weapons):
   """Restricts weapon or weapon tag arg_weapons from player or team arg_players"""
   arg_players = getPlayerList(arg_players)
   if not arg_players: raise IndexError, 'Invalid player list'

   arg_weapons = getWeaponList(arg_weapons)
   if not arg_weapons: raise IndexError, 'Invalid weapon list'

   for item in arg_players:
      for weapon in arg_weapons:
         item.addRestriction(weapon)


def unrestrict(arg_players, arg_weapons):
   """Unrestricts weapon or weapon tag arg_weapons from player or team arg_players"""
   arg_players = getPlayerList(arg_players)
   if not arg_players: raise IndexError, 'Invalid player list'

   arg_weapons = getWeaponList(arg_weapons)
   if not arg_weapons: raise IndexError, 'Invalid weapon list'

   for item in arg_players:
      for weapon in arg_weapons:
         item.removeRestriction(weapon)
