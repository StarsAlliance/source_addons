# ==============================================================================
#   IMPORTS
# ==============================================================================
# Python Imports
import os
import copy

# EventScripts Imports
import langlib
import xa

# ==============================================================================
#   HELPER CLASSES
# ==============================================================================
class LanguageDict(dict):
    """
        XA's Language class 
        
        One of these is created for each strings.ini entry

    """
    # Class variables
    languages = langlib.getLanguages()
    abbreviations = map(langlib.getLangAbbreviation, languages)
    defaultlang = langlib.getDefaultLang()

    def __init__(self, key, value):
        # Create our pseudo dict object
        self.name = key
        
        # Is the value already a dict?
        if isinstance(value, dict):
            self.text = self.mapdict(str, value)
        else:
            self.text = {self.defaultlang:str(value)}

    def __str__(self):
        # Return a printable string
        return self.name
        
    def __repr__(self):
        # Return something that represents our object
        return 'LanguageDict(%s)' % self.name
        
    def __len__(self):
        # Return the length of our pseudo dict
        return len(self.abbreviations)
        
    def __getitem__(self, key):
        # Get a translation from our pseudo dict
        # Is this a valid key for our pseudo dict?
        if key in self.abbreviations:
            # Is there a translation inside your dict?
            if key in self.text:
                return self.text[key]
            
            # Is the default language available?
            elif self.defaultlang in self.text:
                return self.text[self.defaultlang]
                
            # Is the english language available? 
            elif 'en' in self.text:
                return self.text['en']
                
            else:
                # Nothing there, raise an error
                raise IndexError('LanguageDict(%s): No language string available' % self.name)
                
        else:
            # Invalid key, raise an error
            raise IndexError('LanguageDict(%s): No valid abbreviation' % self.name)
            
    def __setitem__(self, key, value):
        # Add a new translation to our pseudo dict
        # Is this a valid key for our pseudo dict?
        if key in self.abbreviations:
            self.text[key] = str(value)
            
        else:
            # Invalid key, raise an error
            raise IndexError('LanguageDict(%s): No valid abbreviation' % self.name)
            
    def __delitem__(self, key):
        # Delete a translation from our pseudo dict
        # Is this a valid key for our pseudo dict?
        if key in self.abbreviations:
            # Is this a custom non-default translation?
            if key != self.defaultlang and key != 'en':
                del self.text[key]
                
            else:
                # No, it's a required translation, raise an error
                raise ValueError('LanguageDict(%s): You can\'t delete the default keys' % self.name)
                
        else:
            # Invalid key, raise an error
            raise IndexError('LanguageDict(%s): No valid abbreviation' % self.name)
            
    def __iter__(self):
        # Return something we can loop through
        return self.abbreviations.__iter__()
        
    def itervalues(self):
        return self.text.itervalues()
        
    def iterkeys(self):
        return self.text.iterkeys()
    
    def iteritems(self):
        return self.text.items()
        
    def __contains__(self, key):
        # Is this a valid key for our pseudo dict?
        return key in self.abbreviations
            
    def clear(self):
        # Oops, translations should not be cleared
        pass

    def copy(self):
        # Create a new copy of our pseudo dict
        return copy.copy(self)

    def has_key(self, key):
        # Is this a valid key for our pseudo dict?
        return self.__contains__(key)

    def items(self):
        # Return our translations
        return self.text.items()
        
    def keys(self):
        # Return our languages
        return self.abbreviations
        
    def update(self, iterable):
        # Update our translations
        return self.text.update(iterable)
        
    def fromkeys(self, seq, value = None):
        # Ooops, what's that? Doesn't matter, might be useful
        return self.text.fromkeys(seq, value)
        
    def values(self):
        # Return our translations
        return self.text.values()
        
    def mapdict(self, function, iterable):
        # Map a dict into our pseudo dict
        if callable(function) and iterable:
            for key in iterable:
                iterable[key] = function(iterable[key])

            return iterable
            
        else:
            raise TypeError

# ==============================================================================
#   MODULE API FUNCTIONS
# ==============================================================================
def createLanguageString(module, text):
    """
        Create a language string
        
        (im not sure what this is for?)
    """
    # Create a new pseudo dict from only one string
    return LanguageDict(text.lower(), text)

def getLanguage(module, filename = None):
    """
        Retrieve a modules language file
        
        module:         module name (usually automatically provided)
        filename:       optional filename (if different from the default strings.ini)
        
        return:         a dictionary style object containing language strings
        
        Handle's retrieving and accessing a modules strings.ini file
        To use this you need to  create a strings.ini file inside your
        module folder containing a VALID set of language strings.
        
        <xa instance>.language.getLanguage()
    """
    # Create a new pseudo dict from a language INI file
    # Did we specify a custom filename?
    if filename:
        filename = '%s/modules/%s/%s.ini' % (xa.coredir(), module, filename)
    else:
        filename = '%s/modules/%s/strings.ini' % (xa.coredir(), module)
        
    # Is there a custom translation file?
    if os.path.exists(filename.replace('.ini', '.custom.ini')):
        customlangobj = langlib.Strings(filename.replace('.ini', '.custom.ini'))
    else:
        customlangobj = None
    
    # Does our translation file exist?
    if os.path.exists(filename):
        langobj = langlib.Strings(filename)
    else:
        raise IOError, 'Could not find %s!' % filename

    # Merge custom translations into the original translations
    if langobj and customlangobj:
        for key in customlangobj:
            if key in langobj:
                langobj[key].update(customlangobj[key])
            else:
                langobj[key] = customlangobj[key]
    
    # Create pseudo dicts for each string key
    if langobj:
        for key in langobj:
            langobj[key] = LanguageDict(key, langobj[key])
    
    # Return our new pseudo dict
    return langobj
