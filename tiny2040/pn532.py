from machine import SPI, Pin
import time

class PN532:
    def __init__(self, spi, cs, reset=None):
        self.spi = spi
        self.cs = cs
        self.cs.value(1)
        self.reset = reset
        
        if self.reset:
            self.reset.value(0)
            time.sleep_ms(400)
            self.reset.value(1)
            time.sleep_ms(100)
            
        self._wakeup()
        
        # Intentar conectar
        ver = self.get_firmware_version()
        if not ver:
            # Segundo intento agresivo
            self._wakeup()
            ver = self.get_firmware_version()
            if not ver:
                raise RuntimeError("PN532 responde a Status pero no envia datos. Revisa VCC=5V.")
            
        self.sam_configuration()

    def _reverse_bit(self, num):
        result = 0
        for _ in range(8):
            result = (result << 1) + (num & 1)
            num >>= 1
        return result

    def _write_data(self, data):
        rev_data = bytearray([self._reverse_bit(x) for x in data])
        self.spi.write(rev_data)

    def _read_data(self, count):
        data = self.spi.read(count)
        return bytearray([self._reverse_bit(x) for x in data])

    def _write_frame(self, data):
        self.cs.value(0)
        time.sleep_ms(2)
        self.spi.write(b'\x80') 
        
        length = len(data) + 1
        chk_sum = (0xD4 + sum(data)) & 0xFF
        
        frame = bytearray([0x00, 0x00, 0xFF, length, (0x100 - length) & 0xFF, 0xD4])
        frame += data
        frame += bytearray([(0x100 - chk_sum) & 0xFF, 0x00])
        
        self._write_data(frame)
        time.sleep_ms(1)
        self.cs.value(1)

    def _wait_ready(self, timeout=1000):
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < timeout:
            self.cs.value(0)
            time.sleep_ms(2) # Pausa aumentada ligeramente
            self.spi.write(b'\x40') 
            status = self._read_data(1)[0]
            self.cs.value(1)
            
            if status == 0x01:
                return True
            time.sleep_ms(5)
        return False

    def _read_frame(self, length):
        if not self._wait_ready(): return None
        
        self.cs.value(0)
        time.sleep_ms(2)
        self.spi.write(b'\xC0') 
        
        # LEER MÁS BYTES: Aumentamos el buffer (+30) para encontrar el inicio si hay ruido
        response = self._read_data(length + 30) 
        self.cs.value(1)
        
        try:
            # Buscamos el preambulo 0xFF (Start Code parte 2)
            start_idx = response.index(b'\xff')
            if len(response) < start_idx + 6: return None
            # Extraer datos validos
            return response[start_idx + 6 : start_idx + 6 + length]
        except ValueError:
            return None

    def _wakeup(self):
        self.cs.value(0)
        time.sleep_ms(2)
        self.spi.write(b'\x55\x55\x00\x00\x00')
        self.cs.value(1)
        time.sleep_ms(50)

    def call_function(self, command, response_length=0, timeout=1000):
        self._write_frame(command)
        if not self._wait_ready(timeout): return None
        return self._read_frame(response_length)

    def get_firmware_version(self):
        return self.call_function(b'\x02', 4)

    def sam_configuration(self):
        self.call_function(b'\x14\x01\x14\x01')

    def read_uid(self, timeout=100):
        resp = self.call_function(b'\x4A\x01\x00', 20, timeout)
        if resp is None or len(resp) < 6: return None
        if resp[0] != 1: return None
        uid_len = resp[5]
        if len(resp) < 6 + uid_len: return None
        return resp[6 : 6 + uid_len]