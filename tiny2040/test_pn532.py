from machine import Pin, SPI
import pn532
import time

# --- CONFIGURACIÓN ---
# SCK=6, MOSI=7, MISO=4, CS=5
# baudrate=100000 (100kHz)
spi = SPI(0, baudrate=100000, polarity=0, phase=0,
          sck=Pin(6), mosi=Pin(7), miso=Pin(4))
cs_pin = Pin(5, Pin.OUT)

def main():
    print("Iniciando prueba de lectura PN532...")
    
    try:
        nfc = pn532.PN532(spi, cs_pin)
        ver = nfc.get_firmware_version()
        print(f"Firmware detectado: IC: {hex(ver[0])}, Ver: {hex(ver[1])}, Rev: {hex(ver[2])}")
        
        nfc.SAM_configuration()
        
        print("Esperando tags NFC (Ctrl+C para salir)...")
        while True:
            uid = nfc.read_passive_target(timeout=500)
            if uid:
                print("Found card with UID:", [hex(i) for i in uid])
            time.sleep_ms(100)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()