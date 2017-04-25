CADENCE_DEVICE_TYPE = 0x7A
SPEED2_DEVICE_TYPE = 0x0F
SPEED_DEVICE_TYPE = 0x7B
SPEED_CADENCE_DEVICE_TYPE = 0x79
POWER_DEVICE_TYPE = 0x0B

# Get the serial number of Raspberry Pi
def getserial():
    machineid = "0000000000000000"
    try:
        f = open('/etc/machine-id', 'r')
        machineid = f.readline()
        f.close()
    except:
        machineid = "ERROR000000000"

    return machineid
