from ant.core import message
from ant.core.constants import *
from ant.core.exceptions import ChannelError
from iConst import *
import thread
from binascii import hexlify
import struct

VPOWER_DEBUG = False
CHANNEL_PERIOD = 8182

# Transmitter for Bicycle Power ANT+ sensor
class PowerMeterTx(object):
    data_lock = thread.allocate_lock()

    class PowerData:
        def __init__(self):
            self.eventCount = 0
            self.eventTime = 0
            self.cumulativePower = 0
            self.instantaneousPower = 0
            self.i = 0

    def __init__(self, antnode, sensor_id):
        self.antnode = antnode
        self.power = 0
        self.cadence = 0
        self.sensor_id = sensor_id

        # Get the channel
        self.channel = antnode.getFreeChannel()
        try:
            self.channel.name = 'C:POWER'
            self.channel.assign('N:ANT+', CHANNEL_TYPE_TWOWAY_TRANSMIT)
            self.channel.setID(POWER_DEVICE_TYPE, sensor_id & 0xFFFF, 5)
            self.channel.setPeriod(8182)
            self.channel.setFrequency(57)
        except ChannelError as e:
            print "Channel config error: "+e.message
        self.powerData = PowerMeterTx.PowerData()
        self.channel.registerCallback(self)

    def open(self):
        self.channel.open()

    def close(self):
        self.channel.close()

    def unassign(self):
        self.channel.unassign()

    def update(self, power, cadence):
        self.data_lock.acquire()
        self.power = power
        self.cadence = cadence
        self.data_lock.release()

    def process(self, msg):
        if isinstance(msg, message.ChannelEventMessage) and \
           msg.getMessageID() == 1 and \
           msg.getMessageCode() == EVENT_TX:
            self.broadcast()
        elif isinstance(msg, message.ChannelAcknowledgedDataMessage):
            payload = msg.getPayload()
            a, page, id_ = struct.unpack('BBB', payload[:3])
            if a == 0 and page == 1 and id_ == 0xAA:
                #print ("ChannelAcknowledgedDataMessage: " + hexlify(payload))
                payload = chr(0x01)
                payload += chr(0xAC)
                payload += chr(0xFF)
                payload += chr(0xFF)
                payload += chr(0xFF)
                payload += chr(0xFF)
                payload += chr(0x00)
                payload += chr(0x00)
                ant_msg = message.ChannelBroadcastDataMessage(self.channel.number, data=payload)
                self.antnode.driver.write(ant_msg.encode())
        else:
            print("Message ID %d Code %d" % (msg.getMessageID(), msg.getMessageCode()))

    # Power was updated, so send out an ANT+ message
    def broadcast(self):
        self.powerData.i += 1
        if self.powerData.i % 61 == 15:
            payload = chr(0x50)  # Manufacturer's Info
            payload += chr(0xFF)
            payload += chr(0xFF)
            payload += chr(0x01) # HW Rev
            payload += chr(0xFF) # MID LSB
            payload += chr(0x00) # MID MSB
            payload += chr(0x01) # Model LSB
            payload += chr(0x00) # Model MSB

        elif self.powerData.i % 61 == 30:
            payload = chr(0x51)  # Product Info
            payload += chr(0xFF)
            payload += chr(0xFF) # SW Rev Supp
            payload += chr(0x01) # SW Rev Main
            payload += chr((self.sensor_id >>  0)& 0xFF) # Serial 0-7
            payload += chr((self.sensor_id >>  8)& 0xFF) # Serial 8-15
            payload += chr((self.sensor_id >> 16)& 0xFF) # Serial 16-23
            payload += chr((self.sensor_id >> 24)& 0xFF) # Serial 24-31
        else:
            self.data_lock.acquire()
            power = self.power
            cadence = self.cadence
            self.data_lock.release()

            self.powerData.eventCount = (self.powerData.eventCount + 1) & 0xff
            self.powerData.cumulativePower = (self.powerData.cumulativePower + int(power)) & 0xffff
            self.powerData.instantaneousPower = int(power)

            payload = chr(0x10)  # standard power-only message
            payload += chr(self.powerData.eventCount)
            payload += chr(0xFF)  # Pedal power not used
            payload += chr(cadence)
            payload += chr(self.powerData.cumulativePower & 0xff)
            payload += chr(self.powerData.cumulativePower >> 8)
            payload += chr(self.powerData.instantaneousPower & 0xff)
            payload += chr(self.powerData.instantaneousPower >> 8)

        ant_msg = message.ChannelBroadcastDataMessage(self.channel.number, data=payload)
        self.antnode.driver.write(ant_msg.encode())
