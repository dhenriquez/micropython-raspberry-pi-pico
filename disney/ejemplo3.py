from neopixel import Neopixel
import utime

numpix = 16
strip = Neopixel(numpix, 0, 28, "RGB")

red = (255, 255, 255)

delay = 0.01

utime.sleep(delay)  


strip.brightness(100)
blank = (0,0,0)

 

while True:
 
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