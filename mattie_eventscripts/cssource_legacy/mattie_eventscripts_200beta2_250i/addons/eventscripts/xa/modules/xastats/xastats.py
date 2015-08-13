import es
import playerlib
import time
import popuplib
import thread
from xa import xa

#######################################
# ADDON INFORMATION
# This describes the XA module
info = es.AddonInfo()
# TODO: Change this to your module's data.  -- TODO
info.name           = "Stats Module"
info.version        = "0.9"
info.author         = "Carlsagan43 (Adminc)"
info.basename       = "xastats"


#######################################
# MODULE SETUP
# Register the module
# this is a global reference to our module
xastats = xa.register(info.basename)

directory = str(es.ServerVar('eventscripts_gamedir')).replace('\\', '/').split('/')[~0]

#######################################
# SERVER VARIABLES
# The list of our server variables
stats_mode              = xastats.setting.createVariable('stats_calculate', 3, "This defines how the stats are caclulated, 0 = by player kills, 1 = by player kill death ratio, 2 = by kills - deaths, 3 = by points")
stats_unique            = xastats.setting.createVariable('stats_unique', 0, "Should players be remembered by steamid or by ip address, 0 = steamid, 1 = ip address. It would be best to use ip addresses when the server is on LAN mode")
stats_pdf               = xastats.setting.createVariable('stats_pdf', 1, "Should the probability density function be used to tell players their chance of getting a high kill streak. If you don't know what this means, it's ok to just leave this alone. If you your server has limited CPU power, then turn this off")
stats_pdfthreshold      = xastats.setting.createVariable('stats_pdfthreshold', 4, "If pdf is turned on, how many kills in a row should the player have before telling them their chance of getting that many kills. Set this higher if you feel that the players on your server regularly get more than 4 kills.")
stats_silent            = xastats.setting.createVariable('stats_silent', 0, "When a player types !statsme, !session, or !rank, should other player see that the player typed it in? 0 = tell everyone, 1 = tell no one")
stats_publicrank        = xastats.setting.createVariable('stats_show_rank_to_all', 1, "This defines whether the command 'rank' is shown to all or not (1 = all players)")
stats_rankdays          = xastats.setting.createVariable('stats_ignore_ranks_after_x_days', 21, "Number of days before a player is made invisible from ranks. If the player rejoins, they are re added to the ranks")
stats_headshot          = xastats.setting.createVariable('stats_points_headshot_multiplier', 1.2, "This is the headshot multiplier. Set it to 1.0 if yout dont want players to get more points for getting headshots")
stats_killmult          = xastats.setting.createVariable('stats_points_multiplier', 5.0, "Kill multiplier. This is multiplied into the point the attacker gets for killing a player")
stats_deathmult         = xastats.setting.createVariable('stats_points_death_multiplier', 1.0, "Death multiplier. This is multiplied into the number of points the victim loses when he gets killed. Set this to 0.0 to turn off point loss")
stats_minkills          = xastats.setting.createVariable('stats_kills_minimum', 10, "Minimum number of kills needed to affect the victim's points. This helps keep new players from overly affecting the score of long time players")
stats_rankthreshold     = xastats.setting.createVariable('stats_kills_required', 10, "Minimum Number of kills needed for the player to be ranked")
stats_poptime           = xastats.setting.createVariable('stats_top_display_time', 15, "Determines how long popups stay open in seconds")
stats_addonly           = xastats.setting.createVariable('stats_points_add_only', 0, "If set to 0 you lose points for being killed, if set to 1 you do not")

bonusTable = {}
bonusTable['teamkill']          = xastats.setting.createVariable('stats_teamkill_bonus', -10, "The number of points a player will lose for teamkilling")
bonusTable['suicide']           = xastats.setting.createVariable('stats_suicide_bonus', -5, "The number of points a player will lose for committing suicide. Note that this does not include players typing kill in console or admin slay")
if directory == "cstrike":
    bonusTable['hostagekill']       = xastats.setting.createVariable('stats_css_hostage_killed_bonus', -15, "How many points the player will lose for killing a hostage")
    bonusTable['hostagerescue']     = xastats.setting.createVariable('stats_css_hostage_rescued_bonus', 5, "How many points a player will gain for rescuing a hostage")
    bonusTable['bombplant']         = xastats.setting.createVariable('stats_css_bomb_planted_bonus', 10, "How many points a player will gain planting the bomb")
    bonusTable['bombdefuse']        = xastats.setting.createVariable('stats_css_bomb_defused_bonus', 10, "How many points a player will gain defusing the bomb")
    bonusTable['teamcteliminated']  = xastats.setting.createVariable('stats_css_t_eliminated_team_bonus', 2, "If Terrorists kill all CT, then all terrrorist will gain this many points")
    bonusTable['teamteliminated']   = xastats.setting.createVariable('stats_css_ct_eliminated_team_bonus', 2, "If CTs kill all Terrorists, then all CTs will gain this many points")
    bonusTable['teambombexplode']   = xastats.setting.createVariable('stats_css_t_target_bombed_team_bonus', 5, "If the bomb explodes, then All Terrorists will gain this many points")
    bonusTable['teambombdefuse']    = xastats.setting.createVariable('stats_css_ct_bomb_defused_team_bonus', 5, "If the bomb is defused, all CTs will gain this many points")
    bonusTable['teambombplant']     = xastats.setting.createVariable('stats_css_t_bomb_planted_team_bonus', 2, "If the bomb is planted, then All Terrorists will gain this many points")
    bonusTable['teamallhostages']   = xastats.setting.createVariable('stats_css_ct_all_hostages_rescued_team_bonus', 10, "If all hostages are rescued, all CTs will gain this many points")
    bonusTable['teamnohostages']    = xastats.setting.createVariable('stats_css_t_no_hostages_rescued_team_bonus', 0, "If Hostages are not rescued, then All Terrorists will gain this many points. Note: This does not stack with any other winning conditions")
    bonusTable['teamhostagekill']   = xastats.setting.createVariable('stats_css_ct_hostage_killed_team_bonus', 1, "If a player kills a hostage, everyone on his team will lose this many points")
    bonusTable['teamhostagerescue'] = xastats.setting.createVariable('stats_css_ct_hostage_rescued_team_bonus', 1, "If a single hostage is rescued, all CTs will gain this many points")
elif directory == "dod":
    bonusTable['teamblockcapture']  = xastats.setting.createVariable('stats_dods_block_capture', 4, "Points given to all players blocking the capture")
    bonusTable['teamcapturepoint']  = xastats.setting.createVariable('stats_dods_capture_point', 4, "Points given to all players that captured the point")
    bonusTable['teamroundwin']      = xastats.setting.createVariable('stats_dods_round_win_bonus', 4, "Points given to all players on winning team")



weaponTable = {}
if directory == "cstrike":
    weaponTable['ak47']         = xastats.setting.createVariable('stats_css_weapon_ak47', 1.0, "Weapon weight (1.0 default)")
    weaponTable['aug']          = xastats.setting.createVariable('stats_css_weapon_aug', 1.0, "Weapon weight (1.0 default)")
    weaponTable['awp']          = xastats.setting.createVariable('stats_css_weapon_awp', 1.0, "Weapon weight (1.0 default)")
    weaponTable['deagle']       = xastats.setting.createVariable('stats_css_weapon_deagle', 1.2, "Weapon weight (1.2 default)")
    weaponTable['elite']        = xastats.setting.createVariable('stats_css_weapon_elite', 1.4, "Weapon weight (1.4 default)")
    weaponTable['famas']        = xastats.setting.createVariable('stats_css_weapon_famas', 1.0, "Weapon weight (1.0 default)")
    weaponTable['fiveseven']    = xastats.setting.createVariable('stats_css_weapon_fiveseven', 1.5, "Weapon weight (1.5 default)")
    weaponTable['flashbang']    = xastats.setting.createVariable('stats_css_weapon_flashbang', 5.0, "Weapon weight (5.0 default)")
    weaponTable['g3sg1']        = xastats.setting.createVariable('stats_css_weapon_g3sg1', 0.8, "Weapon weight (0.8 default)")
    weaponTable['galil']        = xastats.setting.createVariable('stats_css_weapon_galil', 1.1, "Weapon weight (1.1 default)")
    weaponTable['glock']        = xastats.setting.createVariable('stats_css_weapon_glock', 1.4, "Weapon weight (1.4 default)")
    weaponTable['hegrenade']    = xastats.setting.createVariable('stats_css_weapon_hegrenade', 1.8, "Weapon weight (1.8 default)")
    weaponTable['knife']        = xastats.setting.createVariable('stats_css_weapon_knife', 2, "Weapon weight (2.0 default)")
    weaponTable['m249']         = xastats.setting.createVariable('stats_css_weapon_m249', 1.2, "Weapon weight (1.2 default)")
    weaponTable['m3']           = xastats.setting.createVariable('stats_css_weapon_m3', 1.2, "Weapon weight (1.2 default)")
    weaponTable['m4a1']         = xastats.setting.createVariable('stats_css_weapon_m4a1', 1, "Weapon weight (1.0 default)")
    weaponTable['mac10']        = xastats.setting.createVariable('stats_css_weapon_mac10', 1.5, "Weapon weight (1.5 default)")
    weaponTable['mp5navy']      = xastats.setting.createVariable('stats_css_weapon_mp5navy', 1.2, "Weapon weight (1.2 default)")
    weaponTable['p228']         = xastats.setting.createVariable('stats_css_weapon_p228', 1.5, "Weapon weight (1.5 default)")
    weaponTable['p90']          = xastats.setting.createVariable('stats_css_weapon_p90', 1.2, "Weapon weight (1.2 default)")
    weaponTable['scout']        = xastats.setting.createVariable('stats_css_weapon_scout', 1.1, "Weapon weight (1.1 default)")
    weaponTable['sg550']        = xastats.setting.createVariable('stats_css_weapon_sg550', 0.8, "Weapon weight (0.8 default)")
    weaponTable['sg552']        = xastats.setting.createVariable('stats_css_weapon_sg552', 1, "Weapon weight (1.0 default)")
    weaponTable['smokegrenade'] = xastats.setting.createVariable('stats_css_weapon_smokegrenade', 5, "Weapon weight (5.0 default)")
    weaponTable['tmp']          = xastats.setting.createVariable('stats_css_weapon_tmp', 1.5, "Weapon weight (1.5 default)")
    weaponTable['ump45']        = xastats.setting.createVariable('stats_css_weapon_ump45', 1.2, "Weapon weight (1.2 default)")
    weaponTable['usp']          = xastats.setting.createVariable('stats_css_weapon_usp', 1.4, "Weapon weight (1.4 default)")
    weaponTable['xm1014']       = xastats.setting.createVariable('stats_css_weapon_xm1014', 1.1, "Weapon weight (1.1 default)")
elif directory == "dod":
    weaponTable['30cal']        = xastats.setting.createVariable('stats_dods_weapon_30cal', 1.25, "Weapon weight (1.25 default)")
    weaponTable['amerknife']    = xastats.setting.createVariable('stats_dods_weapon_amerknife', 3, "Weapon weight (3.0 default)")
    weaponTable['bar']          = xastats.setting.createVariable('stats_dods_weapon_bar', 1.2, "Weapon weight (1.2 default)")
    weaponTable['bazooka']      = xastats.setting.createVariable('stats_dods_weapon_bazooka', 2.25, "Weapon weight (2.25 default)")
    weaponTable['c96']          = xastats.setting.createVariable('stats_dods_weapon_c96', 1.5, "Weapon weight (1.5 default)")
    weaponTable['colt']         = xastats.setting.createVariable('stats_dods_weapon_colt', 1.6, "Weapon weight (1.6 default)")
    weaponTable['frag_ger']     = xastats.setting.createVariable('stats_dods_weapon_frag_ger', 1, "Weapon weight (1.0 default)")
    weaponTable['frag_us']      = xastats.setting.createVariable('stats_dods_weapon_frag_us', 1, "Weapon weight (1.0 default)")
    weaponTable['garand']       = xastats.setting.createVariable('stats_dods_weapon_garand', 1.3, "Weapon weight (1.3 default)")
    weaponTable['k98']          = xastats.setting.createVariable('stats_dods_weapon_k98', 1.3, "Weapon weight (1.3 default)")
    weaponTable['k98_scoped']   = xastats.setting.createVariable('stats_dods_weapon_k98_scoped', 1.5, "Weapon weight (1.5 default)")
    weaponTable['m1carbine']    = xastats.setting.createVariable('stats_dods_weapon_m1carbine', 1.2, "Weapon weight (1.2 default)")
    weaponTable['mg42']         = xastats.setting.createVariable('stats_dods_weapon_mg42', 1.2, "Weapon weight (1.2 default)")
    weaponTable['mp40']         = xastats.setting.createVariable('stats_dods_weapon_mp40', 1.25, "Weapon weight (1.25 default)")
    weaponTable['mp44']         = xastats.setting.createVariable('stats_dods_weapon_mp44', 1.35, "Weapon weight (1.35 default)")
    weaponTable['p38']          = xastats.setting.createVariable('stats_dods_weapon_p38', 1.5, "Weapon weight (1.5 default)")
    weaponTable['pschreck']     = xastats.setting.createVariable('stats_dods_weapon_pschreck', 2.25, "Weapon weight (2.25 default)")
    weaponTable['punch']        = xastats.setting.createVariable('stats_dods_weapon_punch', 3, "Weapon weight (3.0 default)")
    weaponTable['riflegren_ger']= xastats.setting.createVariable('stats_dods_weapon_riflegren_ger', 1.3, "Weapon weight (1.3 default)")
    weaponTable['riflegren_us'] = xastats.setting.createVariable('stats_dods_weapon_riflegren_us', 1.3, "Weapon weight (1.3 default)")
    weaponTable['smoke_ger']    = xastats.setting.createVariable('stats_dods_weapon_smoke_ger', 5, "Weapon weight (5.0 default)")
    weaponTable['smoke_us']     = xastats.setting.createVariable('stats_dods_weapon_smoke_us', 5, "Weapon weight (5.0 default)")
    weaponTable['spade']        = xastats.setting.createVariable('stats_dods_weapon_spade', 3, "Weapon weight (3.0 default)")
    weaponTable['spring']       = xastats.setting.createVariable('stats_dods_weapon_spring', 1.5, "Weapon weight (1.5 default)")
    weaponTable['thompson']     = xastats.setting.createVariable('stats_dods_weapon_thompson', 1.25, "Weapon weight (1.25 default)")

weaponTable['prop_physics']     = xastats.setting.createVariable('stats_prop_physics', 1.2, "Barrel explosions/collisions weight (1.2 default)")
weaponTable['env_explosion']    = xastats.setting.createVariable('stats_env_explosion', 1.0, "Server created explosions weight (1.0 default)")


#######################################
# GLOBALS
# Initialize our general global data here.
# Localization helper:
sessionTable = None
statTable = None
playerbomb = None
text = xastats.language.getLanguage()
pop  = popuplib.create('session_popup')
pop2 = popuplib.easymenu('stats_adminplayer', None, None)

mani_string  = "steamid,address,lastconnected,rank,points,deaths,headshots,kills,suicides,teamkills,timeconnected,"
mani_string += "damage,hitgeneric,hithead,hitchest,hitstomach,hitleftarm,hitrigharm,hitleftleg,hitrightleg,ak47_kills,"
mani_string += "m4a1_kills,mp5navy_kills,awp_kills,usp_kills,deagle_kills,aug_kills,hegrenade_kills,xm1014_kills,"
mani_string += "knife_kills,g3sg1_kills,sg550_kills,galil_kills,m3_kills,scout_kills,sg552_kills,famas_kills,glock_kills,"
mani_string += "tmp_kills,ump45_kills,p90_kills,m249_kills,elite_kills,mac10_kills,fiveseven_kills,p228_kills,"
mani_string += "flashbang_kills,smokegrenade_kills,shotsfired,shotshit,bombsplanted,bombsdefused,hostagerescues,hostagetouches,"
mani_string += "hostagekills,bombsexploded,bombs_dropped_ignore,bombdefusalattempts,vip_escaped_ignore,vip_killed_ignore,"
mani_string += "ctwins,lost_as_ct_ignore,twins,lost_as_t_ignore,name"


#######################################
# LOAD AND UNLOAD
# Formal system registration and unregistration
def load():
    global sessionTable, statTable

    xastatsmenu = popuplib.easymenu('xastatsmenu',None,menuReader)
    xastatsmenu.settitle(text['menu'])
    xastatsmenu.addoption('resetplayer',text['resetplayer'])
    xastatsmenu.addoption('resetall',text['resetall'])
    xastatsmenu.addoption('importmani',text['importmani'])

    xastats.addMenu("xastatsmenu",text['menu'],'xastatsmenu','manage_stats','ADMIN')

    sessionTable = SessionTable(False)
    statTable = SessionTable(True)

    statTable.readTable()

    for each in map(str, es.getUseridList()): # The session table is something we want to create rather than reload
        player_activate({'userid':each})

    xastats.addCommand('xa_rank',rankPlayer,'stat_rank','UNRESTRICTED').register(('say', 'console')) 
    xastats.addCommand('xa_session',statPopup,'stat_session','UNRESTRICTED').register(('say', 'console')) 
    xastats.addCommand('xa_statsme',statPopup,'stat_statsme','UNRESTRICTED').register(('say', 'console'))
    xastats.addCommand('xa_stats',statPopup,'stat_statsme','UNRESTRICTED').register(('say', 'console'))
    xastats.addCommand('xa_top',viewTop,'stat_top','UNRESTRICTED').register(('say', 'console'))
    xastats.addCommand('xa_hitboxme',hitboxPopup,'stat_hitboxme','UNRESTRICTED').register(('say', 'console'))

    #xastats.addCommand('xa_mani',maniWrapper,'stat_mani','ADMIN').register(('console',))


    thread.start_new_thread(statTable.sortTable, () )



def menuReader(adminid, option, name):
    global statTable, pop2
    if option == "resetall":
        statTable = SessionTable(True)
        statTable.writeTable()
        for each in es.getUseridList():
            sessionTable.add(each)
            statTable.add(each)
        es.tell(adminid, "ALL PLAYER DATA DESTROYED")

    if option == "importmani":
        maniWrapper(adminid)
        

    if option == "resetplayer":
        pop2.delete()
        pop2 = popuplib.easymenu('stats_adminplayer', None, resetPlayer)
        pop2.settitle("Select Player")
        for each in es.getUseridList():
            pop2.addoption(str(each), playerlib.getPlayer(each).attributes["name"] )
        pop2.send(adminid)


def resetPlayer(adminid, option, name):
    statTable.reset(option)
    statTable.add(option)

def unload():
    global sessionTable, statTable, pop, pop2

    # Unregister the module
    for each in es.getUseridList():
        try:
            sessionTable.end(each)
        except:
            pass

    statTable.writeTable()

    del sessionTable, statTable

    pop.delete()
    pop2.delete()
    popuplib.delete("xastatsmenu")
    xa.unregister(xastats)



#######################################
# MODULE FUNCTIONS
# Register your module's functions
""" # Disabled due to suspected bugs
def player_connect(event_var): # lets add a dummy vairable here incase they connect and disconnect before they activate
    global sessionTable
    #sessionTable[event_var["userid"] ] = Session(0)
"""

def player_activate(event_var):
    global sessionTable, statTable
    
    sessionTable.add(event_var["userid"] )
    statTable.add(event_var["userid"] )
    


    

def player_disconnect(event_var):
    global sessionTable, statTable

    sessionTable.end(event_var["userid"])

    





def player_death(event_var):
    global sessionTable, statTable

    victim = str(event_var['userid'])
    attacker = str(event_var['attacker'])
    victimteam = event_var['es_userteam']
    attackerteam = event_var['es_attackerteam']
    weapon = str(event_var['weapon'])
    headshot = int(event_var['headshot'])


    if attacker == victim: # they typed kill in console or the like
        return

    vsess = sessionTable.get(victim)
    vstat = statTable.get(victim)
    
    if attacker == "0": # they committed suicide
        vsess.add("suicides")
        vsess.add("deaths")
        vsess.add("temp_points", int(bonusTable["suicide"]) )
        vstat.add("points", int(bonusTable["suicide"]) )
    else: # one player kills another
        asess = sessionTable.get(attacker) # only add attacker data once we know they exist
        astat = statTable.get(attacker)

        
        if victimteam == attackerteam:  # We have a team killer
            asess.add("teamkills")
            vsess.add("deaths")
            asess.add("temp_points", int(bonusTable["teamkill"]) )
            astat.add("points", int(bonusTable["teamkill"]) )
        else:
            # Lets first rack up all the kills 
            if headshot > 0:
                asess.add("headshots")
            asess.add("kills")
            vsess.add("deaths")

            vsess.add(weapon + "_kills")
            

            # check to see if we should do point calculations
            if int(stats_mode) == 3:
                vscore = vstat.get("points")
                ascore = astat.get("points")

                if headshot > 0:
                    headshot = stats_headshot
                else:
                    headshot = 1.0
                    
                if weapon in weaponTable:
                    vscoreDelta = 1.0 * vscore / ascore * float(weaponTable[weapon]) * float(headshot) * float(stats_deathmult)
                    ascoreDelta = 1.0 * vscore / ascore * float(weaponTable[weapon]) * float(headshot) * float(stats_killmult)
                
                    # lets update the player session.  Note that the socre 
                    # put here is only the score changes made during the session.
                    asess.add("temp_points", int(ascoreDelta) ) 
                    astat.add("points", int(ascoreDelta) ) # lets update the statistics table
    
                    # only subtract player points if the killer has a few kills
                    if astat.getTotal("kills") > int(stats_minkills) and int(stats_addonly) == 0:
                        vsess.add("temp_points", -int(vscoreDelta) )
                        vstat.add("points", -int(vscoreDelta) )

            # can we do PDF calculations?
            if int(stats_pdf) == 1:
                vstat.add("killdev", pow(vsess.get("temp_killstreak"), 2) )

                if vsess.get("temp_killstreak") >= int(stats_pdfthreshold): # should we player that he did well?
                    stddevtemp = vstat.get("killdev")  * (vstat.get("deaths") + vsess.get("deaths") ) 
                    stddevtemp = stddevtemp - pow( vstat.get("kills") + vsess.get("kills"), 2)
                    if stddevtemp < 0: # this shouldn't happen, but if it does...
                        stddevtemp = 0
                        xastats.logging.log("***ERROR*** Standard Deviations gone horribly wrong!")
                    stddev = 1.0 / (vsess.get("deaths") + vstat.get("deaths")) * pow(stddevtemp, 0.5) # we finally have the standard deviation


                        
                    if stddev != 0:
                        e = 2.7182818284590451 # im not importing the math module for a single constant
                        pi = 3.1415926535897931 # not for two either
                        exp = vsess.get("temp_killstreak") - 1.0 * ( vstat.get("kills") + vsess.get("kills") ) / ( vsess.get("deaths") + vstat.get("deaths") )
                        exp = -0.5 * pow(exp / stddev, 2) # dont worry about this.
                        pdf = pow(e, exp) / (stddev * pow(2 * pi , 0.5 )  )  * 100  # this is the probability that we have been looking for
                    else:
                        pdf = 100


                    es.tell(victim, "#multi",
                            "#defaultYou had a #green %0.1f%% #default chance of getting #green%i #defaultkills in a row." % (pdf,
                                                                                                                              vsess.get("temp_killstreak")))
                    # Wow that took a while.  Hope you guys enjoy it!
                            
                        
                        
                          




            #lets finish the kill streak info
            if vsess.get("killstreak") < vsess.get("temp_killstreak"):
                vsess.set("killstreak", vsess.get("temp_killstreak") ) # a new killstreak record
            vsess.set("temp_killstreak", 0)
            asess.add("temp_killstreak") 
            
def player_hurt(event_var):
    global sessionTable

    attacker = str(event_var['attacker'])
    vteam = str(event_var['es_userteam'])
    ateam = str(event_var['es_attackerteam'])
    damage = int(event_var["dmg_health"])
    hitgroup = int(event_var["hitgroup"])

    if ateam == vteam: # no team damage
        pass
    elif attacker == "0":
        pass
    else:
        asess = sessionTable.get(attacker)
        asess.add("shotshit")
        asess.add("damage", damage)
        
        if hitgroup == 0:
            asess.add("hitgeneric")
        elif hitgroup == 1:
            asess.add("hithead")
        elif hitgroup == 2:
            asess.add("hitchest")        
        elif hitgroup == 3:
            asess.add("hitstomach")
        elif hitgroup == 4:
            asess.add("hitleftarm")
        elif hitgroup == 5:
            asess.add("hitrightarm")
        elif hitgroup == 6:
            asess.add("hitleftleg")
        else:
            asess.add("hitrightleg")

def weapon_fire(event_var):
    global sessionTable
    
    asess = sessionTable.get(str(event_var["userid"]) )
    asess.add("shotsfired")


              

def round_end(event_var):
    global sessionTable, statTable
  
    reason = str(event_var["reason"] )

    thread.start_new_thread(statTable.sortTable, () )
    statTable.writeTable()

    
    playerlist = es.createplayerlist()
    winner = str(event_var["winner"])
    for each in playerlist:
        
        if str(playerlist[each]["teamid"]) == "2":
            sessionTable.get(each).add("trounds")
            if winner == "2":
                sessionTable.get(each).add("twins")
                
                if reason == "9": #all ct are dead
                    sessionTable.get(each).add("temp_points", int(bonusTable["teamcteliminated"]) )
                    statTable.get(each).add("points", int(bonusTable["teamcteliminated"]) )
                elif reason == "13": # hostages not rescued
                    sessionTable.get(each).add("temp_points", int(bonusTable["teamnohostages"]) )
                    statTable.get(each).add("points", int(bonusTable["teamnohostages"]) )
                elif reason == "1": #target bombed
                    sessionTable.get(each).add("temp_points", int(bonusTable["teambombexplode"]) )
                    statTable.get(each).add("points", int(bonusTable["teambombexplode"]) )

                
        if str(playerlist[each]["teamid"]) == "3":
            sessionTable.get(each).add("ctrounds")
            if winner == "3":
                sessionTable.get(each).add("ctwins")

                if reason == "8": #all t are dead
                    sessionTable.get(each).add("temp_points", int(bonusTable["teamteliminated"]) )
                    statTable.get(each).add("points", int(bonusTable["teamteliminated"]) )
                elif reason == "11": # all hostages rescued
                    sessionTable.get(each).add("temp_points", int(bonusTable["teamallhostages"]) )
                    statTable.get(each).add("points", int(bonusTable["teamallhostages"]) )
                elif reason == "7": # bomb defused
                    sessionTable.get(each).add("temp_points", int(bonusTable["teambombdefuse"]) )
                    statTable.get(each).add("points", int(bonusTable["teambombdefuse"]) )


def bomb_planted(event_var):
    global sessionTable, statTable
    sessionTable.get(event_var["userid"] ).add("bombsplanted")
    
    sessionTable.get(event_var["userid"]).add("temp_points", int(bonusTable["bombplant"]) )
    statTable.get(event_var["userid"]).add("points", int(bonusTable["bombplant"]) )
    
    playerlist = es.createplayerlist()
    for each in playerlist:
        if str(playerlist[each]["teamid"]) == "2":
            sessionTable.get(each).add("temp_points", int(bonusTable["teambombplant"]) )
            statTable.get(each).add("points", int(bonusTable["teambombplant"]) )

            
def bomb_begindefuse(event_var):
    global sessionTable
    sessionTable.get(event_var["userid"] ).add("bombdefusalattempts")


def bomb_defused(event_var):
    global sessionTable, statTable
    psess = sessionTable.get(event_var["userid"] ).add("bombsdefused")
    
    sessionTable.get(event_var["userid"]).add("temp_points", int(bonusTable["bombdefuse"]) )
    statTable.get(event_var["userid"]).add("points", int(bonusTable["bombdefuse"]) )

    playerlist = es.createplayerlist()
    for each in playerlist:
        if str(playerlist[each]["teamid"]) == "3":
            sessionTable.get(each).add("temp_points", int(bonusTable["teambombdefuse"]) )
            statTable.get(each).add("points", int(bonusTable["teambombdefuse"]) )

def bomb_exploded(event_var):
    global sessionTable, statTable
    sessionTable.get(event_var["userid"] ).add("bombsexploded")

    playerlist = es.createplayerlist()
    for each in playerlist:
        if str(playerlist[each]["teamid"]) == "2":
            sessionTable.get(each).add("temp_points", int(bonusTable["teambombexplode"]) )
            statTable.get(each).add("points", int(bonusTable["teambombexplode"]) )

def hostage_follows(event_var):
    global sessionTable
    sessionTable.get(event_var["userid"] ).add("hostagetouches")   

def hostage_rescued(event_var):
    global sessionTable, statTable
    sessionTable.get(event_var["userid"] ).add("hostagerescues")

    sessionTable.get(event_var["userid"]).add("temp_points", int(bonusTable["hostagerescue"]) )
    statTable.get(event_var["userid"]).add("points", int(bonusTable["hostagerescue"]) )

    playerlist = es.createplayerlist()
    for each in playerlist:
        if str(playerlist[each]["teamid"]) == "3":
            sessionTable.get(each).add("temp_points", int(bonusTable["teamhostagerescue"]) )
            statTable.get(each).add("points", int(bonusTable["teamhostagerescue"]) )

def hostage_killed(event_var):
    global sessionTable, statTable
    sessionTable.get(event_var["userid"] ).add("hostagekills")  

    sessionTable.get(event_var["userid"]).add("temp_points", int(bonusTable["hostagekill"]) )
    statTable.get(event_var["userid"]).add("points", int(bonusTable["hostagekill"]) )

    team = str(event_var['es_userteam'] )
    
    playerlist = es.createplayerlist()
    for each in playerlist:
        if str(playerlist[each]["teamid"]) == team:
            sessionTable.get(each).add("temp_points", -int(bonusTable["teamhostagekill"]) )
            statTable.get(each).add("points", -int(bonusTable["teamhostagekill"]) )
        
def dod_axis_win(event_var):
    global sessionTable, statTable
    
    playerlist = es.createplayerlist()
    for each in playerlist:
        if str(playerlist[each]["teamid"]) == "2":
            sessionTable.get(each).add("temp_points", -int(bonusTable["teamroundwin"]) )
            statTable.get(each).add("points", -int(bonusTable["teamroundwin"]) )

    round_end({'winner': '2', 'reason':'0', 'message':''})

def dod_allies_win(event_var):
    global sessionTable, statTable
    
    playerlist = es.createplayerlist()
    for each in playerlist:
        if str(playerlist[each]["teamid"]) == "3":
            sessionTable.get(each).add("temp_points", -int(bonusTable["teamroundwin"]) )
            statTable.get(each).add("points", -int(bonusTable["teamroundwin"]) )

    round_end({'winner': '3', 'reason':'0', 'message':''})

def dod_bomb_exploded(event_var):
    global sessionTable, statTable
    sessionTable.get(event_var["userid"]).add("bombsexploded")

    sessionTable.get(event_var["userid"]).add("temp_points", int(bonusTable["teambombexplode"]) )
    statTable.get(event_var["userid"]).add("points", int(bonusTable["teambombexplode"]) )

def dod_bomb_defused(event_var):
    global sessionTable, statTable, playerbomb
    sessionTable.get(event_var["userid"]).add("bombsdefused")

    sessionTable.get(event_var["userid"]).add("temp_points", int(bonusTable["bombdefuse"]) )
    statTable.get(event_var["userid"]).add("points", int(bonusTable["bombdefuse"]) )

    playerbomb = event_var['userid']

def dod_capture_blocked(event_var):
    global sessionTable, statTable

    sessionTable.get(event_var["userid"]).add("temp_points", int(bonusTable["teamblockcapture"]) )
    statTable.get(event_var["userid"]).add("points", int(bonusTable["teamblockcapture"]) )

def dod_point_captured(event_var):
    global sessionTable, statTable, playerbomb

    if int(event_var['bomb']) == 1:
        if playerbomb:
            sessionTable.get(playerbomb).add("temp_points", int(bonusTable["teamcapturepoint"]) )
            statTable.get(playerbomb).add("points", int(bonusTable["teamcapturepoint"]) )
    else:
        for each in filter(lambda x: es.getplayerprop(x,"CDODPlayer.m_Shared.dodsharedlocaldata.m_iCPIndex")==int(event_var['cp']), es.getUseridList()):
            sessionTable.get(each).add("temp_points", int(bonusTable["teamcapturepoint"]) )
            statTable.get(each).add("points", int(bonusTable["teamcapturepoint"]) )


class Session():

    def __init__(self, userid, stat=False):
        global weaponScore
        self.sess = {}
        if int(userid) > 0:  # can we generate a generic 
            player = playerlib.getPlayer(userid)
            self.set("steamid", player.attributes['steamid'] )
            self.set("name", player.attributes['name'] )
            self.set("address", player.attributes['address'].split(":")[0] )
            
        else:
            self.set("steamid", "" )
            self.set("name", "" )
            self.set("address", "" )
        if stat == False: # is this a temporary session or should we keep track of it?
            self.set("joined", int(time.time()) )
            self.set("temp_points", 0)
            self.set("temp_killstreak", 0)
        else:
            self.set("joins", 0 )
            self.set("timeconnected", 0)
            self.set("points", 1000)
            self.set("killdev", 0)
            self.set("lastconnected", int(time.time() ) )
            self.set("rank", -1)
        self.set("kills", 0)
        self.set("headshots", 0)
        self.set("deaths", 0)
        self.set("teamkills", 0)   
        self.set("suicides", 0)
        self.set("killstreak", 0)
        
        self.set("ctrounds", 0)
        self.set("trounds", 0)
        self.set("ctwins", 0)
        self.set("twins", 0)
        
        self.set("hostagekills", 0)
        self.set("hostagerescues", 0)
        self.set("hostagetouches", 0)

        self.set("bombsplanted", 0)
        self.set("bombsdefused", 0)
        self.set("bombsexploded", 0)
        self.set("bombdefusalattempts", 0)
        

        self.set("damage", 0)
        self.set("shotsfired", 0)
        self.set("shotshit", 0)
        self.set("hitgeneric", 0)
        self.set("hithead", 0)
        self.set("hitchest", 0)
        self.set("hitstomach", 0)
        self.set("hitleftarm", 0)
        self.set("hitrightarm", 0)
        self.set("hitleftleg", 0)
        self.set("hitrightleg", 0)




        
        self.userid = userid
        
        
        
        
        # if you want ot add more values, do so here


        for each in weaponTable.keys():
            self.set(each + "_kills", 0)


        

    def set(self, key, value): # this will take in a key and a value and associate them in the session dict.  It tries to force all number to ints if possible
        key = str(key)
        try:
            value = int(value)
        except:
            value = str(value)
            
        
        self.sess[key] = value
        return

    def get(self, key):
        key = str(key)
        if not (key in self.sess.keys() ):
            self.set(key, 0)
        return self.sess[key]

    def add(self, key, value = 1):
        key = str(key)
        current = self.get(key)
        self.set(key, value + current)
        #es.msg(" Set %s to %s" % (key, self.get(key)) )

    def getKeys(self):
        return self.sess.keys()

    def unique(self):
        if int(stats_unique) == 1:
            return self.sess["address"]
        else:
            return self.sess["steamid"]
        
    def getTotal(self, key):
        global statTable

        return statTable.total(self.unique(), key) 
    
    def sortTuple(self):
        if int(stats_mode) == 0:
            number = self.getTotal("kills")
        elif int(stats_mode) == 1:
            number = 1.0 *  self.getTotal("kills") / self.getTotal("deaths")
        elif int(stats_mode) == 2:
            number = self.getTotal("kills") - self.getTotal("deaths")
        elif int(stats_mode) == 3:
            number = self.get("points")
        else:
            number = self.getTotal("kills")
        return (number, self.unique() )


class SessionTable():

    useridlist = {} # this should be shared across all tables
    activeList = []
    sortList = []
    
    def __init__(self, stat=False):
        self.sess = {}
        self.stat = stat




    def unique(self, userid):  # returns the unique id of a userid
        userid = str(userid)
        if userid in self.useridlist.keys():
            return self.useridlist[userid]
        elif int(stats_unique) == 0:
            return playerlib.getPlayer(userid).attributes["steamid"]
        else:
            return playerlib.getPlayer(userid).attributes['address'].split(":")[0]

        


    def add(self, userid): # adds a player to the table by userid
        userid = str(userid)
        if int(stats_unique) == 0:
            self.useridlist[userid] = playerlib.getPlayer(userid).attributes["steamid"]
        else:
            self.useridlist[userid] = playerlib.getPlayer(userid).attributes['address'].split(":")[0]

            
        
        key = self.unique(userid)

        if not key in self.sess.keys(): # we want player data to be in the table
            self.sess[key] = Session(userid, self.stat)

        if not key in self.activeList:
            self.activeList.append(key)
            
        return self.sess[key]

    def get(self, userid): # retunrs a Session object
        key = self.unique(userid)
        if key in self.sess.keys():
            return self.sess[key]
        elif es.exists('userid', userid):
            return self.add(userid)
        else:
            es.dbgmsg(0, "[eXtensible Admin] Stats: No such player: %s!" % userid )

    def getInner(self, unique):
        if unique in self.sess.keys():
            return self.sess[unique]
        else:
            es.dbgmsg(0, "[eXtensible Admin] Stats: No such unique: %s!" % unique )

    def total(self, unique, key): # sums the values of a player at an unique  (ie, gets their total kills)
        global sessionTable, statTable

        if unique in sessionTable.sess.keys(): # is the player on the server?
            
            return statTable.sess[unique].get(key) + sessionTable.sess[unique].get(key)
        else:
            try:
                return statTable.sess[unique].get(key)
            except:
                es.msg(unique)
                es.msg(statTable.sess.keys() )

    def end(self, userid):
        global statTable
        
        userid = str(userid)
        if not(userid in self.useridlist.keys() ): # the player joined but never activated
            return
        else:
            key = self.unique(userid)

        self.merge(userid)
        
        if self.sess[key].get("kills") < int(stats_rankthreshold):
            try:
                self.activeList.remove(key)
            except:
                es.msg(key)
                es.msg(self.activeList)

        del self.sess[key]
        del self.useridlist[userid]

        
            
    def reset(self, userid): # destroys any records for the userid
        key = self.unique(userid)
        if key in self.sess.keys():
            self.sess[key] = Session(userid, self.stat)
            
    def size(self):
        return len(self.activeList)

    def merge(self, userid): # merges a sessionTable player into a statTable player
        global statTable, sessionTable
        key = self.unique(userid)
        if self.stat:
            es.dbgmsg(0, "[eXtensible Admin] Stats: Cannot merge stat data into session data!")
            return
        statPlayer = statTable.get(userid)
        sessionPlayer = self.get(userid)
        
        for each in sessionPlayer.getKeys():
            if "temp_" in each:
                pass
            elif each == "joined":
                current = int(time.time() )
                timeconnected = current - sessionPlayer.get("joined")
                statPlayer.add("timeconnected", timeconnected)
                statPlayer.set("lastconnected", current)
            elif each == "killstreak":
                statPlayer.set("killstreak", max(sessionPlayer.get("killstreak"), statPlayer.get("killstreak") ) )
            elif each == "name":
                statPlayer.set("name", sessionPlayer.get("name") )
            elif each == "steamid":
                statPlayer.set("steamid", sessionPlayer.get("steamid") )
            elif each == "address":
                statPlayer.set("address", sessionPlayer.get("address") )
            else:
                statPlayer.add(each, sessionPlayer.get(each) )

    def sortTable(self):
        if self.stat:
            start = time.time()
            sortList = []
            for each in self.activeList:
                if self.total(each, "kills") >= int(stats_rankthreshold):
                    if int(time.time() ) - 3600 * 24 * int(stats_rankdays) > self.sess[each].get("lastconnected"):
                        self.activeList.remove(each)
                    else:
                        sortList = sortList + [ self.sess[each].sortTuple() ]
            sortList.sort(reverse=True)
            i = 1

            for each in sortList:
                if each[1] == "STEAM_ID_PENDING":
                    es.dbgmsg(0, "[eXtensible Admin] Stats: Steamid is still pending, player will not be ranked!")
                else:

                    self.sess[each[1]].set("rank", i)
                    
                    i += 1
            
            self.sortList = sortList

            if float(time.time() - start) > 0.2:
                es.dbgmsg(0, "[eXtensible Admin] Stats: Calculated stats in %0.5f seconds" % (time.time() - start) )
        else:
            es.dbgmsg(0, "[eXtensible Admin] Stats: Session table cannot be sorted!" )

    def writeTable(self):
        if len(self.sess) > 0:
            try:
                pass
            except:
                pass
            if True:
                fp = open(es.getAddonPath('xa') + "/data/stats.txt", "w")

                keyList = Session(0, self.stat).getKeys()

                index = keyList.index("name")
                keyList = keyList[:index] + keyList[index + 1:] # name is not added here simply because it must be at the end.
                
                header = ",".join(keyList + ["name"] ) + "\n" # ***important! name must be the last element in the list!***
                
                fp.write(header)
                
                for each in self.sess:
                    if each != "STEAM_ID_PENDING":
                        line = ""
                        for key in keyList:
                            line = line + str(self.sess[each].get(key) ) + ","
                        line = line + str(self.sess[each].get("name") ) + "\n"
                        fp.write(line)
                fp.close()
            try:
                pass
            except:
                es.dbgmsg(0,  "***ERROR*** Unable to write to table %s" % name)

    def readTable(self):
        try:
            fp = open(es.getAddonPath('xa') + "/data/stats.txt", "r")
        except:
            try:
                fp = open(es.getAddonPath('xa') + "/data/stats.txt", "w")
                fp.close()
                fp = open(es.getAddonPath('xa') + "/data/stats.txt", "r")
            except:
                es.dbgmsg(0, "[eXtensible Admin] Stats: stats.txt could not be read!")
        self.sess = {}
        self.useridlist = {}
        self.activeList = []
        if int(stats_unique) == 0:
            entry = "steamid"
        else:
            entry = "address"
        if True:
            
            header = fp.readline().strip().split(",") # this function splits up the " tokens because players are not allowed to have them in their names

            for line in fp:
                array = line.strip().split(",")

                player = Session(0, self.stat)
                if len(header) != len(array):
                    array = array[:len(header)-1] + [ ",".join(array[len(header)-1:])  ] # if the name has commas in it, lets glue the name back together
                    
                for i in range(len(header) ):
                    player.set(header[i], array[i])
                    
                if len( player.get(entry) ):
                    self.sess[player.get(entry)] = player
                    self.activeList.append( player.get(entry) )
                else:
                    es.dbgmsg(0, "No good key found! Defaulting to name!")  # this should never happen, but the Titanic could never sink
                    self.sess[player.get("name")] = player
        try:
            pass
        except:
            es.dbgmsg(0,  "***ERROR*** Unable to read from table %s")

    def readManiTable(self):
        global mani_string, sessionTable
        selfmoddir = str(es.server_var["eventscripts_gamedir"]).replace("\\", "/")
        
        #es.server.cmd("mani_stats_ignore_ranks_after_x_days 365")
        #es.server.cmd("mani_stats_mode 1")
        #es.server.cmd("mani_stats_kills_required 0")
        #es.server.cmd("mani_stats_write_text_file 1")
        
        #es.event("initialize", "round_end")
        #es.event("fire", "round_end")
        #time.sleep(1)
        try:
           fp = open(selfmoddir + "/cfg/mani_admin_plugin/data/mani_ranks.txt" , "r")
           f = open(es.getAddonPath('xa') + "/data/stats.txt", "w")
        except:
            es.dbgmsg(0,  "***ERROR*** Unable to read from Mani File")
        f.write(mani_string + "\n")
        for line in fp:
            f.write(line)

        f.close()
        fp.close()


        self.sess = {}
        self.useridlist = {}
        self.activeList = []
        self.readTable()
        for each in self.sess:
            self.sess[each].add("ctrounds", self.sess[each].get("ctwins") +  self.sess[each].get("lost_as_ct_ignore") )
            self.sess[each].add("trounds", self.sess[each].get("twins") +  self.sess[each].get("lost_as_t_ignore") )                   
        
        playerList = es.createplayerlist()
        for each in playerList: 
            sessionTable.add(each)
            self.add(each)
        self.sortTable()
        es.msg("***ALL DATA IMPORTED***")
        




def maniWrapper(adminid):
    thread.start_new_thread(statTable.readManiTable, () )
    es.tell(adminid, "***WORKING***")

def timestring(sec): # this function take a number of seconds and turns it into time
    vals = time.gmtime(sec)
    if vals[1] - 1 == 0:
        months = ""
    else:
        months = "%im" % (vals[1] -1)
    if vals[2] - 1 == 0:
        days = ""
    else:
        days = "%id" % (vals[2] - 1)
    if vals[3] == 0:
        hours = ""
    else:
        hours = "%ih" % vals[3]
    if vals[4] == 0:
        minutes = ""
    else:
        minutes = "%im" % vals[4]
    seconds = "%is" % vals[5]

    fullstring = "%s %s %s %s %s" % (months, days, hours, minutes, seconds)

    return fullstring.strip()

def getPercent(top, bottom):
    top = float(top)
    bottom = float(bottom)
    
    if bottom == 0.0:
        if top == 0.0:
            ratio = 0.0
        else:
            ratio = 1.0
    else:
        ratio = top / bottom
    return ratio


    
def rankPlayer():
    global sessionTable, statTable

    userid = str(es.getcmduserid() )
    
    if int(stats_silent) == 0:
        #es.cexec(int(userid), "\"say !rank\"")
        pass
    player = sessionTable.get(userid)
    name = player.get("name")
    kills = player.getTotal("kills")
    deaths = player.getTotal("deaths")
    points = statTable.get(userid).get("points")
    rank = statTable.get(userid).get("rank")
    if deaths == 0:
        if kills == 0:
            kdr = 0.0
        else:
            kdr = kills
    else:
        kdr = 1.0 * kills / deaths
    if int(stats_publicrank) == 1:
        if rank == -1:
            es.msg("Player %s is not yet ranked. Need %s kills to be ranked." % (name, stats_rankthreshold) )
        else:
            es.msg("Player %s is ranked %i/%i with %i points, %i kills, %i deaths, kd ratio of %0.2f" % (name,
                                                                                                         rank,
                                                                                                         statTable.size(),
                                                                                                         points,
                                                                                                         kills,
                                                                                                         deaths,
                                                                                                         kdr)   )
    else:
        if rank == -1:
            es.tell(userid, "%s is not yet ranked. Need %s kills to be ranked." % (name, stats_rankthreshold) )
        else:
            es.tell(userid, "Player %s is ranked %i/%i with %i points, %i kills, %i deaths, kd ratio of %0.2f" % (name,
                                                                                                                  rank,
                                                                                                                  statTable.size(),
                                                                                                                  points,
                                                                                                                  kills,
                                                                                                                  deaths,
                                                                                                                  kdr)   )


def statPopup():
    global sessionTable, statTable, pop

    userid = str(es.getcmduserid() )
    if es.getargv(0).lower()  == "!session":
        stat = False
    else:
        stat = True

    psess = sessionTable.get(userid)
    pstat = statTable.get(userid)

    if stat:
        timeonline = timestring(int(time.time() ) -  psess.get("joined") + pstat.get("timeconnected") )
        kills = psess.getTotal("kills")
        deaths = psess.getTotal("deaths")
        headshots = psess.getTotal("headshots")
        points = pstat.get("points")
        kdr = getPercent(kills, deaths)

        killstreak = pstat.get("killstreak")
        
        suicides = psess.getTotal("suicides")

        accuracy = getPercent(psess.getTotal("shotshit") , psess.getTotal("shotsfired")) * 100

        damage = psess.getTotal("damage")
        
        teamkills = psess.getTotal("teamkills")
        twins = psess.getTotal("twins")
        ctwins = psess.getTotal("ctwins")
        trounds = psess.getTotal("trounds")
        ctrounds = psess.getTotal("ctrounds")
        tpct = getPercent(twins, trounds) * 100
        ctpct = getPercent(ctwins, ctrounds) * 100

        rounds = trounds + ctrounds

        hostagekills = psess.getTotal("hostagekills")
        hostagerescues = psess.getTotal("hostagerescues")


        bombsplanted = psess.getTotal("bombsplanted")
        bombsexploded = psess.getTotal("bombsexploded")
        bombsdefused = psess.getTotal("bombsdefused")
        sign = ""
    else:
        timeonline = timestring( int(time.time() ) -  psess.get("joined") )
        kills = psess.get("kills")
        deaths = psess.get("deaths")
        headshots = psess.get("headshots")
        points = psess.get("temp_points")
        if points < 0:
            sign = "-"
        else:
            sign = "+"
        kdr = getPercent(kills, deaths)
        
        killstreak = psess.get("killstreak")
        
        suicides = psess.get("suicides")
        accuracy = getPercent( psess.get("shotshit") , psess.get("shotsfired")) * 100

        damage = psess.get("damage")
        
        teamkills = psess.get("teamkills")
        twins = psess.get("twins")
        ctwins = psess.get("ctwins")
        trounds = psess.get("trounds")
        ctrounds = psess.get("ctrounds")
        tpct = getPercent(twins, trounds) * 100
        ctpct = getPercent(ctwins, ctrounds) * 100
        
        rounds = trounds + ctrounds

        hostagekills = psess.get("hostagekills")
        hostagerescues = psess.get("hostagerescues")


        bombsplanted = psess.get("bombsplanted")
        bombsexploded = psess.get("bombsexploded")
        bombsdefused = psess.get("bombsdefused")
        
    rank = pstat.get("rank")
    if rank == -1:
        place = ""
    else:
        place = "(%i/%i)" % (rank, statTable.size() )

    pop = popuplib.create('session_popup')
    pop.addline("Data for %s" % psess.get("name") )
    
    pop.addline("----------------------------") 
    pop.addline("Points: %s%s %s" % (sign, points, place ))
    pop.addline("Kills: %s Deaths %s KDR %0.2f" % (kills, deaths, kdr) )
    pop.addline("Headshots: %s" % headshots)

    pop.addline("Killstreak: %i" % killstreak )
    pop.addline("Suicides: %i" % suicides )
    pop.addline("Time: %s" % timeonline )
    
    pop.addline("----------------------------")
    pop.addline("Accuracy: %0.2f Damage: %i Team Kills: %i" % (accuracy, damage, teamkills) )
    
    pop.addline("----------------------------")
    pop.addline("Bombs Planted: %i Exploded: %i Defused: %i" % (bombsplanted, bombsexploded, bombsdefused)  )
    
    pop.addline("----------------------------")
    pop.addline("Hostages Rescued: %i Killed: %i" % (hostagerescues, hostagekills) )
    
    pop.addline("----------------------------")
    pop.addline("Wins as T: %i/%i (%0.2f)" % (twins, trounds, tpct ) )
    pop.addline("Wins as CT: %i/%i (%0.2f)" % (ctwins, ctrounds, ctpct ) )
    pop.addline("Total Rounds: %i" % rounds)
    
    pop.timeout("view", int(stats_poptime))
    pop.send(userid)

        
def viewTop():
    global statTable, pop
    userid = str(es.getcmduserid() )
    if len(es.getargv(1) ) == 0:
        arg = 10
    else:
        try: 
            arg = int(es.getargv(1))
        except:
            arg = 10
    if arg < 10:
        arg = 10
    if arg > statTable.size():
        arg = 10

    if statTable.size() < 10:
        es.msg("Not enough players are tanked yet!")
        return

    
    pop = popuplib.create('session_popup')
    sortList = statTable.sortList
    i = 0
    while i < 10:
        player = statTable.getInner(sortList[i + arg - 10][1])
        pop.addline("%i  %s=%i KDR=%0.2f" % (i + arg - 10 + 1,
                                                       player.get("name"),
                                                       player.get("points"),
                                                       getPercent(player.get("kills") , player.get("deaths") ) ) )
        i = i + 1
                    
    pop.timeout("view", int(stats_poptime))
    pop.send(userid)


def hitboxPopup():
    global sessionTable, pop
    userid = str(es.getcmduserid() )

    player = sessionTable.get(userid)
    length = 100.0

    name = player.get("name")
    damage = player.getTotal("damage")
    fired = player.getTotal("shotsfired")
    hit = player.getTotal("shotshit")
    generic = player.getTotal("hitgeneric")
    head = player.getTotal("hithead")
    chest = player.getTotal("hitchest")
    stomach = player.getTotal("hitstomach")
    leftarm = player.getTotal("hitleftarm")
    rightarm = player.getTotal("hitrightarm")
    leftleg = player.getTotal("hitleftleg")
    rightleg = player.getTotal("hitrightleg")

    accuracy = getPercent(hit, fired) * 100.0
    
    pop = popuplib.create('session_popup')
    pop.addline("Hitbox data for player %s" % name)
    pop.addline("Accuracy %0.2f Damage %i" % (accuracy, damage) )
    pop.addline("----------------------------")

    pop.addline("Body: %0.2f%%" % (getPercent(generic, hit) * 100) )
    pop.addline("%s" % ("|" * int(getPercent(generic, hit) * length ) ) )
    
    pop.addline("Head: %0.2f%%" % (getPercent(head, hit) * 100) )
    pop.addline("%s" % ("|" * int(getPercent(head, hit) * length ) ) )
    
    pop.addline("Chest: %0.2f%%" % (getPercent(chest, hit) * 100) )
    pop.addline("%s" % ("|" * int(getPercent(chest, hit) * length ) ) )
    
    pop.addline("Stomach: %0.2f%%" % (getPercent(stomach, hit) * 100) )
    pop.addline("%s" % ("|" * int(getPercent(stomach, hit) * length ) ) )

    pop.addline("Left Arm: %0.2f%%" % (getPercent(leftarm, hit) * 100) )
    pop.addline("%s" % ("|" * int(getPercent(leftarm, hit) * length ) ) )
    
    pop.addline("Right Arm: %0.2f%%" % (getPercent(rightarm, hit) * 100) )
    pop.addline("%s" % ("|" * int(getPercent(rightarm, hit) * length ) ) )
    
    pop.addline("Left Leg: %0.2f%%" % (getPercent(leftleg, hit) * 100) )
    pop.addline("%s" % ("|" * int(getPercent(leftleg, hit) * length ) ) )

    pop.addline("Right Leg: %0.2f%%" % (getPercent(rightleg, hit) * 100) )
    pop.addline("%s" % ("|" * int(getPercent(rightleg, hit) * length ) ) )
           
    pop.timeout("view", int(stats_poptime))
    pop.send(userid)
