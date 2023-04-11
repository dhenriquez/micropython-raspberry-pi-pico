import utime
from machine import Pin, PWM, UART

motorDa = Pin(27, Pin.OUT)
motorDb = Pin(26, Pin.OUT)

motorAa = Pin(29, Pin.OUT)
motorAb = Pin(28, Pin.OUT)

pwma = PWM(Pin(0))
pwma.freq(1000)

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

uart = UART(1, 9600)

velocidad = 1

def LED(r,g,b):
    rduty = int(65535 -(65535 * r/255))
    gduty = int(65535 -(65535 * g/255))
    bduty = int(65535 -(65535 * b/255))
    rpwm.duty_u16(rduty)
    gpwm.duty_u16(gduty)
    bpwm.duty_u16(bduty)

def derecha():
   motorDa.high()
   motorDb.low()
   
def izquierda():
   motorDa.low()
   motorDb.high()

def avanzar(speed=0):
   if speed == 0:
       speed = 0
   if speed == 1:
       speed = 100
   if speed == 2:
       speed = 180
   if speed == 3:
       speed = 200
   if speed == 4:
       speed = 255
   motorAa.high()
   motorAb.low()
   pwma.duty_u16(int(speed/100*65536))

def retroceder(speed=50):
   motorAa.low()
   motorAb.high()
   pwma.duty_u16(int(speed/100*65536))
   
def stop():
   motorDa.low()
   motorDb.low()
   
   motorAa.low()
   motorAb.low()

while True:
    if uart.any():
        command = uart.read()
        #if 'u' in command:
        #    velocidad = velocidad + 1
        #    if velocidad > 4:
        #        velocidad = 4
        #    avanzar(velocidad)
        #if 'd' in command:
        #    velocidad = velocidad - 1
        #    if velocidad < 0:
        #        velocidad = 0
        #    avanzar(velocidad)
        if 'avanzar' in command:
            uart.write('Avanzando \n')
            LED(255,255,255)
            avanzar(velocidad)
        if 'detener' in command:
            uart.write('Detenido \n')
            LED(255,0,0)
            stop()
        if 'retroceder' in command:
            uart.write('Retrocediendo \n')
            LED(255,255,255)
            retroceder()
        if 'derecha' in command:
            uart.write('Derecha \n')
            derecha()
        if 'izquierda' in command:
            uart.write('Izquierda \n')
            izquierda()