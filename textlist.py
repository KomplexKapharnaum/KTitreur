import random
from threading import Timer
from pyee import EventEmitter

class Textlist(EventEmitter):

    # Init object
    def __init__(self):
        super().__init__()
        self.texts = []
        self.last = None
        self.timer = Timer(0, self.pick)
        self.minInterval = 0
        self.maxInterval = 0

    # PICK FROM LIST (avoid last item)
    def pick(self):
        self.timer.cancel()

        item = None
        if len(self.texts) == 1:
            item = self.texts[0]
        elif len(self.texts) > 1:
            while True:
                it = random.choice(self.texts)
                if it != self.last:
                    item = it
                    break
        self.last = item
        self.emit('pick', item)

        if self.minInterval > 0:
            next = random.randint(self.minInterval,self.maxInterval)/1000.0
            self.timer = Timer(next, self.pick)
            self.timer.start()

        return item


    # Clear list
    def clear(self, now=True):
        self.texts = []
        if now:
            self.pick()


    # Add to list // item should be a tuple (text, scroll_mode)
    def add(self, item):
        if not isinstance(item, tuple):
            item = (item, None)
        self.texts.append( item )


    # set entire list
    def set(self, lst):
        if not isinstance(lst, list):
            lst = [lst]
        self.clear(False)
        for item in lst:
            self.add(item)
        self.pick()


    # Auto pick
    def autoPick(self, minInterval, maxInterval=None):
        if isinstance(minInterval, tuple):
            maxInterval = minInterval[1]
            minInterval = minInterval[0]
        if not maxInterval:
            maxInterval = minInterval
        self.minInterval = int(minInterval)
        self.maxInterval = int(maxInterval)
        self.pick()
