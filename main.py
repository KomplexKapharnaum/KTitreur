import signal
from threading import Lock
from hardware6 import Hardware6
from textlist import Textlist
from udpinterface import Udpinterface

# RUN
DONE = Lock()
DONE.acquire()

def signal_handler(signal, frame):
    global DONE
    DONE.release()
signal.signal(signal.SIGINT, signal_handler)

# HARDWARE
hw = Hardware6('bin/hardware6')
if not hw.start():
    DONE.release()
    print("Error when starting titreur. Exiting.")

# TEXTLIST
texts = Textlist()
texts.on('pick', lambda item: hw.text(item[0],item[1]) )
texts.add("hello")
texts.add("world")
texts.autoPick(100)


# RAW UDP
udp = Udpinterface(3742)
udp.on('intervals', lambda inter: texts.autoPick(inter[0],inter[1]) )
udp.on('scroll',    hw.scroll)
udp.on('clear',     hw.clear)
udp.on('add',       hw.add)
udp.on('text',      texts.set)
udp.on('tick',      hw.tick)

# EXIT
with DONE:
    hw.stop()
