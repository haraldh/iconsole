import serial,struct
from time import sleep
from binascii import hexlify
want = struct.pack('BBBBB', 0xf0, 0xb0, 0x01, 0x01, 0xa2)

port = serial.Serial('/dev/rfcomm0')
print "OK"
got = None
while got != want:
    port.write(struct.pack('BBBBB', 0xf0, 0xa0, 0x01, 0x01, 0x92))
    sleep(0.5)
    got = port.read_all()
    print hexlify(got)

print "init done"
port.write(struct.pack('BBBBB', 0xf0, 0xa1, 0x01, 0x01, 0x93))
sleep(0.5)
print hexlify(port.read_all())
port.write(struct.pack('BBBBB', 0xf0, 0xa0, 0x01, 0x01, 0x92))
sleep(0.5)
print hexlify(port.read_all())
port.write(struct.pack('BBBBB', 0xf0, 0xa0, 0x01, 0x01, 0x92))
sleep(0.5)
print hexlify(port.read_all())
port.write(struct.pack('BBBBB', 0xf0, 0xa0, 0x01, 0x01, 0x92))
sleep(0.5)
print hexlify(port.read_all())
port.write(struct.pack('BBBBB', 0xf0, 0xa0, 0x01, 0x01, 0x92))
sleep(0.5)
print hexlify(port.read_all())
port.write(struct.pack('BBBBB', 0xf0, 0xa0, 0x01, 0x01, 0x92))
sleep(0.5)
print hexlify(port.read_all())
port.write(struct.pack('BBBBBB', 0xf0, 0xa3, 0x01, 0x01, 0x01, 0x96))
sleep(0.5)
print hexlify(port.read_all())
port.write(struct.pack('BBBBBBBBBBBBBBB', 0xf0, 0xa4, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0xa0))
sleep(0.5)
print hexlify(port.read_all())
port.write(struct.pack('BBBBBB', 0xf0, 0xa5, 0x01, 0x01, 0x02, 0x99))
sleep(0.5)
print hexlify(port.read_all())
while True:
    port.write(struct.pack('BBBBB', 0xf0, 0xa2, 0x01, 0x01, 0x94))
    sleep(0.5)
    got = port.read_all()
    if len(got) == 21:
        gota = struct.unpack('BBBBBBBBBBBBBBBBBBBBB', got)
        time = "%02d:%02d:%02d:%02d" % (gota[2]-1, gota[3]-1, gota[4]-1, gota[5]-1)
        speed = "V: % 3.1f km/h" % ((100*(gota[6]-1) + gota[7] -1) / 10.0)
        rpm = "RPM: % 3d" % ((100*(gota[8]-1) + gota[9] -1))
        distance = "D: % 3.1f km" % ((100*(gota[10]-1) + gota[11] -1) / 10.0)
        calories = "% 3d kcal" % ((100*(gota[12]-1) + gota[13] -1))
        hf = "HF % 3d" % ((100*(gota[14]-1) + gota[15] -1))
        watt = "% 3.1f W" % ((100*(gota[16]-1) + gota[17] -1) / 10.0)
        lvl = "L: %d" % (gota[18] -1)
        print "%s - %s - %s - %s - %s - %s - %s - %s" % (time, speed, rpm, distance, calories, hf, watt, lvl)

port.close()
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
# f0:b5:01:01:02:a9 - M: STOPPED

# f0:a5:01:01:04:9b - C: STOP
# f0:b5:01:01:04:ab - M: STOPPED

