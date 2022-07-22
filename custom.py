import machine

class Custom(machine):  # type: ignore

    def __init__(self):
        print("Custom class initialized")
    
    def led(self, port):
        return machine.Pin(port, machine.Pin.OUT)