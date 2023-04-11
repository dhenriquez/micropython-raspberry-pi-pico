from machine import Pin, I2C, PWM
import time, utime, random
from ssd1306 import SSD1306_I2C
#from neopixel import NeoPixel
from neopixel_plus import NeoPixel

# Init Display
# scl and sda can be any pin on i2c bus 1
i2c  = I2C(1, scl=Pin(23), sda=Pin(22), freq=40000)
oled = SSD1306_I2C(72, 40, i2c)
# Title Screen
oled.fill(0)

oled.text('"Daniel0"', 0, 0, 1)
oled.show()
#utime.sleep(5)

#np = NeoPixel(Pin(12), 8)
#np[0] = (255, 255, 255) # set to red, full brightness
#np.write()
#pin = Pin(12, Pin.OUT)
pixel = NeoPixel(12, n=1, bpp=3)
pixel.leds[0] = (219,100,222)
pixel.write()

pixel.rainbow_animation()