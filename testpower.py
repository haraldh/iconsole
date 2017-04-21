import serial, struct, sys, hashlib, curses
from time import sleep
from binascii import hexlify,unhexlify
from ant.core import driver
from ant.core import node
from bluetooth import *
from PowerMeterTx import PowerMeterTx
from iConst import *

power_meter = None

POWER_SENSOR_ID = int(int(hashlib.md5(getserial()).hexdigest(), 16) & 0xfffe) + 1

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

    i = 0
    while True:
        sleep(1)
        power_meter.update(power = i, cadence = i)
        i += 1
        if (i > 200):
            break

    if power_meter:
        print "Closing power meter"
        power_meter.close()
        power_meter.unassign()
    if antnode:
        print "Stopping ANT node"
        antnode.stop()

