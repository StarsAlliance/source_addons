# ./addons/eventscripts/_libs/python/weaponlib.py

import es
from collections import deque

import psyco
psyco.full()


gamename = es.getGameName()

class WeaponManager(object):
   class Weapon(str):
      """ Represents weapons, returning property information and an uniform name """
      def __init__(self, name):
         str.__init__(self, name)
         self.info_name = name

      def setAttributes(self, ammoprop='', tags=(), slot=0, clip=0, maxammo=0):
         self.info_ammoprop = ammoprop
         self.info_tags     = (tags,) if isinstance(tags, str) else tuple(tags)
         self.info_slot     = slot
         self.info_clip     = clip
         self.info_maxammo  = maxammo

      def __getattr__(self, x):
         try:
            return self.get(x)

         except ValueError:
            raise AttributeError, "Weapon instance has no attribute '%s'" % x

      def __getitem__(self, x):
         try:
            return self.get(x)

         except ValueError:
            raise KeyError, "'%s'" % x

      """ Public functions """

      def get(self, info):
         """ Returns weapon properties """
         if info == 'name':
            return self.info_name

         elif info == 'prop':
            return ('CBasePlayer.localdata.m_iAmmo.' + self.info_ammoprop) if self.info_ammoprop else None

         elif info == 'tags':
            return self.info_tags

         elif info == 'slot':
            return self.info_slot

         elif info == 'clip':
            return self.info_clip

         elif info == 'maxammo':
            return int(es.ServerVar('ammo_' + self.info_maxammo + '_max')) if isinstance(self.info_maxammo, str) else self.info_maxammo

         elif info == 'indexlist':
            return list(es.createentitylist(self.name))

         raise ValueError, "No weapon info '%s'" % info

   class IndexIter(object):
      """ Unique iterator object to control the creating of weapon index lists """
      def __init__(self, weapons):
         self.weapons = deque(weapons)
         self.indexes = deque()

      def __iter__(self):
         return self

      def next(self):
         # If there are no indexes in current the list, we need to create a new list
         while not self.indexes:
            # If we have no more weapons the iteration is complete
            if not self.weapons:
               raise StopIteration
            # Create and save the index list for the next weapon
            self.indexes = deque(self.weapons.popleft().indexlist)

         # Remove and return the first index in the index list
         return self.indexes.popleft()

   """ Begin WeaponManager """

   def __init__(self):
      self.weapons = {}

   """ Public functions """

   def getWeapon(self, name):
      """ Returns a Weapon instance if the weapon name is valid otherwise returns None """
      name = self._formatName(name)

      return self.weapons.get(name, None)

   def getWeaponList(self, tag='#all'):
      """
      Returns a list of Weapon instances with the specified tag
      but will also return a single-element list if a weapon name is given instead of tags.
      """
      if str(tag).startswith('#'):
         return filter(lambda x: tag in x.tags, map(lambda x: self.weapons[x], self.weapons))

      else:
         name = self._formatName(tag)
         return [self.weapons[name]] if name in self.weapons else []

   def getWeaponNameList(self, tag='#all'):
      """ Returns the string classnames of the Weapon instances returned by getWeaponList(tag) """
      return map(str, self.getWeaponList(tag))

   def getIndexList(self, tag='#all'):
      """ Compiles and returns a list of all indexes for all Weapon instances returned by getWeaponList(tag) """
      indexlist = []
      for weapon in self.getWeaponList(tag):
         indexlist += weapon.indexlist

      return indexlist

   def xgetIndexList(self, tag='#all'):
      """
      Returns a list of all indexes for all Weapon instances returned by getWeaponList(tag)
      but compiles the lists during iteration.
      """
      return self.IndexIter(self.getWeaponList(tag))

   def getWeaponIndexList(self, tag='#all'):
      """ Returns a list of tuples containing (index, Weapon instance) """
      weaponindexlist = []
      for weapon in self.getWeaponList(tag):
         weaponindexlist += [(index, weapon) for index in weapon.indexlist]

      return weaponindexlist

   """ Private functions """

   def _registerWeapon(self, name, ammoprop='', tags=(), slot=0, clip=0, maxammo=0):
      """ Register a weapon and its properties to the weapon database """
      name = self._formatName(name)

      weapon = self.weapons[name] = self.Weapon(name)
      weapon.setAttributes(ammoprop, tags, slot, clip, maxammo)

   @staticmethod
   def _formatName(name):
      """ Formats the given weapon name to a classname """
      name = str(name).lower()
      if not name.startswith('weapon_'):
         name = 'weapon_' + name
      return name

###

# CS:S weapons

cstrike = WeaponManager()
cstrike._registerWeapon('deagle',       '001', ('#all', '#secondary', '#pistol'),         2, 7,      '50AE')
cstrike._registerWeapon('ak47',         '002', ('#all', '#primary', '#rifle'),            1, 30,     '762mm')
cstrike._registerWeapon('scout',        '002', ('#all', '#primary', '#rifle', '#sniper'), 1, 10,     '762mm')
cstrike._registerWeapon('aug',          '002', ('#all', '#primary', '#rifle'),            1, 30,     '762mm')
cstrike._registerWeapon('g3sg1',        '002', ('#all', '#primary', '#rifle', '#sniper'), 1, 20,     '762mm')
cstrike._registerWeapon('galil',        '003', ('#all', '#primary', '#rifle'),            1, 35,     '556mm')
cstrike._registerWeapon('famas',        '003', ('#all', '#primary', '#rifle'),            1, 25,     '556mm')
cstrike._registerWeapon('m4a1',         '003', ('#all', '#primary', '#rifle'),            1, 30,     '556mm')
cstrike._registerWeapon('sg552',        '003', ('#all', '#primary', '#rifle'),            1, 30,     '556mm')
cstrike._registerWeapon('sg550',        '003', ('#all', '#primary', '#rifle', '#sniper'), 1, 30,     '556mm')
cstrike._registerWeapon('m249',         '004', ('#all', '#primary', '#machinegun'),       1, 100,    '556mm_box')
cstrike._registerWeapon('awp',          '005', ('#all', '#primary', '#rifle', '#sniper'), 1, 10,     '338mag')
cstrike._registerWeapon('tmp',          '006', ('#all', '#primary', '#smg'),              1, 30,     '9mm')
cstrike._registerWeapon('mp5navy',      '006', ('#all', '#primary', '#smg'),              1, 30,     '9mm')
cstrike._registerWeapon('glock',        '006', ('#all', '#secondary', '#pistol'),         2, 20,     '9mm')
cstrike._registerWeapon('elite',        '006', ('#all', '#secondary', '#pistol'),         2, 30,     '9mm')
cstrike._registerWeapon('m3',           '007', ('#all', '#primary', '#shotgun'),          1, 8,      'buckshot')
cstrike._registerWeapon('xm1014',       '007', ('#all', '#primary', '#shotgun'),          1, 7,      'buckshot')
cstrike._registerWeapon('mac10',        '008', ('#all', '#primary', '#smg'),              1, 30,     '45acp')
cstrike._registerWeapon('ump45',        '008', ('#all', '#primary', '#smg'),              1, 25,     '45acp')
cstrike._registerWeapon('usp',          '008', ('#all', '#secondary', '#pistol'),         2, 12,     '45acp')
cstrike._registerWeapon('p228',         '009', ('#all', '#secondary', '#pistol'),         2, 13,     '357sig')
cstrike._registerWeapon('fiveseven',    '010', ('#all', '#secondary', '#pistol'),         2, 20,     '57mm')
cstrike._registerWeapon('p90',          '010', ('#all', '#primary', '#smg'),              1, 50,     '57mm')
cstrike._registerWeapon('hegrenade',    '011', ('#all', '#grenade', '#explosive'),        4, maxammo='hegrenade')
cstrike._registerWeapon('flashbang',    '012', ('#all', '#grenade'),                      4, maxammo='flashbang')
cstrike._registerWeapon('smokegrenade', '013', ('#all', '#grenade'),                      4, maxammo='smokegrenade')
cstrike._registerWeapon('knife',        None,  ('#all', '#knife', '#melee'),              3)
cstrike._registerWeapon('c4',           None,  ('#all', '#objective'),                    5)

###

# HL2DM weapons

hl2mp = WeaponManager()
hl2mp._registerWeapon('crowbar',    None,  ('#all', '#hand', '#melee'),        1)
hl2mp._registerWeapon('stunstick',  None,  ('#all', '#hand', '#melee'),        1)
hl2mp._registerWeapon('physcannon', None,  ('#all', '#tool'),                  1)
hl2mp._registerWeapon('pistol',     '003', ('#all', '#pistol'),                2, 18,     150)
hl2mp._registerWeapon('357',        '005', ('#all', '#pistol'),                2, 6,      12)
hl2mp._registerWeapon('smg1',       '004', ('#all', '#smg'),                   3, 45,     225)
hl2mp._registerWeapon('ar2',        '001', ('#all', '#smg'),                   3, 30,     90)
hl2mp._registerWeapon('crossbow',   '006', ('#all', '#sniper'),                4, 1,      10)
hl2mp._registerWeapon('shotgun',    '007', ('#all', '#shotgun'),               4, 6,      30)
hl2mp._registerWeapon('rpg',        '008', ('#all', '#rocket', '#explosive'),  5, maxammo=3)
hl2mp._registerWeapon('frag',       '010', ('#all', '#grenade', '#explosive'), 5, maxammo=5)
hl2mp._registerWeapon('slam',       '011', ('#all', '#grenade', '#explosive'), 5, maxammo=5)

###

# DoD:S weapons

dod = WeaponManager()
dod._registerWeapon('amerknife',     None,  ('#all', '#hand', '#melee'),                    3)
dod._registerWeapon('spade',         None,  ('#all', '#hand', '#melee'),                    3)
dod._registerWeapon('colt',          '001', ('#all', '#secondary', '#pistol'),              2, 7,      14)
dod._registerWeapon('p38',           '002', ('#all', '#secondary', '#pistol'),              2, 8,      16)
dod._registerWeapon('c96',           '003', ('#all', '#secondary', '#smg'),                 2, 20,     40)
dod._registerWeapon('garand',        '004', ('#all', '#primary', '#rifle'),                 1, 8,      80)
dod._registerWeapon('k98',           '005', ('#all', '#primary', '#rifle'),                 1, 5,      60)
dod._registerWeapon('k98_scoped',    '005', ('#all', '#primary', '#rifle', '#sniper'),      1, 5,      60)
dod._registerWeapon('m1carbine',     '006', ('#all', '#secondary', '#rifle'),               2, 15,     30)
dod._registerWeapon('spring',        '007', ('#all', '#primary', '#rifle', '#sniper'),      1, 5,      50)
dod._registerWeapon('mp44',          '008', ('#all', '#primary', '#smg'),                   1, 30,     180)
dod._registerWeapon('mp40',          '008', ('#all', '#primary', '#smg'),                   1, 30,     180)
dod._registerWeapon('thompson',      '008', ('#all', '#primary', '#smg'),                   1, 30,     180)
dod._registerWeapon('bar',           '009', ('#all', '#primary', '#machinegun'),            1, 20,     240)
dod._registerWeapon('30cal',         '010', ('#all', '#primary', '#machinegun'),            1, 150,    300)
dod._registerWeapon('mg42',          '011', ('#all', '#primary', '#machinegun'),            1, 250,    250)
dod._registerWeapon('bazooka',       '012', ('#all', '#primary', '#bazooka', '#explosive'), 1, 1,      4)
dod._registerWeapon('pschreck',      '012', ('#all', '#primary', '#bazooka', '#explosive'), 1, 1,      4)
dod._registerWeapon('frag_us',       '013', ('#all', '#grenade', '#explosive'),             4, maxammo=2)
dod._registerWeapon('frag_ger',      '014', ('#all', '#grenade', '#explosive'),             4, maxammo=2)
dod._registerWeapon('smoke_us',      '017', ('#all', '#grenade', '#explosive'),             3, maxammo=1)
dod._registerWeapon('smoke_ger',     '018', ('#all', '#grenade', '#explosive'),             3, maxammo=1)
dod._registerWeapon('riflegren_us',  '021', ('#all', '#grenade', '#explosive'),             4, 1,      1)
dod._registerWeapon('riflegren_ger', '022', ('#all', '#grenade', '#explosive'),             4, 1,      1)


dod_numbers_to_weapon = {'1':'amerknife', '3':'colt', '6':'garand', '7':'m1carbine', '9':'spring', '11':'thompson', '14':'bar', '15':'30cal', '17':'bazooka', '19':'frag_us', '21':'frag_us', '23':'smoke_us', '25':'riflegren_us', '27':'riflegren_us', '29':'punch', '31':'garand', '33':'spring', '35':'30cal', '37':'bar', '2':'spade', '4':'p38', '5':'c96', '8':'k98', '10':'k98_scoped', '12':'mp40', '13':'mp44', '16':'mg42', '18':'pschreck', '20':'frag_ger', '22':'frag_ger', '24':'smoke_ger', '26':'riflegren_ger', '28':'riflegren_ger', '30':'punch', '32':'k98', '34':'k98_scoped', '36':'mg42', '38':'mp44'}

def dod_formatName(name): # This function will overwrite the _formatName method of the DoDS WeaponManager instance
   return WeaponManager._formatName(dod_numbers_to_weapon.get(name, name))

dod._formatName = dod_formatName

###

# TF2 weapons
# The getWeapon method for TF2 will return None for taunt, sentry gun, and deflected projectile kills.

tf = WeaponManager()
tf._registerWeapon('scattergun',           '001', ('#all', '#primary', '#scout', '#shotgun'),       1, 6,      32)
tf._registerWeapon('scattergun',           '001', ('#all', '#primary', '#scout', '#shotgun'),       1, 2,      32)
tf._registerWeapon('pistol_scout',         '002', ('#all', '#secondary', '#scout', '#pistol'),      2, 12,     36)
tf._registerWeapon('lunchbox_drink',       '002', ('#all', '#secondary', '#scout', '#tool'),        2, maxammo=1)
tf._registerWeapon('bat',                  None,  ('#all', '#scout', '#melee'),                     3)
tf._registerWeapon('bat_wood',             None,  ('#all', '#scout', '#melee'),                     3, maxammo=1)
tf._registerWeapon('rocketlauncher',       '001', ('#all', '#primary', '#soldier', '#explosive'),   1, 4,      20)
tf._registerWeapon('shotgun_soldier',      '002', ('#all', '#secondary', '#soldier', '#shotgun'),   2, 6,      32)
tf._registerWeapon('shovel',               None,  ('#all', '#soldier', '#melee'),                   3)
tf._registerWeapon('flamethrower',         '001', ('#all', '#primary', '#pyro', '#flame'),          1, maxammo=200)
tf._registerWeapon('shotgun_pyro',         '002', ('#all', '#secondary', '#pyro', '#shotgun'),      2, 6,      32)
tf._registerWeapon('flaregun',             '002', ('#all', '#secondary', '#pyro', '#flame'),        2, maxammo=16)
tf._registerWeapon('fireaxe',              None,  ('#all', '#pyro', '#melee'),                      3)
tf._registerWeapon('grenadelauncher',      '001', ('#all', '#primary', '#demoman', '#explosive'),   1, 4,      16)
tf._registerWeapon('pipebomblauncher',     '002', ('#all', '#secondary', '#demoman', '#explosive'), 2, 8,      24)
tf._registerWeapon('bottle',               None,  ('#all', '#demoman', '#melee'),                   3)
tf._registerWeapon('minigun',              '001', ('#all', '#primary', '#heavy', '#machinegun'),    1, maxammo=200)
tf._registerWeapon('shotgun_hwg',          '002', ('#all', '#secondary', '#heavy', '#shotgun'),     2, 6,      32)
tf._registerWeapon('lunchbox',             None,  ('#all', '#secondary', '#heavy', '#tool'),        2, maxammo=1)
tf._registerWeapon('fists',                None,  ('#all', '#heavy', '#melee'),                     3)
tf._registerWeapon('shotgun_primary',      '001', ('#all', '#primary', '#engineer', '#shotgun'),    1, 6,      32)
tf._registerWeapon('pistol',               '002', ('#all', '#secondary', '#engineer', '#pistol'),   2, 12,     200)
tf._registerWeapon('wrench',               '003', ('#all', '#engineer', '#melee'),                  3, maxammo=200)
tf._registerWeapon('pda_engineer_build',   None,  ('#all', '#engineer', '#tool'),                   4)
tf._registerWeapon('pda_engineer_destroy', None,  ('#all', '#engineer', '#tool'),                   5)
tf._registerWeapon('syringegun_medic',     '001', ('#all', '#primary', '#medic'),                   1, 40,     150)
tf._registerWeapon('medigun',              None,  ('#all', '#secondary', '#medic', '#tool'),        2)
tf._registerWeapon('bonesaw',              None,  ('#all', '#medic', '#melee'),                     3)
tf._registerWeapon('sniperrifle',          '001', ('#all', '#primary', '#sniper'),                  1, maxammo=25)
tf._registerWeapon('smg',                  '002', ('#all', '#secondary', '#sniper'),                2, 25,     75)
tf._registerWeapon('club',                 None,  ('#all', '#sniper', '#melee'),                    3)
tf._registerWeapon('revolver',             '001', ('#all', '#primary', '#spy', '#pistol'),          1, 6,      24)
tf._registerWeapon('builder',              None,  ('#all', '#secondary', '#spy', '#tool'),          2)
tf._registerWeapon('knife',                None,  ('#all', '#spy', '#melee'),                       3)
tf._registerWeapon('spy_pda',              None,  ('#all', '#spy', '#tool'),                        4)


tf_kill_weapon_to_classname = {'tf_projectile_rocket':'rocketlauncher', 'backburner':'flamethrower', 'tf_projectile_flare':'flaregun', 'axtinguisher':'fireaxe', 'tf_projectile_pipe':'grenadelauncher', 'tf_projectile_pipe_remote':'pipebomblauncher', 'gloves':'fists', 'blutsauger':'syringegun_medic', 'ubersaw':'bonesaw'}

def tf_formatName(name): # This function will overwrite the _formatName method of the TF2 WeaponManager instance
   name = str(name).lower()
   name = tf_kill_weapon_to_classname.get(name, name)
   if not name.startswith('tf_weapon_'):
      name = 'tf_weapon_' + name
   return name

tf._formatName = tf_formatName

###

#PVKII weapons

pvkii = WeaponManager()
pvkii._registerWeapon('twosword',     None,  ('#all', '#knight', '#primary', '#melee', '#sword'),             1)
pvkii._registerWeapon('swordshield',  None,  ('#all', '#knight', '#secondary', '#melee', '#sword'),           2)
pvkii._registerWeapon('archersword',  None,  ('#all', '#archer', '#primary', '#melee', '#sword'),             1)
pvkii._registerWeapon('crossbow',     '004', ('#all', '#archer', '#secondary', '#ranged', '#bow'),            2)
pvkii._registerWeapon('longbow',      '005', ('#all', '#archer', '#tertiary', '#ranged', '#bow'),             3)
pvkii._registerWeapon('cutlass',      None,  ('#all', '#skirmisher', '#primary', '#melee', '#sword'),         1)
pvkii._registerWeapon('flintlock',    '003', ('#all', '#skirmisher', '#secondary', '#ranged', '#gun'),        2, 6)
pvkii._registerWeapon('powderkeg',    '001', ('#all', '#skirmisher', '#tertiary', '#special', '#explosive'),  3, maxammo=1)
pvkii._registerWeapon('cutlass2',     None,  ('#all', '#captain', '#primary', '#melee', '#sword'),            1)
pvkii._registerWeapon('blunderbuss',  '006', ('#all', '#captain', '#secondary', '#ranged', '#gun'),           2, 1)
pvkii._registerWeapon('parrot',       '002', ('#all', '#captain', '#tertiary', '#special', '#bird'),          3, 1,      1)
pvkii._registerWeapon('bigaxe',       None,  ('#all', '#beserker', '#primary', '#melee', '#axe'),             1)
pvkii._registerWeapon('axesword',     None,  ('#all', '#beserker', '#secondary', '#melee', '#axe', '#sword'), 2)
pvkii._registerWeapon('twoaxe',       None,  ('#all', '#huscarl', '#primary', '#melee', '#axe'),              1)
pvkii._registerWeapon('vikingshield', None,  ('#all', '#huscarl', '#secondary', '#melee', '#sword'),          2)
pvkii._registerWeapon('throwaxe',     '007', ('#all', '#huscarl', '#tertiary', '#ranged', '#axe'),            3)

###

# Functions that point to the current game

def _getCurrentGame():
   es.dbgmsg(1, 'weaponlib: Current game - "%s"' % gamename)

   if gamename == 'cstrike':
      return cstrike
   elif gamename == 'hl2mp':
      return hl2mp
   elif gamename == 'dod':
      return dod
   elif gamename == 'tf':
      return tf
   elif gamename == 'pvkii':
      return pvkii

   raise NotImplementedError, "weaponlib does not support game '%s'" % gamename

currentgame = _getCurrentGame()


def getWeapon(*a, **kw):
   return currentgame.getWeapon(*a, **kw)
getWeapon.__doc__ = WeaponManager.getWeapon.__doc__

def getWeaponList(*a, **kw):
   return currentgame.getWeaponList(*a, **kw)
getWeaponList.__doc__ = WeaponManager.getWeaponList.__doc__

def getWeaponNameList(*a, **kw):
   return currentgame.getWeaponNameList(*a, **kw)
getWeaponNameList.__doc__ = WeaponManager.getWeaponNameList.__doc__

def getIndexList(*a, **kw):
   return currentgame.getIndexList(*a, **kw)
getIndexList.__doc__ = WeaponManager.getIndexList.__doc__

def xgetIndexList(*a, **kw):
   return currentgame.xgetIndexList(*a, **kw)
xgetIndexList.__doc__ = WeaponManager.xgetIndexList.__doc__

def getWeaponIndexList(*a, **kw):
   return currentgame.getWeaponIndexList(*a, **kw)
getWeaponIndexList.__doc__ = WeaponManager.getWeaponIndexList.__doc__


"""
>>> import weaponlib

>>> glock = weaponlib.getWeapon('glock')

# Each method works for all attributes
>>> glock.get('clip')
7
>>> glock['clip']
7
>>> glock.clip
7

# Instances return weapon name when coerced to a string
>>> str(glock)
'weapon_glock'
"""
"""
import weaponlib

# This should work on any game
def player_death(event_var):
   weapon   = weaponlib.getWeapon(event_var['weapon'])
   attacker = int(event_var['attacker'])
   if weapon and attacker:
      # Refil the attacker's ammo to max
      prop    = weapon.prop
      maxammo = weapon.maxammo
      if prop and maxammo:
         es.setplayerprop(attacker, prop, maxammo)

      # Find the attacker's weapon index
      index  = 0
      handle = es.getplayerhandle(attacker)
      for x in weapon.indexlist:
         if es.getindexprop(x, 'CBaseEntity.m_hOwnerEntity') == handle:
            index = x
            break

      es.tell(userid, 'You were killed by ' + event_var['es_attackername'] + ' with the ' + weapon + ' (ent index %s)' % index)
"""
"""
import es
import weaponlib


def round_start(event_var):
   # Remove all idle primary weapons
   for index in weaponlib.getIndexList('#primary'):
      if es.getindexprop(index, 'CBaseEntity.m_hOwnerEntity') == -1:
         es.server.cmd('es_xremove %s' % index)


def item_pickup(event_var):
   userid = int(event_var['userid'])
   handle = es.getplayerhandle(userid)

   # Remove any idle weapons of the type just picked up
   for index in weaponlib.getIndexList(event_var['item']):
      if es.getindexprop(index, 'CBaseEntity.m_hOwnerEntity') == -1:
         es.server.cmd('es_xremove %s' % index)

   # Gather a list of the player's weapons
   myweapons = []
   for weapon in weaponlib.getWeaponList('#all'):
      for index in weapon.indexlist:
         if es.getindexprop(index, 'CBaseEntity.m_hOwnerEntity') == handle:
            myweapons.append(weapon)
            break

   # Show the player his or her weapons sorted by slot
   if myweapons:
      sorted_weapons = sorted(myweapons, key=lambda x: x.slot)
      es.tell(userid, 'Current weapons: ' + ', '.join(map(str, sorted_weapons)))

   else:
      es.tell(userid, 'You have no weapons')


def player_spawn(event_var):
   userid = int(event_var['userid'])
   handle = es.getplayerhandle(userid)

   usp = weaponlib.getWeapon('usp')
   # Loop through all usps to find the one belonging to the player
   for index in usp.indexlist:
      if es.getindexprop(index, 'CBaseEntity.m_hOwnerEntity') == handle:

         # Remove the player's usp
         es.server.cmd('es_xremove %s' % index)

         # Set the player's usp ammo to 0
         es.setplayerprop(userid, usp.prop, 0)

         # Stop looping
         break

   glock = weaponlib.getWeapon('glock')
   # Loop through all glocks to find the one belonging to the player
   for index in glock.indexlist:
      if es.getindexprop(index, 'CBaseEntity.m_hOwnerEntity') == handle:
         # Make the player drop the glock
         es.sexec(userid, 'use weapon_glock')
         es.sexec(userid, 'drop')

         # Set the player's glock ammo to max
         es.setplayerprop(userid, glock.prop, glock.maxammo)

         # Stop looping
         break

   # Loop though each primary weapon and set the player's ammo to the number of bullets in one clip
   for weapon in weaponlib.getWeaponList('#primary'):
      for index in weapon.indexlist:
         if es.getindexprop(index, 'CBaseEntity.m_hOwnerEntity') == handle:
            es.setplayerprop(userid, weapon.prop, weapon.clip)
            return
"""