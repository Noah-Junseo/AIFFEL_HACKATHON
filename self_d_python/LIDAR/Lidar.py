import numpy as np

from serial import Serial #pip install pySerial
from time import sleep
from math import atan, pi, sin, cos
from threading import Thread

class LidarMeasure:
    def __init__(self, angle, distance):
        self.angle = angle
        self.distance = distance
    def __repr__(self):
        return ""+str(self.angle)+": "+str(self.distance)+"mm"

class LidarX2:
    def __init__(self, port):
        self.port = port
        self.baudrate = 115200
        self.connected = False
        self.measureThread = None
        self.stopThread = False
        self.measureList = []
        self.serial = None
        self.count = 0
        self.result_list = []
    def open(self):
        try:
            if not self.connected:
                # Open serial
                self.serial = Serial(self.port, self.baudrate)
                timeout = 4000  # ms
                while not self.serial.isOpen() and timeout > 0:
                    timeout -= 10  # ms
                    sleep(0.01)  # 10ms
                if self.serial.isOpen():
                    self.connected = True
                    self.serial.flushInput()
                else:
                    return False
                # Start measure thread
                self.stopThread = False
                self.measureThread = Thread(target=LidarX2.__measureThread, args=(self,))
                self.measureThread.setDaemon(True)
                self.measureThread.start()
                return True
        except Exception as e:
            print(e)
        return False
    def close(self):
        self.stopThread = True
        if self.measureThread:
            self.measureThread.join()
        if self.connected:
            self.serial.close()
            self.connected = False
    def getMeasures(self):
            return list(self.measureList)
    def __measureThread(self):
        startAngle = 0
        while not self.stopThread:
            measures = self.__readMeasures()
            if len(measures) == 0:
                continue
            # Get Start an End angles
            endAngle = measures[len(measures)-1].angle
            # Clear measures in the angle range
            i = 0
            while i < len(self.measureList):
                m = self.measureList[i]
                inRange = False
                if endAngle > startAngle:
                    inRange = startAngle <= m.angle and m.angle <= endAngle
                else:
                    inRange = (startAngle <= m.angle and m.angle <= 360) or (0 <= m.angle and m.angle <= endAngle)
                if inRange:
                    self.measureList.pop(i)
                    i -= 1
                i += 1
            # Add measures
            for m in measures:
                self.__insort_measure(self.measureList, m)
            startAngle = endAngle
    def __insort_measure(self, l, m, lo=0, hi=None):
        if lo < 0:
            raise ValueError('lo must be non-negative')
        if hi is None:
            hi = len(l)
        while lo < hi:
            mid = (lo + hi) // 2
            if m.angle < l[mid].angle:
                hi = mid
            else:
                lo = mid + 1
        l.insert(lo, m)
    def __readByte(self):
        # serial.read can return byte or str depending on python version...
        return self.__strOrByteToInt(self.serial.read(1))
    def __strOrByteToInt(self, value):
        if isinstance(value, str):
            return int(value.encode('hex'), 16)
        if isinstance(value, int):
            return value
        return int.from_bytes(value, byteorder='big')
    def __readMeasures(self):
        result_list = []
        count = 0
        while(count<8):
            result = []
            # Check and flush serial
            if not self.connected:
                return result
            # Wait for data start bytes
            found = False
            checksum = 0x55AA
            while not found and not self.stopThread:
                while self.serial.read(1) != b"\xaa":
                    pass
                if self.serial.read(1) == b"\x55":
                    found = True
            if self.stopThread:
                return []
            # Check packet type
            ct = self.__readByte()
    #        if ct != 0:
    #            return result
            # Get sample count in packet
            ls = self.__readByte()
            sampleCount = ls#int(ls.encode('hex'), 16)
            if sampleCount == 0:
                return result
            # Get start angle
            fsaL = self.__readByte()
            fsaM = self.__readByte()
            fsa = fsaL + fsaM * 256
            checksum ^= fsa
            startAngle = (fsa>>1)/64
            # Get end angle
            lsaL = self.__readByte()
            lsaM = self.__readByte()
            lsa = lsaL + lsaM * 256
            endAngle = (lsa>>1)/64
            # Compute angle diff
            aDiff = float(endAngle - startAngle)
            if (aDiff < 0):
                aDiff = aDiff + 360
            # Get checksum
            csL = self.__readByte()
            csM = self.__readByte()
            cs = csL + csM * 256
            # Read and parse data
            dataRaw = self.serial.read(sampleCount*2)
            data = []
            for i in range(0, sampleCount*2):
                data.append(self.__strOrByteToInt(dataRaw[i]))
            for i in range(0, sampleCount*2, 2):
                # Get distance
                siL = data[i]
                siM = data[i+1]
                checksum ^= (siL + siM * 256)
                distance = float(siL + siM * 256)/4
                # Get angle and correct value from distance
                angle = startAngle+(aDiff/float(sampleCount))*i/2
                angleCorrection = 0
                if distance > 0:
                    angleCorrection = (atan(21.8 * ((155.3 - distance) / (155.3 * distance))) * (180 / pi))
                angle = angle + angleCorrection
                if angle>360:
                    angle = angle-360
                # Append to result
                result.append(LidarMeasure(angle,distance))
            checksum ^= (ct + ls * 256)
            checksum ^= lsa
            # Validate checksum
            if checksum == cs:
                if(ct>>4&0x01):
                    self.count = 0
                else:
                    self.count += 1
                result_list.extend(result)
                count +=1
        count = 0
        return result_list

def sector_mask(shape,centre,radius,angle_range):
    """
    Return a boolean mask for a circular sector. The start/stop angles in  
    `angle_range` should be given in clockwise order.
    """
    x,y = np.ogrid[:shape[0],:shape[1]]
    cx,cy = centre
    tmin,tmax = np.deg2rad(angle_range)
    # ensure stop angle > start angle
    if tmax < tmin:
            tmax += 2*np.pi
    # convert cartesian --> polar coordinates
    r2 = (x-cx)*(x-cx) + (y-cy)*(y-cy)
    theta = np.arctan2(x-cx,y-cy) - tmin
    # wrap angles between 0 and 2*pi
    theta %= (2*np.pi)
    # circular mask
    circmask = r2 <= radius*radius
    # angular mask
    anglemask = theta <= (tmax-tmin)
    return circmask*anglemask

def process(value):
    if value.distance < 5000 and ((value.angle>0 and value.angle<120) or (value.angle>240 and value.angle<360)):
        y = value.distance*cos(((value.angle/180.0)*pi))
        x = value.distance*sin(((value.angle/180.0)*pi))
        return [x, y]