from machine import Pin, Timer
from neopixel_plus import NeoPixel

pixel = NeoPixel(12, n=1, bpp=3)
pixel.leds[0] = (219,100,222)
pixel.write()

timer = Timer()

def blink(timer):
    pixel.toggle()

timer.init(freq=2.5, mode=Timer.PERIODIC, callback=blink)