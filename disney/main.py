from mfrc522 import MFRC522
from neopixel import Neopixel
import utime
import time

def is_in_list(value, magicBand):
 for magic_band in magicBand:
    if magic_band == value:
        return True
 return False

def standby():
    numpix = 16
    strip = Neopixel(numpix, 0, 28, "RGB")
    red = (255, 255, 255)
    delay = 0.01
    utime.sleep(delay)  
    strip.brightness(100)
    blank = (0,0,0)
    strip.show()
    for x in range(14):
        strip.set_pixel(x+1, red)
        strip.show()
        utime.sleep(delay)
        strip.set_pixel(x, red)
        strip.show()
        utime.sleep(delay)
        strip.set_pixel(x+2, red)
        strip.show()
        utime.sleep(delay)
        strip.set_pixel(x, blank)
        utime.sleep(delay)
        strip.set_pixel(x+1, blank)
        utime.sleep(delay)
        strip.set_pixel(x+2, blank)
        strip.show()

def access():
    numpix = 16
    strip = Neopixel(numpix, 0, 28, "RGB")
    red = (255, 0, 0)
    delay = 0.01
    utime.sleep(delay)  
    strip.brightness(100)
    blank = (0,0,0)
    strip.show()
    for x in range(14):
        strip.set_pixel(x+1, red)
        strip.show()
        utime.sleep(delay)
        strip.set_pixel(x, red)
        strip.show()
        utime.sleep(delay)
        strip.set_pixel(x+2, red)
        strip.show()
        utime.sleep(delay)
        strip.set_pixel(x, blank)
        utime.sleep(delay)
        strip.set_pixel(x+1, blank)
        utime.sleep(delay)
        strip.set_pixel(x+2, blank)
        strip.show()

def deny():
    numpix = 16
    strip = Neopixel(numpix, 0, 28, "RGB")
    red = (0, 255, 0)
    delay = 0.01
    utime.sleep(delay)  
    strip.brightness(100)
    blank = (0,0,0)
    strip.show()
    for x in range(14):
        strip.set_pixel(x+1, red)
        strip.show()
        utime.sleep(delay)
        strip.set_pixel(x, red)
        strip.show()
        utime.sleep(delay)
        strip.set_pixel(x+2, red)
        strip.show()
        utime.sleep(delay)
        strip.set_pixel(x, blank)
        utime.sleep(delay)
        strip.set_pixel(x+1, blank)
        utime.sleep(delay)
        strip.set_pixel(x+2, blank)
        strip.show()

def main2():
    magicBand = [36139050614483972, 4161432918]

    lector = MFRC522(spi_id=0, sck=2, miso=4, mosi=3, cs=1, rst=0)

    print("Lector activo...\n")
    
    while True:
        (stat, tag_type) = lector.request(lector.REQIDL)
        if stat == lector.OK:
            (stat, uid) = lector.SelectTagSN()
            if stat == lector.OK:
                identificador = int.from_bytes(bytes(uid), "little", False)
                print("UID: " + str(identificador))

def main():
    magicBand = [36139050614483972, 4161432918]

    lector = MFRC522(spi_id=0, sck=2, miso=4, mosi=3, cs=1, rst=0)

    print("Lector activo...\n")
    
    while True:
        #(stat, tag_type) = lector.request(lector.REQIDL)
        (stat, tag_type) = lector.request(lector.REQIDL)
        if stat == lector.OK:
            (stat, uid) = lector.SelectTagSN()
            if stat == lector.OK:
                identificador = int.from_bytes(bytes(uid), "little", False)
                print("UID: " + str(identificador))
                if is_in_list(identificador, magicBand):
                    access()
                else:
                    deny()
        else:
            standby()
            
if __name__ == "__main__":
    main()