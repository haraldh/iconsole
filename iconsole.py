# f0:b2   01:01:04:06 03:11     01:3b  01:07  01:0d   01:01  0f:33    09      02
#           T: 3:05   21.0km/h  RPM58  D:0.6  cal 12  HF 0   W:1450   LVL8
#
# 0 1 : f0:b2
# 2 3 4 5 : d:h:m:s
# 6 7: SPEED kmh * 10
# 8 9: RPM
# 10 11: distance in 10m
# 12 13: calories
# 14 15: HF
# 16 17: WATT * 10
# 18: LVL
# 19: ?
# 20: checksum? sum of all fields?


# f0:a0:01:01:92    - C: PING
# f0:b0:01:01:a2    - M: PONG

# f0:a1:01:01:93    - C: Status?
# f0:b1:01:01:21:c4 - M: ??


# f0:a6:01:01:12:aa - C: LEVEL 17
# f0:a6:01:01:02:9a - C: LEVEL  1

# f0:a5:01:01:02:99 - C: START
# f0:b5:01:01:02:a9 - M: STARTED

# f0:a5:01:01:04:9b - C: STOP
# f0:b5:01:01:04:ab - M: STOPPED

# 93 rpm - 100 W - lvl 1        1.075
# 77 rpm - 100 W - lvl 2        1.3
# 48 rpm - 143.4 W - lvl 12     2.98

# 23.5 W pro Stufe auf 81

# 12 - 350.8 - 82
#      357.7   83
#      364.6   84   6.9 pro rpm

import serial,struct
from time import sleep
from binascii import hexlify

INIT_A0 = struct.pack('BBBBB', 0xf0, 0xa0, 0x02, 0x02, 0x94)
PING = struct.pack('BBBBB', 0xf0, 0xa0, 0x01, 0x01, 0x92)
PONG = struct.pack('BBBBB', 0xf0, 0xb0, 0x01, 0x01, 0xa2)
STATUS = struct.pack('BBBBB', 0xf0, 0xa1, 0x01, 0x01, 0x93)
INIT_A3 = struct.pack('BBBBBB', 0xf0, 0xa3, 0x01, 0x01, 0x01, 0x96)
INIT_A4 = struct.pack('BBBBBBBBBBBBBBB', 0xf0, 0xa4, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0xa0)
START = struct.pack('BBBBBB', 0xf0, 0xa5, 0x01, 0x01, 0x02, 0x99)
STOP = struct.pack('BBBBBB', 0xf0, 0xa5, 0x01, 0x01, 0x04, 0x9b)
READ = struct.pack('BBBBB', 0xf0, 0xa2, 0x01, 0x01, 0x94)

port = serial.Serial('/dev/rfcomm3')
print "OK"
import signal

class GracefulInterruptHandler(object):

    def __init__(self, sig=signal.SIGINT):
        self.sig = sig

    def __enter__(self):

        self.interrupted = False
        self.released = False

        self.original_handler = signal.getsignal(self.sig)

        def handler(signum, frame):
            self.release()
            self.interrupted = True

        signal.signal(self.sig, handler)

        return self

    def __exit__(self, type, value, tb):
        self.release()

    def release(self):

        if self.released:
            return False

        signal.signal(self.sig, self.original_handler)

        self.released = True

        return True

def send_ack(packet, expect=None, plen=0):
    if expect == None:
        expect = 0xb0 | (ord(packet[1]) & 0xF)

    if plen == 0:
        plen = len(packet)

    got = None
    while got == None:
        sleep(0.1)
        port.read_all()
        port.write(packet)
        port.flush()
        #print "->" + hexlify(packet)
        i = 0
        while got == None and i < 6:
            i+=1
            sleep(0.1)
            got = port.read_all()
            if len(got) == plen:
                #print "<-" + hexlify(got)
                pass
            else:
                if len(got) > 0:
                    #print "Got len == %d" % len(got)
                    pass
                got = None

        if got and len(got) >= 3 and got[0] == packet[0] and ord(got[1]) == expect:
            break
        got = None
    return got

def send_level(lvl):
    packet = struct.pack('BBBBBB', 0xf0, 0xa6, 0x01, 0x01, lvl+1, (0xf0+0xa6+3+lvl) & 0xFF)
    got = send_ack(packet)
    return got


#send_level(10)

i = 0
with GracefulInterruptHandler() as h:
    send_ack(PING)
    print "ping done"

    send_ack(INIT_A0, expect=0xb7, plen=6)
    print "A0 done"

    for i in range(0, 5):
        send_ack(PING)
        print "ping done"

    send_ack(STATUS, plen=6)
    print "status done"

    send_ack(PING)
    print "ping done"

    send_ack(INIT_A3)
    print "A3 done"

    send_ack(INIT_A4)
    print "A4 done"

    send_ack(START)
    print "START done"

    while True:
        if h.interrupted:
            break
        sleep(0.4)
        i+=1
        #    if i % 20 == 2:
        #        send_level((i/20) +1)

        got = send_ack(READ, plen=21)
        if len(got) == 21:
            gota = struct.unpack('BBBBBBBBBBBBBBBBBBBBB', got)
            time = "%02d:%02d:%02d:%02d" % (gota[2]-1, gota[3]-1, gota[4]-1, gota[5]-1)
            speed = "V: % 3.1f km/h" % ((100*(gota[6]-1) + gota[7] -1) / 10.0)
            rpm = "% 3d RPM" % ((100*(gota[8]-1) + gota[9] -1))
            distance = "D: % 3.1f km" % ((100*(gota[10]-1) + gota[11] -1) / 10.0)
            calories = "% 3d kcal" % ((100*(gota[12]-1) + gota[13] -1))
            hf = "HF % 3d" % ((100*(gota[14]-1) + gota[15] -1))
            watt = "% 3.1f W" % ((100*(gota[16]-1) + gota[17] -1) / 10.0)
            lvl = "L: %d" % (gota[18] -1)
            print "%s - %s - %s - %s - %s - %s - %s - %s" % (time, speed, rpm, distance, calories, hf, watt, lvl)

send_ack(STOP)
print "STOP done"

for i in range(0, 5):
    send_ack(PING)
    print "ping done"

port.close()
