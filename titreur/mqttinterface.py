from pyee import EventEmitter
import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc):
        print("MQTT: Connected returned result: "+mqtt.connack_string(rc))

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("MQTT: Unexpected disconnection.")
    else:
        print("MQTT: disconnected.")
    userdata.stop()
    userdata.connected = False

def on_subscribe(client, userdata, mid, granted_qos):
    print("MQTT: subscribed", userdata, mid, granted_qos)

def on_message(client, userdata, message):
    print("MQTT: Receivedz message '" + str(message.payload) + "' on topic '" + message.topic + "' with QoS " + str(message.qos))
    command  = '/'.join(message.topic.split('/')[2:])
    # print('--comand', command)
    args = None
    if command.startswith('leds'):
        args = list(message.payload)
    else: 
        args = message.payload.decode().split('|')
    userdata.emit(command, args)
    # print("--", command, args)

class Mqttinterface(EventEmitter):

    # Init object
    def __init__(self, addr):
        super().__init__()
        self.connected = False 
        self.broker = addr
        self.connect()
        
        
    def connect(self):
        print('MQTT: connecting to ', self.broker)
        channel = '1'
        try:
            with open('/root/id') as f:
                channel = f.read().strip()
        except:
            pass
        
        try:
            print('CHANNEL: ', channel)
            self.client = mqtt.Client(userdata=self)
            self.client.connect(self.broker)
            self.client.subscribe("titreur/all/#", 2)
            self.client.subscribe("titreur/c"+channel+"/#", 2)
            
            self.client.on_connect = on_connect
            self.client.on_disconnect = on_disconnect
            self.client.on_subscribe = on_subscribe
            self.client.on_message = on_message
            self.client.loop_start()
            self.connected = True 
            print('MQTT: connected !')
        except:
            self.connected = False
            print('MQTT: connection error..')
            
    
    def check(self):
        if not self.connected:
            self.connect()

    def stop(self):
        self.client.loop_stop(True)


