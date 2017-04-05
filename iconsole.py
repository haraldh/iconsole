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
    if len(got) > 14:
        gota = struct.unpack('BBBBBBBBBBBBBBBBBBBBB', got)
        print "%02d:%02d:%02d - RPM: % 3d - HF: % 3d - %s" % (gota[3]-1, gota[4]-1, gota[5]-1, gota[9]-1, gota[15]-1, str(gota[6:]))

port.close()

# 0 1 : 240 178
# 2 3 4 5 : d:h:m:s
# 6 7: unknown
# 8 9: RPM
# 10 11: unknown / calories?
# 12 13: unknown / distance?
# 14 15: HF
# 16 17: unknown
# 18 19: 2 2 - level?
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

