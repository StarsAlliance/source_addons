import es
from playerlib import getPlayerList
from xa import xa

info = es.AddonInfo()
info.name       = "Objectives"
info.version    = "0.1"
info.author     = "Wonder"
info.basename   = "xaobjectives"

xaobjectives = xa.register(info.basename)

def load():
    global slay, text

    slay = xaobjectives.setting.createVariable("css_objectives", "1", "If 1, losing team will be slain.")
    text = xaobjectives.language.getLanguage()

    if es.getgame() != "Counter-Strike: Source":
        raise AttributeError, "Counter-Strike: Source"

def unload():
    xaobjectives.unregister()

def round_end(eventVar):
    if int(slay):
        if eventVar["winner"] == "2" and es.getlivingplayercount(3):
            xaobjectives.logging.log("Counter-Terrorists slayed for failing to meet their objectives")
            cts, ts = getPlayerList("#ct"), getPlayerList("#t")
            for i in cts:
                i.kill()
                es.tell(int(i), "#multi", text("lost"))
            for i in ts:
                es.tell(int(i), "#multi", text("won"))
        elif eventVar["winner"] == "3" and es.getlivingplayercount(2):
            xaobjectives.logging.log("Terrorists slayed for failing to meet their objectives")
            ts, cts = getPlayerList("#t"), getPlayerList("#ct")
            for i in ts:
                i.kill()
                es.tell(int(i), "#multi", text("lost"))
            for i in cts:
                es.tell(int(i), "#multi", text("won"))

def round_start(eventVar):
    if int(slay):
        es.msg("#multi", text("round_start"))
