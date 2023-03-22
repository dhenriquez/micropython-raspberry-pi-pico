import machine

class Led(machine.Pin):  # type: ignore

    def __init__(self, port):
        self.led = machine.Pin(port, machine.Pin.OUT)
    
    def on(self):
        self.led.value(1)
    
    def off(self):
        self.led.value(0)
    
    def toggle(self):
        self.led.toggle()

class Temperature(machine.ADC):
    
    def __init__(self, port):
        self.sensor = machine.ADC(port)
        self.factor = 3.3 / (65535)
    
    def get(self):
        reading = self.sensor.read_u16() * self.factor
        return (27 - (reading - 0.706)/0.001721)