# ./addons/eventscripts/_libs/python/esthread.py

import es
import gamethread
import sys
import time
import threading
import psyco
psyco.full()

"""
Basic Library for threaded events and method calls.
Started by Hunter.
"""

class ThreadedEvent(threading.Thread):
    def __init__ (self, event_method, event_var):
        es.dbgmsg(1, '[ESThread] ThreadedEvent.__init__(%s, %s)' % (event_method, event_var))
        threading.Thread.__init__(self)
        self.event_var = event_var
        self.event_method = event_method
    def run(self):
        es.dbgmsg(1, '[ESThread] ThreadedEvent.run()')
        try:
            self.event_method(self.event_var)
        except NameError:
            pass

class ThreadedMethod(threading.Thread):
    def __init__ (self, method):
        es.dbgmsg(1, '[ESThread] ThreadedMethod.__init__(%s)' % method)
        threading.Thread.__init__(self)
        self.method = method
        self.args = ()
        self.kw = {}
        self.result = None
        self.done = False
    def execute(self):
        es.dbgmsg(1, '[ESThread] ThreadedMethod.execute()')
        self.result = es.__dict__[self.method](*self.args, **self.kw)
        self.done = True
    def run(self):
        es.dbgmsg(1, '[ESThread] ThreadedMethod.run()')
        if es.__dict__.has_key(self.method):
            gamethread.queue(self.execute)
            while not self.done:
                time.sleep(0.001)

class Event(object):
    def __init__ (self, event_method):
        es.dbgmsg(1, '[ESThread] Event.__init__(%s)' % event_method)
        self.event_method = event_method
        self.thread = None
    def __call__(self, event_var):
        es.dbgmsg(1, '[ESThread] Event.__call__(%s)' % event_var)
        self.thread = ThreadedEvent(self.event_method, event_var)
        self.thread.start()

class Method(object):
    def __init__ (self, method):
        es.dbgmsg(1, '[ESThread] Method.__init__(%s)' % method)
        self.thread = ThreadedMethod(method)
    def __call__(self, *args, **kw):
        es.dbgmsg(1, '[ESThread] Method.__call__(%s, %s)' % (args, kw))
        self.thread.args = args
        self.thread.kw = kw
        self.thread.start()
        self.thread.join()
        return self.thread.result

class ESThread(object):
    def __init__(self, module):
        es.dbgmsg(1, '[ESThread] ESThread.__init__(%s)' % module)
        self.classes = {}
        self.module = module
        self.add = self.__call__
    def __call__(self, *args, **kw):
        es.dbgmsg(1, '[ESThread] ESThread.__call__(%s, %s)' % (args, kw))
        if len(args) and (args[0] in self.classes) or ('__name__' in dir(args[0]) and args[0].__name__ in self.classes):
            self.unregisterEventListener(*args, **kw)
        else:
            self.registerEventListener(*args, **kw)
    def __getattr__(self, name):
        es.dbgmsg(1, '[ESThread] ESThread.__getattr__(%s)' % name)
        try:
            return getattr(self.module, name)
        except AttributeError:
            return Method(name)
    def registerEventListener(self, listener, event_class=None):
        es.dbgmsg(1, '[ESThread] ESThread.registerEventListener(%s, %s)' % (listener, event_class))
        if not event_class:
            event_class = listener
            listener = event_class.__name__
        if not listener in self.classes:
            self.classes[listener] = event_class
        else:
            raise NameError, 'Listener "%s" does already exist!' % listener
        for method in self.classes[listener].__dict__:
            if not method.startswith('_') and type(self.classes[listener].__dict__[method]).__name__ == 'function':
                es.addons.registerForEvent(self.classes[listener], method, Event(self.classes[listener].__dict__[method]))
    def unregisterEventListener(self, listener):
        es.dbgmsg(1, '[ESThread] ESThread.unregisterEventListener(%s)' % listener)
        if not listener in self.classes:
            raise NameError, 'Listener "%s" does not exist!' % listener
        for method in self.classes[listener].__dict__:
            if not method.startswith('_') and type(self.classes[listener].__dict__[method]).__name__ == 'function':
                es.addons.unregisterForEvent(self.classes[listener], method)
        del self.classes[listener]

sys.modules[__name__] = ESThread(sys.modules[__name__])
