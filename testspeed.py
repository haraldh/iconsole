import serial, struct, sys, hashlib, curses
from time import sleep
from binascii import hexlify
from ant.core import driver
from ant.core import node
from bluetooth import *
from SpeedTx import SpeedTx
from const import *

speed = None

SPEED_SENSOR_ID = int(int(hashlib.md5(getserial()).hexdigest(), 16) & 0xfffe) + 2

if  __name__ =='__main__':
    stick = driver.USB1Driver(device="/dev/ttyANT", log=None, debug=True)
    antnode = node.Node(stick)
    print("Starting ANT node")
    antnode.start()
    key = node.NetworkKey('N:ANT+', NETKEY)
    antnode.setNetworkKey(0, key)

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
        speed.update(speed = 25)
        #print("Speed: %s" % i)
        i += 1
        if (i > 200):
            break

    if speed:
        print "Closing speed sensor"
        speed.close()
        speed.unassign()
    if antnode:
        print "Stopping ANT node"
        antnode.stop()

