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
from binascii import hexlify
from ant.core import driver
from ant.core import node
from PowerMeterTx import PowerMeterTx
from constants import *
from bluetooth import *
from ant.core import message
from ant.core.constants import *
from ant.core.exceptions import ChannelError

INIT_A0 = struct.pack('BBBBB', 0xf0, 0xa0, 0x02, 0x02, 0x94)
PING = struct.pack('BBBBB', 0xf0, 0xa0, 0x01, 0x01, 0x92)
PONG = struct.pack('BBBBB', 0xf0, 0xb0, 0x01, 0x01, 0xa2)
STATUS = struct.pack('BBBBB', 0xf0, 0xa1, 0x01, 0x01, 0x93)
INIT_A3 = struct.pack('BBBBBB', 0xf0, 0xa3, 0x01, 0x01, 0x01, 0x96)
INIT_A4 = struct.pack('BBBBBBBBBBBBBBB', 0xf0, 0xa4, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0xa0)
START = struct.pack('BBBBBB', 0xf0, 0xa5, 0x01, 0x01, 0x02, 0x99)
STOP = struct.pack('BBBBBB', 0xf0, 0xa5, 0x01, 0x01, 0x04, 0x9b)
READ = struct.pack('BBBBB', 0xf0, 0xa2, 0x01, 0x01, 0x94)
POWER_SENSOR_ID = int(int(hashlib.md5(getserial()).hexdigest(), 16) & 0xfffe) + 1
DEBUG = False
LOG = None
NETKEY = '\xB9\xA5\x21\xFB\xBD\x72\xC3\x45'
power_meter = None

SPEED_DEVICE_TYPE = 0x7B
CADENCE_DEVICE_TYPE = 0x7A
SPEED_CADENCE_DEVICE_TYPE = 0x79
POWER_DEVICE_TYPE = 0x0B

VPOWER_DEBUG = False
CHANNEL_PERIOD = 8182

# Get the serial number of Raspberry Pi
def getserial():
    # Extract serial from cpuinfo file
    cpuserial = "0000000000000000"
    try:
        f = open('/proc/cpuinfo', 'r')
        for line in f:
            if line[0:6] == 'Serial':
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR000000000"

    return cpuserial

# Transmitter for Bicycle Power ANT+ sensor
class PowerMeterTx(object):
    class PowerData:
        def __init__(self):
            self.eventCount = 0
            self.eventTime = 0
            self.cumulativePower = 0
            self.instantaneousPower = 0

    def __init__(self, antnode, sensor_id):
        self.antnode = antnode

        # Get the channel
        self.channel = antnode.getFreeChannel()
        try:
            self.channel.name = 'C:POWER'
            self.channel.assign('N:ANT+', CHANNEL_TYPE_TWOWAY_TRANSMIT)
            self.channel.setID(POWER_DEVICE_TYPE, sensor_id, 0)
            self.channel.setPeriod(8182)
            self.channel.setFrequency(57)
        except ChannelError as e:
            print "Channel config error: "+e.message
        self.powerData = PowerMeterTx.PowerData()

    def open(self):
        self.channel.open()

    def close(self):
        self.channel.close()

    def unassign(self):
        self.channel.unassign()

    # Power was updated, so send out an ANT+ message
    def update(self, power, cadence):
        if VPOWER_DEBUG: print 'PowerMeterTx: update called with power ', power
        self.powerData.eventCount = (self.powerData.eventCount + 1) & 0xff
        if VPOWER_DEBUG: print 'eventCount ', self.powerData.eventCount
        self.powerData.cumulativePower = (self.powerData.cumulativePower + int(power)) & 0xffff
        if VPOWER_DEBUG: print 'cumulativePower ', self.powerData.cumulativePower
        self.powerData.instantaneousPower = int(power)
        if VPOWER_DEBUG: print 'instantaneousPower ', self.powerData.instantaneousPower

        payload = chr(0x10)  # standard power-only message
        payload += chr(self.powerData.eventCount)
        payload += chr(0xFF)  # Pedal power not used
        payload += chr(cadence)
        payload += chr(self.powerData.cumulativePower & 0xff)
        payload += chr(self.powerData.cumulativePower >> 8)
        payload += chr(self.powerData.instantaneousPower & 0xff)
        payload += chr(self.powerData.instantaneousPower >> 8)

        ant_msg = message.ChannelBroadcastDataMessage(self.channel.number, data=payload)
        #sys.stdout.write('+')
        #sys.stdout.flush()
        if VPOWER_DEBUG: print 'Write message to ANT stick on channel ' + repr(self.channel.number)
        self.antnode.driver.write(ant_msg.encode())

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
        sleep(0.3)
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
            power_meter.update(power = ic.power, cadence = ic.rpm)

if  __name__ =='__main__':
    sock = btcon()
    stick = driver.USB1Driver(device="/dev/ttyUSB0", log=LOG, debug=DEBUG)
    antnode = node.Node(stick)
    print("Starting ANT node")
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

    curses.wrapper(main)

    if sock:
        send_ack(STOP)
        send_ack(PING)
        sock.close()

    if power_meter:
        print "Closing power meter"
        power_meter.close()
        power_meter.unassign()
    if antnode:
        print "Stopping ANT node"
        antnode.stop()

