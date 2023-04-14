# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

from machine import Pin, I2C
import time
from ssd1306 import SSD1306_I2C

# Init Display
# scl and sda can be any pin on i2c bus 1
i2c  = I2C(1, scl=Pin(40), sda=Pin(41), freq=40000)
oled = SSD1306_I2C(72, 40, i2c)
# Title Screen
oled.fill(0)

oled.text('"Hello World"', 0, 0, 1)
oled.show()
time.sleep(5)

import network
sta_if = network.WLAN(network.STA_IF); sta_if.active(True)
sta_if.scan()                             # Scan for available access points
sta_if.connect("CONY", "constancita") # Connect to an AP
sta_if.isconnected()                      # Check for successful connection
print(sta_if.config('channel'))
print(sta_if.config('ssid'))
oled.fill(0)
oled.text(sta_if.config('ssid'), 0, 0, 1)
oled.show()