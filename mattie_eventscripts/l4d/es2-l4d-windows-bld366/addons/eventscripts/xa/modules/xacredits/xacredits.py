import es
import usermsg
from xa import xa


#plugin information
info = es.AddonInfo()
info.name           = "XA Credits"
info.version        = "1"
info.author         = "Errant"
info.basename       = "xacredits"



xamodule             = xa.register(info.basename)

def load():
    xamodule.addCommand('xa_credits', credits_cmd, "xa_credits", "UNRESTRICTED", "xa_credits", True).register(('console','server'))
    
def credits_cmd():
    userid = es.getcmduserid()
    usermsg.echo(userid,' == eXtensible Admin Credits ==')
    usermsg.echo(userid,'The following people helped create XA')
    usermsg.echo(userid,'Project Lead:      NATO|Hunter')
    usermsg.echo(userid,'Release Manager:   Errant')
    usermsg.echo(userid,'Community Manager: Freddukes')
    usermsg.echo(userid,'Website:           Ojii')
    usermsg.echo(userid,'Eventscripts:      Mattie')
    usermsg.echo(userid,' ')
    usermsg.echo(userid,'# Contributors')
    usermsg.echo(userid,'Superdave,Venjax,jeff91,juba_pornborn,Sumguy41')
    usermsg.echo(userid,'HitThePipe,Undead,British.Assassin,101Satoon101')
    usermsg.echo(userid,'adminc,Soynuts,XE_ManUp,JoeyT2006,Omega_K2,colster')
    usermsg.echo(userid,'dajayguy,awuh0,AMMUT,chatcon,chrisber,chriske21')
    usermsg.echo(userid,'claridon,Einlanzers,GODJonez,JAMES,rio,thekiller')
    usermsg.echo(userid,'tim3port,Brettonawak')