from pyee import EventEmitter
import socket

class Udpinterface(EventEmitter):

    # Init object
    def __init__(self, port):
        super().__init__()
        self.sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
        self.sock.bind(("0.0.0.0", port))
        self.sock.settimeout(0.1)
        print("UDP listening on", port)

    # Read UDP input
    def check(self):
        try:
            data, address = self.sock.recvfrom(4096)
            data = data.decode('utf-8').strip().split(' ')
            print ("REceived", data, "from", address)

            # speed TIMEMIN [TIMEMAX]
            if data[0] == "auto":
            	if len(data) >= 3 and data[2] != "#":
            		SPEEDMIN = int(data[1])
            		SPEEDMAX = int(data[2])
            	elif len(data) >= 2:
            		SPEEDMIN = int(data[1])
            		SPEEDMAX = int(data[1])
            	self.emit('auto', (SPEEDMIN, SPEEDMAX))

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
