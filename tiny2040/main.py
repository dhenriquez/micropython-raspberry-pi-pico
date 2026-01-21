from machine import Pin, SPI
import neopixel
import time
import math
import json
import pn532

# --- CONFIGURACIÓN ---
PIN_NEO  = 29 
NUM_LEDS = 16
BRILLO   = 0.8 

# --- COLORES ---
C_BLANCO = (255, 255, 255)
C_VERDE  = (0, 255, 0)
C_ROJO   = (255, 0, 0)
C_AZUL   = (0, 0, 255)
C_OFF    = (0, 0, 0)
C_G_AZUL   = (66, 133, 244)
C_G_ROJO   = (234, 67, 53)
C_G_AMARILLO = (251, 188, 5)
C_G_VERDE  = (52, 168, 83)

# --- HARDWARE ---
np = neopixel.NeoPixel(Pin(PIN_NEO), NUM_LEDS)

# Configuración SPI (BAJA VELOCIDAD PARA ESTABILIDAD)
# SCK=6, MOSI=7, MISO=4, SS=5
# CAMBIO CLAVE: baudrate=100000 (100kHz) en lugar de 1000000
spi = SPI(0, baudrate=100000, polarity=0, phase=0,
          sck=Pin(6), mosi=Pin(7), miso=Pin(4))
cs_pin = Pin(5, Pin.OUT)

nfc = None
print("Iniciando PN532...")

try:
    nfc = pn532.PN532(spi, cs_pin)
    ver = nfc.get_firmware_version()
    if ver:
        nfc.SAM_configuration()
        print(f"Lector OK. Firmware: {hex(ver[0])} Rev {hex(ver[1])}")
    else:
        print("Lector responde STATUS pero no datos (revisa cables).")
except Exception as e:
    print(f"Error iniciando Lector: {str(e)}")

usuarios = []

def cargar_usuarios():
    global usuarios
    try:
        with open('users.json', 'r') as f:
            usuarios = json.load(f)
            print(f"Usuarios cargados: {len(usuarios)}")
    except:
        usuarios = []

# --- ANIMACIONES ---

def anim_idle_respiracion():
    t = time.ticks_ms() / 1000.0
    factor = (math.sin(t * 3) + 1) / 2 * 0.9 + 0.1 
    r = int(C_BLANCO[0] * BRILLO * factor)
    g = int(C_BLANCO[1] * BRILLO * factor)
    b = int(C_BLANCO[2] * BRILLO * factor)
    np.fill((r, g, b))
    np.write()

def anim_procesando_cometa():
    np.fill(C_OFF)
    pos = int((time.ticks_ms() / 40) % NUM_LEDS) 
    for i in range(5): 
        idx = (pos - i) % NUM_LEDS
        intensidad = 1.0 - (i / 5.0) 
        color = (int(200*intensidad*BRILLO), int(200*intensidad*BRILLO), int(255*intensidad*BRILLO))
        np[idx] = color
    np.write()

def parpadear_fade(color_objetivo, veces=3):
    pasos = 40
    for _ in range(veces):
        for i in range(pasos):
            progreso = i / pasos
            angulo = progreso * math.pi
            factor = math.sin(angulo)
            r = int(color_objetivo[0] * BRILLO * factor)
            g = int(color_objetivo[1] * BRILLO * factor)
            b = int(color_objetivo[2] * BRILLO * factor)
            np.fill((r, g, b))
            np.write()
            time.sleep_ms(10)
        np.fill(C_OFF)
        np.write()
        time.sleep_ms(100)

def anim_acceso_concedido():
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
    start_t = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_t) < 3000:
        current_time = time.ticks_ms()
        np.fill(C_OFF)
        pos_cabeza = int((current_time / 30) % NUM_LEDS)
        hue_base = int((current_time / 10) % 256)
        for i in range(8):
            idx = (pos_cabeza - i) % NUM_LEDS
            fade = (1.0 - (i / 8.0)) ** 2
            hue_pixel = (hue_base + (i * 10)) & 255
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
    parpadear_fade(C_ROJO, 3)

def anim_intro_google():
    colores_google = [C_G_AZUL, C_G_ROJO, C_G_AMARILLO, C_G_VERDE]
    start_t = time.ticks_ms()
    
    # Ejecutar animacion por 3 segundos
    while time.ticks_diff(time.ticks_ms(), start_t) < 3000:
        np.fill(C_OFF)
        t = time.ticks_ms()
        
        # Rotacion con velocidad variable (Efecto "Ease-In-Out")
        # Combinamos avance lineal con una onda seno para variar la velocidad
        # (t / 60) da el avance base
        # 6 * sin(t / 300) añade aceleracion y frenado ciclico
        rotacion = (t / 60) + 6 * math.sin(t / 300.0)
        offset = int(rotacion)
        
        for i in range(NUM_LEDS):
            # Dividir anillo en 4 secciones
            # Usamos RESTA en el offset para giro horario habitual en aros LED
            seccion = (i - offset) % NUM_LEDS
            idx_color = (seccion * 4) // NUM_LEDS
            
            # Asignar color correspondiente a la seccion
            c = colores_google[idx_color % 4]
            # Aplicar brillo
            color_final = (int(c[0]*BRILLO), int(c[1]*BRILLO), int(c[2]*BRILLO))
            np[i] = color_final
            
        np.write()
        time.sleep_ms(15)
    
    np.fill(C_OFF)
    np.write()

# --- PROGRAMA PRINCIPAL ---
def main():
    cargar_usuarios()
    # Animación de inicio tipo Google
    anim_intro_google()
    
    np.fill(C_OFF); np.write()
    time.sleep(0.5)
    
    print("Sistema Listo. Esperando MagicBand...")
    
    while True:
        anim_idle_respiracion()
        
        uid = None
        if nfc: 
            try:
                uid = nfc.read_passive_target(timeout=100) 
            except Exception:
                pass 

        if uid:
            inicio_proc = time.ticks_ms()
            uid_str = "0x" + "".join("{:02x}".format(x) for x in uid)
            print(f"\nDetectado: {uid_str}")
            
            while time.ticks_diff(time.ticks_ms(), inicio_proc) < 1000:
                anim_procesando_cometa()
            
            cargar_usuarios()
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
                    print(f"ACCESO CONCEDIDO: {nombre}")
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
            
            np.fill(C_OFF); np.write()
            time.sleep(1)
        
        time.sleep_ms(10)

if __name__ == '__main__':
    main()