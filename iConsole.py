#!/usr/bin/env python

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

import serial, struct, sys, hashlib, curses
from time import sleep
from binascii import hexlify,unhexlify
from ant.core import driver
from ant.core import node
from bluetooth import *
from PowerMeterTx import PowerMeterTx
from SpeedTx import SpeedTx
from iConst import *

INIT_A0 = struct.pack('BBBBB', 0xf0, 0xa0, 0x02, 0x02, 0x94)
PING = struct.pack('BBBBB', 0xf0, 0xa0, 0x01, 0x01, 0x92)
PONG = struct.pack('BBBBB', 0xf0, 0xb0, 0x01, 0x01, 0xa2)
STATUS = struct.pack('BBBBB', 0xf0, 0xa1, 0x01, 0x01, 0x93)
INIT_A3 = struct.pack('BBBBBB', 0xf0, 0xa3, 0x01, 0x01, 0x01, 0x96)
INIT_A4 = struct.pack('BBBBBBBBBBBBBBB', 0xf0, 0xa4, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0xa0)
START = struct.pack('BBBBBB', 0xf0, 0xa5, 0x01, 0x01, 0x02, 0x99)
STOP = struct.pack('BBBBBB', 0xf0, 0xa5, 0x01, 0x01, 0x04, 0x9b)
READ = struct.pack('BBBBB', 0xf0, 0xa2, 0x01, 0x01, 0x94)
DEBUG = False
LOG = None
power_meter = None
speed = None

POWER_SENSOR_ID = int(int(hashlib.md5(getserial()).hexdigest(), 16) & 0xfffe) + 1
SPEED_SENSOR_ID = int(int(hashlib.md5(getserial()).hexdigest(), 16) & 0xfffe) + 2

class IConsole(object):
    def __init__(self, got):
        gota = struct.unpack('BBBBBBBBBBBBBBBBBBBBB', got)
        self.time_str = "%02d:%02d:%02d:%02d" % (gota[2]-1, gota[3]-1, gota[4]-1, gota[5]-1)
        self.speed = ((100*(gota[6]-1) + gota[7] -1) / 10.0)
        self.speed_str = "V: % 3.1f km/h" % self.speed
        self.rpm = ((100*(gota[8]-1) + gota[9] -1))
        self.rpm_str = "% 3d RPM" % self.rpm
        self.distance = ((100*(gota[10]-1) + gota[11] -1) / 10.0)
        self.distance_str = "D: % 3.1f km" % self.distance
        self.calories = ((100*(gota[12]-1) + gota[13] -1))
        self.calories_str = "% 3d kcal" % self.calories
        self.hf = ((100*(gota[14]-1) + gota[15] -1))
        self.hf_str = "HF % 3d" % self.hf
        self.power = ((100*(gota[16]-1) + gota[17] -1) / 10.0)
        self.power_str = "% 3.1f W" % self.power
        self.lvl = gota[18] -1
        self.lvl_str = "L: %d" % self.lvl

def send_ack(packet, expect=None, plen=0):
    if expect == None:
        expect = 0xb0 | (ord(packet[1]) & 0xF)

    if plen == 0:
        plen = len(packet)

    got = None
    while got == None:
        sleep(0.1)
        sock.sendall(packet)
        i = 0
        while got == None and i < 6:
            i+=1
            sleep(0.1)
            got = sock.recv(plen)
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
        #print "---> Retransmit"
    return got

def send_level(lvl):
    packet = struct.pack('BBBBBB', 0xf0, 0xa6, 0x01, 0x01, lvl+1, (0xf0+0xa6+3+lvl) & 0xFF)
    got = send_ack(packet)
    return got

def btcon():
    addr = None
    devs = discover_devices(duration=2, lookup_names = True)
    for (addr, name) in devs:
        if name.startswith("i-CONSOLE"):
            break
        addr = None

    if addr == None:
        print("could not find i-CONSOLE bluetooth")
        sys.exit(0)

    service_matches = find_service( address = addr, uuid = SERIAL_PORT_CLASS )

    if len(service_matches) == 0:
        print("couldn't find i-Console serial port")
        sys.exit(0)

    first_match = service_matches[0]
    port = first_match["port"]
    name = first_match["name"]
    host = first_match["host"]

    print("connecting to \"%s\" on %s" % (name, host))

    # Create the client socket
    sock=BluetoothSocket( RFCOMM )

    sock.connect((host, port))
    return sock

def prints(w, s):
    w.addstr(3, 0, s)
    w.clrtoeol()
    w.refresh()

#send_level(10)
def main(win):
    curses.noecho()
    curses.cbreak()
    win.nodelay(True)
    win.keypad(1)
    win.refresh()

    prints(win, "OK")
    i = 0
    send_ack(PING)
    prints(win, "ping done")

    send_ack(INIT_A0, expect=0xb7, plen=6)
    prints(win, "A0 done")

    for i in range(0, 5):
        send_ack(PING)
        prints(win, "ping done")

    send_ack(STATUS, plen=6)
    prints(win, "status done")

    send_ack(PING)
    prints(win, "ping done")

    send_ack(INIT_A3)
    prints(win, "A3 done")

    send_ack(INIT_A4)
    prints(win, "A4 done")

    send_ack(START)
    prints(win, "START done")

    level = 1

    while True:
        sleep(0.25)
        while True:
            key = win.getch()
            if key == ord('q'):
                return
            elif key == ord('a') or key == curses.KEY_UP or key == curses.KEY_RIGHT:
                if level < 31:
                    level += 1
                prints(win, "Level: %d" % level)
                send_level(level)

            elif key == ord('y') or key == curses.KEY_DOWN or key == curses.KEY_LEFT:
                if level > 1:
                    level -= 1
                prints(win, "Level: %d" % level)
                send_level(level)
            elif key == -1:
                break

        got = send_ack(READ, plen=21)
        if len(got) == 21:
            ic = IConsole(got)
            power_meter.update(power = ic.power, cadence = ic.rpm)
            speed.update(ic.speed)
            win.addstr(0,0, "%s - %s - %s - %s - %s - %s - %s - %s" % (ic.time_str,
                                                             ic.speed_str,
                                                             ic.rpm_str,
                                                             ic.distance_str,
                                                             ic.calories_str,
                                                             ic.hf_str,
                                                             ic.power_str,
                                                             ic.lvl_str))
            win.clrtoeol()
            win.refresh()

if  __name__ =='__main__':
    NETKEY = unhexlify(sys.argv[1])
    stick = driver.USB1Driver(device="/dev/ttyANT", log=LOG, debug=DEBUG)
    antnode = node.Node(stick)
    print("Starting ANT node on network %s" % sys.argv[1])
    antnode.start()
    key = node.NetworkKey('N:ANT+', NETKEY)
    antnode.setNetworkKey(0, key)

    print("Starting power meter with ANT+ ID " + repr(POWER_SENSOR_ID))
    try:
        # Create the power meter object and open it
        power_meter = PowerMeterTx(antnode, POWER_SENSOR_ID)
        power_meter.open()
    except Exception as e:
        print("power_meter error: " + e.message)
        power_meter = None

    print("Starting speed sensor with ANT+ ID " + repr(SPEED_SENSOR_ID))
    try:
        speed = SpeedTx(antnode, SPEED_SENSOR_ID, wheel = 0.1)
        speed.open()
    except Exception as e:
        print("speed error: " + e.message)
        speed = None

    sock = btcon()

    curses.wrapper(main)

    if sock:
        send_ack(STOP)
        send_ack(PING)
        sock.close()

    if speed:
        print "Closing speed sensor"
        speed.close()
        speed.unassign()
    if power_meter:
        print "Closing power meter"
        power_meter.close()
        power_meter.unassign()
    if antnode:
        print "Stopping ANT node"
        antnode.stop()

