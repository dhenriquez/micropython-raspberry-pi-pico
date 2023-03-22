# Display Image & text on I2C driven ssd1306 OLED display 
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import framebuf
import utime

WIDTH  = 128                                            # oled display width
HEIGHT = 32                                            # oled display height

i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=200000)       # Init I2C using pins GP8 & GP9 (default I2C0 pins)
print("I2C Address      : "+hex(i2c.scan()[0]).upper()) # Display device address
print("I2C Configuration: "+str(i2c))                   # Display I2C config


oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)                  # Init oled display
led = Pin(25, Pin.IN)
led.off()
# Raspberry Pi logo as 32x32 bytearray
while True:
    # Clear the oled display in case it has junk on it.
    oled.fill(0)

    # Add some text
    oled.text("Dhenriquez",0,0)
    oled.text("2022",0,10)

    # Finally update the oled display so the image & text is displayed
    oled.show()
    utime.sleep(5)
    break
oled.poweroff()