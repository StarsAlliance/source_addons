import es
import popuplib
import playerlib
import cfglib
import time
from xa import xa, logging

import os
import urllib2

#plugin information
info = es.AddonInfo()
info.name           = "XA Update Check"
info.version        = "1"
info.author         = "Errant"
info.basename       = "xaupdate"

class Check(object):
    #url = 'http://xa.eventscripts.com/api/version'
    url = 'http://dev.xa.ojii.ch/api/version'
    last = None
    remote_version = None
    # in seconds...
    update_every = 86400
    
    def update(self):
        try:
            # try to open the check URL
            u = urllib2.urlopen(self.url)
            self.remote_version = u.read()
            self.last = time.time()
            logging.log('xaupdate','Retrieved latest version information from %s' %self.url)
            logging.log('xaupdate','Latest version is %s' %self.remote_version)
            if xa.info.version != self.remote_version:
                logging.log('xaupdate','There is a newer version of XA available')
            else:
                logging.log('xaupdate','XA is up to date')
        except HTTPError:
            # error
            logging.log('xaupdate','Unable to download version information')

check = Check()

xamodule        = xa.register(info.basename)
xalanguage      = xamodule.language.getLanguage()



def load(): 
    # if we are loading xaupdate at the same time as server boot then we can safely run a check
    if es.ServerVar('eventscripts_currentmap') != "":
        es_map_start({})
    else:
        # otherwise just create a dummy menu
        create_menu()
    xamodule.addMenu('xaupdate_menu', xalanguage['xaupdate'], 'xaupdate_menu', 'xaupdate_menu', 'ADMIN')
    
def es_map_start():
    if check.last or (time.time()-last_check) > update_every:
        check.update()
        create_menu()
    
def create_menu():
    menu = popuplib.create('xaupdate_menu')
    menu.addline('XA Update Check')
    menu.addline(' ')
    menu.addline('XA Version:      %s' % xa.info.version)
    if check.remote_version:
        menu.addline('Current Release: %s' % check.remote_version)
    else:
        menu.addline('Current Release: %s' % check.remote_version)
    menu.addline(' ' )
    if None == check.last:
        menu.addline('Last checked:    Never')
    else:
        menu.addline('Last checked:    %s' % time.strftime("%d/%m/%y %H:%M",time.gmtime(check.last)))
    menu.addline(' ')
    if check.remote_version and xa.info.version != check.remote_version:
        menu.addline('A newer version is available!')
    else:
        menu.addline('XA is up to date')
    menu.addline(' ')
    menu.addline('->0. Close')
        
    
    

