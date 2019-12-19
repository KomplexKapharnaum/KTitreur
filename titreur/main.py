import signal, sys
from hardware6 import Hardware6
from textlist import Textlist
from udpinterface import Udpinterface
from mqttinterface import Mqttinterface
from oscinterface import OscInterface

# RUN
RUN = True

if len(sys.argv) < 2:
        print('no broker specified, default to 2.0.0.1')
        brokerIP = "2.0.0.1"
else : 
        brokerIP = sys.argv[1]

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
texts.on('color', hw.leds)

# RAW UDP
UDP_PORT = 3742
udp = Udpinterface(UDP_PORT)
udp.on('speed',     texts.autoPick )
udp.on('scroll',    hw.scroll)
udp.on('clear',     texts.clear)
udp.on('add',       texts.add)
udp.on('rm',        texts.rm)
udp.on('text',      texts.set)
udp.on('tick',      texts.pick)

# MQTT
mqtt = Mqttinterface(brokerIP)
mqtt.on('titre/speed',     texts.autoPick )
mqtt.on('titre/scroll',    hw.scroll)
mqtt.on('titre/clear',     texts.clear) 
mqtt.on('titre/add',       texts.add)
mqtt.on('titre/rm',        texts.rm)
mqtt.on('titre/text',      texts.set)
mqtt.on('titre/tick',      texts.pick)
mqtt.on('leds/dmx',         hw.dmx)

# OSC
osc = OscInterface(9137)
osc.on('leds/dmx', hw.dmx )

# STARTUP BEHAVIOUR 
texts.set( ["  BEAUCOUPBEAUCOUPBEAUCOUP ", 'SCROLL_BIG', 127] )
texts.autoPick(500)

# LOOP
while RUN:
    udp.check()

# EXIT
hw.stop()
mqtt.stop()
