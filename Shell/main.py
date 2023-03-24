import utime
from machine import Pin

motor1a = Pin(14, Pin.OUT)
motor1b = Pin(15, Pin.OUT)

def forward():
    print("f")
    motor1a.value(1)
    motor1b.value(0)

def backward():
    print("b")
    motor1a.value(0)
    motor1b.value(1)

def stop():
    print("S")
    motor1a.value(0)
    motor1b.value(0)

def test():
   print("Iniciando test")
   utime.sleep(5)
   forward()
   utime.sleep(5)
   backward()
   utime.sleep(5)
   stop()
   utime.sleep(5)

for i in range(5):
    test()
print("fin")