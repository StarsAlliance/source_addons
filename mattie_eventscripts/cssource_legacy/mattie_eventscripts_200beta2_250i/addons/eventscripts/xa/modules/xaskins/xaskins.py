import es
import os
import popuplib
import playerlib
from xa import xa

info = es.AddonInfo()
info.name           = "Skins"
info.version        = "0.5"
info.author         = "Don"
info.basename       = "xaskins"

skinmenu                = ['Admin T', 'Admin CT', 'Public T', 'Public CT', 'Reserved T', 'Reserved CT', 'Misc']
skinnames               = ['admin_t', 'admin_ct', 'public_t', 'public_ct', 'reserved_t', 'reserved_ct', 'misc']
skinlist                = {}
playermenu              = {}
skins_downloadable      = 1

if xa.isManiMode():
    xaskins_skinfiles_path  = xa.gamedir() + "/cfg/mani_admin_plugin/skins/"
else:
    xaskins_skinfiles_path  = xa.gamedir() + "/cfg/xa/skins/"

###############
### GLOBALS ###
###############

xaskins                 = xa.register(info.basename)
xalanguage              = xaskins.language.getLanguage()

players = {}
players['exists']         = xaskins.playerdata.createUserSetting("exists")
players['admin_t']        = xaskins.playerdata.createUserSetting("admin_t")
players['admin_ct']       = xaskins.playerdata.createUserSetting("admin_ct")
players['reserved_t']     = xaskins.playerdata.createUserSetting("reserved_t")
players['reserved_ct']    = xaskins.playerdata.createUserSetting("reserved_ct")
players['public_t']       = xaskins.playerdata.createUserSetting("public_t")
players['public_ct']      = xaskins.playerdata.createUserSetting("public_ct")

skins = {}
skins['admin_t_skin']        = xaskins.playerdata.createUserSetting("admin_t_skin")
skins['admin_ct_skin']       = xaskins.playerdata.createUserSetting("admin_ct_skin")
skins['reserved_t_skin']     = xaskins.playerdata.createUserSetting("reserved_t_skin")
skins['reserved_ct_skin']    = xaskins.playerdata.createUserSetting("reserved_ct_skin")
skins['public_t_skin']       = xaskins.playerdata.createUserSetting("public_t_skin")
skins['public_ct_skin']      = xaskins.playerdata.createUserSetting("public_ct_skin")

def load():
    """
    This function is called when the script is es_load-ed 
    Register client console and server command
    """
    xaskins.registerCapability("skin_admin", "ADMIN")
    xaskins.registerCapability("skin_reserved", "POWERUSER")
    xaskincommand = xaskins.addCommand("xaskin", _sendmenu, "set_skin", "UNRESTRICTED")
    xaskincommand.register(['console', 'server'])
    xaskins.addRequirement('xasettings')
    xaskins.xasettings.registerMethod("xaskins", _sendmenu, xalanguage["player skins"])
    check_if_files_exist()
    if str(es.ServerVar('eventscripts_currentmap')) != "": es_map_start(None)

def unload():
    """ This function is called when the script is es_unload-ed """
    xaskins.xasettings.unregister("xaskins")
    xaskins.delRequirement("xasettings")
    xaskins.unregister()

def es_map_start(event_var):
    for i in range(7):
        add_skin_files(i)

def player_activate(event_var):
    """
    This function is called when a player is validated
    Check if the player is in the database yet
    If not in the database then go create a record
    """
    create_record(event_var)
        
def player_spawn(event_var):
    """
    This function is called when a player spawns.  It gets the player's current level
    Check if the player is in the database yet
    If not in the database then go create a record
    """
    if es.getplayerprop(event_var['userid'], 'CBasePlayer.pl.deadflag'):
        """ This accounts for the spawn event which runs before player_activate """
        return
    create_record(event_var)
    """ then gets the team and then the model and sets it """
    if event_var['es_steamid'] != "BOT":
        if event_var['es_userteam'] in ("2", "3"):
            if xaskins.isUseridAuthorized(int(event_var['userid']), "skin_admin"):
                level = "admin"
            elif xaskins.isUseridAuthorized(int(event_var['userid']), "skin_reserved"):
                level = "reserved"
            else:
                level = "public"
            team = {"2":"t", "3":"ct"}[event_var['es_userteam']]
            xaplayerdata_skin = skins[level + '_' + team + '_skin']
            model = xaplayerdata_skin.get(int(event_var['userid']))
            if str(model) != "None":
                myPlayer = playerlib.getPlayer(event_var['userid'])
                myPlayer.set('model', model)
                
def create_record(event_var):
    userid = int(event_var['userid'])
    if not players['exists'].exists(userid):
        players['exists'].set(userid, "1")
        players['admin_t'].set(userid, "None")
        players['admin_ct'].set(userid, "None")
        players['reserved_t'].set(userid, "None")
        players['reserved_ct'].set(userid, "None")
        players['public_t'].set(userid, "None")
        players['public_ct'].set(userid, "None")
        skins['admin_t_skin'].set(userid, "None")
        skins['admin_ct_skin'].set(userid, "None")
        skins['reserved_t_skin'].set(userid, "None")
        skins['reserved_ct_skin'].set(userid, "None")
        skins['public_t_skin'].set(userid, "None")
        skins['public_ct_skin'].set(userid, "None")
        xaskins.playerdata.saveUserSetting()
    
def _sendmenu(playerid = False):
    """ This function handles the console and client command.  Probably need to modify for use with XA """
    if not playerid:
        playerid = es.getcmduserid()
    if popuplib.exists("xaskinmenu" + str(playerid)):
        popuplib.delete("xaskinmenu" + str(playerid))
    page = popuplib.easymenu("xaskinmenu" + str(playerid), "_tempcore", _selectmenu)
    # This is commented out becuase popuplib seems to have a bug
    # page.cachemode = "user"
    page.settitle(xalanguage["choose skins"])
    for skinName in skinmenu:
        skinIndex = skinmenu.index(skinName)
        if (skinName != "Misc") and ((xaskins.isUseridAuthorized(playerid, "skin_admin") and ("admin" == skinnames[skinIndex][:5])) or \
                (xaskins.isUseridAuthorized(playerid, "skin_reserved") and ("reserved" == skinnames[skinIndex][:8])) or \
                ("public" == skinnames[skinIndex][:6])):
            xaplayerdata = players[skinnames[skinIndex]]
            mySkin       = xaplayerdata.get(playerid)
            page.addoption(skinnames[skinIndex], xaskins.language.createLanguageString(skinName + " - " + mySkin) )
    page.send(playerid)

def _selectmenu(userid, choice, name):
    """ This function makes the submenu for whichever set of skins was chosen """
    playermenu[userid] = choice
    if popuplib.exists("xaskinselect"+str(userid)):
        popuplib.delete("xaskinselect"+str(userid))
    page = popuplib.easymenu("xaskinselect"+str(userid), "_tempcore", _selectsubmenu)
    # This is commented out becuase popuplib seems to have a bug
    # page.cachemode = "user"
    page.settitle(xalanguage["choose skins"])
    if choice in skinlist:
        for skinName in skinlist[choice]:
            page.addoption(skinName, xaskins.language.createLanguageString(skinName) )
    else:
        page.addoption(None, xalanguage["no skins"], False)
    page.submenu(0, "xaskinmenu%s" % userid)
    page.c_exitformat = "0. Back"
    page.send(userid)

def _selectsubmenu(userid, choice, name):
    """ In this function we need to set the model path into the player's settings """
    if choice:
        levelset          = playermenu[userid]
        mynewskin         = skinlist[levelset][choice]
        xaplayerdata      = players[levelset]
        xaplayerdata_skin = skins[levelset + '_skin']
        xaplayerdata.set(userid, choice)
        #xaplayerdata_skin.set(userid, choice)
        xaplayerdata_skin.set(userid, mynewskin)
        xaskins.playerdata.saveUserSetting()
    
def add_skin_files(skinIndex):
    """ This function reads in the 7 main skin files and parses each one """
    skinName = skinnames[skinIndex]
    skinlist[skinName] = {}
    filePath = xaskins_skinfiles_path + skinName + ".txt" 
    fp = open(filePath, "r")
    lines = map(lambda x: x.strip(), filter(lambda x: not x.startswith('//') and bool(x.strip()), fp.read().split("\n") ) )
    fp.close()
    for line in lines:
        if line[0] != '"':
            xaskins.logging.log("Line \"%s\" inside file %s does not encase the file name in quotes"%(line, filePath))
            return
        lastSpace = line.rfind(' ')
        if lastSpace == -1:
            xaskins.logging.log("Cannot find a space within the line \"%s\""%line)
            return
        skinfile  = line[lastSpace + 1:]
        skinname  = line[:lastSpace]
        skinname  = skinname.strip('"')
        skinmodel = makedownloadable(skinfile, skinName)
        skinlist[skinName][skinname] = skinmodel
            
def makedownloadable(skinfile,skingroup):
    """ This function reads each model/material list files and makes them downloadable if cvar set.  Also returns model name """
    strPath = xaskins_skinfiles_path + skingroup + "/" + skinfile
    if not os.path.isfile(strPath):
        xaskins.logging.log("Cannot find the text file which contains all the download files for skin %s"%skingroup)
        return None
    sp = open(xaskins_skinfiles_path + skingroup + "/" + skinfile, "r")
    for line in sp:
        line = line.strip()
        if not line.startswith('//') and bool(line):
            if not line.count("."):
                """ Allow users to just give us folder names """
                directory = os.path.join(xa.gamedir(), line ) 
                if os.path.isdir(directory):
                    for fileName in os.listdir(directory):
                        if skins_downloadable == 1:
                            es.stringtable("downloadables", line + "/" + fileName)
                        if fileName.endswith('.mdl'):
                            model = line + "/" + fileName
            else:
                if skins_downloadable == 1:
                    es.stringtable("downloadables", line)
                if line.endswith('.mdl'):
                    model = line
    return model
            
def findsplit(phrase):
    """ This function just splits the lines in the main skin files and returns the line position of the split """
    return phrase.rfind(" ")

def check_if_files_exist():
    if not os.path.isdir(xa.gamedir() + "/cfg/xa"):
        os.mkdir(xa.gamedir() + "/cfg/xa")
    if not os.path.isdir(xaskins_skinfiles_path):
        os.mkdir(xaskins_skinfiles_path)
    for fileName in skinnames:
        if not os.path.isfile(xaskins_skinfiles_path + fileName + ".txt"):
            open(xaskins_skinfiles_path + fileName + ".txt", 'w').close()
        if not os.path.isdir(xaskins_skinfiles_path + fileName):
            os.mkdir(xaskins_skinfiles_path + fileName)
    installationFilePath = xaskins_skinfiles_path + "_INSTALLATION.txt" 
    if not os.path.isfile(installationFilePath):
        fileStream = open(installationFilePath, 'w')
        fileStream.write("""\
--------------
XASkins by Don
    ../cfg/xa/skins/_INSTALLATION.txt
--------------

Skins is an eXtensible Admin module created by Don. This installation file
will help you set up custom skins for your server.

To first enable skins, you need to open your xa.cfg found in ../cfg/ and
remove the "//" at the start of the following line:
// xa load xaskins

xaskins will now load as a default module whenever the server starts.

If you ave reached this file, in the same directory as this (../cfg/xa/skins)
you should see several text files and several folders.

---------------
Adding skins to the menu
---------------

The basic principle of setting up skins is as follows:

    1. Set it up so the server adds the skins into the menu.
    2. Make sure that the server knows the correct model paths to your models
       and materials.
       
We are going to discuss option 1 in this section.

The basic overview of XASkins is to allow several user groups to have individual
skins, and it gives them the choice of which skin to pick. The skins are based
on their powers and team. Each "power" has two teams, (t and ct). This allows
each user group (or power) to have seperate models available dependant on which
team they are in. Lets take an example, consider a user having the power level
of administration. They have 2 files assosiated to the admin power:

    o admin_t  - the models available to terrorist admins
    o admin_ct - the models available to counter-terrorist admins
    
Within each of these files, you can place a model on each line. The correct
syntax of the line should be as follows:

    "Model Name As Shown On Popup" file_to_show_downloads.txt
    
Now, there are two parts of this line. The first part is the name which will be
showed to all users. E.g. If we had "Terrorist Admin Skin" then when the user
brings up the menu, "Terrorist Admin Skin" will be displayed there. This name
must be enclosed in quotation marks ("").

The second part is the file assosiated with model. This part is just a file name.
The location of this file should be in the following directory:

    o ../cfg/xa/skins/<power_team>/
    
For example, if this skin is for the power group "admin" and for "terrorists",
the file must be places within:

    o ../cfg/xa/skins/admin_t/
    
The next section will help you set up the downloads. If you want to know what
the powers mean, scroll to the end of this installation file which will tell you
what each power group means.

---------------
Setting up the model paths
---------------

As I stated in the previous section, the server must know where to get your
models from. The way we do this is by creating a .txt file in the folder directory
of ../cfg/xa/skins/<power_team>/.

In the previous part, we added a skin to the menu by opening:

    o ../cfg/xa/skins/admin_t.txt
    
and adding the line:

    o "My Model Name" modeldownloads.txt
    
As I have said, the second part will tell the server which file to read the
downloads from. Because we are working on "admin_t" this file must be located within:
    
    o ../cfg/xa/skins/admin_t/
    
So, create a new file in that directory and name it "modeldownloads.txt". The
directory of the file should be as follows:

    o ../cfg/xa/skins/admin_t/modeldownloads.txt
    
Open the file in notepad. We now have to write our model locations on a new line.
You have two choices here:

    1. Name every specific model / material
    2. Only give the folder path to the models and materials
    
I will be working on the latter option since it's simpler. Lets imagine the path
to the models from the ../cstrike/ directory is as follows:

    o models/player/ics/admin_skin

Imagine that within that folder, it should contain all the models and files
related to your admin model you wish to use (generally there are 6 files;
.dx80.vtx, .dx90.vtx, .mdl, .phy, .sw.vtx and .vvd). Rather than specifying
each individual file, just put the following line in:

models/player/ics/admin_skin

and every file within that folder will be added to the download list and all
clients who join your server will download that file.

Also, just a reminder, you have to do the same for your materials. The materials
location is USUALLY in the exact same location as your "models", except it starts
with materials first. So in this case, the material directory would be as follows:

materials/models/player/ics/admin_skin

Just to reiterate, you can give the exact path to your model or material, so the
following is also legal:

models/player/ics/admin_skin/admin_skin.mdl

If you have followed this correctly, you should have a file in:

    o ../cfg/xa/skins/admin_t/modeldownloads.txt
    
With the following in between the lines within that file:
--------------------------------------
models/player/ics/admin_skin
material/smodels/player/ics/admin_skin
--------------------------------------

To get the file to be recognised, just restart your server and you'll be able
to access your skins by sayig "xa" in chat and going to:

    Player Settings > Skins
    
That is all, thank you for reading.

---------------
Power List
---------------

The following list is a definition of each of the powers:

    o admin - Administrator. If you are using capibilities (such as group auth)
              then the admins must have the power "skin_admin"
              
    o reserved - This power is generally assosiated with players who donate to
                 your server for example. They don't have true power, yet they
                 have additional services which the generic public don't get.
                 They must be a "POWERUSER" and have the right "skin_reserved"
                 
    o public - This usergroup is for anyone joining your server. Everybody who
               joins instantly gets this capability.
               
    o misc - Stands for "miscelaneous". The reason this doesn't have a team is
             because it will not show up in the menu and thus users can't
             choose skins from the ones you right in this text file. The only
             reason this is here is to allow others to download scripts. This
             will only be used by people who force a skin by other means
             (such as another mod.) The only thing putting skins in this file
             will do is download them.

----------------
Additional reads:
----------------

   o http://eventscripts.com/pages/Authorization_FAQ

An FAQ regarding authorization rights. It also tells you what POWERUSER and ADMIN
mean.""")
        fileStream.close()