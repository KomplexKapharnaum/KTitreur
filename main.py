import signal
from hardware6 import Hardware6
from textlist import Textlist
from udpinterface import Udpinterface

# RUN
RUN = True

def signal_handler(signal, frame):
    global RUN
    RUN = False
signal.signal(signal.SIGINT, signal_handler)

# HARDWARE
hw = Hardware6('bin/hardware6')
RUN = hw.start()

# TEXTLIST
texts = Textlist()
texts.on('pick', hw.text)

# RAW UDP
udp = Udpinterface(3742)
udp.on('auto',      texts.autoPick )
udp.on('scroll',    hw.scroll)
udp.on('clear',     texts.clear)
udp.on('add',       texts.add)
udp.on('text',      texts.set)
udp.on('tick',      texts.pick)

# OSC


# DEFAULT BEHAVIOUR
texts.add( (" beaucoup / beaucoup", 'NO_SCROLL_NORMAL') )
texts.add( ("beaucoup beaucoup", 'NO_SCROLL_BIG') )
texts.add( ("           beaucoup /     beaucoup", 'SCROLL_LOOP_NORMAL') )
texts.add( ("    beaucoup beaucoup", 'SCROLL_LOOP_BIG') )
texts.autoPick(2000)

# LOOP
while RUN:
    udp.check()

# EXIT
hw.stop()
