import es
import langlib
import os
import playerlib
import time
from xa import xa

#plugin information
info = es.AddonInfo()
info.name       = "Flood Control"
info.version    = "0.2"
info.author     = "Venjax"
info.basename   = "xafloodcontrol"

xafloodcontrol = xa.register(info.basename)
lang_text = xafloodcontrol.language.getLanguage() 
chat_flood_time = xafloodcontrol.setting.createVariable('chat_flood_time', '1.5', "The amount of time (in seconds) that after a player speaks they are restricted from speaking again")
timer = {}

def floodcontrol(userid, message, teamonly):
    #floodcontrol function. Eats spam according to time set in config options.
    global timer
    try:
        if not userid in timer.keys():
         timer[userid] = time.time()
         return userid, message, teamonly
        else:
         if time.time() - float(chat_flood_time) < timer[userid]:
             es.tell(userid, lang_text('chat flood', {}, playerlib.getPlayer(userid).get('lang')))
             timer[userid] = time.time()
             return 0, message, teamonly
         else:
             timer[userid] = time.time()
             return userid, message, teamonly
    except Exception, inst:
         es.dbgmsg(0, "Error: ", inst)
         return userid, message, teamonly

def load():
    #Load Function for Chat Flood Control for XA.
    if str(chat_flood_time) != '0':
        if not floodcontrol in es.addons.SayListeners:
            es.addons.registerSayFilter(floodcontrol)
        else:
            es.dbgmsg(0, 'chat_flood_time set to 0, exiting...')

def server_cvar(event_var):
    if event_var['cvarname'] == xafloodcontrol.setting.getVariableName('chat_flood_time'):
        if event_var['cvarvalue'] == '0':
            if floodcontrol in es.addons.SayListeners:
                es.addons.unregisterSayFilter(floodcontrol)
        else:
            if not floodcontrol in es.addons.SayListeners:
                es.addons.registerSayFilter(floodcontrol)

def unload():
    #Unloads XA Flood Control, and unregisteres saylisteners - if registered
    if floodcontrol in es.addons.SayListeners:
        es.addons.unregisterSayFilter(floodcontrol)
    xafloodcontrol.unregister()

def es_map_start(event_var):
    timer.clear()
