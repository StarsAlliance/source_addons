#################################
#PLEASE DO NOT REMOVE THIS FILE!#
#################################

try:
    import es
    es.dbgmsg(0, '[eXtensible Admin] Module folder enabled')
except:
    raise IOError, 'Could not enable module folder!'
