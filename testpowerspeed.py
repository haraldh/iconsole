import serial, struct, sys, hashlib, curses
from time import sleep
from binascii import hexlify,unhexlify
from ant.core import driver
from ant.core import node
from PowerMeterTx import PowerMeterTx
from SpeedTx import SpeedTx
from iConst import *

power_meter = None
POWER_SENSOR_ID = int(int(hashlib.md5(getserial()).hexdigest(), 16) & 0xFFFFfffe) + 1
speed = None
SPEED_SENSOR_ID = int(int(hashlib.md5(getserial()).hexdigest(), 16) & 0xFFFFfffe) + 2

if  __name__ =='__main__':
    NETKEY = unhexlify(sys.argv[1])
    stick = driver.USB1Driver(device="/dev/ttyANT", log=None, debug=True)
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

    i = 0
    while True:
        sleep(1)
        power_meter.update(power = i, cadence = i)
        speed.update(speed = 25)
        i += 1
        if (i > 200):
            break

    if power_meter:
        print "Closing power meter"
        power_meter.close()
        power_meter.unassign()
    if speed:
        print "Closing speed sensor"
        speed.close()
        speed.unassign()
    if antnode:
        print "Stopping ANT node"
        antnode.stop()

