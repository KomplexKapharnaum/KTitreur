from pyee import EventEmitter
import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc):
        print("MQTT: Connected returned result: "+mqtt.connack_string(rc))

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("MQTT: Unexpected disconnection.")
    else:
        print("MQTT: disconnected.")

def on_subscribe(client, userdata, mid, granted_qos):
    print("MQTT: subscribed", userdata, mid, granted_qos)

def on_message(client, userdata, message):
    print("MQTT: Receivedz message '" + str(message.payload) + "' on topic '" + message.topic + "' with QoS " + str(message.qos))
    command  = '/'.join(message.topic.split('/')[2:])
    # print('--comand', command)
    args = None
    if command.startswith('titre'):
        args = message.payload.decode().split('§')
    elif command.startswith('leds'):
        args = list(message.payload)
    userdata.emit(command, args)
    # print("--", command, args)

class Mqttinterface(EventEmitter):

    # Init object
    def __init__(self, addr):
        super().__init__()

        channel = '1'
        try:
            with open('/root/id') as f:
                channel = f.read().strip()
        except:
            pass

        print('CHANNEL: ', channel)

        self.client = mqtt.Client(userdata=self)
        self.client.connect(addr)
        self.client.subscribe("k32/all/titre/#", 2)
        self.client.subscribe("k32/c"+channel+"/titre/#", 2)
        self.client.subscribe("k32/c16/titre/#", 2)

        self.client.subscribe("k32/all/leds/#", 2)
        self.client.subscribe("k32/c"+channel+"/leds/#", 2)
        self.client.subscribe("k32/c16/leds/#", 2)
        
        self.client.on_connect = on_connect
        self.client.on_disconnect = on_disconnect
        self.client.on_subscribe = on_subscribe
        self.client.on_message = on_message
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop(True)


