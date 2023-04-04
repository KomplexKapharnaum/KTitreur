
import random
import curses
import os.path
import threading
import time
import socket
import subprocess
import paho.mqtt.client as mqtt


BROADCAST = '10.0.255.255'
DEVICES = ['10.0.11.1', '10.0.11.2', '10.0.11.3', '10.0.11.4', '10.0.11.5', '10.0.11.6', '10.0.11.7', 'webapp']
TITREURS = []
PORT = 3742
CONSOLE = []
BROKER = '10.0.0.1'

mqttc = mqtt.Client()
mqttc.connect(BROKER)
mqttc.loop_start()


def getMode(txt):
    if '/' in txt:
        if len(txt.split('/')[1]) < 9: return 'NO_SCROLL_NORMAL'
        else: return 'SCROLL_LOOP_NORMAL'
    else:
        if len(txt) < 13: return 'NO_SCROLL_BIG'
        else: return 'SCROLL_LOOP_BIG'


class Titreur():
    def __init__(self, ip):
        global PORT
        self.ip = ip
        self.id = DEVICES.index(ip)+1
        self.port = PORT
        self.selected = True
        # self.mode = None
        self.scene_val = 0
        self.scroll_val = 0
        self.speed_val = [1000,1000]
        self.currentPL = []
        self.scenario = ScenarioThread(self)
        self.information = ''

    def send(self, cmd):
        # try:
        #     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #     sock.sendto(cmd.encode('utf-8'), (self.ip, self.port))
        # except:
        #     print("UDP send error")
        cmds = cmd.split(' ')
        args = cmds[1:]
        if cmds[0] == 'add' or cmds[0] == 'text':
            args = reversed(args)
        txt = "§".join(args)
        if self.ip == 'webapp':
            dest = 'webapp'
        else:
            dest = str(self.id)
        mqttc.publish('titreur/c'+dest+'/'+cmds[0], payload=txt, qos=1, retain=False)

    def clear(self):
        self.currentPL = []
        self.send('clear')

    def text(self, txt, mode=None ):
        self.currentPL = [txt]
        if not mode: mode = getMode(txt)
        txt = txt.replace(" ", "_")
        if txt == '': txt = '_'
        self.send('text '+mode+' '+txt)

    def add(self, txt, mode=None):
        self.currentPL.append(txt)
        txt = txt.replace(" ", "_")
        if not mode: mode = getMode(txt)
        self.send('add '+mode+' '+txt)

    def scene(self, num):
        self.scene_val = num
        self.scenario.stop()
        self.scenario = ScenarioThread(self)
        self.scenario.scene(num)

    def stop(self):
        self.scene_val = 0
        self.scenario.stop()
        self.info("")

    def info(self, txt):
        self.information = txt

    def speed(self, min, max=None):
        if not max: max = min
        self.speed_val = [min,max]
        self.send('speed '+str(min)+' '+str(max))

    def scroll(self, s):
        self.scroll_val = s
        self.send('scroll '+str(s))


class ScenarioThread(threading.Thread):
    def __init__(self, titreur):
        threading.Thread.__init__(self)
        self._titreur = titreur
        self._scene = 0
        self._event = threading.Event()

    def scene(self, num):
        self._scene = num
        self.start()


    def run(self):
        path = 'fx-'+str(self._scene)+'.txt'
        path = os.path.join( os.path.dirname(os.path.realpath(__file__)), '../fx' , path )

        if not os.path.exists(path):
            self._titreur.info("ERROR: File "+path+" not found")
            return False

        with open(path) as f:
            content = f.readlines()
        content = [x.strip() for x in content]   # remove \n

        doLoop = True
        self._titreur.info("")
        while doLoop:
            doLoop = False
            for line in content:
                if self._event.is_set(): break
                line = line.strip()
                if line.startswith('#loop'):
                    self._titreur.info("Loop.")
                    doLoop = True
                    break
                elif line.startswith('#quit'):
                    doLoop = False
                    break
                else:

                    # PARSING
                    if line.startswith('#'):
                        data = line.split(' ')

                        if data[0] == "#waitms":
                            if len(data) > 1:
                                self._event.wait(timeout=int(data[1])/1000.0)

                        elif data[0] == "#wait":
                            if len(data) > 1:
                                time = int(float(data[1])*1000)
                                if len(data) > 2:
                                    time2 = int(float(data[2])*1000)
                                    time = random.randint(time,time2)
                                self._event.wait(timeout=time/1000.0)

                        elif data[0] == "#clear":
                            self._titreur.clear()

                        elif data[0] == "#text":
                            if len(data) > 1:
                                self._titreur.text((' ').join(data[1:]))

                        elif data[0] == "#add":
                            if len(data) > 1:
                                self._titreur.add((' ').join(data[1:]))

                        elif data[0] == "#speed":
                            if len(data) == 2: data.append(data[1])
                            if len(data) > 1:
                                self._titreur.speed(data[1], data[2])

                        elif data[0] == "#scroll":
                            if len(data) > 1:
                                self._titreur.scroll(data[1])

        if self._event.is_set():
            self._titreur.info("Stopped.")
        self._titreur.info("Done.")


    def stop(self):
        if self.isAlive():
            self._event.set()
            self.join()
        self._event.clear()



def sendtoall(line):
    global BROADCAST, PORT
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(line.encode('utf-8'), (BROADCAST, PORT))
    except:
        print("UDP broadcast error")


def main(win):
    global DEVICES, BROADCAST, TITREURS, PORT

    win.nodelay(True)
    win.scrollok(1)
    win.keypad(1)
    curses.initscr()
    curses.cbreak()
    curses.noecho()
    curses.resize_term(130,130)
    curses.curs_set(0)

    for ip in DEVICES:
        TITREURS.append( Titreur(ip) )

    showHelp = False
    page = 'play'
    freetxt = ''
    playtxt = ''
    poscursor = 0

    while 1:
        # try:
            key = win.getch()

            # if key == -1:
            #     time.sleep(0.1)
            #     continue

            # DEVICE SELECTOR
            if key >= 265 and key <= 276:
                if key == 276: # F12
                    sel = [ti for ti in TITREURS if ti.selected]
                    for t in TITREURS: t.selected = (len(sel) == 0)
                elif key == 273: # F9
                    for t in TITREURS: t.selected = not t.selected
                elif key == 274:  # F10
                    showHelp = not showHelp
                else: # F1 -> F8
                    k = key-265
                    if k < len(DEVICES):
                        for t in TITREURS:
                            if t.ip == DEVICES[k]:
                                t.selected = not t.selected
            
            # CLEARALL
            elif key == 360 or key == 27: # END  OR ESC
                for t in TITREURS:
                    if t.scene_val > 0: t.stop()
                    t.clear()

            # CLEARSELECTED
            elif key == 330: # SUPPR
                for t in [ti for ti in TITREURS if ti.selected]:
                    if t.scene_val > 0: t.stop()
                    t.clear()

            # MODE SCENE
            elif key == 338 or key == 444 or key == 560: # PAGEDOWN or CTRL + ARROW RIGHTa
                page = 'scene'

            # MODE FREETYPE
            elif key == 339 or key == 481 or key == 525:  # PAGEUP or CTRL + ARROW DOWN
                page = 'free'
                freetxt = ''
                poscursor = 0
                for t in [ti for ti in TITREURS if ti.selected]:
                    t.speed(0)

            # MODE PLAYLIST
            elif key == 262 or key == 443 or key == 545: # HOME or CTRL + ARROW LEFT
                page = 'play'
                playtxt = ''
                poscursor = 0
                for t in [ti for ti in TITREURS if ti.selected]:
                    t.speed(2000)


            #
            # DISPLAY
            #
            win.clear()
            win.addstr("\n BEAUCOUP BEAUCOUP \n\n", curses.A_STANDOUT)


            #
            # DEVICES
            #
            win.addstr(" DEVICES \n\n", curses.A_STANDOUT)
            for k, t in enumerate(TITREURS):
                mode = curses.A_STANDOUT if t.selected else curses.A_BOLD
                win.addstr(" ")
                win.addstr(" "+str(k+1)+" ", mode)
                win.addstr("  ")

                if t.scene_val > 0:
                    win.addstr("SCENE "+str(t.scene_val), curses.A_DIM)
                else:
                    win.addstr("[speed "+str(t.speed_val[0])+"]", curses.A_DIM)

                win.addstr("\t"+(' | ').join(t.currentPL))
                win.addstr("\n      ")

                if t.scene_val > 0:
                    win.addstr(t.information, curses.A_DIM)
                else:
                    idi = t.ip.split('.')
                    if len(idi) >= 4: idi = "id ."+idi[3] 
                    else: idi = t.ip
                    win.addstr("- "+idi)
                # else:
                #     win.addstr("scroll "+str(t.scroll_val), curses.A_DIM)

                win.addstr("\n\n")
            win.addstr("\n")

            #
            # MODE SCENE
            #
            if page == 'scene':

                if key >= 48 and key <= 57:
                    fx = key-48
                    for t in [ti for ti in TITREURS if ti.selected]:
                        t.scene(fx)

                win.addstr(" MODE SCENE FX \n", curses.A_STANDOUT)
                win.addstr("   Select scene FX:  0 -> 9")

            #
            # MODE FREETYPE
            #
            if page == 'free':
                cFt = freetxt
                # BACKSPACE
                if key == 263 or key == 127 or key == 8:
                    if poscursor > 0:
                        freetxt = freetxt[0 : poscursor-1 : ] + freetxt[poscursor : :]
                        poscursor -= 1
                # CHAR
                elif key >= 32 and key <= 168:
                    freetxt = freetxt[:poscursor] + chr(key) + freetxt[poscursor:]
                    poscursor += 1
                # ENTER = clear
                elif key == 10:
                    freetxt = ''
                    poscursor = 0
                # LEFT = move cursor
                elif key == 260:
                    if poscursor > 0: 
                        poscursor -= 1
                # RIGHT = move cursor
                elif key == 261:
                    if poscursor < len(freetxt): 
                        poscursor += 1


                if cFt != freetxt:
                    for t in [ti for ti in TITREURS if ti.selected]:
                        if t.scene_val > 0: t.stop()
                        if freetxt != '': t.text(freetxt)
                        else: t.clear()

                win.addstr(" MODE FREE TYPE \n", curses.A_STANDOUT)
                win.addstr("   Enter = clear for next \n")
                win.addstr("   /     = second line\n\n")
                win.addstr("   "+" ".join(freetxt.replace("/", "\n   ")))
                win.addstr("\n   ")
                for k in range(12):
                    if poscursor == k:
                        win.addstr("° ")
                    else:
                        win.addstr("| ")
                win.addstr("\n   1 2 3 4 5 6 7 8 9 0 1 2")


            #
            # MODE PLAYLIST
            #
            if page == 'play':

                # CHAR
                # BACKSPACE
                if key == 263 or key == 127 or key == 8:
                    if poscursor > 0:
                        playtxt = playtxt[0 : poscursor-1 : ] + playtxt[poscursor : :]
                        poscursor -= 1
                elif key >= 32 and key <= 168:
                    playtxt = playtxt[:poscursor] + chr(key) + playtxt[poscursor:]
                    poscursor += 1
                # ENTER = add
                elif key == 10:
                    for t in [ti for ti in TITREURS if ti.selected]:
                        if t.scene_val > 0: t.stop()
                        # SCROLL SPEED
                        if playtxt.startswith('<') or playtxt.startswith('>'):
                            data = playtxt[1:]
                            # SCROLL
                            if data.startswith('<') or data.startswith('>'):
                                data = data[1:].strip().split(' ')[0]
                                t.scroll(data)
                            # SPEED
                            else:
                                data = data.strip().split(' ')[0]
                                t.speed(data, data)
                        else: t.add(playtxt)
                    playtxt = ''
                    poscursor = 0
                # LEFT = move cursor
                elif key == 260:
                    if poscursor > 0: 
                        poscursor -= 1
                # RIGHT = move cursor
                elif key == 261:
                    if poscursor < len(playtxt): 
                        poscursor += 1

                win.addstr(" MODE PLAYLIST \n", curses.A_STANDOUT)
                win.addstr("   Enter = add text to playlist \n")
                win.addstr("   /     = second line\n")
                win.addstr("   >500  = change speed (ms)\n")
                # win.addstr("   >> 100  = scroll speed \n")
                win.addstr("\n   "+" ".join(playtxt.replace("/", "\n   ")))
                win.addstr("\n   ")
                for k in range(12):
                    if poscursor == k:
                        win.addstr("° ")
                    else:
                        win.addstr("| ")
                win.addstr("\n   1 2 3 4 5 6 7 8 9 0 1 2")


            if key == -1: time.sleep(0.1)
            else: win.addstr("\n\n"+str(key))

            #
            # HELP
            #
            if showHelp:
                win.addstr(" \n\n\n\n")
                win.addstr(" CONTROLS \n", curses.A_STANDOUT)
                win.addstr("   fn+left \t= PLAYLIST mode \n")
                win.addstr("   fn+up \t= FREE TYPE mode \n")
                win.addstr("   fn+down \t= SCENE FX mode \n")
                win.addstr(" \n")
                win.addstr("   F1-F8 \t= SELECT Device (toggle) \n")
                win.addstr("   F9 \t\t= INVERT Selection \n")
                win.addstr("   F12 \t\t= SELECT None / All \n")
                win.addstr(" \n")
                win.addstr("   esc \t\t= CLEAR All \n")
                win.addstr("   suppr \t= CLEAR Selected \n")
                win.addstr(" \n")
                win.addstr("   NB: To send channel 8 to WebApp you must start K32-Bridge\n")
            else:
                win.addstr(" \n\n\n\n")
                win.addstr("   press F10 to display controls ... \n")

            curses.doupdate()
            curses.curs_set(0)



        # except Exception as e:
        #    # No input
        #    pass


curses.wrapper(main)
