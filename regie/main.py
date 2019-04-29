
import random
import curses
import os.path
import threading
import time
import socket
import subprocess

# ///////////////
# import pandas as pd
# from pandas import ExcelFile
#
# path = 'beaucoup.xlsx'
# path = os.path.join( os.path.dirname(os.path.realpath(__file__)), '../scenario' , path )
#
# xl = pd.ExcelFile(path)
# print(xl.sheet_names)
#
# df = xl.parse("Sheet1")
# print(df.head())
#
#
# exit()
# ///////////////

BROADCAST = '2.0.255.255'
DEVICES = ['2.0.11.44', '2.0.11.45', '2.0.11.48', '2.0.11.50', '2.0.11.51', '2.0.11.52']
TITREURS = []
PORT = 3742
CONSOLE = []


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
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(cmd.encode('utf-8'), (self.ip, self.port))
        except:
            print("UDP send error")

    def clear(self):
        self.currentPL = []
        self.send('clear')

    def text(self, txt, mode=None ):
        self.currentPL = [txt]
        if not mode: mode = getMode(txt)
        if txt == '': txt = '_'
        self.send('text '+mode+' '+txt)

    def add(self, txt, mode=None):
        self.currentPL.append(txt)
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
    curses.resizeterm(100,200)
    curses.curs_set(0)

    for ip in DEVICES:
        TITREURS.append( Titreur(ip) )

    page = 'scene'
    freetxt = ''
    playtxt = ''

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
                else: # F1 -> F8
                    k = key-265
                    if k < len(DEVICES):
                        for t in TITREURS:
                            if t.ip == DEVICES[k]:
                                t.selected = not t.selected

            # CLEARALL
            elif key == 360 or key == 259: # END or ARROW UP
                for t in TITREURS:
                    if t.scene_val > 0: t.stop()
                    t.clear()

            # CLEARSELECTED
            elif key == 330: # SUPPR
                for t in [ti for ti in TITREURS if ti.selected]:
                    if t.scene_val > 0: t.stop()
                    t.clear()

            # MODE SCENE
            elif key == 339 or key == 261: # PAGEUP or ARROW RIGHT
                page = 'scene'

            # MODE FREETYPE
            elif key == 262 or key == 258:  # HOME or ARROW DOWN
                page = 'free'
                freetxt = ''
                for t in [ti for ti in TITREURS if ti.selected]:
                    t.speed(0)

            # MODE PLAYLIST
            elif key == 331 or key == 260: # INSER or ARROW LEFT
                page = 'play'
                playtxt = ''
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
                    win.addstr("speed "+str(t.speed_val[0])+" "+str(t.speed_val[1]), curses.A_DIM)

                win.addstr("\t"+(' | ').join(t.currentPL))
                win.addstr("\n      ")

                if t.scene_val > 0:
                    win.addstr(t.information, curses.A_DIM)
                else:
                    win.addstr("scroll "+str(t.scroll_val), curses.A_DIM)

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
                if key == 263 or key == 127:
                    freetxt = freetxt[:-1]
                # CHAR
                elif key >= 32 and key <= 168:
                    freetxt += chr(key)
                # ENTER = clear
                elif key == 10:
                    freetxt = ''

                if cFt != freetxt:
                    for t in [ti for ti in TITREURS if ti.selected]:
                        if t.scene_val > 0: t.stop()
                        if freetxt != '': t.text(freetxt)
                        else: t.clear()

                win.addstr(" MODE FREE TYPE \n", curses.A_STANDOUT)
                win.addstr("   Enter = clear for next \n")
                win.addstr("   /     = second line\n\n")
                win.addstr("   "+freetxt.replace("/", "\n   "))


            #
            # MODE PLAYLIST
            #
            if page == 'play':

                # CHAR
                # BACKSPACE
                if key == 263 or key == 127:
                    playtxt = playtxt[:-1]
                elif key >= 32 and key <= 168:
                    playtxt += chr(key)
                # ENTER = add
                elif key == 10:
                    for t in [ti for ti in TITREURS if ti.selected]:
                        if t.scene_val > 0: t.stop()
                        if playtxt.startswith('#speed') or playtxt.startswith('<<') or playtxt.startswith('>>'):
                            data = playtxt.split(' ')
                            if len(data) == 2: data.append(data[1])
                            if len(data) > 1:
                                t.speed(data[1], data[2])
                        else: t.add(playtxt)
                    playtxt = ''

                win.addstr(" MODE PLAYLIST \n", curses.A_STANDOUT)
                win.addstr("   Enter = add text to playlist \n")
                win.addstr("   /     = second line\n\n")
                win.addstr("   "+playtxt.replace("/", "\n   "))


            if key == -1: time.sleep(0.1)
            else: win.addstr("\n\n"+str(key))


            curses.doupdate()
            curses.curs_set(0)



        # except Exception as e:
        #    # No input
        #    pass


curses.wrapper(main)
