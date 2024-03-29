import logging
from subprocess import Popen, PIPE, STDOUT
import fcntl, os
from pyee import EventEmitter

class Hardware6(EventEmitter):

    # Init titreur object
    def __init__(self, binarypath):
        super().__init__()

        self.currentTxtCmd = ""

        my_path = os.path.abspath(os.path.dirname(__file__))
        self.binarypath =  os.path.join(my_path, binarypath)
        self.running = False
        self.log = logging.getLogger('hardware process')

        self.speed = 60

        self.MODES = {}
        self.MODES['NO_SCROLL_NORMAL'] = 0
        self.MODES['SCROLL_NORMAL'] = 1
        self.MODES['SCROLL_LOOP_NORMAL'] = 2
        self.MODES['SCROLL_VERTICAL_NORMAL'] = 11		# broken
        self.MODES['SCROLL_VERTICAL_LOOP_NORMAL'] = 12	# broken
        self.MODES['NO_SCROLL_BIG'] = 100
        self.MODES['SCROLL_BIG'] = 101
        self.MODES['SCROLL_LOOP_BIG'] = 102
        self.MODES['SCROLL_VERTICAL_BIG'] = 111			# broken
        self.MODES['SCROLL_VERTICAL_LOOP_BIG'] = 112	# broken


    # Start communication with hardware
    def start(self):

        # Start external binary
        try:
            self.proc = Popen([self.binarypath], stdout=PIPE, stdin=PIPE, stderr=PIPE)


            # Wait for #INITHARDWARE
            line = self.proc.stdout.readline().strip()
            if line != b"#INITHARDWARE":
                self.log.critical("Can't start hardware communication: "+str(line))
                self.running = False
                return False

            # Send init command
            self.log.info("Initializing hardware..")
            self.proc.stdin.write(b'initconfig -carteVolt ? -name kxkm -titreurNbr 6 -manualmode 1\n')
            self.proc.stdin.flush()

            # Wait for #HARDWAREREADY
            line = self.proc.stdout.readline().strip()
            if line != b"#HARDWAREREADY":
                self.log.critical("Can't init hardware: "+str(line))
                self.running = False
                return False

            # Titreur is ready
            self.log.info("Hardware initialized")
            self.running = True
        except:
            pass
        
        return True


    # Stop communication
    def stop(self):
        self.proc.kill()
        self.running = False


    # Start communication with hardware
    def non_block_read(self, pipe):
        if not self.running:
            return
        fd = pipe.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        try:
            return pipe.read()
        except:
            return ""


    # Read everything from hardware
    def flush_output(self):
        while True:
            out = self.non_block_read(self.proc.stdout)
            if out == "" or not out:
                break
            self.log.debug(" -- hardware6 says:", out.strip())
        while True:
            out = self.non_block_read(self.proc.stderr)
            if out == "" or not out:
                break
            self.log.debug(" -- hardware6 err:", out.strip())


    # Send CMD
    def send(self, cmd):
        try:
            self.flush_output()
            self.proc.stdin.write(cmd.encode('utf-8'))
            self.proc.stdin.flush()
            self.flush_output()
        except:
            pass

    # Display text on Titreur
    def text(self, txt, mode=None):
        if isinstance(txt, list):
            if len(txt) > 2:
                self.scroll(txt[2])
            if len(txt) > 1:
                mode = txt[1]
            txt = txt[0] 
        if not txt:
            txt = ' '

        txt = txt.split(';')
        cmd = 'texttitreur'
        cmd += ' -line1 ' + txt[0].replace(' ', '_')
        if len(txt) > 1:
            cmd += ' -line2 ' + txt[1].replace(' ', '_')

        if not mode in self.MODES.keys():
            if len(txt) > 1:
                mode = 'NO_SCROLL_NORMAL'
            else:
                mode = 'NO_SCROLL_BIG'

        cmd += ' -type ' + mode
        cmd += ' -speed ' + str(self.speed)
        cmd += '\n'
        
        if self.currentTxtCmd != cmd:
            self.currentTxtCmd = cmd
            self.send(cmd)
            print(cmd)

    # Set text scroll speed
    def scroll(self, speed):
        self.speed = 128-int(speed)


    # change strip color
    def leds(self, color, strobe=0, fade=0):
        color = color.lstrip('#')
        RGB = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        cmd = 'setlight'
        cmd += ' -rgb ' + str(RGB[0]) +' '+ str(RGB[1]) +' '+ str(RGB[2]) 
        if (fade > 0):       cmd += ' -fade ' + str(fade)
        if (strobe > 0):     cmd += ' -strob ' + str(strobe)
        cmd += '\n'

        if self.currentTxtCmd != cmd:
            self.currentTxtCmd = cmd
            self.send(cmd)

    def dmx(self, values):

        RGB = [values[1], values[2], values[3]]
        MASTER = values[0]
        RGB[0] = int((RGB[0]*MASTER)/255)
        RGB[1] = int((RGB[1]*MASTER)/255)
        RGB[2] = int((RGB[2]*MASTER)/255)
        print("DMX", MASTER, RGB)
        cmd = 'setlight'
        cmd += ' -rgb ' + str(RGB[0]) +' '+ str(RGB[1]) +' '+ str(RGB[2]) 
        cmd += '\n'

        if self.currentTxtCmd != cmd:
            self.currentTxtCmd = cmd
            self.send(cmd)

            
