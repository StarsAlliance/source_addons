import es
import repeat
import playerlib
from xa import xa

#plugin information
info = es.AddonInfo() 
info.name     = 'High Ping Kicker' 
info.version  = '1.2a'
info.author   = 'SumGuy14'
info.basename = 'xahighpingkick' 

gUserid = {}

# register module with XA
xahighpingkick = xa.register(info.basename)

# Localization helper:
text = xahighpingkick.language.getLanguage()

# make config vars
maxping       = xahighpingkick.setting.createVariable('ping_maxping', 300, 'Maximum ping of a player before they are kicked')
check         = xahighpingkick.setting.createVariable('ping_check', 10, 'How many total times to check the players ping over a period of time before they are kicked')
interval      = xahighpingkick.setting.createVariable('ping_interval', 5, 'How often the players ping is checked, in seconds')
exceedlimit   = xahighpingkick.setting.createVariable('ping_exceedlimit', 3, 'If the players ping is above the max when checked this many times, player will be kicked')

def load():
    """ Make sure all people on the server when this is loaded are not forgotten """
    for userid in playerlib.getUseridList('#human'):
        player_activate({'userid': userid})

def unload(): 
    for userid in gUserid:
        player_disconnect({'userid': userid})
    xahighpingkick.unregister()

def player_activate(event_var):
    userid = int(event_var['userid'])
    if not userid in gUserid:
        player = playerlib.getPlayer(userid)
        if not player.isbot:
            player._hpk_violations = 0
            gUserid[userid] = repeat.create('hpk_track_%s' % userid, _tracker, player)
            gUserid[userid].start(float(interval), float(check))

def player_disconnect(event_var):
    userid = int(event_var['userid'])
    if userid in gUserid:
        gUserid[userid].delete()
        del gUserid[userid]

def _tracker(player):
    if player.isOnline():
        player.refreshAttributes()
        if int(maxping) and player.ping >= int(maxping):
            player._hpk_violations += 1
        if int(exceedlimit) and player._hpk_violations >= int(exceedlimit):
            player.kick(reason=text('kick', {}, player.lang))
            xahighpingkick.logging.log('Kicked for breaking the high ping limit', userid)
