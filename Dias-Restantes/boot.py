import network
import socket
import time
import ntptime
import random
import ujson
import os
from machine import Pin, I2C, reset
import esp32
from esp32 import NVS
from ssd1306 import SSD1306_I2C

try:
    import mdns
    MDNS_AVAILABLE = True
except ImportError:
    MDNS_AVAILABLE = False
    print("mDNS no disponible en esta versión de MicroPython")

HOSTNAME = "config"  # Se accederá como config.local

# Configuración del Access Point
AP_SSID = "ESP32-Configurador"
AP_PASSWORD = "12345678"

# Variables globales
oled = None
wifi_configurado = False
fecha_configurada = False
ssid_guardado = ""
password_guardado = ""
fecha_objetivo = ""
fecha_destino = None

# Variables globales para el scroll
scroll_offset = 0
scroll_timer = 0
scroll_texts = []
SCROLL_SPEED = 500  # milisegundos entre cada desplazamiento
MAX_CHAR_PER_LINE = 9  # máximo caracteres por línea

# ===== VARIABLES GLOBALES DE PANTALLA =====
SCREEN_WIDTH = 72
SCREEN_HEIGHT = 40
MAX_LINES = SCREEN_HEIGHT // 8  # Número máximo de líneas de texto (cada línea ocupa 8 píxeles)
MAX_CHAR_PER_LINE = SCREEN_WIDTH // 8  # Máximo caracteres por línea (cada carácter ocupa ~8 píxeles)


# Variables globales adicionales
modo_display = "normal"  # "normal", "numeros_grandes", o "solo_numero"

def dibujar_mickey_mouse():
    """
    Dibujar logo de Mickey Mouse en OLED 72x40
    Cabeza grande en el centro y dos orejas más pequeñas
    """
    if not oled:
        return
    
    # Limpiar pantalla
    oled.fill(0)
    
    # Coordenadas para las tres círculos de Mickey
    # Oreja izquierda: centro en (20, 12), radio 8
    # Cabeza principal: centro en (36, 20), radio 12  
    # Oreja derecha: centro en (52, 12), radio 8
    
    # Función auxiliar para dibujar círculo relleno
    def dibujar_circulo_relleno(cx, cy, radio):
        for y in range(max(0, cy - radio), min(40, cy + radio + 1)):
            for x in range(max(0, cx - radio), min(72, cx + radio + 1)):
                # Calcular distancia al centro
                dx = x - cx
                dy = y - cy
                if dx*dx + dy*dy <= radio*radio:
                    oled.pixel(x, y, 1)
    
    # Dibujar oreja izquierda
    dibujar_circulo_relleno(22, 12, 6)
    
    # Dibujar oreja derecha  
    dibujar_circulo_relleno(50, 12, 6)
    
    # Dibujar cabeza principal (más grande)
    dibujar_circulo_relleno(36, 23, 12)
    
    """ Opcional: Agregar ojos y sonrisa
    # Ojo izquierdo
    oled.pixel(32, 16, 0)  # pixel negro (borrar)
    oled.pixel(31, 16, 0)
    oled.pixel(32, 17, 0)
    oled.pixel(31, 17, 0)
    
    # Ojo derecho
    oled.pixel(40, 16, 0)
    oled.pixel(41, 16, 0)
    oled.pixel(40, 17, 0)
    oled.pixel(41, 17, 0)
    
    # Sonrisa simple (línea curva)
    oled.pixel(33, 22, 0)
    oled.pixel(34, 23, 0)
    oled.pixel(35, 24, 0)
    oled.pixel(36, 24, 0)
    oled.pixel(37, 24, 0)
    oled.pixel(38, 23, 0)
    oled.pixel(39, 22, 0)"""
    
    oled.show()

def animacion_fuegos_artificiales():
    """
    Mostrar animación de fuegos artificiales después del logo de Mickey Mouse
    Optimizado para cualquier tamaño de pantalla OLED
    """
    if not oled:
        return
    
    # Configuración de la animación
    duracion_total = 10000  # 10 segundos
    tiempo_inicio = time.ticks_ms()
    
    # Lista para almacenar las explosiones activas
    explosiones = []
    
    # Clase para manejar cada explosión
    class Explosion:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.radio = 0
            self.max_radio = random.randint(min(SCREEN_WIDTH, SCREEN_HEIGHT)//8, min(SCREEN_WIDTH, SCREEN_HEIGHT)//4)
            self.particulas = []
            self.tiempo_vida = 0
            self.max_vida = random.randint(800, 1200)  # milisegundos
            
            # Crear partículas iniciales
            num_particulas = random.randint(8, 12)
            for _ in range(num_particulas):
                angulo = random.uniform(0, 6.28)  # 0 a 2π
                velocidad = random.uniform(0.5, 2.0)
                self.particulas.append({
                    'x': float(x),
                    'y': float(y),
                    'vx': velocidad * math.cos(angulo),
                    'vy': velocidad * math.sin(angulo),
                    'vida': random.randint(600, 1000)
                })
        
        def actualizar(self, dt):
            self.tiempo_vida += dt
            
            # Expandir el círculo principal
            if self.radio < self.max_radio:
                self.radio += 0.3
            
            # Actualizar partículas
            for particula in self.particulas[:]:  # Copia para poder modificar durante iteración
                particula['x'] += particula['vx']
                particula['y'] += particula['vy']
                particula['vida'] -= dt
                
                # Aplicar algo de gravedad
                particula['vy'] += 0.02
                
                # Eliminar partículas muertas
                if particula['vida'] <= 0:
                    self.particulas.remove(particula)
        
        def dibujar(self):
            # Dibujar círculo principal (si aún está creciendo)
            if self.radio < self.max_radio:
                self.dibujar_circulo(int(self.x), int(self.y), int(self.radio))
            
            # Dibujar partículas
            for particula in self.particulas:
                px = int(particula['x'])
                py = int(particula['y'])
                if 0 <= px < SCREEN_WIDTH and 0 <= py < SCREEN_HEIGHT:
                    oled.pixel(px, py, 1)
        
        def dibujar_circulo(self, cx, cy, radio):
            """Dibujar círculo usando algoritmo de Bresenham"""
            if radio <= 0:
                return
                
            x = 0
            y = radio
            d = 3 - 2 * radio
            
            while y >= x:
                self.dibujar_puntos_circulo(cx, cy, x, y)
                x += 1
                if d > 0:
                    y -= 1
                    d = d + 4 * (x - y) + 10
                else:
                    d = d + 4 * x + 6
        
        def dibujar_puntos_circulo(self, cx, cy, x, y):
            """Dibujar los 8 puntos simétricos del círculo"""
            puntos = [
                (cx + x, cy + y), (cx - x, cy + y),
                (cx + x, cy - y), (cx - x, cy - y),
                (cx + y, cy + x), (cx - y, cy + x),
                (cx + y, cy - x), (cx - y, cy - x)
            ]
            
            for px, py in puntos:
                if 0 <= px < SCREEN_WIDTH and 0 <= py < SCREEN_HEIGHT:
                    oled.pixel(px, py, 1)
        
        def esta_viva(self):
            return self.tiempo_vida < self.max_vida and (self.radio < self.max_radio or len(self.particulas) > 0)
    
    # Importar math para las funciones trigonométricas
    import math
    
    # Contador para crear nuevas explosiones
    ultimo_fuego = 0
    intervalo_fuegos = random.randint(300, 600)  # Milisegundos entre fuegos
    
    print("Iniciando animación de fuegos artificiales...")
    
    while time.ticks_diff(time.ticks_ms(), tiempo_inicio) < duracion_total:
        tiempo_actual = time.ticks_ms()
        dt = 50  # Delta time fijo para consistencia
        
        # Crear nueva explosión ocasionalmente
        if tiempo_actual - ultimo_fuego > intervalo_fuegos:
            x = random.randint(SCREEN_WIDTH//5, SCREEN_WIDTH*4//5)  # Evitar bordes
            y = random.randint(SCREEN_HEIGHT//4, SCREEN_HEIGHT*3//4)  # Evitar bordes
            explosiones.append(Explosion(x, y))
            ultimo_fuego = tiempo_actual
            intervalo_fuegos = random.randint(200, 500)  # Nuevo intervalo aleatorio
        
        # Limpiar pantalla
        oled.fill(0)
        
        # Actualizar y dibujar todas las explosiones
        for explosion in explosiones[:]:  # Copia para poder modificar durante iteración
            explosion.actualizar(dt)
            explosion.dibujar()
            
            # Eliminar explosiones muertas
            if not explosion.esta_viva():
                explosiones.remove(explosion)
        
        # Agregar algunas estrellas de fondo ocasionalmente
        if random.randint(1, 10) > 7:  # 30% de probabilidad
            for _ in range(random.randint(1, 3)):
                sx = random.randint(0, SCREEN_WIDTH-1)
                sy = random.randint(0, SCREEN_HEIGHT-1)
                oled.pixel(sx, sy, 1)
        
        oled.show()
        time.sleep_ms(dt)
    
    print("Animación de fuegos artificiales completada")

def init_lcd():
    """Inicializar OLED I2C con dimensiones configurables"""
    global oled
    try:
        i2c = I2C(1, scl=Pin(40), sda=Pin(41), freq=40000)
        oled = SSD1306_I2C(SCREEN_WIDTH, SCREEN_HEIGHT, i2c)

        dibujar_mickey_mouse()
        time.sleep(5)
        
        return True
    except Exception as e:
        print("Error LCD: {}".format(e))
        return False

def mostrar_en_oled(lineas, limpiar=True, auto_scroll=True):
    """
    Mostrar texto en OLED con scroll horizontal automático
    Ajustado para dimensiones configurables
    """
    global scroll_texts, scroll_offset, scroll_timer
    
    if not oled:
        return
    
    # NO procesar si estamos en modos especiales
    if modo_display in ["numeros_grandes", "solo_numero"]:
        return
    
    try:
        if limpiar:
            oled.fill(0)
        
        # Guardar textos para scroll si es necesario
        if auto_scroll:
            scroll_texts = []
            for i, linea in enumerate(lineas):
                if i < MAX_LINES:  # máximo líneas según altura de pantalla
                    scroll_texts.append(str(linea))
        
        # Mostrar cada línea
        for i, linea in enumerate(lineas):
            if i < MAX_LINES:  # máximo líneas según altura de pantalla
                texto = str(linea)
                
                # Si el texto es largo y auto_scroll está activado
                if len(texto) > MAX_CHAR_PER_LINE and auto_scroll:
                    # Aplicar scroll horizontal
                    texto_scroll = aplicar_scroll_horizontal(texto, i)
                    oled.text(texto_scroll, 0, i * 8, 1)
                else:
                    # Truncar texto si es muy largo y no hay scroll
                    texto_truncado = texto[:MAX_CHAR_PER_LINE]
                    oled.text(texto_truncado, 0, i * 8, 1)
        
        oled.show()
        
    except Exception as e:
        print("Error mostrando en OLED: {}".format(e))

def aplicar_scroll_horizontal(texto, linea_index):
    """
    Aplicar scroll horizontal a un texto largo
    
    Args:
        texto: String original
        linea_index: Índice de la línea (0-4)
    
    Returns:
        String con la porción visible del texto
    """
    global scroll_offset
    
    if len(texto) <= MAX_CHAR_PER_LINE:
        return texto
    
    # Calcular posición de scroll
    # Cada línea puede tener diferente offset si es necesario
    texto_extendido = texto + "   "  # Agregar espacios al final
    texto_len = len(texto_extendido)
    
    # Obtener la subsección visible
    start_pos = scroll_offset % texto_len
    end_pos = start_pos + MAX_CHAR_PER_LINE
    
    if end_pos <= texto_len:
        return texto_extendido[start_pos:end_pos]
    else:
        # Wrap around cuando llegamos al final
        parte1 = texto_extendido[start_pos:]
        parte2 = texto_extendido[:end_pos - texto_len]
        return parte1 + parte2

def actualizar_scroll():
    """
    Actualizar el scroll horizontal (llamar en el loop principal)
    """
    global scroll_offset, scroll_timer

    # NO hacer scroll si estamos en modo números grandes o solo número
    if modo_display in ["numeros_grandes", "solo_numero"]:
        return
    
    current_time = time.ticks_ms()
    
    # Solo hacer scroll si hay textos largos
    tiene_textos_largos = False
    for texto in scroll_texts:
        if len(texto) > MAX_CHAR_PER_LINE:
            tiene_textos_largos = True
            break
    
    if tiene_textos_largos and time.ticks_diff(current_time, scroll_timer) >= SCROLL_SPEED:
        scroll_offset += 1
        scroll_timer = current_time
        
        # Redibujar pantalla con nuevo offset
        mostrar_en_oled(scroll_texts, True, True)

def cargar_configuracion_json():
    """Cargar configuración desde archivo JSON"""
    global ssid_guardado, password_guardado, fecha_objetivo, modo_display
    
    try:
        # Verificar si existe el archivo
        if "config.json" in os.listdir():
            with open("config.json", "r") as f:
                config = ujson.load(f)
                
            ssid_guardado = config.get("ssid", "")
            password_guardado = config.get("password", "")
            fecha_objetivo = config.get("fecha", "")
            modo_display = config.get("modo_display", "normal")
            
            print("Configuración cargada desde JSON")
        else:
            print("Archivo config.json no existe, usando valores por defecto")
            ssid_guardado = ""
            password_guardado = ""
            fecha_objetivo = ""
            modo_display = "normal"
            
    except Exception as e:
        print("Error cargando configuración JSON: {}".format(e))
        ssid_guardado = ""
        password_guardado = ""
        fecha_objetivo = ""
        modo_display = "normal"

def guardar_configuracion_json():
    """Guardar toda la configuración en archivo JSON"""
    try:
        config = {
            "ssid": ssid_guardado,
            "password": password_guardado,
            "fecha": fecha_objetivo,
            "modo_display": modo_display
        }
        
        with open("config.json", "w") as f:
            ujson.dump(config, f)
        
        print("Configuración guardada en JSON")
        return True
        
    except Exception as e:
        print("Error guardando configuración JSON: {}".format(e))
        return False

def guardar_wifi_json(ssid, password):
    """Guardar credenciales WiFi en JSON"""
    global ssid_guardado, password_guardado
    ssid_guardado = ssid
    password_guardado = password
    return guardar_configuracion_json()

def guardar_fecha_json(fecha):
    """Guardar fecha objetivo en JSON"""
    global fecha_objetivo
    fecha_objetivo = fecha
    return guardar_configuracion_json()

def limpiar_configuracion_json():
    """Limpiar configuración JSON"""
    try:
        if "config.json" in os.listdir():
            os.remove("config.json")
        
        global ssid_guardado, password_guardado, fecha_objetivo, modo_display
        ssid_guardado = ""
        password_guardado = ""
        fecha_objetivo = ""
        modo_display = "normal"
        
        print("Configuración JSON limpiada")
        return True
        
    except Exception as e:
        print("Error limpiando configuración JSON: {}".format(e))
        return False

def conectar_wifi(ssid, password):
    """Conectar a WiFi"""
    global wifi_configurado
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    
    # Esperar conexión
    intentos = 0
    mostrar_en_oled(['Conectando a', '{}...'.format(ssid[:12])])
    print("Conectando a {}...".format(ssid), end="")
    while not wlan.isconnected() and intentos < 20:
        time.sleep(0.5)
        intentos += 1
        print(".", end="")
    
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print("\nWiFi conectado. IP: {}".format(ip))
        mostrar_en_oled(['WiFi Conectado!', 'IP: {}'.format(ip)])
        wifi_configurado = True

        # AGREGAR CONFIGURACIÓN mDNS AQUÍ
        if MDNS_AVAILABLE:
            try:
                # Configurar mDNS
                mdns.start(HOSTNAME, "MicroPython with mDNS")
                mdns.add_service('_http', '_tcp', 80, HOSTNAME)
                print("mDNS configurado: {}.local".format(HOSTNAME))
                mostrar_en_oled(['WiFi Conectado!', 'IP: {}'.format(ip), '{}.local'.format(HOSTNAME)])
                time.sleep(3)  # Mostrar más tiempo para ver la URL
            except Exception as e:
                print("Error configurando mDNS: {}".format(e))
                mostrar_en_oled(['WiFi Conectado!', 'IP: {}'.format(ip), 'mDNS Error'])
                time.sleep(2)
        else:
            mostrar_en_oled(['WiFi Conectado!', 'IP: {}'.format(ip), 'Solo IP disponible'])
            time.sleep(2)
        
        # Sincronizar tiempo
        try:
            print("Sincronizando tiempo con servidor NTP...")
            ntptime.host = "pool.ntp.org"
            ntptime.settime()
            print("Tiempo sincronizado.")
            mostrar_en_oled(['WiFi Conectado!', 'Tiempo OK'])
        except Exception as e:
            print("Error sincronizando tiempo: {}".format(e))
            mostrar_en_oled(['WiFi Conectado!', 'Error NTP'])
        time.sleep(2)
        return True
    else:
        print("\nFallo la conexion WiFi.")
        mostrar_en_oled(['Error WiFi', 'Conexion fallida'])
        wlan.active(False)
        time.sleep(2)
        return False

def crear_access_point():
    """Crear Access Point"""
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=AP_SSID, password=AP_PASSWORD, authmode=network.AUTH_WPA_WPA2_PSK)
    
    ip = ap.ifconfig()[0]
    print("Access Point '{}' creado. IP: {}".format(AP_SSID, ip))
    mostrar_en_oled(['Modo Config', 'Red: {}'.format(AP_SSID[:12]), 'IP: {}'.format(ip), 'Conectate'])

def escanear_redes():
    """Escanear redes WiFi disponibles"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    redes = wlan.scan()
    
    redes_lista = []
    for red in redes:
        ssid = red[0].decode('utf-8')
        rssi = red[3]
        redes_lista.append((ssid, rssi))
    
    return redes_lista

def parsear_fecha(fecha_str):
    """Parsear fecha en formato YYYY-MM-DD"""
    try:
        partes = fecha_str.split('-')
        year = int(partes[0])
        month = int(partes[1])
        day = int(partes[2])
        
        if year < 2024 or month < 1 or month > 12 or day < 1 or day > 31:
            return None
            
        return (year, month, day, 0, 0, 0, 0, 0)
    except:
        return None

def configurar_fecha_destino(fecha_str):
    """Configurar fecha destino"""
    global fecha_configurada, fecha_destino, fecha_objetivo
    
    fecha_destino = parsear_fecha(fecha_str)
    if fecha_destino:
        fecha_configurada = True
        fecha_objetivo = fecha_str  # ← AGREGAR ESTA LÍNEA para mantener sincronizado
        return True
    return False

def calcular_dias_restantes():
    """Calcular días restantes hasta la fecha objetivo (días completos)"""
    if not fecha_configurada or not fecha_destino:
        return None
    
    try:
        # Tiempo actual
        tiempo_actual = time.localtime()
        
        # Crear fecha actual solo con año, mes, día (sin hora)
        fecha_actual_simple = (tiempo_actual[0], tiempo_actual[1], tiempo_actual[2], 0, 0, 0, 0, 0)
        
        # Convertir a timestamp (ambas fechas a medianoche)
        ts_actual = time.mktime(fecha_actual_simple)
        ts_destino = time.mktime(fecha_destino)
        
        # Diferencia en días completos
        diferencia = int((ts_destino - ts_actual) / 86400)
        
        return diferencia
    except Exception as e:
        print("Error calculando días: {}".format(e))
        return None

def guardar_modo_display_json(modo):
    """Guardar modo de visualización en JSON"""
    global modo_display
    modo_display = modo
    return guardar_configuracion_json()

def dibujar_numero_grande(numero, x, y):
    """
    Dibujar un número grande en el OLED usando patrones de puntos
    Ajustado para dimensiones configurables de pantalla
    """
    if not oled:
        return
    
    # Calcular tamaño de dígito basado en pantalla (máximo 8x12 por defecto)
    digit_width = min(8, SCREEN_WIDTH // 4)  # Máximo 4 dígitos por pantalla
    digit_height = min(12, SCREEN_HEIGHT - 4)  # Dejar margen arriba y abajo
    
    # Patrones para números grandes (escalables)
    patrones = {
        '0': [
            0b01111110,
            0b11000011,
            0b11000011,
            0b11000011,
            0b11000011,
            0b11000011,
            0b11000011,
            0b11000011,
            0b11000011,
            0b11000011,
            0b11000011,
            0b01111110
        ],
        '1': [
            0b00011000,
            0b00111000,
            0b01111000,
            0b00011000,
            0b00011000,
            0b00011000,
            0b00011000,
            0b00011000,
            0b00011000,
            0b00011000,
            0b00011000,
            0b01111110
        ],
        '2': [
            0b01111110,
            0b11000011,
            0b00000011,
            0b00000011,
            0b00000110,
            0b00001100,
            0b00011000,
            0b00110000,
            0b01100000,
            0b11000000,
            0b11000000,
            0b11111111
        ],
        '3': [
            0b01111110,
            0b11000011,
            0b00000011,
            0b00000011,
            0b00111110,
            0b00111110,
            0b00000011,
            0b00000011,
            0b00000011,
            0b11000011,
            0b11000011,
            0b01111110
        ],
        '4': [
            0b11000011,
            0b11000011,
            0b11000011,
            0b11000011,
            0b11000011,
            0b11111111,
            0b01111111,
            0b00000011,
            0b00000011,
            0b00000011,
            0b00000011,
            0b00000011
        ],
        '5': [
            0b11111111,
            0b11000000,
            0b11000000,
            0b11000000,
            0b11111110,
            0b01111111,
            0b00000011,
            0b00000011,
            0b00000011,
            0b11000011,
            0b11000011,
            0b01111110
        ],
        '6': [
            0b01111110,
            0b11000011,
            0b11000000,
            0b11000000,
            0b11111110,
            0b11111111,
            0b11000011,
            0b11000011,
            0b11000011,
            0b11000011,
            0b11000011,
            0b01111110
        ],
        '7': [
            0b11111111,
            0b00000011,
            0b00000110,
            0b00000110,
            0b00001100,
            0b00001100,
            0b00011000,
            0b00011000,
            0b00110000,
            0b00110000,
            0b01100000,
            0b01100000
        ],
        '8': [
            0b01111110,
            0b11000011,
            0b11000011,
            0b11000011,
            0b01111110,
            0b01111110,
            0b11000011,
            0b11000011,
            0b11000011,
            0b11000011,
            0b11000011,
            0b01111110
        ],
        '9': [
            0b01111110,
            0b11000011,
            0b11000011,
            0b11000011,
            0b11000011,
            0b11000011,
            0b01111111,
            0b01111110,
            0b00000011,
            0b00000011,
            0b11000011,
            0b01111110
        ]
    }
    
    numero_str = str(numero)
    
    # Calcular posición centrada para el número basada en dimensiones de pantalla
    total_width = len(numero_str) * (digit_width + 1)  # digit_width + 1 píxel de separación
    start_x = max(0, (SCREEN_WIDTH - total_width) // 2)
    
    for i, digito in enumerate(numero_str):
        if digito in patrones:
            patron = patrones[digito]
            digit_x = start_x + i * (digit_width + 1)
            
            for row in range(min(digit_height, len(patron))):
                if y + row < SCREEN_HEIGHT:  # Verificar límites del OLED
                    byte_pattern = patron[row]
                    for bit in range(digit_width):
                        if byte_pattern & (0b10000000 >> bit):
                            if digit_x + bit < SCREEN_WIDTH:  # Verificar límites del OLED
                                oled.pixel(digit_x + bit, y + row, 1)

def dibujar_numero_extra_grande(numero, centrar=True):
    """
    Dibujar un número extra grande ocupando toda la pantalla OLED
    Usando patrones bitmap completos similares a dibujar_numero_grande()
    """
    if not oled:
        return
    
    # Patrones bitmap completos para números extra grandes (16x24 píxeles)
    patrones_xxl = {
        '0': [
            0b0001111111000000,
            0b0011111111100000,
            0b0111111111110000,
            0b0111100001110000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b0111100001110000,
            0b0111111111110000,
            0b0011111111100000,
            0b0001111111000000,
            0b0000000000000000
        ],
        '1': [
            0b0000011100000000,
            0b0000111100000000,
            0b0001111100000000,
            0b0011111100000000,
            0b0111111100000000,
            0b1111111100000000,
            0b0000111100000000,
            0b0000111100000000,
            0b0000111100000000,
            0b0000111100000000,
            0b0000111100000000,
            0b0000111100000000,
            0b0000111100000000,
            0b0000111100000000,
            0b0000111100000000,
            0b0000111100000000,
            0b0000111100000000,
            0b0000111100000000,
            0b0000111100000000,
            0b1111111111110000,
            0b1111111111110000,
            0b1111111111110000,
            0b1111111111110000,
            0b0000000000000000
        ],
        '2': [
            0b0001111111000000,
            0b0011111111100000,
            0b0111111111110000,
            0b0111100001110000,
            0b1111000000111000,
            0b0000000000111000,
            0b0000000000111000,
            0b0000000001110000,
            0b0000000011110000,
            0b0000000111100000,
            0b0000001111000000,
            0b0000011110000000,
            0b0000111100000000,
            0b0001111000000000,
            0b0011110000000000,
            0b0111100000000000,
            0b1111000000000000,
            0b1111000000000000,
            0b1111000000000000,
            0b1111111111110000,
            0b1111111111110000,
            0b1111111111110000,
            0b1111111111110000,
            0b0000000000000000
        ],
        '3': [
            0b0001111111000000,
            0b0011111111100000,
            0b0111111111110000,
            0b0111100001110000,
            0b0000000000111000,
            0b0000000000111000,
            0b0000000001110000,
            0b0000111111100000,
            0b0000111111100000,
            0b0000111111110000,
            0b0000000001110000,
            0b0000000000111000,
            0b0000000000111000,
            0b0000000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b0111100001110000,
            0b0111111111110000,
            0b0011111111100000,
            0b0001111111000000,
            0b0000000000000000,
            0b0000000000000000,
            0b0000000000000000,
            0b0000000000000000
        ],
        '4': [
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111111111111000,
            0b1111111111111000,
            0b1111111111111000,
            0b1111111111111000,
            0b0000000000111000,
            0b0000000000111000,
            0b0000000000111000,
            0b0000000000111000,
            0b0000000000111000,
            0b0000000000111000,
            0b0000000000111000,
            0b0000000000111000,
            0b0000000000111000,
            0b0000000000111000,
            0b0000000000000000
        ],
        '5': [
            0b1111111111110000,
            0b1111111111110000,
            0b1111111111110000,
            0b1111111111110000,
            0b1111000000000000,
            0b1111000000000000,
            0b1111000000000000,
            0b1111111111000000,
            0b1111111111100000,
            0b1111111111110000,
            0b0000000001110000,
            0b0000000000111000,
            0b0000000000111000,
            0b0000000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b0111100001110000,
            0b0111111111110000,
            0b0011111111100000,
            0b0001111111000000,
            0b0000000000000000,
            0b0000000000000000,
            0b0000000000000000,
            0b0000000000000000
        ],
        '6': [
            0b0001111111000000,
            0b0011111111100000,
            0b0111111111110000,
            0b0111100001110000,
            0b1111000000000000,
            0b1111000000000000,
            0b1111000000000000,
            0b1111111111000000,
            0b1111111111100000,
            0b1111111111110000,
            0b1111100001110000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b0111100001110000,
            0b0111111111110000,
            0b0011111111100000,
            0b0001111111000000,
            0b0000000000000000,
            0b0000000000000000,
            0b0000000000000000,
            0b0000000000000000
        ],
        '7': [
            0b1111111111110000,
            0b1111111111110000,
            0b1111111111110000,
            0b1111111111110000,
            0b0000000000111000,
            0b0000000001110000,
            0b0000000001110000,
            0b0000000011110000,
            0b0000000011100000,
            0b0000000111100000,
            0b0000000111000000,
            0b0000001111000000,
            0b0000001110000000,
            0b0000011110000000,
            0b0000011100000000,
            0b0000111100000000,
            0b0000111000000000,
            0b0001111000000000,
            0b0001110000000000,
            0b0011110000000000,
            0b0011100000000000,
            0b0111100000000000,
            0b0000000000000000,
            0b0000000000000000
        ],
        '8': [
            0b0001111111000000,
            0b0011111111100000,
            0b0111111111110000,
            0b0111100001110000,
            0b1111000000111000,
            0b1111000000111000,
            0b0111100001110000,
            0b0011111111100000,
            0b0001111111000000,
            0b0011111111100000,
            0b0111111111110000,
            0b0111100001110000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b0111100001110000,
            0b0111111111110000,
            0b0011111111100000,
            0b0001111111000000,
            0b0000000000000000,
            0b0000000000000000,
            0b0000000000000000,
            0b0000000000000000
        ],
        '9': [
            0b0001111111000000,
            0b0011111111100000,
            0b0111111111110000,
            0b0111100001110000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b1111000000111000,
            0b0111100001110000,
            0b0111111111110000,
            0b0011111111111000,
            0b0001111111111000,
            0b0000000000111000,
            0b0000000000111000,
            0b0000000000111000,
            0b0111100001110000,
            0b0111111111110000,
            0b0011111111100000,
            0b0001111111000000,
            0b0000000000000000,
            0b0000000000000000,
            0b0000000000000000,
            0b0000000000000000
        ]
    }
    
    numero_str = str(numero)
    num_digitos = len(numero_str)
    
    # Calcular dimensiones según número de dígitos y tamaño de pantalla
    if num_digitos == 1:
        # Un dígito: usar patrón completo 16x24, centrado
        digit_width = 16
        spacing = 0
        start_x = (SCREEN_WIDTH - digit_width) // 2
        start_y = (SCREEN_HEIGHT - 24) // 2
        pattern_height = 24
        bits_to_draw = 16
    elif num_digitos == 2:
        # Dos dígitos: usar patrón completo pero más compacto
        digit_width = 14
        spacing = 2
        total_width = (digit_width * 2) + spacing
        start_x = (SCREEN_WIDTH - total_width) // 2
        start_y = (SCREEN_HEIGHT - 24) // 2
        pattern_height = 24
        bits_to_draw = 14
    elif num_digitos == 3:
        # Tres dígitos: reducir altura y ancho
        digit_width = 11
        spacing = 1
        total_width = (digit_width * 3) + (spacing * 2)
        start_x = max(0, (SCREEN_WIDTH - total_width) // 2)
        start_y = (SCREEN_HEIGHT - 20) // 2  # Altura reducida
        pattern_height = 20
        bits_to_draw = 11
    else:
        # Cuatro o más dígitos: muy compacto
        digit_width = 9
        spacing = 1
        total_width = (digit_width * num_digitos) + (spacing * (num_digitos - 1))
        start_x = max(0, (SCREEN_WIDTH - total_width) // 2)
        start_y = (SCREEN_HEIGHT - 16) // 2  # Altura muy reducida
        pattern_height = 16
        bits_to_draw = 9
    
    # Dibujar cada dígito
    for i, digito in enumerate(numero_str):
        if digito in patrones_xxl:
            patron = patrones_xxl[digito]
            digit_x = start_x + i * (digit_width + spacing)
            
            for row in range(pattern_height):
                if start_y + row < SCREEN_HEIGHT and row < len(patron):  # Verificar límites Y
                    byte_pattern = patron[row]
                    
                    for bit in range(bits_to_draw):
                        # Usar máscara dinámica según el ancho
                        mask = 0b1000000000000000 >> bit
                        if byte_pattern & mask:
                            pixel_x = digit_x + bit
                            pixel_y = start_y + row
                            if pixel_x < SCREEN_WIDTH and pixel_y >= 0 and pixel_y < SCREEN_HEIGHT:  # Verificar límites
                                oled.pixel(pixel_x, pixel_y, 1)

def mostrar_dias_numeros_grandes(dias):
    """Mostrar días con números grandes centrados - ajustado para pantalla configurable"""
    if not oled:
        return
    
    # Limpiar pantalla completamente
    oled.fill(0)
    
    # Validar que el número no sea demasiado grande
    numero_mostrar = abs(dias)
    if numero_mostrar > 9999:  # Máximo 4 dígitos
        numero_mostrar = 9999
    
    # Calcular posición Y centrada para el número
    digit_height = min(12, SCREEN_HEIGHT - 16)  # Dejar espacio para texto
    number_y = (SCREEN_HEIGHT - digit_height) // 2
    
    # Mostrar el número grande centrado
    dibujar_numero_grande(numero_mostrar, 0, number_y)
    
    # Mostrar texto pequeño arriba o abajo según el caso y espacio disponible
    text_size = 8  # Altura de una línea de texto
    if SCREEN_HEIGHT >= 32:  # Si hay suficiente espacio para texto arriba y abajo
        if dias > 0:
            # Centrar texto "FALTAN" arriba
            text_x = (SCREEN_WIDTH - (6 * 8)) // 2  # "FALTAN" = 6 chars
            oled.text("FALTAN", max(0, text_x), 0, 1)
            # Centrar texto "DIAS" abajo
            text_x = (SCREEN_WIDTH - (4 * 8)) // 2  # "DIAS" = 4 chars
            oled.text("DIAS", max(0, text_x), SCREEN_HEIGHT - text_size, 1)
        elif dias == 0:
            # Centrar texto "HOY!" arriba
            text_x = (SCREEN_WIDTH - (4 * 8)) // 2  # "HOY!" = 4 chars
            oled.text("HOY!", max(0, text_x), 0, 1)
            # Centrar texto "EL DIA" abajo
            text_x = (SCREEN_WIDTH - (6 * 8)) // 2  # "EL DIA" = 6 chars
            oled.text("EL DIA", max(0, text_x), SCREEN_HEIGHT - text_size, 1)
        else:
            # Centrar texto "PASO:" arriba
            text_x = (SCREEN_WIDTH - (5 * 8)) // 2  # "PASO:" = 5 chars
            oled.text("PASO:", max(0, text_x), 0, 1)
            # Centrar texto "DIAS" abajo
            text_x = (SCREEN_WIDTH - (4 * 8)) // 2  # "DIAS" = 4 chars
            oled.text("DIAS", max(0, text_x), SCREEN_HEIGHT - text_size, 1)
    
    oled.show()

def mostrar_solo_numero(dias):
    """Mostrar solo el número de días ocupando toda la pantalla - ajustado para pantalla configurable"""
    if not oled:
        return
    
    # Limpiar pantalla completamente
    oled.fill(0)
    
    # Validar que el número no sea demasiado grande
    numero_mostrar = abs(dias)
    if numero_mostrar > 9999:  # Máximo 4 dígitos
        numero_mostrar = 9999
    
    # Casos especiales para números pequeños (hacer aún más grandes)
    if numero_mostrar == 0:
        # Cero especial - muy grande y centrado
        dibujar_cero_especial()
    else:
        # Dibujar solo el número, sin texto adicional
        dibujar_numero_extra_grande(numero_mostrar)
    
    oled.show()

def dibujar_cero_especial():
    """Dibujar un cero extra especial para el día cero - ajustado para pantalla configurable"""
    if not oled:
        return
    
    # Calcular dimensiones del cero basado en el tamaño de pantalla
    cero_width = min(20, SCREEN_WIDTH - 4)  # Dejar margen de 2 píxeles a cada lado
    cero_height = min(32, SCREEN_HEIGHT - 4)  # Dejar margen de 2 píxeles arriba y abajo
    
    # Generar patrón de cero escalable
    def generar_patron_cero(width, height):
        patron = []
        for y in range(height):
            row = 0
            for x in range(width):
                # Calcular si este pixel debe estar encendido (forma de óvalo)
                center_x = width / 2
                center_y = height / 2
                
                # Normalizar coordenadas
                nx = (x - center_x) / (width / 2)
                ny = (y - center_y) / (height / 2)
                
                # Ecuación de elipse con grosor
                distance = (nx * nx) + (ny * ny)
                
                # Crear el anillo del cero (entre dos elipses)
                if 0.5 <= distance <= 1.0:
                    row |= (1 << (width - 1 - x))
            
            patron.append(row)
        return patron
    
    patron_cero = generar_patron_cero(cero_width, cero_height)
    
    # Centrar el cero en la pantalla
    start_x = (SCREEN_WIDTH - cero_width) // 2
    start_y = (SCREEN_HEIGHT - cero_height) // 2
    
    for row in range(len(patron_cero)):
        if start_y + row >= 0 and start_y + row < SCREEN_HEIGHT:
            byte_pattern = patron_cero[row]
            
            for bit in range(cero_width):
                if byte_pattern & (1 << (cero_width - 1 - bit)):
                    pixel_x = start_x + bit
                    pixel_y = start_y + row
                    if pixel_x >= 0 and pixel_x < SCREEN_WIDTH and pixel_y >= 0 and pixel_y < SCREEN_HEIGHT:
                        oled.pixel(pixel_x, pixel_y, 1)

def actualizar_pantalla():
    """Actualizar información en LCD según el modo seleccionado - ajustado para pantalla configurable"""
    if not oled:
        return
    
    # Si no hay fecha configurada, mostrar mensaje de configuración
    if not fecha_configurada:
        if not wifi_configurado:
            # No tiene WiFi NI fecha configurada
            mostrar_en_oled(['Modo Config', 'Conectate al AP:', AP_SSID])
        else:
            # Tiene WiFi pero no fecha
            mostrar_en_oled(['WiFi Conectado', '', 'Falta configurar', 'la fecha objetivo!'])
        return
    
    # TIENE FECHA CONFIGURADA - Calcular días
    dias = calcular_dias_restantes()
    if dias is None:
        # Error calculando días
        if not wifi_configurado:
            mostrar_en_oled(['Error tiempo', 'AP: {}'.format(AP_SSID[:MAX_CHAR_PER_LINE-4]), 'IP: 192.168.4.1'])
        else:
            mostrar_en_oled(['Error tiempo', 'Verifique NTP'])
        return
    
    # MOSTRAR DÍAS SEGÚN EL MODO SELECCIONADO
    if modo_display == "solo_numero":
        mostrar_solo_numero(dias)
    elif modo_display == "numeros_grandes":
        mostrar_dias_numeros_grandes(dias)
    else:
        # Modo normal - MODIFICADO para mostrar info de AP cuando no hay WiFi
        if not wifi_configurado:
            # SIN WiFi: Mostrar días + info del AP
            if dias > 0:
                mostrar_en_oled(['FALTAN: {} DIAS'.format(dias), 'Fecha: {}'.format(fecha_objetivo[:MAX_CHAR_PER_LINE]), '', 'AP: {}'.format(AP_SSID[:MAX_CHAR_PER_LINE-4]), 'IP: 192.168.4.1'])
            elif dias == 0:
                mostrar_en_oled(['HOY ES EL DIA!', '***************', '', 'AP: {}'.format(AP_SSID[:MAX_CHAR_PER_LINE-4]), 'IP: 192.168.4.1'])
            else:
                mostrar_en_oled(['PASO: {} DIAS'.format(abs(dias)), 'Fecha: {}'.format(fecha_objetivo[:MAX_CHAR_PER_LINE]), '', 'AP: {}'.format(AP_SSID[:MAX_CHAR_PER_LINE-4]), 'IP: 192.168.4.1'])
        else:
            # CON WiFi: Mostrar días normalmente
            if dias > 0:
                mostrar_en_oled(['FALTAN:', '', '{} DIAS'.format(dias), '', 'Fecha: {}'.format(fecha_objetivo)])
            elif dias == 0:
                mostrar_en_oled(['***********', '', 'HOY ES EL DIA!', '', '***********'])
            else:
                mostrar_en_oled(['PASO HACE:', '', '{} DIAS'.format(abs(dias)), '', 'Fecha: {}'.format(fecha_objetivo)])


# ========== ALTERNATIVA: Pantalla rotativa ==========
# Si quieres que alterne entre mostrar días y info del AP

def actualizar_pantalla_rotativa():
    """Actualizar pantalla alternando entre días y info AP cuando no hay WiFi"""
    global ultimo_cambio_pantalla, mostrar_info_ap
    
    if not oled:
        return
    
    # Inicializar variables si no existen
    if 'ultimo_cambio_pantalla' not in globals():
        globals()['ultimo_cambio_pantalla'] = 0
        globals()['mostrar_info_ap'] = False
    
    if not fecha_configurada:
        if not wifi_configurado:
            mostrar_en_oled(['Modo Config', 'Conectate al AP:', AP_SSID])
        else:
            mostrar_en_oled(['WiFi Conectado', '', 'Falta configurar', 'la fecha objetivo!'])
        return
    
    dias = calcular_dias_restantes()
    if dias is None:
        if not wifi_configurado:
            mostrar_en_oled(['Error tiempo', 'AP: {}'.format(AP_SSID[:9]), 'IP: 192.168.4.1'])
        else:
            mostrar_en_oled(['Error tiempo', 'Verifique NTP'])
        return
    
    # LÓGICA DE ROTACIÓN (solo cuando no hay WiFi)
    if not wifi_configurado and modo_display == "normal":
        # Cambiar cada 5 segundos
        tiempo_actual = time.time()
        if tiempo_actual - ultimo_cambio_pantalla > 5:
            mostrar_info_ap = not mostrar_info_ap
            ultimo_cambio_pantalla = tiempo_actual
        
        if mostrar_info_ap:
            # Mostrar info del Access Point
            mostrar_en_oled(['Access Point', 'Activo:', '', 'Red: {}'.format(AP_SSID[:9]), 'IP: 192.168.4.1'])
        else:
            # Mostrar días restantes
            if dias > 0:
                mostrar_en_oled(['FALTAN:', '', '{} DIAS'.format(dias), '', 'Fecha: {}'.format(fecha_objetivo[:10])])
            elif dias == 0:
                mostrar_en_oled(['***********', '', 'HOY ES EL DIA!', '', '***********'])
            else:
                mostrar_en_oled(['PASO HACE:', '', '{} DIAS'.format(abs(dias)), '', 'Fecha: {}'.format(fecha_objetivo[:10])])
    else:
        # Mostrar según modo seleccionado (con WiFi o modos especiales)
        if modo_display == "solo_numero":
            mostrar_solo_numero(dias)
        elif modo_display == "numeros_grandes":
            mostrar_dias_numeros_grandes(dias)
        else:
            # Modo normal con WiFi
            if dias > 0:
                mostrar_en_oled(['FALTAN:', '', '{} DIAS'.format(dias), '', 'Fecha: {}'.format(fecha_objetivo)])
            elif dias == 0:
                mostrar_en_oled(['***********', '', 'HOY ES EL DIA!', '', '***********'])
            else:
                mostrar_en_oled(['PASO HACE:', '', '{} DIAS'.format(abs(dias)), '', 'Fecha: {}'.format(fecha_objetivo)])


# ========== OPCIÓN SIMPLE: Solo en modo normal ==========
# Mostrar info AP solo en modo normal, en otros modos solo días

def actualizar_pantalla_simple():
    """Mostrar días + info AP solo en modo normal - ajustado para pantalla configurable"""
    if not oled:
        return
    
    if not fecha_configurada:
        if not wifi_configurado:
            mostrar_en_oled(['Modo Config', 'Conectate al AP:', AP_SSID])
        else:
            mostrar_en_oled(['WiFi Conectado', '', 'Falta configurar', 'la fecha objetivo!'])
        return
    
    dias = calcular_dias_restantes()
    if dias is None:
        if not wifi_configurado:
            mostrar_en_oled(['Error tiempo', 'AP: {}'.format(AP_SSID[:MAX_CHAR_PER_LINE-4])]) 
        else:
            mostrar_en_oled(['Error tiempo', 'Verifique NTP'])
        return
    
    # MOSTRAR SEGÚN MODO Y ESTADO WIFI
    if modo_display == "solo_numero" or modo_display == "numeros_grandes":
        # En modos especiales: SOLO mostrar días (sin info AP)
        if modo_display == "solo_numero":
            mostrar_solo_numero(dias)
        else:
            mostrar_dias_numeros_grandes(dias)
    else:
        # Modo normal: Mostrar días + info AP si no hay WiFi
        if not wifi_configurado:
            # Sin WiFi: Días + info AP
            if dias > 0:
                mostrar_en_oled(['FALTAN: {} DIAS'.format(dias), '', 'AP: {}'.format(AP_SSID[:MAX_CHAR_PER_LINE-4]), '192.168.4.1'])
            elif dias == 0:
                mostrar_en_oled(['HOY ES EL DIA!', '', 'AP: {}'.format(AP_SSID[:MAX_CHAR_PER_LINE-4]), '192.168.4.1'])
            else:
                mostrar_en_oled(['PASO: {} DIAS'.format(abs(dias)), '', 'AP: {}'.format(AP_SSID[:MAX_CHAR_PER_LINE-4]), '192.168.4.1'])
        else:
            # Con WiFi: Días normalmente
            if dias > 0:
                mostrar_en_oled(['FALTAN:', '', '{} DIAS'.format(dias), '', 'Fecha: {}'.format(fecha_objetivo)])
            elif dias == 0:
                mostrar_en_oled(['***********', '', 'HOY ES EL DIA!', '', '***********'])
            else:
                mostrar_en_oled(['PASO HACE:', '', '{} DIAS'.format(abs(dias)), '', 'Fecha: {}'.format(fecha_objetivo)])

def generar_html_base():
    """Generar HTML base con diseño moderno y Premium"""
    return """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
<title>ESP32 Config</title>
<style>
:root {
    --primary: #6366f1;
    --primary-hover: #4f46e5;
    --bg: #0f172a;
    --card-bg: #1e293b;
    --text: #f8fafc;
    --text-muted: #94a3b8;
    --border: #334155;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
}
* { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background-color: var(--bg);
    color: var(--text);
    margin: 0;
    padding: 16px;
    line-height: 1.5;
}
.container { max-width: 420px; margin: 0 auto; }
.header { text-align: center; margin-bottom: 24px; padding-top: 10px; }
.app-icon { font-size: 40px; margin-bottom: 10px; display: block; }
.header h1 {
    font-size: 1.25rem;
    font-weight: 700;
    margin: 0;
    color: var(--text);
    letter-spacing: -0.025em;
}
.subtitle { color: var(--text-muted); font-size: 0.875rem; margin-top: 4px; }

/* Cards */
.card {
    background: var(--card-bg);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(255,255,255,0.05);
}
.card-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Status Badges */
.status-badge {
    display: inline-flex;
    align-items: center;
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 0.875rem;
    font-weight: 500;
    background: rgba(255,255,255,0.1);
    color: var(--text);
}
.status-badge.ok { background: rgba(16, 185, 129, 0.2); color: #34d399; }
.status-badge.warn { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
.status-badge.err { background: rgba(239, 68, 68, 0.2); color: #f87171; }

/* Inputs */
.form-group { margin-bottom: 20px; }
label { display: block; margin-bottom: 8px; font-size: 0.9rem; font-weight: 500; color: var(--text-muted); }
input[type="text"], input[type="password"], input[type="date"], select {
    width: 100%;
    padding: 12px 16px;
    background: #020617;
    border: 1px solid var(--border);
    border-radius: 12px;
    color: white;
    font-size: 16px; /* Evita zoom en iOS */
    transition: all 0.2s;
    outline: none;
}
input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2); }

/* Buttons */
.btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    padding: 14px;
    border: none;
    border-radius: 12px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    text-decoration: none;
    margin-bottom: 12px;
    gap: 8px;
}
.btn:active { transform: scale(0.98); }
.btn-primary { 
    background: linear-gradient(135deg, var(--primary) 0%, #4338ca 100%);
    color: white;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
}
.btn-secondary { background: #334155; color: white; }
.btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text-muted); }
.btn-danger { background: rgba(239, 68, 68, 0.15); color: #f87171; }

/* WiFi Selector */
.wifi-list { display: flex; flex-direction: column; gap: 8px; max-height: 280px; overflow-y: auto; }
.wifi-item {
    display: flex;
    align-items: center;
    padding: 12px;
    background: rgba(255,255,255,0.03);
    border-radius: 10px;
    cursor: pointer;
    border: 1px solid transparent;
    transition: all 0.2s;
}
.wifi-item:hover { background: rgba(255,255,255,0.05); }
.wifi-item.selected { 
    background: rgba(99, 102, 241, 0.15); 
    border-color: var(--primary); 
}
.wifi-info { flex: 1; }
.wifi-ssid { font-weight: 500; display: block; }
.wifi-rssi { font-size: 0.75rem; color: var(--text-muted); }

/* Signal Icons */
.signal-icon { display: flex; align-items: flex-end; gap: 2px; height: 12px; margin-right: 12px; }
.bar { width: 3px; background: #475569; border-radius: 1px; }
.s-1 .b1 { background: var(--text-muted); }
.s-2 .b1, .s-2 .b2 { background: var(--text-muted); }
.s-3 .b1, .s-3 .b2, .s-3 .b3 { background: var(--success); }
.s-4 .bar { background: var(--success); }

/* Switches Radio */
.radio-switch { display: flex; background: #020617; padding: 4px; border-radius: 12px; margin-bottom: 20px; }
.radio-option { flex: 1; text-align: center; padding: 10px; border-radius: 8px; cursor: pointer; color: var(--text-muted); font-size: 0.9rem; font-weight: 500; transition: all 0.2s; }
.radio-option.active { background: var(--card-bg); color: var(--text); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
input[type="radio"] { display: none; }

</style>
<script>
function selectWifi(ssid, element) {
    document.getElementById('ssid_input').value = ssid;
    document.querySelectorAll('.wifi-item').forEach(el => el.classList.remove('selected'));
    element.classList.add('selected');
    document.getElementById('password_input').focus();
    
    // Ocultar manual si se selecciona lista
    document.getElementById('manual_group').style.display = 'none';
}
function toggleManual() {
    document.getElementById('manual_group').style.display = 'block';
    document.getElementById('ssid_input').value = '';
    document.getElementById('ssid_input').focus();
    document.querySelectorAll('.wifi-item').forEach(el => el.classList.remove('selected'));
}
</script>
</head>
<body>
<div class="container">
"""

def pagina_principal():
    """Página principal con Dashboard"""
    html = generar_html_base()
    
    html += "<div class='header'><span class='app-icon'>📅</span><h1>Configurador</h1><div class='subtitle'>ESP32 Day Counter</div></div>"
    
    # Estado del Sistema
    html += "<div class='card'>"
    html += "<div class='card-title'>Estado del Sistema</div>"
    
    # WiFi Status
    html += "<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;'>"
    html += "<span>WiFi</span>"
    if wifi_configurado:
        wlan = network.WLAN(network.STA_IF)
        ssid = wlan.config('essid')
        ip = wlan.ifconfig()[0]
        html += "<span class='status-badge ok'>Conectado</span></div>"
        html += "<div style='font-size:0.85rem; color:var(--text-muted); margin-bottom:16px;'>Red: <strong>{}</strong><br>IP: {}</div>".format(ssid, ip)
        
        # mDNS info
        if MDNS_AVAILABLE:
            html += "<div style='background:rgba(99,102,241,0.1); padding:10px; border-radius:8px; font-size:0.85rem; color:#818cf8; text-align:center;'>Access: <a href='http://{}.local' style='color:inherit; font-weight:bold;'>{}.local</a></div>".format(HOSTNAME, HOSTNAME)
    else:
        html += "<span class='status-badge err'>Sin Conexión</span></div>"
        html += "<div style='font-size:0.85rem; color:var(--text-muted);'>Conéctate para sincronizar fecha y hora.</div>"
    html += "</div>" # End Card
    
    # Fecha Status
    html += "<div class='card'>"
    html += "<div class='card-title'>Evento Objetivo</div>"
    if fecha_configurada:
        dias = calcular_dias_restantes()
        texto_dias = "Calculando..." if dias is None else "{} Días".format(dias)
        html += "<div style='text-align:center; padding:10px;'>"
        html += "<div style='font-size:2rem; font-weight:700; color:var(--primary);'>{}</div>".format(texto_dias)
        html += "<div style='font-size:0.9rem; color:var(--text-muted);'>{}</div>".format(fecha_objetivo)
        html += "</div>"
    else:
        html += "<div style='text-align:center; padding:15px; border:2px dashed var(--border); border-radius:12px; color:var(--text-muted);'>"
        html += "No hay fecha configurada</div>"
    html += "</div>" # End Card
    
    # Acciones
    html += "<div style='display:grid; gap:10px;'>"
    html += "<a href='/wifi' class='btn btn-primary'>📡 Configurar WiFi</a>"
    html += "<a href='/fecha' class='btn btn-secondary'>📅 Configurar Fecha</a>"
    html += "<a href='/display' class='btn btn-secondary'>📺 Personalizar Display</a>"
    
    html += "<form action='/reset' method='GET' onsubmit='return confirm(\"¿Resetear de fábrica?\");' style='margin-top:20px;'>"
    html += "<button type='submit' class='btn btn-danger'>⚠️ Resetear Fábrica</button></form>"
    html += "</div>"
    
    html += "</div></body></html>"
    return html

def pagina_display():
    """Página Display Mejorada"""
    html = generar_html_base()
    html += "<div class='header'><h1>Personalizar</h1><div class='subtitle'>Opciones de Visualización</div></div>"
    
    # Preview de Pantalla (Simulada CSS)
    html += "<div class='card' style='text-align:center;'>"
    html += "<div class='card-title' style='justify-content:center;'>Vista Previa ({}x{}px)</div>".format(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    # Simular OLED con aspect ratio correcto
    aspect_ratio = SCREEN_WIDTH / SCREEN_HEIGHT
    html += "<div style='background:black; width:100%; max-width:200px; aspect-ratio:{}; margin:0 auto; border-radius:4px; border:2px solid #333; position:relative; display:flex; align-items:center; justify-content:center; overflow:hidden;'>".format(aspect_ratio)
    
    # Contenido simulado según modo
    if modo_display == "solo_numero":
        html += "<span style='color:cyan; font-family:monospace; font-size:40px; line-height:1;'>123</span>"
    elif modo_display == "numeros_grandes":
        html += "<div style='color:white; font-family:monospace; font-size:10px; display:flex; flex-direction:column; align-items:center; gap:2px;'><span>FALTAN</span><span style='font-size:24px; color:cyan;'>123</span><span>DIAS</span></div>"
    else:
        html += "<div style='color:white; font-family:monospace; font-size:8px; width:100%; padding:4px; text-align:left;'>FALTAN:<br>123 DIAS<br><br>Fecha: 2025...</div>"
    
    html += "</div>"
    html += "</div>"
    
    html += "<form action='/setdisplay' method='POST'>"
    html += "<div class='card'>"
    html += "<div class='card-title'>Estilo de Pantalla</div>"
    
    # Opciones como lista seleccionable
    options = [
        ('normal', 'Vista Normal', 'Texto detallado con scroll'),
        ('numeros_grandes', 'Números Grandes', 'Énfasis en los días restantes'),
        ('solo_numero', 'Solo Número', 'Máxima visibilidad del contador')
    ]
    
    for val, label, desc in options:
        checked = "checked" if modo_display == val else ""
        selected_cls = "selected" if modo_display == val else ""
        html += "<label class='wifi-item {}' onclick='document.querySelectorAll(\".wifi-item\").forEach(e=>e.classList.remove(\"selected\")); this.classList.add(\"selected\");'>".format(selected_cls)
        html += "<input type='radio' name='modo' value='{}' {} style='display:block; width:auto; margin-right:10px;'>".format(val, checked)
        html += "<div class='wifi-info'><span class='wifi-ssid'>{}</span>".format(label)
        html += "<span class='wifi-rssi'>{}</span></div>".format(desc)
        html += "</label>"
    
    html += "</div>"
    
    html += "<button type='submit' class='btn btn-primary'>💾 Guardar Cambios</button>"
    html += "</form>"
    html += "<a href='/' class='btn btn-outline'>Cancelar</a>"
    html += "</div></body></html>"
    return html

def pagina_wifi():
    """Página WiFi Modernizada com Selector Visual"""
    html = generar_html_base()
    html += "<div class='header'><h1>Conexión WiFi</h1><div class='subtitle'>Selecciona una red</div></div>"
    
    redes = escanear_redes()
    
    html += "<form action='/setwifi' method='POST' id='wifi-form'>"
    html += "<input type='hidden' name='ssid_option' value='select'>" # Default to select
    
    # Lista de Redes
    html += "<div class='card'>"
    html += "<div class='card-title'>Redes Disponibles</div>"
    html += "<div class='wifi-list'>"
    
    if redes:
        # Ordenar por señal (RSSI)
        redes.sort(key=lambda x: x[1], reverse=True)
        
        for ssid, rssi in redes:
            ssid_safe = ssid.replace("'", "&#39;")
            
            # Calcular barras de señal
            bars_class = "s-1"
            if rssi > -50: bars_class = "s-4"
            elif rssi > -70: bars_class = "s-3"
            elif rssi > -80: bars_class = "s-2"
            
            html += "<div class='wifi-item' onclick='selectWifi(\"{}\", this)'>".format(ssid_safe)
            html += "<div class='signal-icon {}'><div class='bar b1'></div><div class='bar b2'></div><div class='bar b3'></div><div class='bar b4'></div></div>".format(bars_class)
            html += "<div class='wifi-info'><span class='wifi-ssid'>{}</span><span class='wifi-rssi'>{} dBm</span></div>".format(ssid, rssi)
            # Icono candado
            html += "<span style='font-size:12px; color:var(--text-muted);'>🔒</span>"
            html += "</div>"
    else:
        html += "<div style='text-align:center; padding:20px; color:var(--text-muted);'>No se encontraron redes.<br><small>Intenta de nuevo o ingresa manual.</small></div>"

    html += "<div style='text-align:center; margin-top:12px;'>"
    html += "<button type='button' class='btn-outline' style='width:auto; display:inline-block; padding:8px 16px; font-size:0.8rem;' onclick='toggleManual()'>➕ Agregar Manualmente</button>"
    html += "</div>"
    
    html += "</div>" # End Card lista
    
    # Credenciales Input
    html += "<div class='card' style='background:#162032;'>"
    
    # Input Manual (Oculto por defecto)
    html += "<div id='manual_group' style='display:none; margin-bottom:15px;'>"
    html += "<label>Nombre de Red (SSID)</label>"
    html += "<input type='text' name='ssid_manual' id='ssid_input' placeholder='Escribe el nombre...'>"
    html += "</div>"
    
    # Input Oculto para selección de lista
    html += "<input type='hidden' name='ssid_select' id='ssid_input_hidden'>" # Compatibilidad con logica anterior
    
    html += "<label>Contraseña</label>"
    html += "<div style='position:relative;'>"
    html += "<input type='password' name='password' id='password_input' placeholder='Ingresa la contraseña' required>"
    # Ojo toggle
    html += "<span onclick='var x=document.getElementById(\"password_input\"); x.type = x.type==\"password\"?\"text\":\"password\";' style='position:absolute; right:12px; top:12px; cursor:pointer; opacity:0.6;'>👁️</span>"
    html += "</div>"
    
    # Hack para unificar inputs en el submit
    html += "<script>document.getElementById('wifi-form').onsubmit = function() { var manual = document.getElementById('ssid_input').value; if(manual) { document.querySelector('input[name=\"ssid_option\"]').value='manual'; document.querySelector('input[name=\"ssid_manual\"]').value=manual; } else { return false; } };</script>"
    
    html += "</div>"
    
    html += "<button type='submit' class='btn btn-primary'>Conectar</button>"
    html += "</form>"
    html += "<a href='/' class='btn btn-outline'>Cancelar</a>"
    html += "</div></body></html>"
    return html

def pagina_fecha():
    """Página de Configuración de Fecha"""
    html = generar_html_base()
    html += "<div class='header'><h1>Fecha Objetivo</h1><div class='subtitle'>¿Cuándo es el evento?</div></div>"
    
    html += "<form action='/setfecha' method='POST'>"
    html += "<div class='card'>"
    
    if fecha_configurada:
         html += "<div style='background:rgba(16,185,129,0.1); border-radius:8px; padding:12px; margin-bottom:20px; font-size:0.9rem; display:flex; align-items:center; gap:10px;'><span style='color:#34d399;'>✅</span> <span>Configurado actualmente: <strong>{}</strong></span></div>".format(fecha_objetivo)
    
    html += "<div class='form-group'>"
    html += "<label>Selecciona la nueva fecha</label>"
    html += "<input type='date' name='fecha' required style='font-size:1.2rem; text-align:center; letter-spacing:2px;'>"
    html += "</div>"
    
    html += "<div style='font-size:0.8rem; color:var(--text-muted); text-align:center;'>El contador calculará los días restantes automáticamente desde hoy.</div>"
    
    html += "</div>"
    
    html += "<button type='submit' class='btn btn-primary'>Establecer Fecha</button>"
    html += "</form>"
    html += "<a href='/' class='btn btn-outline'>Cancelar</a>"
    html += "</div></body></html>"
    return html

def parsear_form_data(data):
    """Parsear datos del formulario"""
    params = {}
    pairs = data.split('&')
    for pair in pairs:
        if '=' in pair:
            key, value = pair.split('=', 1)
            # Decodificar URL básico
            value = value.replace('+', ' ')
            value = value.replace('%40', '@')
            value = value.replace('%21', '!')
            value = value.replace('%23', '#')
            value = value.replace('%24', '$')
            value = value.replace('%25', '%')
            value = value.replace('%26', '&')
            value = value.replace('%27', "'")
            value = value.replace('%28', '(')
            value = value.replace('%29', ')')
            value = value.replace('%2A', '*')
            value = value.replace('%2B', '+')
            value = value.replace('%2C', ',')
            value = value.replace('%2D', '-')
            value = value.replace('%2E', '.')
            value = value.replace('%2F', '/')
            value = value.replace('%3A', ':')
            value = value.replace('%3B', ';')
            value = value.replace('%3C', '<')
            value = value.replace('%3D', '=')
            value = value.replace('%3E', '>')
            value = value.replace('%3F', '?')
            value = value.replace('%5B', '[')
            value = value.replace('%5C', '\\')
            value = value.replace('%5D', ']')
            value = value.replace('%5E', '^')
            value = value.replace('%5F', '_')
            value = value.replace('%60', '`')
            value = value.replace('%7B', '{')
            value = value.replace('%7C', '|')
            value = value.replace('%7D', '}')
            value = value.replace('%7E', '~')
            params[key] = value
    return params

def manejar_request(client):
    """Manejar request HTTP"""
    global wifi_configurado, fecha_configurada, ssid_guardado, password_guardado, fecha_objetivo, modo_display
    
    try:
        request = client.recv(1024).decode('utf-8')
        
        # Extraer método y path
        lines = request.split('\r\n')
        if not lines:
            return
            
        first_line = lines[0]
        method, path, _ = first_line.split(' ')
        
        # Extraer datos POST si existen
        post_data = ""
        if method == "POST":
            # Buscar datos después de línea vacía
            for i, line in enumerate(lines):
                if line == "" and i + 1 < len(lines):
                    post_data = lines[i + 1]
                    break
        
        # Enrutamiento
        if path == "/" or path.startswith("/?"):
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + pagina_principal()
        
        elif path == "/display":
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + pagina_display()
            
        elif path == "/setdisplay" and method == "POST":
            params = parsear_form_data(post_data)
            if 'modo' in params:
                nuevo_modo = params['modo']
                if nuevo_modo in ['normal', 'numeros_grandes', 'solo_numero']:  # AGREGADO solo_numero
                    modo_display = nuevo_modo
                    guardar_modo_display_json(nuevo_modo) #guardar_modo_display(nuevo_modo)
                    
                    html = generar_html_base()
                    html += "<h1>¡Modo Cambiado!</h1>"
                    
                    # Mostrar nombre del modo
                    nombre_modo = "Vista Normal"
                    if nuevo_modo == "numeros_grandes":
                        nombre_modo = "Números Grandes"
                    elif nuevo_modo == "solo_numero":
                        nombre_modo = "Solo Número"
                    
                    html += "<div class='success'>Nuevo modo: {}</div>".format(nombre_modo)
                    html += "<br><a href='/'><button class='btn-primary'>Volver</button></a></div></body></html>"
                    response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html
                else:
                    response = "HTTP/1.1 400 Bad Request\r\n\r\nModo inválido"
            else:
                response = "HTTP/1.1 400 Bad Request\r\n\r\nModo no recibido"
            
        elif path == "/wifi":
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + pagina_wifi()
            
        elif path == "/setwifi" and method == "POST":
            params = parsear_form_data(post_data)
            
            # Determinar qué SSID usar
            ssid = ""
            if 'ssid_option' in params:
                if params['ssid_option'] == 'manual' and 'ssid_manual' in params:
                    ssid = params['ssid_manual'].strip()
                elif params['ssid_option'] == 'select' and 'ssid_select' in params:
                    ssid = params['ssid_select'].strip()
            
            if ssid and 'password' in params:
                password = params['password']
                
                html = generar_html_base()
                html += "<h1>Conectando a WiFi...</h1>"
                html += "<p><strong>Red:</strong> {}</p>".format(ssid)
                html += "<p>Por favor espera mientras se establece la conexión...</p>"
                html += "<div class='info'>Esta página se actualizará automáticamente.</div>"
                html += "<script>setTimeout(function(){ window.location.href = '/'; }, 10000);</script>"
                html += "</div></body></html>"
                
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html
                client.send(response.encode('utf-8'))
                client.close()
                
                # Intentar conectar
                time.sleep(1)
                if conectar_wifi(ssid, password):
                    guardar_wifi_json(ssid, password) #guardar_wifi(ssid, password)
                    ssid_guardado = ssid
                    password_guardado = password
                return
            else:
                html = generar_html_base()
                html += "<h1>Error</h1>"
                html += "<div class='alert'>Por favor selecciona una red y proporciona la contraseña.</div>"
                html += "<a href='/wifi'><button class='btn-secondary'>Volver</button></a>"
                html += "</div></body></html>"
                response = "HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\n\r\n" + html
                
        elif path == "/fecha":
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + pagina_fecha()
            
        elif path == "/setfecha" and method == "POST":
            params = parsear_form_data(post_data)
            if 'fecha' in params:
                fecha = params['fecha']
                if configurar_fecha_destino(fecha):
                    guardar_fecha_json(fecha) #guardar_fecha(fecha)
                    fecha_objetivo = fecha
                    
                    html = generar_html_base()
                    html += "<h1>¡Fecha Configurada!</h1><div class='success'>Fecha objetivo: {}</div>".format(fecha)
                    html += "<br><a href='/'><button class='btn-primary'>Volver</button></a></div></body></html>"
                    response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html
                else:
                    response = "HTTP/1.1 400 Bad Request\r\n\r\nError al configurar fecha"
            else:
                response = "HTTP/1.1 400 Bad Request\r\n\r\nFecha no recibida"
                
        elif path == "/reset":
            detener_mdns()  # AGREGAR ESTA LÍNEA
            limpiar_configuracion_json() #limpiar_configuracion()
            html = generar_html_base()
            html += "<h1>Reset Completo</h1><p>Configuración borrada. El ESP32 se reiniciará...</p></div></body></html>"
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html
            client.send(response.encode('utf-8'))
            client.close()
            time.sleep(2)
            reset()
            
        else:
            # Redireccionar a página principal (portal cautivo)
            response = "HTTP/1.1 302 Found\r\nLocation: /\r\n\r\n"
        
        client.send(response.encode('utf-8'))
        
    except Exception as e:
        print("Error manejando request: {}".format(e))
    finally:
        client.close()

class DNSServer:
    def __init__(self, ip_address):
        self.ip_address = ip_address
        self.port = 53
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(False)
        self.socket.bind((ip_address, self.port))

    def handle_request(self):
        try:
            data, addr = self.socket.recvfrom(1024)
            if not data:
                return

            transaction_id = data[0:2]
            
            packet = transaction_id + b'\x81\x80\x00\x01\x00\x01\x00\x00\x00\x00'
            
            # 1. Copiar la Pregunta (Question Section) saneada
            # Buscar el fin de la sección de pregunta (marcada por un byte 0x00)
            fin_pregunta = data.find(b'\x00', 12)
            if fin_pregunta > 0:
                # Copiar hasta el fin del nombre + 4 bytes (Tipo y Clase)
                packet += data[12:fin_pregunta + 5]
            else:
                # Fallback por si acaso
                packet += data[12:]

            # 2. Agregar la Cabecera de la Respuesta (Answer Section Header)
            # C0 0C = Puntero al nombre en el offset 12 (comienzo de la pregunta)
            packet += b'\xc0\x0c'
            packet += b'\x00\x01' # TYPE A
            packet += b'\x00\x01' # CLASS IN
            packet += b'\x00\x00\x00\x3c' # TTL 60s
            packet += b'\x00\x04' # RDLENGTH 4 bytes
            
            # 3. Agregar la IP (RDATA)
            packet += bytes(map(int, self.ip_address.split('.')))

            self.socket.sendto(packet, addr)

        except OSError as e:
            if e.errno != 11: # 11 es EWOULDBLOCK (sin datos), lo cual es normal
                print("DNS Server Error: {}".format(e))
                
def main():
    """Función principal"""
    global wifi_configurado, fecha_configurada
    
    print("Iniciando ESP32 Contador de Días...")
    
    # Intento robusto de inicializar pantalla
    try:
        init_lcd()
    except Exception as e:
        print("Advertencia: No se pudo iniciar LCD, continuando sin pantalla. Error: {}".format(e))

    cargar_configuracion_json()
    
    ap_ip = '192.168.4.1'
    dns_server = None

    try:
        # CREAR SIEMPRE EL ACCESS POINT (NUEVO)
        crear_access_point()
        ap_ip = network.WLAN(network.AP_IF).ifconfig()[0]
        dns_server = DNSServer(ap_ip)
        print("Servidor DNS iniciado en {}".format(ap_ip))
    except Exception as e:
        print("Error crítico iniciando Red/DNS: {}".format(e))
        # Intentar seguir aunque falle DNS

    # Intentar conectar WiFi guardado
    if ssid_guardado:
        if oled:
            try:
                oled.fill(0)
                oled.text('Conectando WiFi', 0, 0, 1)
                oled.show()
            except: pass
        
        if conectar_wifi(ssid_guardado, password_guardado):
            wifi_configurado = True
            print("WiFi conectado, pero AP sigue activo")
        else:
            print("WiFi falló, usando solo AP")
            wifi_configurado = False

    if fecha_objetivo:
        configurar_fecha_destino(fecha_objetivo)
    
    # Resto del código...
    last_update = time.time()
    
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    web_socket = socket.socket()
    web_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    web_socket.bind(addr)
    web_socket.listen(1)
    web_socket.setblocking(False)

    print("Servidor web iniciado en modo no bloqueante en http://{}/".format(ap_ip))
    
    try:
        while True:
            if dns_server:
                try:
                    dns_server.handle_request()
                except Exception as e:
                    print("Error en loop DNS: {}".format(e))

            try:
                client, addr = web_socket.accept()
                client.settimeout(2.0)
                print("Cliente web conectado desde {}".format(addr))
                manejar_request(client)
            except OSError as e:
                if e.errno != 11:
                    print("Error aceptando cliente: {}".format(e))
                pass
            except Exception as e:
                print("Error genérico en web server: {}".format(e))
            
            # Actualizar pantalla periódicamente
            if time.time() - last_update >= 1:
                try:
                    actualizar_pantalla_simple()
                except Exception as e:
                    print("Error actualizando pantalla: {}".format(e))
                last_update = time.time()
            
            if modo_display not in ["numeros_grandes", "solo_numero"]:
                try:
                    actualizar_scroll()
                except: pass
            
            time.sleep_ms(50)
                
    except KeyboardInterrupt:
        print("Deteniendo servidores...")
    finally:
        web_socket.close()
        if dns_server:
            dns_server.socket.close()

# Llamar a main al final con captura de errores global
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Si todo falla, escribir el error en un archivo para que el usuario pueda leerlo
        print("CRASH CRITICO: {}".format(e))
        with open("crash_log.txt", "w") as f:
            f.write("Error fatal: {}\n".format(e))
            import sys
            sys.print_exception(e, f)