from machine import Pin, SPI
import neopixel
import time
import math
import json
import mfrc522

# --- CONFIGURACIÓN ---
PIN_NEO  = 29 
NUM_LEDS = 16
BRILLO   = 0.8 # Brillo máximo global

# --- COLORES ---
C_BLANCO = (255, 255, 255)
C_VERDE  = (0, 255, 0)
C_ROJO   = (255, 0, 0)
C_AZUL   = (0, 0, 255)
C_OFF    = (0, 0, 0)

# --- HARDWARE ---
np = neopixel.NeoPixel(Pin(PIN_NEO), NUM_LEDS)
spi = SPI(0, baudrate=1000000, polarity=0, phase=0,
          sck=Pin(6), mosi=Pin(7), miso=Pin(4))

try:
    lector = mfrc522.MFRC522(spi, sda=5, rst=0)
    print("Lector OK")
except:
    print("Error Lector")

usuarios = []

def cargar_usuarios():
    global usuarios
    try:
        with open('users.json', 'r') as f:
            usuarios = json.load(f)
            print(f"Usuarios cargados: {len(usuarios)}")
    except:
        usuarios = []
        print("Error cargando users.json")

# --- ANIMACIONES ---

def anim_idle_respiracion():
    # Luz blanca suave (Standby)
    t = time.ticks_ms() / 1000.0
    factor = (math.sin(t * 3) + 1) / 2 * 0.9 + 0.1 
    r = int(C_BLANCO[0] * BRILLO * factor)
    g = int(C_BLANCO[1] * BRILLO * factor)
    b = int(C_BLANCO[2] * BRILLO * factor)
    np.fill((r, g, b))
    np.write()

def anim_procesando_cometa():
    # Cometa blanco girando (Procesando)
    np.fill(C_OFF)
    pos = int((time.ticks_ms() / 40) % NUM_LEDS) 
    for i in range(5): 
        idx = (pos - i) % NUM_LEDS
        intensidad = 1.0 - (i / 5.0) 
        color = (int(200*intensidad*BRILLO), int(200*intensidad*BRILLO), int(255*intensidad*BRILLO))
        np[idx] = color
    np.write()

def parpadear_fade(color_objetivo, veces=3):
    # Parpadeo suave tipo "respiración" (Fade In/Out)
    pasos_por_parpadeo = 50 # Suavidad de la transición
    
    for _ in range(veces):
        # Ciclo de subida y bajada (usamos media onda senoidal: 0 a Pi)
        for i in range(pasos_por_parpadeo):
            # Progreso de 0.0 a 1.0
            progreso = i / pasos_por_parpadeo
            # Ángulo de 0 a Pi (3.14159...)
            angulo = progreso * math.pi
            # Factor va de 0 -> 1 -> 0 suavemente
            factor = math.sin(angulo)
            
            # Aplicamos el factor y el brillo global al color objetivo
            r = int(color_objetivo[0] * BRILLO * factor)
            g = int(color_objetivo[1] * BRILLO * factor)
            b = int(color_objetivo[2] * BRILLO * factor)
            
            np.fill((r, g, b))
            np.write()
            time.sleep_ms(10) # Velocidad del fade
            
        # Asegurar apagado breve entre parpadeos
        np.fill(C_OFF)
        np.write()
        time.sleep_ms(100)

def anim_acceso_concedido():
    # NORMAL: Giro verde + 3 Fades Verdes
    for _ in range(NUM_LEDS * 2): 
        np.fill(C_OFF)
        pos = int((time.ticks_ms() / 20) % NUM_LEDS)
        for i in range(4):
            idx = (pos - i) % NUM_LEDS
            intensidad = 1.0 - (i / 4.0)
            np[idx] = (0, int(255*intensidad*BRILLO), 0)
        np.write()
        time.sleep_ms(15)
    
    parpadear_fade(C_VERDE, 3)

def anim_acceso_vip():
    # VIP: Cometa Arcoíris + 3 Fades Verdes
    start_t = time.ticks_ms()
    velocidad_giro = 30
    longitud_cola = 8
    
    while time.ticks_diff(time.ticks_ms(), start_t) < 3000:
        current_time = time.ticks_ms()
        np.fill(C_OFF)
        pos_cabeza = int((current_time / velocidad_giro) % NUM_LEDS)
        hue_base = int((current_time / 10) % 256)
        
        for i in range(longitud_cola):
            idx = (pos_cabeza - i) % NUM_LEDS
            fade = 1.0 - (i / float(longitud_cola))
            fade = fade * fade
            hue_pixel = (hue_base + (i * 5)) & 255
            
            r, g, b = 0, 0, 0
            if hue_pixel < 85:
                r, g, b = hue_pixel * 3, 255 - hue_pixel * 3, 0
            elif hue_pixel < 170:
                hue_pixel -= 85
                r, g, b = 255 - hue_pixel * 3, 0, hue_pixel * 3
            else:
                hue_pixel -= 170
                r, g, b = 0, hue_pixel * 3, 255 - hue_pixel * 3
            
            np[idx] = (int(r*BRILLO*fade), int(g*BRILLO*fade), int(b*BRILLO*fade))
        np.write()
        time.sleep_ms(10)
    
    parpadear_fade(C_VERDE, 3)

def anim_acceso_denegado():
    # DENEGADO: 3 Fades Rojos
    parpadear_fade(C_ROJO, 3)

# --- PROGRAMA PRINCIPAL ---
def main():
    cargar_usuarios()
    print("Listo. Esperando MagicBand...")
    
    np.fill(C_OFF)
    np.write()
    time.sleep(0.5)
    
    while True:
        # Estado 1: IDLE
        anim_idle_respiracion()
        
        # Estado 2: LECTURA
        (stat, tag_type) = lector.request(lector.REQALL)
        if stat == lector.OK:
            (stat, uid) = lector.anticoll()
            if stat == lector.OK:
                inicio_proc = time.ticks_ms()
                uid_str = "0x" + "".join("{:02x}".format(x) for x in uid)
                print(f"\nDetectado: {uid_str}")
                
                # Estado 3: PROCESANDO (Giro blanco mínimo 1 seg)
                while time.ticks_diff(time.ticks_ms(), inicio_proc) < 1000:
                    anim_procesando_cometa()
                
                # Búsqueda y Decisión
                usuario_encontrado = None
                for u in usuarios:
                    if u['uid'].lower() == uid_str.lower():
                        usuario_encontrado = u
                        break
                
                if usuario_encontrado:
                    nombre = usuario_encontrado.get('user', 'Usuario')
                    status = usuario_encontrado.get('status', 'denegado')
                    tipo   = usuario_encontrado.get('usertype', 'normal')

                    if status == 'habilitado':
                        print(f"ACCESO CONCEDIDO: {nombre} ({tipo})")
                        if tipo == 'vip':
                            anim_acceso_vip()
                        else:
                            anim_acceso_concedido()
                    else:
                        print(f"ACCESO DENEGADO (Status): {nombre}")
                        anim_acceso_denegado()
                else:
                    print("ACCESO DENEGADO (Desconocido)")
                    anim_acceso_denegado()
                
                # Limpieza final
                np.fill(C_OFF)
                np.write()
                time.sleep(1)
        
        time.sleep_ms(10)

if __name__ == '__main__':
    main()