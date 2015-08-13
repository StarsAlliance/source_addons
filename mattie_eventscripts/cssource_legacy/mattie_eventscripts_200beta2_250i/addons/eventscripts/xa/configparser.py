import es
import os
import keyvalues
import xa

import psyco
psyco.full()

###########################
#Module methods start here#
########################################################
# All methods that should be able to be called through #
# the API need to have "module" as first parameter     #
########################################################
def getList(module, filename, modfolder = False):
    if modfolder == False:
        filename = ("%s/cfg/xa/%s" % (xa.gamedir(), filename)).replace("\\", "/")
    else:
        filename = ("%s/%s" % (xa.gamedir(), filename)).replace("\\", "/")
    if os.path.exists(filename):
          lines = []
          try:
              file = open(filename, "rU")
              for line in file:
                  if line and (line[0:2] != '//') and (line != '\n'):
                      line = line.replace("\r", "").replace("\n", "").replace("\t", " ").replace("  ", " ")
                      lines.append(line)
          finally:
              file.close()
          return lines
    return False

def getAliasList(module, filename, modfolder = False):
    if modfolder == False:
        filename = ("%s/cfg/xa/%s" % (xa.gamedir(), filename)).replace("\\", "/")
    else:
        filename = ("%s/%s" % (xa.gamedir(), filename)).replace("\\", "/")
    if os.path.exists(filename):
        lines = {}
        try:
            file = open(filename, "rU")
            for line in file:
                if line and (line[0:2] != '//') and (line != '\n'):
                    line = line.replace("\r", "").replace("\n", "").replace("\t", " ").replace("  ", " ")[1:].split("\" ", 1)
                    lines[line[0].replace("\"", "")] = line[1]
        finally:
            file.close()
        return lines
    return False

def getKeyList(module, filename, modfolder = False):
    if modfolder == False:
        filename = ("%s/cfg/xa/%s" % (xa.gamedir(), filename)).replace("\\", "/")
    else:
        filename = ("%s/%s" % (xa.gamedir(), filename)).replace("\\", "/")
    if os.path.exists(filename):
        kv = keyvalues.KeyValues()
        kv.load(filename)
        return kv
    return False
