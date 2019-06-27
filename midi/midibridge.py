
import rtmidi
import time, signal
import xlrd
import paho.mqtt.client as mqtt

#
# TITREUR
#
def getMode(txt):
    if '/' in txt:
        if len(txt.split('/')[1]) < 9: return 'NO_SCROLL_NORMAL'
        else: return 'SCROLL_LOOP_NORMAL'
    else:
        if len(txt) < 13: return 'NO_SCROLL_BIG'
        else: return 'SCROLL_LOOP_BIG'


#
# XLS
#
class XlsParser():
    def __init__(self, path):
        self.workbook = xlrd.open_workbook(path)
        self.worksheet = self.workbook.sheet_by_index(0)
        self.bank(1)

    def bank(self, b):
        self.offset = max(1, 16*(b-1)+1)

    def note2txt(self, note):
        # C1 = 24 // C2 = 36
        colx = (note//12)-1 
        rowx = self.offset + (note%12) + 1
        return self.worksheet.cell_value( rowx, colx )


#
# MIDI
#
MIDITYPE = {
                8: 'NOTEOFF', 
                9: 'NOTEON',
                10: 'AFTERTOUCH',
                11: 'CC',
                12: 'PC',
                13: 'PRESSURE',
                14: 'PITCHBEND',
                15: 'SYSTEM'
            }

MIDISYS = {
                0: 'SYSEX', 
                1: 'MTC',
                2: 'SONGPOS',
                3: 'SONGSEL',
                4: 'UNDEFINED1',
                5: 'UNDEFINED2',
                6: 'TUNE',
                7: 'SYSEXEND',
                8: 'CLOCK',
                9: 'UNDEFINED3',
                10: 'START',
                11: 'CONTINUE',
                12: 'STOP',
                13: 'UNDEFINED4',
                14: 'SENSING',
                15: 'RESET'
            }

class MidiMessage():
    def __init__(self, message):
        self.message = message

        self.type = message[0]//16
        self.channel = message[0]%16
        self.values = message[1:]

        if self.maintype() == 'NOTEON' and self.values[1] == 0:
            self.type == 8     # convert to NOTEOFF

        # Convert Note Value
        # if self.type == 'NOTEON' or self.type == 'NOTEOFF':
            # self.values[0] += 1     
    
    def maintype(self):
        return MIDITYPE[self.type]
    
    def systype(self):
        return MIDISYS[self.channel]

    def payload_raw(self):
        return self.maintype() + ' ' + self.channel + '/' + '-'.join([str(v).zfill(3) for v in self.values ])+'§NO_SCROLL_NORMAL'
    


class MidiToMQTTHandler(object):
    def __init__(self, mqttc, parser):
        self._wallclock = time.time()
        self._mqttc = mqttc
        self._parser = parser

    def __call__(self, event, data=None):
        msg, deltatime = event
        self._wallclock += deltatime
        mm = MidiMessage(msg)

        if mm.maintype() == 'NOTEON':
            txt = self._parser.note2txt( mm.values[0] ) 
            txt += '§' + getMode(txt)
            self._mqttc.publish('titreur/add', payload=txt, qos=2, retain=False)

        elif mm.maintype() == 'NOTEOFF':
            txt = self._parser.note2txt( mm.values[0] ) 
            txt += '§' + getMode(txt)
            self._mqttc.publish('titreur/rm', payload=txt, qos=2, retain=False)


class MidiInterface():
    def __init__(self, name, addr, parser):
        self.name = name

        self.mqttc = mqtt.Client()
        self.mqttc.connect(addr)
        self.mqttc.loop_start()

        self.midiIN = rtmidi.MidiIn()
        self.midiIN.open_virtual_port(name)
        self.midiIN.set_callback( MidiToMQTTHandler(self.mqttc, parser), data=None)
    
    def stop(self):
        self.mqttc.loop_stop(True)
        del self.midiIN




if __name__ == '__main__':
    xls = XlsParser("MidiMapping.xls")
    midiIN = MidiInterface("Ktitreur-Midi", "2.0.0.1", xls)


    def signal_handler(sig, frame):
        print('You pressed Ctrl+C!')
        midiIN.stop()
    signal.signal(signal.SIGINT, signal_handler)
    print('Press Ctrl+C')
    signal.pause()