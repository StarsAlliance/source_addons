# // ******************************
# // Mattie's MugMod v2.0
# //      for Counter-Strike: Source
# //
# // * Description:
# //      Any knife kill will steal the victim's money.
# //
# // * Install instructions:
# //       1. Install Mattie's EventScripts plugins:
# //            http://mattie.info/cs
# //
# //       2. Add the following line somewhere in autoexec.cfg:
# //           es_load mugmod
# //
# // ******************************
import es
import langlib
import playerlib
import random

info = es.AddonInfo() 
info.name     = "Mattie's Mugmod" 
info.version  = "2.0" 
info.url      = "http://addons.eventscripts.com/addons/view/mugmod" 
info.basename = "mugmod" 
info.author   = "Mattie"


# all our server variables are declared here
mattie_mugmod     = es.ServerVar("mattie_mugmod",     1, "Enable/disable Mattie's MugMod")
mugmod_announce   = es.ServerVar("mugmod_announce",   1, "Announces MugMod each round.")
mugmod_taunt      = es.ServerVar("mugmod_taunt",      1, "Taunts the mugging victim with a random message.")
mugmod_sounds     = es.ServerVar("mugmod_sounds",     1, "Enables kill sounds for MugMod")
mugmod_soundfile  = es.ServerVar("mugmod_soundfile",  "bot/owned.wav", "Sound played for a mugging if mugmod_sounds is 1")
mugmod_percentage = es.ServerVar("mugmod_percentage", 100, "Percentage of money stolen during a mugging.")
text = None

def load():
    global text
    mattie_mugmod.makepublic()
    # load our strings
    text = langlib.Strings(es.getAddonPath("mugmod") + "/strings.ini")

def round_start(event_var):
  if mattie_mugmod > 0 and mugmod_announce > 0:
      es.msg("#multi", text("mugmod announcement"))

def player_death(event_var):
    if mattie_mugmod > 0:
        if event_var['weapon'] == "knife":
             # don't mug if they're on the same team.
             if event_var['es_attackerteam'] != event_var['es_userteam']:
                  victim = playerlib.getPlayer(event_var['userid'])
                  attacker = playerlib.getPlayer(event_var['attacker'])
                  # take money
                  killercash = attacker.get("cash")
                  victimcash = victim.get("cash")
                  muggedamount = (victimcash * mugmod_percentage) / 100
                  # complete the transaction
                  victim.set("cash", victimcash - muggedamount)
                  attacker.set("cash", muggedamount + killercash)

                  # build the tokens for string replacement
                  tokens = {}
                  tokens['attacker'] = attacker.get("name")
                  tokens['victim']   =   victim.get("name")
                  tokens['dollars']  = muggedamount
                  
                  # tell the victim
                  es.tell(victim, text("mugged notice", tokens, victim.get("lang")))
                  # tell the attacker
                  es.tell(attacker, text("mugger notice", tokens, attacker.get("lang")))
                  
                  # play sound
                  if mugmod_sounds > 0: 
                      es.emitsound("player", int(attacker), str(mugmod_soundfile), 1, 0.6)
                  
                  if mugmod_taunt > 0:
                    # say message
                    if muggedamount <= 200:
                       es.sexec(int(attacker), "say %s" % text("poor victim"))
                    else:
                       # rich victim
                       choices = [x for x in text.keys() if x[0:8] == 'mugging:']
                       chosen = random.choice(choices)
                       es.sexec(int(attacker), "say %s" % text(chosen))
             else:
                if mugmod_taunt > 0:
                  # team knifer!
                  es.sexec(int(attacker), "say %s" % text("team mugger"))


# ******************************
#   END MUGMOD SCRIPT
# ****************************** 
