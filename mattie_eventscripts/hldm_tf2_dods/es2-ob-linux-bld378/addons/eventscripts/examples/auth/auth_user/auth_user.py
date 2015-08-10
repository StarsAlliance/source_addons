import es
import services

def load():
  auth = services.use("auth")
  auth.registerCapability("can_spawn2", auth.ADMIN)

def player_spawn(event_var):
  user = int(event_var['userid'])
  auth = services.use("auth")
  if not auth.isUseridAuthorized(user, "can_spawn2"):
    es.sexec(user, "kill")
