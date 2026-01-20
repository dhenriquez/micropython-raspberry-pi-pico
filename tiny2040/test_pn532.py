from machine import Pin, SPI
import time

# --- CONFIGURACIÓN DE PINES (SPI) ---
# Verifica que estos sean EXACTAMENTE tus pines soldados
SCK_PIN  = 6
MOSI_PIN = 7
MISO_PIN = 4
CS_PIN   = 5

def test_spi():
    print(f"Iniciando prueba SPI en pines: SCK={SCK_PIN}, MOSI={MOSI_PIN}, MISO={MISO_PIN}, CS={CS_PIN}")
    
    spi = SPI(0, baudrate=1000000, polarity=0, phase=0,
              sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN), miso=Pin(MISO_PIN))
    cs = Pin(CS_PIN, Pin.OUT)
    cs.value(1)
    
    # Secuencia de despertar (Wakeup)
    print("Enviando señal de despertar...")
    cs.value(0)
    time.sleep_ms(2)
    spi.write(b'\x55\x55\x00\x00\x00')
    cs.value(1)
    time.sleep_ms(50)
    
    # Intentar obtener versión de firmware
    # Comando: 0x02 (GetFirmwareVersion)
    # En SPI PN532, los comandos se escriben invertidos (LSB first) y envueltos en tramas.
    # Trama cruda de GetFirmware: 
    # Preamble(00) Start(00 FF) Len(02) LCS(FE) TFI(D4) CMD(02) DCS(2A) Post(00)
    # TFI + CMD + DCS = D4 + 02 + 2A = 100 (Checksum OK)
    
    # Escribir comando 0x02
    print("Enviando comando GetFirmwareVersion...")
    write_frame(spi, cs, b'\x02')
    
    # Esperar respuesta
    print("Esperando respuesta (Status byte)...")
    if wait_ready(spi, cs):
        print("¡Chip respondió 'Listo'! Leyendo datos...")
        # Leer respuesta
        data = read_frame(spi, cs, 4)
        if data:
            print("\n------------------------------------------------")
            print(f"¡ÉXITO! Firmware detectado: IC:{hex(data[0])} Ver:{hex(data[1])} Rev:{hex(data[2])}")
            print("El hardware está bien conectado.")
            print("------------------------------------------------\n")
        else:
            print("Error: El chip dijo 'Listo' pero no envió datos válidos.")
    else:
        print("\n------------------------------------------------")
        print("FALLO: El chip NO responde.")
        print("Posibles causas:")
        print("1. FALTA ENERGÍA: Conecta VCC a 5V (VBUS), no a 3.3V.")
        print("2. SWITCHES MAL: Asegura 1=Abajo, 2=Arriba.")
        print("3. CABLES: Verifica MISO/MOSI. (A veces RX/TX están cruzados en etiquetas).")
        print("------------------------------------------------\n")

# --- FUNCIONES AUXILIARES (Bits Invertidos para PN532 SPI) ---
def reverse_bit(num):
    result = 0
    for _ in range(8):
        result = (result << 1) + (num & 1)
        num >>= 1
    return result

def write_frame(spi, cs, data):
    # 1. Armar trama
    length = len(data) + 1
    chk = (0xD4 + sum(data)) & 0xFF
    frame = bytearray([0x00, 0x00, 0xFF, length, (0x100 - length) & 0xFF, 0xD4])
    frame += data
    frame += bytearray([(0x100 - chk) & 0xFF, 0x00])
    
    # 2. Invertir bits
    rev_frame = bytearray([reverse_bit(x) for x in frame])
    
    # 3. Enviar: CS Low -> Write(0x80 inverted) -> Data -> CS High
    cs.value(0)
    time.sleep_ms(2)
    spi.write(b'\x80') # Data Write command (LSB first)
    spi.write(rev_frame)
    time.sleep_ms(1)
    cs.value(1)

def wait_ready(spi, cs, timeout=1000):
    start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start) < timeout:
        cs.value(0)
        time.sleep_ms(1)
        spi.write(b'\x40') # Status Read command (LSB first)
        val = spi.read(1)[0]
        cs.value(1)
        
        # Invertir lo leído para ver si es 0x01
        real_val = reverse_bit(val)
        if real_val == 0x01:
            return True
        time.sleep_ms(10)
    return False

def read_frame(spi, cs, length):
    cs.value(0)
    time.sleep_ms(1)
    spi.write(b'\xC0') # Data Read command
    # Leer suficiente para cabecera + datos
    raw = spi.read(length + 15)
    cs.value(1)
    
    # Invertir todo
    data = bytearray([reverse_bit(x) for x in raw])
    
    # Buscar inicio trama 0x00 0xFF
    try:
        idx = data.index(b'\xff')
        # Extraer carga útil
        return data[idx + 6 : idx + 6 + length]
    except:
        return None

if __name__ == '__main__':
    test_spi()