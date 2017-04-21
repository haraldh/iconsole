from ant.core import message
from ant.core.constants import *
from ant.core.exceptions import ChannelError
from iConst import *
import thread
from binascii import hexlify
import struct
import time

SPEED_DEBUG = False
CHANNEL_PERIOD = 8182

# Transmitter for Bicycle Speed ANT+ sensor
class SpeedTx(object):
    data_lock = thread.allocate_lock()

    class SpeedData:
        def __init__(self):
            self.revCounts = 0
            self.ucMessageCount = 0
            self.ulRunTime = 0
            self.ucPageChange = 0
            self.ucExtMesgType = 0

    def __init__(self, antnode, sensor_id, wheel = 0.100):
        self.antnode = antnode
        self.speed = 0
        self.lastTime = 0
        self.wheel = wheel
        self.remWay = 0
        # Get the channel
        self.channel = antnode.getFreeChannel()
        try:
            self.channel.name = 'C:SPEED'
            self.channel.assign('N:ANT+', CHANNEL_TYPE_TWOWAY_TRANSMIT)
            self.channel.setID(SPEED_DEVICE_TYPE, sensor_id, 0)
            self.channel.setPeriod(8118)
            self.channel.setFrequency(57)
        except ChannelError as e:
            print "Channel config error: "+e.message
        self.data = SpeedTx.SpeedData()
        self.channel.registerCallback(self)

    def open(self):
        self.channel.open()

    def close(self):
        self.channel.close()

    def unassign(self):
        self.channel.unassign()

    def update(self, speed):
        self.data_lock.acquire()
        self.speed = speed
        if self.lastTime == 0:
            self.lastTime = time.time()
        self.data_lock.release()

    def process(self, msg):
        if isinstance(msg, message.ChannelEventMessage) and \
           msg.getMessageID() == 1 and \
           msg.getMessageCode() == EVENT_TX:
            self.broadcast()

    def broadcast(self):
        now = time.time()
        self.data_lock.acquire()
        if self.lastTime != 0:
            way = self.speed * (now - self.lastTime) / 3.6 + self.remWay
            rev = int( way / self.wheel )
            self.remWay = way - rev * self.wheel
            self.data.revCounts += rev
        self.lastTime = now
        self.data_lock.release()
        #print "Rev: %d Way: %f" % (rev, way)

        self.data.ucPageChange += 0x20;
        self.data.ucPageChange &= 0xF0;

        self.data.ucMessageCount += 1
        if self.data.ucMessageCount >= 65:
            self.data.ucMessageCount = 0
            self.data.ucExtMesgType += 1
            if self.data.ucExtMesgType >= 4:
                self.data.ucExtMesgType = 1

            if self.data.ucExtMesgType == 1:
                ulElapsedTime2 = int(now/2)
                payload = chr(0x01)
                payload += chr((ulElapsedTime2 >> 8) & 0xFF)
                payload += chr((ulElapsedTime2 >> 16) & 0xFF)
                payload += chr((ulElapsedTime2 >> 24) & 0xFF)
            elif self.data.ucExtMesgType == 2:
                payload = chr(0x02)
                payload += chr(0x02)
                payload += chr(0xFE)
                payload += chr(0x21)
            elif self.data.ucExtMesgType == 3:
                payload = chr(0x03)
                payload += chr(0x01)
                payload += chr(0x01)
                payload += chr(0x01)
        else:
            payload = chr(self.data.ucPageChange & 0x80)
            payload += chr(0xFF)
            payload += chr(0xFF)
            payload += chr(0xFF)

        usTime1024 = int(now * 1024)
        payload += chr(usTime1024 & 0xff)
        payload += chr((usTime1024 >> 8) & 0xff)
        payload += chr(self.data.revCounts & 0xff)
        payload += chr((self.data.revCounts >> 8) & 0xff)

        #print "Broadcast: %s" % hexlify(payload)
        ant_msg = message.ChannelBroadcastDataMessage(self.channel.number, data=payload)
        self.antnode.driver.write(ant_msg.encode())
