from pyee import EventEmitter
import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc):
        print("MQTT: Connected returned result: "+connack_string(rc))

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("MQTT: Unexpected disconnection.")
    else:
        print("MQTT: disconnected.")

def on_subscribe(client, userdata, mid, granted_qos):
    print("MQTT: subscribed", userdata, mid, granted_qos)

def on_message(client, userdata, message):
    print("MQTT: Received message '" + str(message.payload) + "' on topic '" + message.topic + "' with QoS " + str(message.qos))
    command  = message.topic.split('/')[1:]
    args = message.payload.decode().split('§')
    userdata.emit(command[0], tuple(args))
    # print("emit", command[0], tuple(args))

class Mqttinterface(EventEmitter):

    # Init object
    def __init__(self, addr):
        super().__init__()

        self.client = mqtt.Client(userdata=self)
        self.client.connect("2.0.0.1")
        self.client.subscribe("titreur/#", 2)
        self.client.on_connect = on_connect
        self.client.on_disconnect = on_disconnect
        self.client.on_subscribe = on_subscribe
        self.client.on_message = on_message
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop(True)


    # Read UDP input
    def callback(self):
        try:
            data, address = self.sock.recvfrom(4096)
            data = data.decode('utf-8').strip().split(' ')

            # speed TIMEMIN [TIMEMAX]
            if data[0] == "speed":
            	if len(data) >= 3 and data[2] != "#":
            		SPEEDMIN = int(data[1])
            		SPEEDMAX = int(data[2])
            	elif len(data) >= 2:
            		SPEEDMIN = int(data[1])
            		SPEEDMAX = int(data[1])
            	self.emit('speed', (SPEEDMIN, SPEEDMAX))

            # scrool speed
            elif data[0] == "scroll":
            	if len(data) >= 2:
            		SCROLLSPEED = int(data[1])
            		self.emit('scroll', SCROLLSPEED)

            # clear
            elif data[0] == "clear":
            	self.emit('clear')

            # add text
            elif data[0] == "add":
            	if len(data) >= 3:
            		mode = data[1]
            		txt = "_".join(data[2:])
            		self.emit('add', (txt, mode))

            # text
            elif data[0] == "text":
            	if len(data) >= 3:
            		mode = data[1]
            		txt = "_".join(data[2:])
            		self.emit('text', (txt, mode))

            # tick
            elif data[0] == "tick":
            	self.emit('tick')


        except socket.timeout:
            pass

