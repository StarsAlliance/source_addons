#################################################
#                XAAUTHMANAGE.PY                #
#################################################

import es
import os.path
import shelve
import playerlib
import popuplib
import services
from xa import xa
from sqlite3 import dbapi2 as sqlite

info = es.AddonInfo()
info.name        = "Auth Manage"
info.version     = "0.7"
info.author      = "HitThePipe, freddukes"
info.basename    = "xaauthmanage"

class connection(object):
    def __init__(self,path):
        self.con = sqlite.connect(path)
        self.cur = self.con.cursor()
    def execute(self,sql):
        self.cur.execute(sql)
        self.con.commit()
    def query(self,sql):
        self.cur.execute(sql)
        return self.cur.fetchall()
    def close(self):
        self.con.close()


xaauthmanage = xa.register(info.basename)
lang = xaauthmanage.language.getLanguage()

auth = services.use('auth')
authaddon = auth.name
if authaddon not in ('group_auth','basic_auth'):
    raise ImportError('Unsupported Auth Provider!')

prefix = '#green[AuthManage]#default'

###################################################
#      EVENTS

def load():
    es.dbgmsg(1,'*****authmanage load')
    xaauthcmd = xaauthmanage.addCommand('xa_auth', _sendmain, 'manage_auth', 'ADMIN')
    xaauthcmd.register('say')
   
    if authaddon == 'group_auth':
        """ GroupAuth specific setup """
        global db,gauthmain,groupsmain,newgroup,usermenu,capmain
        db = connection(es.getAddonPath('examples/auth/group_auth') + '/es_group_auth.sqldb')

        xanewgroupcmd = xaauthmanage.addCommand('newgroup', _inputbox_handle, 'manage_auth', 'ADMIN', 'Add group')
        xanewgroupcmd.register('console')
		
        gauthmain = popuplib.easymenu('maingroupauthmenu',None,_gauthmain_select)
        gauthmain.settitle(lang['auth manage'])
        gauthmain.addoption('players', lang['current players'])
        gauthmain.addoption('groups', lang['groups'])
        gauthmain.addoption('users', lang['users'])
        gauthmain.addoption('capabilities', lang['capabilities'])
        xaauthmanage.addMenu('maingroupauthmenu',lang['xa menu choice'],'maingroupauthmenu','manage_auth','ADMIN')

        groupsmain = popuplib.create('groupsmainmenu')
        groupsmain.addline(lang('manage groups'))
        groupsmain.addlineAll('-------------------------------')
        groupsmain.addline(popuplib.langstring('->1. ',lang['groups users']))
        groupsmain.addline(popuplib.langstring('->2. ',lang['groups caps']))
        groupsmain.addline(popuplib.langstring('->3. ',lang['add group']))
        groupsmain.addline(popuplib.langstring('->4. ',lang['remove group']))
        groupsmain.addlineAll('-------------------------------')
        groupsmain.addline(popuplib.langstring('9. ',lang['main menu']))
        groupsmain.addline(popuplib.langstring('0. ',lang['close']))
        groupsmain.select(1,_groupsmain_select)
        groupsmain.select(2,_groupsmain_select)
        groupsmain.select(3,_newgroup_handle)
        groupsmain.select(4,_groupsmain_select)        
        groupsmain.submenu(9,'maingroupauthmenu')

        usermenu = popuplib.create('usermenu')
        usermenu.addlineAll('blah')
        usermenu.addlineAll('------------------')
        usermenu.addline(popuplib.langstring('->1. ',lang['drop user from group']))
        usermenu.addline(popuplib.langstring('->2. ',lang['add user to group']))
        usermenu.addline(popuplib.langstring('->3. ',lang['drop user from all groups']))
        usermenu.addlineAll('------------------')
        usermenu.addline(popuplib.langstring('->8. ',lang['back']))
        usermenu.addline(popuplib.langstring('->9. ',lang['main menu']))
        usermenu.addlineAll('------------------')
        usermenu.addline(popuplib.langstring('->0. ',lang['close']))
        usermenu.select(1,_user_groups)
        usermenu.select(2,_user_groups)
        usermenu.select(3,_user_dropfrom_all)
        usermenu.submenu(8,'usersmenu')
        usermenu.submenu(9,'maingroupauthmenu')

        capmain = popuplib.create('capmain')
        capmain.addline(lang['manage caps'])
        capmain.addlineAll('blah')
        capmain.addlineAll('------------------')
        capmain.addline(popuplib.langstring('->1. ',lang['cap groups']))
        capmain.addline(popuplib.langstring('->2. ',lang['add cap to group']))
        capmain.addline(popuplib.langstring('->3. ',lang['remove cap from group']))
        capmain.addlineAll('------------------')
        capmain.addline(popuplib.langstring('->8. ',lang['back']))
        capmain.addline(popuplib.langstring('->9. ',lang['main menu']))
        capmain.addlineAll('------------------')
        capmain.addline(popuplib.langstring('->0. ',lang['close']))
        capmain.select(1, _capmain_select)
        capmain.select(2, _capmain_select)
        capmain.select(3, _capmain_select)
        capmain.submenu(8,'capsmenu')
        capmain.submenu(9,'maingroupauthmenu')
        
        xaauthmanage.logging.log('group_auth use setup complete.')

    elif authaddon == 'basic_auth':
        """ BasicAuth specific setup """
        global bauthmain, b_admins, b_admins_path, admindetail, basicadmins, basicadmins_default, adminlevel
        b_admins = {}
        b_admins_path = es.getAddonPath('xa/modules/xaauthmanage') + '/admins'
        basicadmins_default = str(es.ServerVar('BASIC_AUTH_ADMIN_LIST'))
        es.dbgmsg(1,'basicadmins_default=%s' %basicadmins_default)
        basicadmins = basicadmins_default.split(';')
        _basic_auth_convar()
        adminlevel = 0        
        
        bauthmain = popuplib.easymenu('mainbasicauthmenu',None,_bauthmain_select)
        bauthmain.settitle(lang['auth manage'])
        bauthmain.addoption('players', lang['current players'])
        bauthmain.addoption('admins', lang['admin list'])	
        xaauthmanage.addMenu('mainbasicauthmenu',lang['xa menu choice'],'mainbasicauthmenu','manage_auth','ADMIN')
	
        admindetail = popuplib.create('admindetail')
        admindetail.addline(lang('admin detail'))
        admindetail.addlineAll('------------------')
        admindetail.addline('name')
        admindetail.addline('steam')
        admindetail.addline('userid')
        admindetail.addline('status')
        admindetail.addline('level')
        admindetail.addlineAll('------------------')
        admindetail.addline(popuplib.langstring('->1. ',lang['suspend admin']))
        admindetail.addline(popuplib.langstring('->2. ',lang['unsuspend admin']))
        admindetail.addline(popuplib.langstring('->3. ',lang['remove admin']))
        admindetail.addlineAll('------------------')
        admindetail.addline(popuplib.langstring('8. ',lang['main menu']))
        admindetail.addline(popuplib.langstring('9. ',lang['back']))
        admindetail.addline(popuplib.langstring('0. ',lang['close']))
        admindetail.select(1, _admin_suspend)
        admindetail.select(2, _admin_unsuspend) 
        admindetail.select(3, _admin_remove)
        admindetail.submenu(8, 'mainbasicauthmenu')
        admindetail.select(9, _adminlist)

        xaauthmanage.logging.log('basic_auth use setup complete.')
        
    """ 
    If the addon is loaded whilst people are playing, ensure they are in
    the database.
    """
    for player in es.getUseridList():
        fakeEventVariable = {}
        fakeEventVariable['es_steamid']  = es.getplayersteamid(player)
        fakeEventVariable['es_username'] = es.getplayername(player)
        player_activate(fakeEventVariable)
	
def unload():
    es.dbgmsg(1,'*****unload')
    if authaddon == 'basic_auth': 
        popuplib.delete('admindetail')
        if int(popuplib.exists('adminlistmenu')):
            popuplib.delete('adminlistmenu')
        es.dbgmsg(1,'basicadmins_default=%s' %basicadmins_default)
        es.set('BASIC_AUTH_ADMIN_LIST', basicadmins_default)
    elif authaddon == 'group_auth':
        popuplib.delete('groupsmainmenu')
        popuplib.delete('usermenu')
        popuplib.delete('capmain')
        if int(popuplib.exists('groupsmenu')):
            popuplib.delete('groupsmenu')
        if int(popuplib.exists('groupslist')):
            popuplib.delete('groupslist')
        if int(popuplib.exists('groupsusers')):
            popuplib.delete('groupsusers')
        if int(popuplib.exists('groupcaps')):
            popuplib.delete('groupcaps')
		
    if int(popuplib.exists('playermenu')):
        popuplib.delete('playermenu')

    xa.unregister(xaauthmanage)

def player_activate(event_var):
    if event_var['es_steamid'] != 'BOT':
        if authaddon == 'basic_auth':
            steamid, name = event_var['es_steamid'], event_var['es_username']
            _update_badmins(steamid,name,None,None)
       
def player_changename(event_var):
    if authaddon == 'basic_auth':
        _update_badmins(event_var['es_steamid'],event_var['newname'],None,None)


###################################################
#       MAIN MENUS SELECT

def _gauthmain_select(userid,choice,popupid):
    es.dbgmsg(1,'*****_gauthmain_select')
    if choice == 'players':
        _playerlist(userid)
    elif choice == 'groups':
        groupsmain.send(userid)
    elif choice == 'users':
        _userslist(userid)
    elif choice == 'capabilities':
        _capslist(userid)
    else:
        _sendmain()

def _bauthmain_select(userid,choice,popupid):
    es.dbgmsg(1,'*****_bauthmain_select')
    master = es.getplayersteamid(userid)
    b_admins = shelve.open(b_admins_path)
    if b_admins.has_key(master) and int(b_admins[master][1]):
        if choice == 'players':
            _playerlist(userid)
        elif choice == 'admins':
            _adminlist(userid)
    else:
        es.tell(userid,'#multi', prefix + lang('master access only'))
    b_admins.close	


###############################################
#   BASIC_AUTH METHODS

def _adminlist(userid,choice=None,popupid=None):
    es.dbgmsg(1,'*****_adminlist')
    global adminlist
    b_admins = shelve.open(b_admins_path)
    adminlist = popuplib.easymenu('adminlistmenu', None, _adminlist_select)
    for admin in b_admins:
        adminlist.addoption((admin,b_admins[admin]), b_admins[admin][0])
    adminlist.settitle(lang['admin list'])
    adminlist.send(userid)
    b_admins.close
        
def _adminlist_select(userid,choice,popupid):
    es.dbgmsg(1,'*****_adminlist_select')
    global admindetail
    es.set('_pdetails', 0)
    admindetail.modlineAll(3, choice[1][0])
    admindetail.modlineAll(4, choice[0])
    id = int(es.getuserid(choice[0]))
    if id:
        admindetail.modlineAll(5, 'Userid: %d' %id)
    else:
        admindetail.modlineAll(5, 'Userid: Not active')
    if not int(choice[1][2]):
        admindetail.modlineAll(6, lang['status good'])
    else:
        admindetail.modlineAll(6, lang['status suspended'])
    if int(choice[1][1]): 
        admindetail.modlineAll(7, lang['master'])
    else:
        admindetail.modlineAll(7, lang['normal'])
    admindetail.menuvalue('_pdetails',1,choice[0])
    admindetail.menuvalue('_pdetails',2,choice[0])
    admindetail.menuvalue('_pdetails',3,choice[0])
    admindetail.send(userid)

def _addadmin_select(userid,choice,popupid):
    es.dbgmsg(1,'*****_addadmin_select')
    if choice[1]:
        id = es.getuserid(choice[0])
        steamid = es.getplayersteamid(id)
        basicadmins = str(es.ServerVar('BASIC_AUTH_ADMIN_LIST'))
        basicadmins = basicadmins.split(';')
        if steamid not in basicadmins:
            _update_badmins(steamid,choice[0],'0','0')
        else:
            es.tell(userid, '#multi', prefix + choice[0] + ' is already an admin.')

def _admin_suspend(userid,choice,popupid):
    es.dbgmsg(1,'*****_admin_suspend')
    steamid = str(es.ServerVar('_pdetails'))
    _update_badmins(steamid,None,None,'1')

def _admin_unsuspend(userid,choice,popupid):
    es.dbgmsg(1,'*****_admin_unsuspend')
    _update_badmins(str(es.ServerVar('_pdetails')),None,None,'0')

def _admin_remove(userid,choice,popupid):
    es.dbgmsg(1,'*****_admin_remove')
    _update_badmins(str(es.ServerVar('_pdetails')),'_pdelete',None,None)
    
def _basic_auth_convar():
    es.dbgmsg(1,'*****_basic_auth_convar')       
    b_admins = shelve.open(b_admins_path)
    es.dbgmsg(1,'*****b_admins=%s' %b_admins)
    for admin in basicadmins_default.split(';'):
        es.dbgmsg(1,'*****admin=%s' %admin)
        if admin:                
            if not b_admins.has_key(admin):
                b_admins[admin] = ('-new-', '1', '0')
    newlist = ''
    for admin in b_admins:
        if not int(b_admins[admin][2]): #don't include suspended admins           
            newlist = newlist + admin + ';'
    es.set('BASIC_AUTH_ADMIN_LIST', newlist)
    b_admins.close()

def _update_badmins(steamid,name=None,master=None,suspend=None):
    es.dbgmsg(1,'*****_update_badmins')
    b_admins = shelve.open(b_admins_path)
    if b_admins.has_key(steamid):
        if name and b_admins[steamid][0] != name: #name change
            if name != '_pdelete':
                b_admins[steamid] = (name, b_admins[steamid][1], b_admins[steamid][2])
            else:
                del b_admins[steamid]
        if suspend and not master: #suspend/unsuspend admin
            b_admins[steamid] = (b_admins[steamid][0],b_admins[steamid][1],suspend)   
    elif name and master and suspend: #add new admin
        b_admins[steamid] = (name,master,suspend) 
    b_admins.close()
    _basic_auth_convar()    



#############################################
#    GROUP_AUTH METHODS

def _set_playergroup(userid,choice,popupid=None):
    es.dbgmsg(1,'*****_set_playergroup')
    steamid = '"' + es.getplayersteamid(es.getuserid(choice[1])) + '"'
    es.server.queuecmd('gauth user create %s %s' % (choice[1], steamid))
    es.server.queuecmd('gauth user join %s %s' %(choice[1], choice[0]))
  
  #========= gauthmain groups use ================
def _groupsmain_select(userid,choice,popupid):
    es.dbgmsg(1,'*****_groupsmain_select')
    global groupslist
    if choice != 3:
        groups = db.query("SELECT GroupName FROM Groups WHERE GroupName!='UnidentifiedPlayers' and GroupName!='IdentifiedPlayers';")
        if groups:
            if choice == 1:
                groupslist = popuplib.easymenu('groupslist', None, _groupusers_list)
                for group in groups:
                    es.dbgmsg(1,'*****group=%s' %group)
                    group = utfcode(group[0])
                    groupslist.addoption(group,group)
                groupslist.settitle(lang['select for users'])   
            if choice == 2:
                groupslist = popuplib.easymenu('groupslist', None, _groupcaps_list)
                for group in groups:
                    es.dbgmsg(1,'*****group=%s' %group)
                    group = utfcode(group[0])
                    groupslist.addoption(group,group)
                groupslist.settitle(lang['select for caps'])
            if choice == 4:
                groupslist = popuplib.easymenu('groupslist', None, _remove_group)
                for group in groups:
                    es.dbgmsg(1,'*****group=%s' %group)
                    group = utfcode(group[0])
                    groupslist.addoption(group,group)
                groupslist.settitle(lang['select remove group'])
            groupslist.send(userid)
        else:
            es.tell(userid, '#multi', prefix + lang('no groups'))    
    if choice == 3:
        _newgroup_handle(userid)

def _groupusers_list(userid,choice,popupid):
    es.dbgmsg(1,'*****_groupusers_list')
    users = db.query("SELECT ALL Name FROM vwPlayersGroups WHERE GroupName='%s'" %choice)
    if users:
        groupusers = popuplib.easymenu('groupusers', None, _groupuser_remove)
        for user in users:
            groupusers.addoption((user[0],choice), utfcode(user[0]))
        groupusers.settitle(choice + ' ' + lang('users') + '\n ' + lang('select to remove'))
        groupusers.send(userid)   
    else:
        es.tell(userid, '#multi', prefix + lang('no users in group') + ' ' + choice)

def _groupuser_remove(userid,choice=None,popupid=None):
    es.dbgmsg(1,'*****_groupuser_remove')
    es.server.queuecmd('gauth user leave %s %s' %(choice[0],choice[1]))
    if popupid == 'groupusers':
        groupsmain.send(userid)
    if popupid == 'usergroups':
        _userslist(userid)

def _groupcaps_list(userid,choice,popupid=None):
    es.dbgmsg(1,'*****_groupcaps_list')
    caps = db.query("SELECT ALL CName FROM vwCapsGroups WHERE GroupName='%s'" %choice)
    if caps:
        groupcaps = popuplib.easymenu('groupcaps', None, _groupcap_remove)
        for cap in caps:
            groupcaps.addoption((cap[0],choice), utfcode(cap[0]))
        groupcaps.settitle(choice + ' ' + lang('capabilities') + '\n ' + lang('select to remove'))
        groupcaps.send(userid)
    else:
        es.tell(userid, '#multi', prefix + lang('no caps in group') + ' ' + choice)       

def _groupcap_remove(userid,choice=None,popupid=None):
    es.dbgmsg(1,'*****_groupcap_remove')
    es.server.queuecmd('gauth power revoke %s %s' %(choice[0],choice[1]))
    groupsmain.send(userid) 

def _remove_group(userid,choice,popupid):
    es.dbgmsg(1,'*****_remove_group')
    es.server.queuecmd('gauth group delete %s' %choice)

def _newgroup_handle(userid,choice,popupid):
    es.dbgmsg(1,'*****_newgroup_handle')
    if auth.isUseridAuthorized(userid, 'manage_auth'):
        es.escinputbox(30,userid,'Add a group:\n <groupname- no spaces>, <grouptype>\n -Accepted types (in order of most powerful to least)\n- admin \n  poweruser \n  known \n  all','<groupname> <access level>','newgroup')

def _inputbox_handle():
    es.dbgmsg(1,'*****_inputbox_handle')
    userid = es.getcmduserid()    
    count = int(es.getargc())
    if count == 3:
        groupname = es.getargv(1)
        level = es.getargv(2)
        level = level.lower()        
        if level in ('root','admin','poweruser','known','all'):
            if level == 'root': 
                level = 0
            if level == 'admin': 
                level = 1
            if level == 'poweruser': 
                level = 2
            if level == 'known': 
                level = 4
            if level == 'all': 
                level = 128            
            es.server.queuecmd('gauth group create %s %d' %(groupname,level))
            es.esctextbox(10, userid, "New group added", "You have added group: %s with access level %s" %(groupname,level))
        else:
            es.esctextbox(10, userid, "Invalid level", "Accepted levels:\n -admin\n -poweruser\n -known\n -all")
    else:
        es.esctextbox(10, userid, "Invalid Entry", "<groupname-no spaces> <level>")
  #------------- end gauthmain groups use ------------------        

  #============= gauthmain users use =================
def _userslist(userid):
    es.dbgmsg(1,'*****_userslist')
    users = db.query("SELECT Name FROM Players WHERE Name!='UNKNOWN'")
    if users:
        global usersmenu
        usersmenu = popuplib.easymenu('usersmenu', None, _usersmenu_select)
        for user in users:
            usersmenu.addoption(user,utfcode(user[0]))
        usersmenu.settitle(lang('all users'))
        usersmenu.send(userid)    	
    else:
        es.dbgmsg(0,'*****no users')

def _usersmenu_select(userid,choice,popupid):
    es.dbgmsg(1,'*****_usersmenu_select')
    global usermenu
    es.set('_puser',0)
    usermenu.modlineAll(1,'User: %s' %choice)
    usermenu.menuvalue('_puser',1,choice[0])
    usermenu.menuvalue('_puser',2,choice[0])
    usermenu.menuvalue('_puser',3,choice[0])
    usermenu.send(userid)
	
def _user_groups(userid,choice,popupid):
    es.dbgmsg(1,'*****_user_groups')
    guser = utfcode(es.ServerVar('_puser'))
    if int(choice) == 1:
        groups = db.query("SELECT GroupName FROM vwPlayersGroups  WHERE Name='%s'" %guser)
        if groups:
            usergroups = popuplib.easymenu('usergroups', None, _groupuser_remove)
            for group in groups:
                usergroups.addoption((guser,group[0]), group[0])
            usergroups.settitle(lang('drop user from group'))
        else:
            es.tell(userid,'#multi',prefix + '#lightgreen' + guser + '#default' + lang('not in groups'))
    elif int(choice) == 2:
        es.dbgmsg(1,'*****add user to group')
        groups = db.query("SELECT GroupName FROM Groups WHERE GId NOT IN (SELECT GId FROM PlayersGroups WHERE UId=(SELECT Uid FROM Players WHERE Name='%s') AND (SELECT GId FROM Groups WHERE GId IN (SELECT GId FROM PlayersGroups))) AND GroupName!='UnidentifiedPlayers' AND GroupName!='IdentifiedPlayers'" %guser)
        if groups:
            usergroups = popuplib.easymenu('usergroups', None, _groupuser_add)
            for group in groups:
                usergroups.addoption((guser,group[0]), group[0])
            usergroups.settitle(lang('add user to group'))
        else:
            es.tell(userid,'#multi',prefix + '#lightgreen' + guser + '#default' + lang('in all groups'))
    if groups:
        usergroups.send(userid)

def _groupuser_add(userid,choice,popupid):
    es.dbgmsg(1,'*****_groupuser_add')
    es.server.queuecmd('gauth user join %s %s' %(choice[0],choice[1]))
    usermenu.send(userid)

def _user_dropfrom_all(userid,choice,popupid):
    es.dbgmsg(1,'*****_user_dropfrom_all')
    guser = utfcode(es.ServerVar('_puser'))
    es.server.queuecmd('gauth user delete %s' %guser)
  #------------- end gauthmain users use ------------------ 
 
  #============= gauthmain caps use ================= 
def _capslist(userid):
    es.dbgmsg(1,'*****_capslist')
    global capsmenu
    caps = db.query("SELECT ALL CName FROM Caps")
    if caps:
        capsmenu = popuplib.easymenu('capsmenu', None, _capsmenu_select)
        for cap in caps:
            capsmenu.addoption(cap[0],cap[0])
        capsmenu.settitle(lang('capabilities'))
        capsmenu.send(userid)
    else:
        es.tell(userid,'#multi',prefix + '#lightgreen' + guser + '#default' + lang('no registered capabilities'))

def _capsmenu_select(userid,choice,popupid):
    es.dbgmsg(1,'*****_capsmenu_select')
    global capmain
    es.set('_pcap',0)
    capmain.modlineAll(2,' - ' + choice)
    capmain.menuvalue('_pcap',1,choice)
    capmain.menuvalue('_pcap',2,choice)
    capmain.menuvalue('_pcap',3,choice)
    capmain.send(userid)

def _capmain_select(userid,choice,popupid):
    es.dbgmsg(1,'*****_capmain_select')
    global capgroups
    capname = es.ServerVar('_pcap')
    if int(choice) == 1:
        groups = db.query("SELECT GroupName FROM Groups WHERE GId IN (SELECT GId FROM GroupCaps WHERE GroupCaps.CId=(SELECT CId FROM Caps WHERE CName='%s'))" %capname)
        if groups:
            action = 'go'
            capgroups = popuplib.easymenu('capgroups',None,_capgroup_set)
            for group in groups:	
                capgroups.addoption((action,capname,group[0]),utfcode(group[0]))
            capgroups.settitle(lang('cap groups'))                   
        else:
            es.tell(userid,'#multi',prefix + '#lightgreen' + capname + '#default' + lang('not in groups'))
            capmain.send(userid)
    elif int(choice) == 2:
        groups = db.query("SELECT GroupName FROM Groups WHERE GId NOT IN (SELECT GId FROM GroupCaps WHERE GroupCaps.CId=(SELECT CId FROM Caps WHERE CName='%s'))" %capname)
        if groups:
            action = 'give'
            capgroups = popuplib.easymenu('capgroups',None,_capgroup_set)
            for group in groups:	
                capgroups.addoption((action,capname,group[0]),utfcode(group[0]))
            capgroups.settitle(lang('add cap to group'))              
        else:
            es.tell(userid,'#multi',prefix + '#lightgreen' + capname + '#default' + lang('in all groups'))
    elif int(choice) == 3:
        groups = db.query("SELECT GroupName FROM Groups WHERE GId IN (SELECT GId FROM GroupCaps WHERE GroupCaps.CId=(SELECT CId FROM Caps WHERE CName='%s'))" %capname)
        if groups:
            action = 'revoke'
            capgroups = popuplib.easymenu('capgroups',None,_capgroup_set)
            for group in groups:	
                capgroups.addoption((action,capname,group[0]),utfcode(group[0]))
            capgroups.settitle(lang('remove cap from group'))              
        else:
            es.tell(userid,'#multi',prefix + '#lightgreen' + capname + '#default' + lang('not in groups'))
    es.dbgmsg(1,'*****groups=%s' %groups)
    if groups:
        capgroups.send(userid)
    #else:
    #    capmain.send(userid)
def _capgroup_set(userid,choice,popupid):
    es.dbgmsg(1,'*****_capgroup_set')
    if choice[0] == 'go':
        _groupcaps_list(userid,choice[2],None)        
    else:
        es.server.queuecmd('gauth power %s %s %s' %(choice[0],choice[1],choice[2]))
        capmain.send(userid)    
    


#############################################
#    COMMON METHODS

def utfcode(value):
    if type(value).__name__ == 'unicode':
        return value.encode('utf-8')
    return value
 
def convertQuery(result):
    newresult = list()
    for row in result:
        newrow = [utfcode(item) for item in row]
        newresult.append(newrow)
    return newresult

def _sendmain():
    es.dbgmsg(1,'*****_sendmain')
    userid = es.getcmduserid()
    if auth.isUseridAuthorized(userid, 'manage_auth'):
        if authaddon == 'group_auth':
            gauthmain.send(userid)
        elif authaddon == 'basic_auth':
            master = es.getplayersteamid(userid)
            b_admins = shelve.open(b_admins_path)
            if b_admins.has_key(master) and int(b_admins[master][1]):
                bauthmain.send(userid)
            else:
                es.tell(userid,'#multi', prefix + lang('master access only'))
            b_admins.close
    else:
        es.tell(userid, '#multi', prefix + lang('master access only'))	

def _playerlist(userid):
    es.dbgmsg(1,'*****_playerlist')
    global playermenu
    #uncomment following line, #all is for testing only	
    players = playerlib.getPlayerList('#human')
    #players = playerlib.getPlayerList('#all')
    playermenu = popuplib.easymenu('playermenu',None,_manage_player)
    for player in players:
        name = player.get('name')
	# bug 29 - strip special chars from names
	name = names.translate(None,'\'\\"/- #')
        playermenu.addoption(name,utfcode(name))
    playermenu.settitle(lang['current players'])
    playermenu.send(userid)
    
def _manage_player(userid,choice,popupid):
    es.dbgmsg(1,'*****_manage_player')
    if authaddon == 'group_auth':
        groups = db.query("SELECT GroupName FROM Groups WHERE GroupName!='UnidentifiedPlayers' and GroupName!='IdentifiedPlayers';")
        if popuplib.exists('groupsmenu'):
            popuplib.delete('groupsmenu')
        groupsmenu = popuplib.easymenu('groupsmenu', None, _set_playergroup)
        for group in groups:
            group = utfcode(group)
            groupsmenu.addoption((group[0],choice), utfcode(group[0]))
        groupsmenu.settitle(choice + '\n-' + lang('add player to group'))
        groupsmenu.send(userid)
    else:
        global addadmin
        addadmin = popuplib.easymenu('addadmin', None, _addadmin_select)
        token = {'choice':str(choice)}
        addadmin.settitle(lang('make admin', token))
        addadmin.addoption((choice,1), lang['yes'])
        addadmin.addoption('no',lang['no'])
        addadmin.send(userid)
