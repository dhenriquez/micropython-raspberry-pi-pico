from machine import Pin, ADC, PWM, I2C
from ssd1306 import SSD1306_I2C
import framebuf
import time

WIDTH  = 128 #oled display width
HEIGHT = 64 #oled display height

sda = Pin(0)
scl = Pin(1)
i2c = I2C(0, sda=sda, scl=scl, freq=400000)
i2c.writeto(60, "holla")
print("I2C Address      : "+hex(i2c.scan()[0]).upper())
print("I2C Configuration: "+str(i2c))

oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)
oled.text("ELECTRONOOBS",5,8)
oled.show()

if False:

    led = Pin(25, Pin.OUT)
    button = Pin(14, Pin.IN, Pin.PULL_DOWN)
    buz = Pin(15, Pin.OUT)
    pot = ADC(28)
    led = PWM(Pin(25))
    led.freq(1000)

    while True:
        led.duty_u16(pot.read_u16())

    factor = 3.3 / 65535
    while True:
        print(pot.read_u16() * factor)
        time.sleep(2)
        if button.value():
            print(button.value())
            led.toggle()
            buz.toggle()
            time.sleep(0.5)
