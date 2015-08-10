# ==============================================================================
#   IMPORTS
# ==============================================================================
# Python Imports
import os

# EventScripts Imports
import es
import keyvalues
import xa

# ==============================================================================
#   MODULE API FUNCTIONS
# ==============================================================================
def getList(module, filename, modfolder = False):
    # Return variable
    lines = []
    
    # Is the filename relative to the modfolder?
    if modfolder:
        filename = ('%s/%s' % (xa.gamedir(), filename)).replace('\\', '/')
    else:
        filename = ('%s/cfg/xa/%s' % (xa.gamedir(), filename)).replace('\\', '/')
    
    # Does the file exist?
    if os.path.exists(filename):
        # Try reading the file into the list
        try:
            file = open(filename, 'rU')
            for line in file:
                if line and (line[0:2] != '//') and (line != '\n'):
                    line = line.replace('\r', '').replace('\n', '').replace('\t', ' ').replace('  ', ' ')
                    lines.append(line)
        finally:
            file.close()
    
    # Return the line list
    return lines

def getAliasList(module, filename, modfolder = False):
    # Return variable
    lines = {}
    
    # Is the filename relative to the modfolder?
    if modfolder:
        filename = ('%s/%s' % (xa.gamedir(), filename)).replace('\\', '/')
    else:
        filename = ('%s/cfg/xa/%s' % (xa.gamedir(), filename)).replace('\\', '/')
    
    # Does the file exist?
    if os.path.exists(filename):
        # Try reading the file into the dict
        try:
            file = open(filename, 'rU')
            for line in file:
                if line and (line[0:2] != '//') and (line != '\n'):
                    line = line.replace('\r', '').replace('\n', '').replace('\t', ' ').replace('  ', ' ').replace('"', '\'')[1:].split('\' ', 1)
                    if line and len(line) >= 2:
                        lines[line[0].replace('\'', '')] = line[1]
        finally:
            file.close()
    
    # Return the line dict
    return lines

def getKeyList(module, filename, modfolder = False):
    # Is the filename relative to the modfolder?
    if modfolder:
        filename = ('%s/%s' % (xa.gamedir(), filename)).replace('\\', '/')
    else:
        filename = ('%s/cfg/xa/%s' % (xa.gamedir(), filename)).replace('\\', '/')
    
    # Does the file exist?
    if os.path.exists(filename):
        # Load the file into a new KeyValues object
        try:
            kv = keyvalues.KeyValues()
            kv.load(filename)
        except:
            kv = None
        
        # Return ou new KeyValues object
        return kv
