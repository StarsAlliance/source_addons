import es
import playerlib
from xa import xa

info                = es.AddonInfo() 
info.name           = "Extended Admin Say" 
info.version        = "0.2" 
info.author         = "freddukes" 
info.basename       = "xaextendedsay" 

xaextendedsay = xa.register(info.basename) 
xalanguage    = xaextendedsay.language.getLanguage() 

def load():
    xaextendedsay.addRequirement("xasay")
    xaextendedsay.xasay.registerSayPrefix("@@" , _admin_say_tell, "admin_tell", "ADMIN")
    xaextendedsay.xasay.registerSayPrefix("@@@", _admin_say_center, "admin_say", "ADMIN")
    
def unload():
    xaextendedsay.delRequirement("xasay")
    xaextendedsay.unregister()
    
def _admin_say_tell(adminid, message, teamonly):
    position = 0 
    tokens = {}
    username = ''
    messagetokens = message.split()
    if not messagetokens:
        return
    if messagetokens[0].startswith('"') and message.count('"') >= 2:
        for part in messagetokens:
            position += 1
            username += ' '+part.strip('"')
            if part.endswith('"'):
                break
        try:
            message = ' '.join(messagetokens[position:])
        except:
            message = ''
    elif messagetokens[0].startswith("'") and message.count("'") >= 2:
        for part in messagetokens:
            position += 1
            username += ' '+part.strip("'")
            if part.endswith("'"):
                break
        try:
            message = ' '.join(messagetokens[position:])
        except:
            message = ''
    else:
        username = messagetokens[0]
        message = ' '.join(messagetokens[1:])
    
    tokens['message']   = message
    tokens['adminname'] = es.getplayername(adminid)
    
    if username.startswith('#'):
        tokens['username']  = username
        pl = playerlib.getPlayerList(username)
        if pl:
            for player in pl:
                if not teamonly: 
                    es.tell(int(player) , '#multi', xalanguage('admin to player', tokens, player.get("lang")))
                else:
                    es.centertell(int(player) , xalanguage('admin center to player', tokens, player.get("lang")))
            if not teamonly:
                es.tell(adminid, '#multi', xalanguage('admin to player', tokens, playerlib.getPlayer(adminid).get("lang")))
            else:
                es.centertell(adminid, xalanguage('admin center to player', tokens, playerlib.getPlayer(adminid).get("lang")))
            xaextendedsay.logging.log("has said '%s' to group %s" % (message, username), adminid, True )
        else:
            xaextendedsay.logging.log("has said '%s' to %s, but no group existed" % (message, username), adminid, True )  
    else:
        username = username.lstrip()
        userid = es.getuserid(username)
        if userid:  
            tokens['username']  = es.getplayername(userid) 
            if not teamonly: 
                es.tell(userid , '#multi', xalanguage('admin to player', tokens, playerlib.getPlayer(userid).get("lang"))) 
                es.tell(adminid, '#multi', xalanguage('admin to player', tokens, playerlib.getPlayer(adminid).get("lang")))
                xaextendedsay.logging.log("has said '%s' to user %s [%s]" % (message, tokens['username'], es.getplayersteamid(userid) ), adminid, True ) 
            else: 
                es.centertell(userid , xalanguage('admin center to player', tokens, playerlib.getPlayer(userid).get("lang"))) 
                es.centertell(adminid, xalanguage('admin center to player', tokens, playerlib.getPlayer(adminid).get("lang")))
                xaextendedsay.logging.log("has said '%s' to user %s [%s]" % (message, tokens['username'], es.getplayersteamid(userid) ), adminid, True )  
        else: 
            tokens['username'] = username
            es.tell(adminid, '#multi', xalanguage('no player found', tokens, playerlib.getPlayer(adminid).get("lang"))) 
    return (0,'',0)
    
def _admin_say_center(userid, message, teamonly): 
    tokens = {} 
    tokens['username'] = es.getplayername(userid) 
    tokens['message']  = message 
    if not teamonly: 
        for player in filter(lambda x: not es.getplayersteamid(x) == "BOT", es.getUseridList()): 
            es.centertell(player, xalanguage('center message', tokens, playerlib.getPlayer(player).get("lang")))
        xaextendedsay.logging.log("has said '%s' in center chat" % message, userid, True ) 
    else: 
        for player in playerlib.getPlayerList('#admin_say'): 
            es.centertell(int(player), xalanguage('admin only center message', tokens, player.get("lang")))
        xaextendedsay.logging.log("has said '%s' in admin only center chat" %  message, userid, True ) 
    return (0,'',0)
    
