import machine, utime, time
from machine import I2C
from machine import Pin, UART, I2C
from ssd1306 import SSD1306_I2C
from neopixel_plus import NeoPixel

i2c  = I2C(1, scl=Pin(23), sda=Pin(22), freq=40000)
oled = SSD1306_I2C(72, 40, i2c)

#GPS Module UART Connection
#Pi Pic gps_module = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
gps_module = UART(1, baudrate=9600, tx=Pin(24), rx=Pin(25))

#print gps module connection details
print(gps_module)

#Used to Store NMEA Sentences
buff = bytearray(255)

TIMEOUT = False

#store the status of satellite is fixed or not
FIX_STATUS = False

#Store GPS Coordinates
latitude = ""
longitude = ""
satellites = ""
gpsTime = ""

pixel = NeoPixel(12, n=1, bpp=3)
pixel.leds[0] = (0,0,255)
pixel.write()

#function to get gps Coordinates
def getPositionData(gps_module):
    global FIX_STATUS, TIMEOUT, latitude, longitude, satellites, gpsTime
    
    #run while loop to get gps data
    #or terminate while loop after 5 seconds timeout
    timeout = time.time() + 8   # 8 seconds from now
    while True:
        gps_module.readline()
        buff = str(gps_module.readline())
        #parse $GPGGA term
        #b'$GPGGA,094840.000,2941.8543,N,07232.5745,E,1,09,0.9,102.1,M,0.0,M,,*6C\r\n'
        #b'$GNGGA,142824.00,3325.32433,S,07038.80008,W,1,04,10.60,579.8,M,30.6,M,,*7F\r\n'
        print(buff)
        parts = buff.split(',')
        
        #if no gps displayed remove "and len(parts) == 15" from below if condition
        if (parts[0] == "b'$GNGGA" and len(parts) == 15):
            if(parts[1] and parts[2] and parts[3] and parts[4] and parts[5] and parts[6] and parts[7]):
                print(buff)
                print("Message ID   : " + parts[0])
                print("UTC time     : " + parts[1])
                print("Latitude     : " + parts[2])
                print("N/S          : " + parts[3])
                print("Longitude    : " + parts[4])
                print("E/W          : " + parts[5])
                print("Position Fix : " + parts[6])
                print("# de Sat     : " + parts[7])
                print("Dilución Hori: " + parts[8])
                print("MSNM         : " + parts[9])
                print("Unidad MSNM  : " + parts[10])
                print("Alt Relativa : " + parts[11])
                print("Unidad Alt Re: " + parts[12])
                print("N/a          : " + parts[13])
                print("N/a          : " + parts[14])
                
                latitude = convertToDigree(parts[2])
                # parts[3] contain 'N' or 'S'
                if (parts[3] == 'S'):
                    latitude = -(float(latitude))
                longitude = convertToDigree(parts[4])
                # parts[5] contain 'E' or 'W'
                if (parts[5] == 'W'):
                    longitude = -(float(longitude))
                satellites = parts[7]
                hora = (int(parts[1][0:2])) - 3
                gpsTime =  str(hora) + ":" + parts[1][2:4] + ":" + parts[1][4:6]
                FIX_STATUS = True
                break
                
        if (time.time() > timeout):
            TIMEOUT = True
            break
        utime.sleep_ms(500)
        
#function to convert raw Latitude and Longitude
#to actual Latitude and Longitude
def convertToDigree(RawDegrees):

    RawAsFloat = float(RawDegrees)
    firstdigits = int(RawAsFloat/100) #degrees
    nexttwodigits = RawAsFloat - float(firstdigits*100) #minutes
    
    Converted = float(firstdigits + nexttwodigits/60.0)
    Converted = '{0:.6f}'.format(Converted) # to 6 decimal places
    return str(Converted)
    
    
while True:
    
    getPositionData(gps_module)

    #if gps data is found then print it on lcd
    if(FIX_STATUS == True):
        pixel.leds[0] = (0,255,0)
        pixel.write()
        print(latitude)
        print(longitude)
        oled.fill(0)
        oled.text("Lt:"+ str(latitude), 0, 0)
        oled.text("Lg:"+ str(longitude), 0, 10)
        oled.text("Sats:"+ str(satellites), 0, 20)
        oled.text("H:"+ str(gpsTime), 0, 30)
        oled.show()
        
            
    if(TIMEOUT == True):
        pixel.leds[0] = (255,0,0)
        pixel.write()
        print("Request Timeout: No GPS data is found.")
        oled.fill(0)
        oled.text("Sin Datos", 0, 0)
        oled.text("GPS", 0, 10)
        oled.show()
        TIMEOUT = False