import es
import urllib
import usermsg
from xa import xa


#plugin information
info = es.AddonInfo()
info.name           = "XA Browse"
info.version        = "1"
info.author         = "Errant"
info.basename       = "xabrowse"



xamodule             = xa.register(info.basename)
#xalanguage           = xamodule.language.getLanguage()



def load():
    xamodule.addCommand('xa_browse', browse_cmd, "xa_browse", "UNRESTRICTED", "xa_browse <url>", True).register(('console',))
    
def unload():
    xamodule.unregister()
    
def browse_cmd():
    args = [es.getargv(x) for x in xrange(1, es.getargc())]
    if not len(args):
        xamodule.logging.log("Incorrect usage: xa_browse <url>")
        return
    url = urllib.quote(args[0])
    if not url.startswith('http://'):
        url = 'http://'+url
    xamodule.logging.log("Opening url: %s" % url)
    usermsg.motd(es.getcmduserid(), 2, "XA Browse", url)
    
    
    
