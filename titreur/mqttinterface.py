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
    command  = message.topic.split('/')[2:]
    args = message.payload.decode().split('§')
    userdata.emit(command[0], tuple(args))
    print("--", command[0], tuple(args))

class Mqttinterface(EventEmitter):

    # Init object
    def __init__(self, addr):
        super().__init__()

        id = '0'
        with open('/root/id') as f:
            id = f.read().strip()
        
        print('ID: ', id)

        self.client = mqtt.Client(userdata=self)
        self.client.connect("2.0.0.1")
        self.client.subscribe("titreur/all/#", 2)
        self.client.subscribe("titreur/"+id+"/#", 2)
        self.client.on_connect = on_connect
        self.client.on_disconnect = on_disconnect
        self.client.on_subscribe = on_subscribe
        self.client.on_message = on_message
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop(True)


