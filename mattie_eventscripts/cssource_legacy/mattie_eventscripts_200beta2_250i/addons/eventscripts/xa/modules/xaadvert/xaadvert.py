import re
import es
import gamethread
import playerlib
import msglib
import usermsg
import time
from xa import xa

#plugin information
info = es.AddonInfo() 
info.name     = 'Advert' 
info.version  = '1.0' 
info.author   = 'Rio'
info.basename = 'xaadvert' 

# register module with XA 
xaadvert = xa.register(info.basename) 

next_advert = 0 
colors = {'{RED}': '255 0 0 255', '{BLUE}': '0 0 255 255', '{GREEN}': '0 255 0 255', '{MAGENTA}': '139 0 139 255', '{BROWN}': '128 42 42 255', '{GREY}': '128 128 128', '{CYAN}':  '0 204 204 255', '{YELLOW}': '255 255 0 255', '{ORANGE}': '255 127 0 255', '{WHITE}': '255 255 255 255', '{PINK}': '255 0 204 255'} 

def load(): 
   global adverts, time_between_advert, adverts_chat_area, adverts_top_left, advert_col_red, advert_col_green, advert_col_blue, advert_dead_only, adverts_bottom_area, xaadvertlist 

   # make config vars 
   adverts              = xaadvert.setting.createVariable('adverts', 1, 'Turns adverts on or off') 
   time_between_advert  = xaadvert.setting.createVariable('time_between_advert', 120, 'Time between adverts displayed') 
   adverts_chat_area    = xaadvert.setting.createVariable('adverts_chat_area', 1, 'Allow adverts in chat area of screen') 
   adverts_top_left     = xaadvert.setting.createVariable('adverts_top_left', 1, 'Allow adverts in top left corner of screen') 
   advert_col_red       = xaadvert.setting.createVariable('advert_col_red', 0, 'Red component colour of adverts (255 = max)') 
   advert_col_green     = xaadvert.setting.createVariable('advert_col_green', 0, 'Green component colour of adverts (255 = max)') 
   advert_col_blue      = xaadvert.setting.createVariable('advert_col_blue', 255, 'Blue component colour of adverts (255 = max)') 
   advert_dead_only     = xaadvert.setting.createVariable('advert_dead_only', 0, 'Specify if all players or only dead players can see adverts') 
   adverts_bottom_area  = xaadvert.setting.createVariable('adverts_bottom_area', 0, 'Show adverts in the hint text area') 
    
   # get advert list 
   if xa.isManiMode(): 
      xaadvertlist = xaadvert.configparser.getList('cfg/mani_admin_plugin/adverts.txt', True) 
   else: 
      xaadvertlist = xaadvert.configparser.getList('adverts.txt') 
    
   # start timer 
   gamethread.delayedname(time_between_advert, 'adverts', display_advert) 

def unload(): 
   # stop timer 
   gamethread.cancelDelayed('adverts') 
   
   # unregister module with XA 
   xaadvert.unregister() 
    
def display_advert(): 
   global next_advert 
    
   # repeat the timer 
   gamethread.delayedname(time_between_advert, 'adverts', display_advert) 
    
   if adverts and xaadvertlist and es.ServerVar('eventscripts_currentmap') != '': 
      # start at the beginning 
      if next_advert >= len(xaadvertlist): 
         next_advert = 0 
          
      # get advert          
      advert_text = xaadvertlist[next_advert] 
            
      tags = re.compile(r'(?P<tag>\{\w+\})') 
      for tag in tags.findall(advert_text):              
         advert_text = advert_text.replace(tag,tag.upper()) 

      # set color 
      color = '%s %s %s 255' % (str(advert_col_red), str(advert_col_green), str(advert_col_blue)) 
      for k in colors: 
         if k in advert_text: 
            color = colors[k] 
            advert_text = advert_text.replace(k, '') 
                        
                
      # set tags 
      if str(es.ServerVar('eventscripts_nextmapoverride')) != '': 
         advert_text = advert_text.replace('{NEXTMAP}', str(es.ServerVar('eventscripts_nextmapoverride'))) 
      else: 
         advert_text = advert_text.replace('{NEXTMAP}', 'UNKNOWN') 
          
      advert_text = advert_text.replace('{CURRENTMAP}', str(es.ServerVar('eventscripts_currentmap'))) 
      advert_text = advert_text.replace('{TICKRATE}', 'UNKNOWN') 
      
      if int(es.ServerVar('mp_friendlyfire')): 
         advert_text = advert_text.replace('{FF}', 'on') 
      else: 
         advert_text = advert_text.replace('{FF}', 'off') 
          
      advert_text = advert_text.replace('{THETIME}', str(time.strftime("%H:%M:%S", time.localtime()))) 
      advert_text = advert_text.replace('{SERVERHOST}', 'UNKNOWN') 

      # send top text  
      if int(adverts_top_left):
         if int(advert_dead_only) == 1: 
            xaadvert_playerlist = playerlib.getPlayerList('#human,#dead') 
         else: 
            xaadvert_playerlist = playerlib.getPlayerList('#human') 
            
         toptext = msglib.VguiDialog(title=advert_text, level=5, time=25, mode=msglib.VguiMode.MSG) 
         toptext['color'] = color 

         for k in xaadvert_playerlist: 
            toptext.send(k.userid) 
            
      # send chat text  
      if int(adverts_chat_area):
         if int(advert_dead_only) == 1: 
            xaadvert_playerlist = playerlib.getPlayerList('#human,#dead') 
            for k in xaadvert_playerlist: 
               es.tell(k.userid, '#lightgreen', advert_text) 
         else: 
            es.msg('#lightgreen', advert_text) 
      
      # send bottom text 
      if int(adverts_bottom_area):
         if int(advert_dead_only) == 1: 
            xaadvert_playerlist = playerlib.getPlayerList('#human,#dead') 
         else: 
            xaadvert_playerlist = playerlib.getPlayerList('#human') 
            
         for k in xaadvert_playerlist: 
            usermsg.hudhint(k.userid, advert_text) 
            
      next_advert = next_advert + 1
