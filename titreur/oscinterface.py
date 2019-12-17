from pyee import EventEmitter
import liblo
import socket

class OscInterface(EventEmitter):

    # Init object
    def __init__(self, port):
        super().__init__()

        self.channel = '1'
        with open('/root/id') as f:
            self.channel = f.read().strip()

        self.server = liblo.ServerThread(port)
        self.server.add_method(None, None, self.handler)
        self.server.start()
        print("OSC listening on", port)

    # Read UDP input
    def handler(self, path, args, types, src, userdata):
        path = path.split('/')[1:]

        # check destination
        if path[0] != 'k32' or (path[1] != 'all' and  path[1] != 'c'+self.channel):
            return

        command = "/".join(path[2:])
        self.emit(command, args)
        