def atoi(chr):
    if(ord(chr)>=96 and ord(chr)<=102):
        return ord(chr)-87
    elif(ord(chr)>=65 and ord(chr)<=70):
        return ord(chr)-55
    elif(ord(chr)>=48 and ord(chr)<=57):
        return ord(chr)-48
    else:
        return -1

def GPS_data_check(_res):
    if(_res[0] != '$'):
        return -1

    checksum=0
    for i in range(1, len(_res)):
        if ord(_res[i]) == 0:
            continue
        if _res[i] == '*':
            break
        checksum ^= ord(_res[i])

    if(checksum == atoi(_res[len(_res)-4])*16+atoi(_res[len(_res)-3])):
        return 1
    else:
        return -1

def compass_correction(ser, heading):
    packets = bytearray()
    packets.append(0xFF)
    packets.append(0xFF)
    packets.append(0xFB)
    for chr in list(str(heading)):
        packets.append(int(chr))

    checksum = 0x00
    for byte in packets:
        checksum ^= byte
    packets.append(ord('*'))
    packets.append(checksum)
    packets.append(ord('\n'))

    ser.write(packets)
    ser.flush()

def motor(ser, L_motor_speed, R_motor_speed):
    """
    0xFF
    0xFF
    0xFD
    L_speed 하위 8비트
    L_speed 하위 16비트
    L_speed 하위 24비트
    L_speed 하위 32비트
    R_speed 하위 8비트
    R_speed 하위 16비트
    R_speed 하위 24비트
    R_speed 하위 32비트
    checksum
    """

    L_motor_speed = L_motor_speed + 1024
    R_motor_speed = R_motor_speed + 1024

    packets = bytearray()
    packets.append(0xFF)
    packets.append(0xFF)
    packets.append(0xFD)
    for chr in list(reversed(str(L_motor_speed))):
        packets.append(ord(chr))
    packets.append(ord(','))
    for chr in list(reversed(str(R_motor_speed))):
        packets.append(ord(chr))

    checksum = 0x00
    for byte in packets:
        checksum ^= byte
    packets.append(ord('*'))
    packets.append(checksum)
    packets.append(ord('\n'))
    ser.write(packets)
    ser.flush()

def IMU_data_check(_res):
    if(_res[0] != '@'):
        return -1

    checksum=0
    for i in range(1, len(_res)):
        if ord(_res[i]) == 0:
            continue
        if _res[i] == '*':
            break
        checksum ^= ord(_res[i])

    if(checksum == atoi(_res[len(_res)-4])*16+atoi(_res[len(_res)-3])):
        return 1
    else:
        return -1
