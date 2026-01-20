from machine import Pin, SPI
import time

class MFRC522:
    OK = 0
    NOTAGERR = 1
    ERR = 2
    REQIDL = 0x26
    REQALL = 0x52 # <--- Esta era la línea que faltaba

    def __init__(self, spi, sda, rst):
        self.spi = spi
        self.sda = Pin(sda, Pin.OUT)
        self.rst = Pin(rst, Pin.OUT)
        self.sda.value(1)
        self.rst.value(1)
        self.init()

    def _wreg(self, reg, val):
        self.sda.value(0)
        self.spi.write(b'%c' % int((reg << 1) & 0x7e))
        self.spi.write(b'%c' % int(val))
        self.sda.value(1)

    def _rreg(self, reg):
        self.sda.value(0)
        self.spi.write(b'%c' % int(((reg << 1) & 0x7e) | 0x80))
        val = self.spi.read(1)
        self.sda.value(1)
        return val[0]

    def _sflags(self, reg, mask):
        self._wreg(reg, self._rreg(reg) | mask)

    def _cflags(self, reg, mask):
        self._wreg(reg, self._rreg(reg) & (~mask))

    def init(self):
        self.rst.value(0)
        time.sleep_ms(10)
        self.rst.value(1)
        self._wreg(0x01, 0x0F)
        self._wreg(0x2A, 0x8D)
        self._wreg(0x2B, 0x3E)
        self._wreg(0x2D, 30)
        self._wreg(0x2C, 0)
        self._wreg(0x15, 0x40)
        self._wreg(0x11, 0x3D)
        self._wreg(0x26, 0x79)
        self._sflags(0x14, 0x03)

    def _tocard(self, cmd, send):
        recv = []
        bits = 0
        irq_en = 0
        wait_irq = 0
        stat = self.ERR
        
        if cmd == 0x0E:
            irq_en = 0x12
            wait_irq = 0x10
        elif cmd == 0x0C:
            irq_en = 0x77
            wait_irq = 0x30
            
        self._wreg(0x02, irq_en | 0x80)
        self._cflags(0x04, 0x80)
        self._sflags(0x0A, 0x80)
        self._wreg(0x01, 0x00)
        
        for c in send: 
            self._wreg(0x09, c)
        self._wreg(0x01, cmd)
        
        if cmd == 0x0C: 
            self._sflags(0x0D, 0x80)
            
        i = 2000
        while True:
            n = self._rreg(0x04)
            i -= 1
            if not ((i != 0) and not (n & 0x01) and not (n & wait_irq)):
                break
                
        self._cflags(0x0D, 0x80)
        
        if i:
            if (self._rreg(0x06) & 0x1B) == 0x00:
                stat = self.OK
                if cmd == 0x0C:
                    n = self._rreg(0x0A)
                    lbits = self._rreg(0x0C) & 0x07
                    if lbits != 0: 
                        bits = (n - 1) * 8 + lbits
                    else: 
                        bits = n * 8
                    if n == 0: n = 1
                    if n > 16: n = 16
                    for _ in range(n):
                        recv.append(self._rreg(0x09))
        return stat, recv, bits

    def _calculate_crc(self, data):
        self._cflags(0x05, 0x04)
        self._sflags(0x0A, 0x80)
        for c in data:
            self._wreg(0x09, c)
        self._wreg(0x01, 0x03)
        i = 0xFF
        while True:
            n = self._rreg(0x05)
            i -= 1
            if not ((i != 0) and not (n & 0x04)):
                break
        return [self._rreg(0x22), self._rreg(0x21)]

    def request(self, mode):
        self._wreg(0x0D, 0x07)
        (stat, recv, bits) = self._tocard(0x0C, [mode])
        if (stat != self.OK) or (bits != 0x10):
            stat = self.ERR
        return stat, bits

    def anticoll(self):
        self._wreg(0x0D, 0x00)
        (stat, recv, bits) = self._tocard(0x0C, [0x93, 0x20])
        
        if stat != self.OK:
            return self.ERR, []

        if len(recv) == 5:
            if recv[0] == 0x88:
                # MagicBand 1/2 detectada (UID 7 bytes)
                cmd = [0x93, 0x70] + recv
                crc = self._calculate_crc(cmd)
                cmd += crc
                (stat, recv_ack, _) = self._tocard(0x0C, cmd)
                if stat != self.OK:
                    return self.ERR, []
                uid_part1 = recv[1:4]
                self._wreg(0x0D, 0x00)
                (stat, recv2, bits) = self._tocard(0x0C, [0x95, 0x20])
                if stat == self.OK and len(recv2) == 5:
                    return self.OK, uid_part1 + recv2[:4]
                else:
                    return self.ERR, []
            return self.OK, recv[:4]

        return self.ERR, []