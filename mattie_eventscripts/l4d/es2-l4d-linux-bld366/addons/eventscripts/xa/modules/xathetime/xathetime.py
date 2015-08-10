# ./xa/modules/xathetime/xathetime.py

import es
import time
from xa import xa

#plugin information
info = es.AddonInfo()
info.name       = "The Time"
info.version    = "1.0"
info.author     = "Unknown"
info.basename   = "xathetime"

xathetime               = xa.register(info.basename)
adjust_time             = xathetime.setting.createVariable('adjust_time', 0, 'Minutes to add to server clock')
military_time           = xathetime.setting.createVariable('military_time', 0, '0 = use 12hr format, 1 = use 24hr format')
thetime_player_only     = xathetime.setting.createVariable('thetime_player_only', 1, '0 = time is sent to all players on request, 1 = time is only sent to the requesting player')
thetime_timezone        = xathetime.setting.createVariable('thetime_timezone', 'GMT', 'Timezone to display -- DOES NOT AFFECT TIME DISPLAYED')


def load():
    """ """
    xathetime.addCommand('thetime', show_time, 'display_thetime', 'UNRESTRICTED').register(('console', 'say'))


def unload():
    """ """
    xathetime.unregister()


def show_time():
    """ """
    int_userid = es.getcmduserid()
    xathetime.logging.log('requested the current time' % int_userid)

    tuple_time = time.localtime(time.time() + (60 * int(adjust_time)))
    if int(military_time):
        int_hour = tuple_time[3]
    else:
        int_hour = tuple_time[3] % 12
    str_time = '%s:%02d %s %s-%s-%s' % (int_hour, tuple_time[4], thetime_timezone, tuple_time[2], tuple_time[1], tuple_time[0])

    if int(thetime_player_only):
        es.tell(int_userid, str_time)
    else:
        es.msg(str_time)
