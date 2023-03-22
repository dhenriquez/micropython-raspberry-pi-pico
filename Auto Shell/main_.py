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


"""
from custom import Led, Temperature
from ssd1306 import SSD1306_I2C

import machine
import utime

led = Led(25)
# alert = Led(2)
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
        #alert.on()
        oled.text(str(temperatura), 0, 0)
        oled.show()
    else:
        #alert.off()
        oled.fill(0)
        oled.poweroff()
    print(temperatura)
"""

# Tony Goodhew 11th March 2021

import utime
from machine import Pin, PWM

#Setup RGB LED
# Construct PWM objects with RGB LED
rpwm = PWM(Pin(18)) # RED
gpwm = PWM(Pin(19)) # GREEN
bpwm = PWM(Pin(20)) # BLUE
# Set the PWM frequency.
rpwm.freq(1000)
gpwm.freq(1000)
bpwm.freq(1000)
# Turn off
rduty = 65535
gduty = 65535
bduty = 65535
rpwm.duty_u16(rduty)
gpwm.duty_u16(gduty)
bpwm.duty_u16(bduty)

def LED(r,g,b):
    rduty = int(65535 -(65535 * r/255))
    gduty = int(65535 -(65535 * g/255))
    bduty = int(65535 -(65535 * b/255))
#    print(rduty)
#    print(gduty)
#    print(bduty)
    rpwm.duty_u16(rduty)
    gpwm.duty_u16(gduty)
    bpwm.duty_u16(bduty)

LED(255,0,255)
utime.sleep(0.3)
LED(0,0,0)
utime.sleep(0.3)
# Blink
for i in range(4):
    LED(0,0,255)
    utime.sleep(0.3)
    LED(0,0,0)
    utime.sleep(0.3)
# Fade UP
for i in range(255):
    print(i)
    LED(i,i,i)
    utime.sleep(0.01)
utime.sleep(3)
# Fade DOWN
for ii in range(255,-1,-1):
    print(ii)
    LED(ii,0,ii)
    utime.sleep(0.01)

