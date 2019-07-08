import signal, sys
from hardware6 import Hardware6
from textlist import Textlist
from udpinterface import Udpinterface
from mqttinterface import Mqttinterface

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
UDP_PORT = 3742
if len(sys.argv) >= 2:
    UDP_PORT = int(sys.argv[1])
udp = Udpinterface(UDP_PORT)
udp.on('speed',     texts.autoPick )
udp.on('scroll',    hw.scroll)
udp.on('clear',     texts.clear)
udp.on('add',       texts.add)
udp.on('rm',        texts.rm)
udp.on('text',      texts.set)
udp.on('tick',      texts.pick)

# MQTT
mqtt = Mqttinterface("2.0.0.1")
mqtt.on('speed',     texts.autoPick )
mqtt.on('scroll',    hw.scroll)
mqtt.on('clear',     texts.clear)
mqtt.on('add',       texts.add)
mqtt.on('rm',        texts.rm)
mqtt.on('text',      texts.set)
mqtt.on('tick',      texts.pick)

# STARTUP BEHAVIOUR
texts.set( ("  BEAUCOUP ", 'NO_SCROLL_BIG') )
#texts.add( (" beaucoup / beaucoup", 'NO_SCROLL_NORMAL') )
#texts.add( ("           beaucoup /     beaucoup", 'SCROLL_LOOP_NORMAL') )
#texts.add( ("    beaucoup beaucoup", 'SCROLL_LOOP_BIG') )
texts.autoPick(500)

# LOOP
while RUN:
    udp.check()

# EXIT
hw.stop()
mqtt.stop()
