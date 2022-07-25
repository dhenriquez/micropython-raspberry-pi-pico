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