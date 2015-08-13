import settinglib
from settinglib import Setting_base

import es
import os
import time
import playerlib
import popuplib

import psyco
psyco.full()

## Setting_setting class is the setting base class
class Setting_list(Setting_base):
    def __init__(self, pSettingid, pDescription, pFilename, pFiletype):
        #initialization of setting
        self.name = pSettingid          #setting name for backwards compatibility
        self.descr = pDescription       #description
        self.filename = pFilename
        self.filetype = pFiletype
        Setting_base.__init__(self, 'list')
    def send(self, pUsers, prio=False, locked=False):
        try:
            # try if pUsers is just a single userid
            userid = int(pUsers)
            pUsers = [userid]
        except TypeError:
            pass
        if locked:
            optionstate = 0
        else:
            optionstate = 1
        for userid in pUsers:
            player = playerlib.getPlayer(userid)
            if player:
                steamid = playerlib.uniqueid(userid, True)
                helpline = self.languages('setting '+self.keyvalues['config']['type']+' help', (), player.get('lang'))
                self.popup[userid] = popuplib.easymenu('_setting_%s_user%s' % (self.name, userid), '_setting_choice', settinglib._submit)
                self.popup[userid].settingid = self.name
                self.popup[userid].c_titleformat = self.keyvalues['config']['descr'] + (' '*(30-len(self.keyvalues['config']['descr']))) + ' (%p/%t)\n' + helpline
                if not steamid in self.keyvalues['users']:
                    self.initUser(userid)
                for option in self.keyvalues['options']:
                    display = self.keyvalues['options'][option]['display']
                    userdata = self.keyvalues['users'][steamid]['data']
                    if option in userdata:
                        if userdata[option]['state']:
                            active = self.languages('setting list active', (), player.get('lang'))
                            self.popup[userid].addoption(int(option), display + ' ('+active+')', optionstate)
                            continue
                    self.popup[userid].addoption(int(option), display, optionstate)
                if self.backmenuvar:
                    self.popup[userid].submenu(10, self.backmenuvar)
                self.popup[userid].send(userid, prio)
    def sendglobal(self, pUsers, prio=False, locked=False):
        try:
            # try if pUsers is just a single userid
            userid = int(pUsers)
            pUsers = [userid]
        except TypeError:
            pass
        if locked:
            optionstate = 0
        else:
            optionstate = 1
        for userid in pUsers:
            player = playerlib.getPlayer(userid)
            if player:
                helpline = self.languages('setting '+self.keyvalues['config']['type']+' help', (), player.get('lang'))
                self.popup['global'] = popuplib.easymenu('_setting_%s_user%s_global' % (self.name, userid), '_setting_choice', settinglib._submitGlobal)
                self.popup['global'].settingid = self.name
                self.popup['global'].c_titleformat = self.keyvalues['config']['descr'] + (' '*(30-len(self.keyvalues['config']['descr']))) + ' (%p/%t)\n' + helpline
                for option in self.keyvalues['options']:
                    display = self.keyvalues['options'][option]['display']
                    userdata = self.keyvalues['options']
                    if option in userdata:
                        if userdata[option]['globstate']:
                            active = self.languages('setting list active', (), player.get('lang'))
                            self.popup['global'].addoption(int(option), display + ' ('+active+')', optionstate)
                            continue
                    self.popup['global'].addoption(int(option), display, optionstate)
                if self.backmenuvar:
                    self.popup['global'].submenu(10, self.backmenuvar)
                self.popup['global'].send(userid, prio)
    def menuUserSubmit(self, userid, value):
        if es.exists('userid',userid):
            self.set(int(value), userid)
            if self.keyvalues['config']['sound']:
                es.playsound(userid, self.keyvalues['config']['sound'], 1.0)
            if self.keyvalues['config']['resend']:
                self.send(userid, True)
    def menuUserGlobalSubmit(self, userid, value):
        if es.exists('userid',userid):
            self.set(int(value))
            if self.keyvalues['config']['sound']:
                es.playsound(userid, self.keyvalues['config']['sound'], 1.0)
            if self.keyvalues['config']['resend']:
                self.sendglobal(userid, True)
    def setoption(self, option, text, state=None):    #edit/add an option
        option = self.isValidOption(option)
        if option:
            for thisoption in self.keyvalues['options']:
                if int(thisoption) == int(option):
                    self.keyvalues['options'][thisoption]['display'] = text
                    if state:
                        self.keyvalues['options'][thisoption]['state'] = 1
                    else:
                        self.keyvalues['options'][thisoption]['state'] = 0
            self.save()
        else:
            es.dbgmsg(0,'Settinglib: Cannot modify option #%s(%s) in %s' % (option, text, self.name))
    def addoption(self, key, text, state=None):            #add an option to the end of the list
        option = len(self.keyvalues['options'].keys())+1
        for thisoption in self.keyvalues['options']:
            if self.keyvalues['options'][thisoption]['keyname'] == key:
                option = thisoption
        self.keyvalues['options'][option] = self.createKey(option)
        self.keyvalues['options'][option]['keyname'] = key
        self.keyvalues['options'][option]['display'] = text
        if state:
            self.keyvalues['options'][option]['state'] = 1
            self.keyvalues['options'][option]['globstate'] = 1
        else:
            self.keyvalues['options'][option]['state'] = 0
            self.keyvalues['options'][option]['globstate'] = 1
        self.save()
    def deloption(self, option):          #delete an option
        arg = option
        option = self.isValidOption(option)
        if option:
            options = len(self.keyvalues['options'].keys())
            for thisoption in range(int(option),options):
                if (thisoption+1) in self.keyvalues['options']:
                    self.keyvalues['options'][thisoption] = self.keyvalues['options'][thisoption+1]
            del self.keyvalues['options'][options]
            for steamid in self.keyvalues['users']:
                for thisoption in range(int(option),options):
                    if (thisoption+1) in self.keyvalues['users'][steamid]['data']:
                        self.keyvalues['users'][steamid]['data'][thisoption] = self.keyvalues['users'][steamid]['data'][thisoption+1]
                if options in self.keyvalues['users'][steamid]['data']:
                    del self.keyvalues['users'][steamid]['data'][options]
            self.save()
        else:
            raise IndexError('Settinglib: Cannot delete option %s, it does not exists'%arg)
    def setdefault(self, option, overwrite=None):
        arg = option
        option = self.isValidOption(option)
        if option:
            for thisoption in self.keyvalues['options']:
                if thisoption == option:
                    self.keyvalues['options'][thisoption]['state'] = 1
                else:
                    self.keyvalues['options'][thisoption]['state'] = 0
            if overwrite:
                for steamid in self.keyvalues['users']:
                    for thisoption in self.keyvalues['users'][steamid]['data']:
                        if thisoption == option:
                            self.keyvalues['users'][steamid]['data'][thisoption]['state'] = 1
                        else:
                            self.keyvalues['users'][steamid]['data'][thisoption]['state'] = 0
        else:
            raise IndexError('Settinglib: Cannot set option %s as default, it does not exists'%arg)
    def set(self, option, userid=None):
        arg = option
        option = self.isValidOption(option)
        if option:
            if userid:
                steamid = playerlib.uniqueid(userid, True)
                if steamid:
                    if not steamid in self.keyvalues['users']:
                        self.initUser(int(userid))
                    for thisoption in self.keyvalues['users'][steamid]['data']:
                        if thisoption == option:
                            self.keyvalues['users'][steamid]['data'][thisoption]['state'] = 1
                        else:
                            self.keyvalues['users'][steamid]['data'][thisoption]['state'] = 0
                else:
                    raise IndexError('Settinglib: Cannot find userid %s'%userid)
            else:
                for thisoption in self.keyvalues['options']:
                    if thisoption == option:
                        self.keyvalues['options'][thisoption]['globstate'] = 1
                    else:
                        self.keyvalues['options'][thisoption]['globstate'] = 0
        else:
            raise IndexError('Settinglib: Cannot set option #%s, it does not exists'%arg)
    def get(self, userid=None):
        if userid:
            steamid = playerlib.uniqueid(userid, True)
            if steamid:
                if not steamid in self.keyvalues['users']:
                    self.initUser(userid)
                for thisoption in self.keyvalues['users'][steamid]['data']:
                    if self.keyvalues['users'][steamid]['data'][thisoption]['state']:
                        return self.keyvalues['options'][thisoption]['keyname']
            else:
                raise IndexError('Settinglib: Cannot find userid %s'%option)
        else:
            for thisoption in self.keyvalues['options']:
                if self.keyvalues['options'][thisoption]['globstate']:
                    return self.keyvalues['options'][thisoption]['keyname']
    def toggle(self, option, userid=None):
        arg = option
        option = self.isValidOption(option)
        if option:
            if self.keyvalues['config']['type'] == 'toggle':
                state = self.get(option, userid)
                if state:
                    self.set(option, False, userid)
                else:
                    self.set(option, True, userid)
            else:
                raise TypeError('Settinglib: Cannot toggle a setting with type list')
        else:
            raise IndexError('Settinglib: Cannot toggle option #%s, it does not exists'%arg)
