from custom import Led, Temperature
from ssd1306 import SSD1306_I2C

import machine
import utime

led = Led(25)
alert = Led(2)
temp = Temperature(4)

WIDTH  = 128 #oled display width
HEIGHT = 32 #oled display height

sda = machine.Pin(0)
scl = machine.Pin(1)
i2c = machine.I2C(0, sda=sda, scl=scl, freq=400000)

oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)
oled.text("hola",0,0)
oled.show()
utime.sleep(2)
oled.fill(0)

while True:
    led.toggle()
    utime.sleep(0.8)
    temperatura = temp.get()
    if temperatura > 21:
        oled.poweron()
        oled.fill(0)
        alert.on()
        oled.text(str(temperatura), 0, 0)
        oled.show()
    else:
        alert.off()
        oled.fill(0)
        oled.poweroff()
    print(temperatura)
    
    