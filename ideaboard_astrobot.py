import time
import math
import board
import busio
import digitalio
import keypad
import struct
from ideaboard import IdeaBoard
from adafruit_lsm6ds.lsm6ds3trc import LSM6DS3TRC
ib = IdeaBoard()
TX_PIN = board.IO26
RX_PIN = board.IO25
BAUD_INICIAL = 2400
BAUD_DATOS = 115200
TIMEOUT_NACK_ADVERTENCIA = 0.5
TIMEOUT_NACK_DESCONEXION = 2.0
TIEMPO_CONFIRMACION_PARADA = 0.15
uart = None
connected = False
last_nack = 0.0
advertencia_nack_mostrada = False
MODO_RUEDAS = 0
MODO_ACCESORIOS = 1
DIRECCION_ADELANTE = 0
DIRECCION_ATRAS = 1
CODIGO_GIRO_SOBRE_EJE = 7
MENSAJE_DETENER = 3
mensaje_actual = MENSAJE_DETENER
keys = keypad.Keys((board.IO0,), value_when_pressed=False, pull=True)

def boton_presionado():
 evento = keys.events.get()
 return bool(evento and evento.released)

def limpiar_eventos_boton():
 while keys.events.get() is not None:
  pass
sensor_externo_derecho = ib.DigitalIn(board.IO33, pull=ib.UP)
sensor_centro_derecho = ib.DigitalIn(board.IO32, pull=ib.UP)
sensor_centro = ib.DigitalIn(board.IO35, pull=ib.UP)
sensor_centro_izquierdo = ib.DigitalIn(board.IO34, pull=ib.UP)
sensor_externo_izquierdo = ib.DigitalIn(board.IO39, pull=ib.UP)
SENSOR_NEGRO_ES_LOW = False
CORRECCION_LINEA = 1
SIGNO_CORRECCION_LINEA = -1
MUESTRAS_CONFIRMACION_INTERSECCION = 1
MUESTRAS_LIBERACION_INTERSECCION = 3
MOSTRAR_DIAGNOSTICO_SENSORES = True
INTERVALO_DIAGNOSTICO_SENSORES = 0.3
i2c = board.I2C()
imu = LSM6DS3TRC(i2c, address=106)
offset_giroscopio_z = None
VELOCIDAD_BASE = 20
CORRECCION_MAXIMA = 3
KP_CORRECCION = 1.0
ERROR_RUMBO_MINIMO = 0.2
ZONA_MUERTA_GIRO = 0.05
SIGNO_GIROSCOPIO = 1.0
SIGNO_CORRECCION = 1
MOSTRAR_DIAGNOSTICO_CONTROL = False
INTERVALO_DIAGNOSTICO = 1.0
TOLERANCIA_ANGULO_GIRO = 1.5
VELOCIDAD_ANGULAR_DETENIDA = 1.0
TIEMPO_ESTABLE_GIRO = 0.1
TIEMPO_MAXIMO_GIRO_90 = 8.0
MOSTRAR_DIAGNOSTICO_GIRO = False
INTERVALO_DIAGNOSTICO_GIRO = 0.5
COLOR_ESPERANDO_BOTON = (0, 0, 255)
COLOR_CALIBRANDO = (255, 80, 0)
COLOR_AVANCE_HASTA = (0, 255, 0)
COLOR_REVERSA_HASTA = (0, 120, 255)
COLOR_AVANCE = (0, 255, 255)
COLOR_REVERSA = (0, 80, 255)
COLOR_GIRO = (120, 0, 255)
COLOR_DETENERSE = (255, 255, 255)
COLOR_GARRA = (255, 120, 0)
COLOR_PALA = (120, 255, 0)
COLOR_GARRA_PALA = (255, 120, 255)
COLOR_INTERSECCION_DERECHA = (255, 255, 0)
COLOR_INTERSECCION_IZQUIERDA = (255, 0, 255)
COLOR_INTERSECCION_T = (255, 0, 0)
COLOR_ERROR = (255, 0, 0)
COLOR_APAGADO = (0, 0, 0)

def limitar(valor, minimo, maximo):
 return max(minimo, min(valor, maximo))

def normalizar_angulo(angulo):
 while angulo > 180:
  angulo -= 360
 while angulo < -180:
  angulo += 360
 return angulo

def validar_segundos(segundos):
 if not isinstance(segundos, (int, float)):
  raise ValueError('segundos debe ser numerico')
 if segundos < 0:
  raise ValueError('Los segundos no pueden ser negativos')

def validar_velocidad(velocidad, nombre='velocidad'):
 if not isinstance(velocidad, int):
  raise ValueError(nombre + ' debe ser un numero entero')
 if velocidad < 0 or velocidad > 60:
  raise ValueError(nombre + ' debe estar entre 0 y 60')
 if velocidad % 10 != 0:
  raise ValueError(nombre + ' debe ser multiplo de 10')

def validar_correccion(correccion):
 if not isinstance(correccion, int):
  raise ValueError('La correccion debe ser un numero entero')
 if correccion < -3 or correccion > 3:
  raise ValueError('La correccion debe estar entre -3 y 3')

def cuantizar_correccion(correccion):
 correccion = limitar(float(correccion), -3.0, 3.0)
 magnitud = int(math.floor(abs(correccion) + 0.5))
 if correccion < 0:
  magnitud = -magnitud
 return int(limitar(magnitud, -3, 3))

def convertir_direccion(direccion):
 if direccion == DIRECCION_ADELANTE:
  return DIRECCION_ADELANTE
 if direccion == DIRECCION_ATRAS:
  return DIRECCION_ATRAS
 if isinstance(direccion, str):
  direccion = direccion.strip().lower()
  if direccion in ('adelante', 'frente', 'subir', 'abrir'):
   return DIRECCION_ADELANTE
  if direccion in ('atras', 'atrás', 'reversa', 'bajar', 'cerrar'):
   return DIRECCION_ATRAS
 raise ValueError("direccion debe ser 'adelante' o 'atras'")

def convertir_direccion_giro(direccion):
 if not isinstance(direccion, str):
  raise ValueError('direccion de giro debe ser texto')
 direccion = direccion.strip().lower()
 if direccion == 'izquierda':
  return DIRECCION_ATRAS
 if direccion == 'derecha':
  return DIRECCION_ADELANTE
 raise ValueError("direccion debe ser 'izquierda' o 'derecha'")

def direccion_giro_opuesta(direccion):
 if direccion == 'izquierda':
  return 'derecha'
 return 'izquierda'

def codificar_ruedas(velocidad_base, correccion=0, direccion='adelante'):
 validar_velocidad(velocidad_base, 'velocidad_base')
 validar_correccion(correccion)
 bit_direccion = convertir_direccion(direccion)
 indice_velocidad = velocidad_base // 10
 indice_correccion = correccion + 3
 return MODO_RUEDAS << 7 | bit_direccion << 6 | indice_velocidad << 3 | indice_correccion

def codificar_giro(direccion, velocidad_base):
 validar_velocidad(velocidad_base, 'velocidad_base')
 if velocidad_base == 0:
  raise ValueError('La velocidad del giro debe ser al menos 10')
 bit_direccion = convertir_direccion_giro(direccion)
 indice_velocidad = velocidad_base // 10
 return MODO_RUEDAS << 7 | bit_direccion << 6 | indice_velocidad << 3 | CODIGO_GIRO_SOBRE_EJE

def codificar_accesorios(velocidad_garra, velocidad_pala, direccion='adelante'):
 validar_velocidad(velocidad_garra, 'velocidad_garra')
 validar_velocidad(velocidad_pala, 'velocidad_pala')
 bit_direccion = convertir_direccion(direccion)
 indice_garra = velocidad_garra // 10
 indice_pala = velocidad_pala // 10
 return MODO_ACCESORIOS << 7 | bit_direccion << 6 | indice_garra << 3 | indice_pala

def establecer_mensaje(mensaje):
 global mensaje_actual
 if not isinstance(mensaje, int) or mensaje < 0 or mensaje > 255:
  raise ValueError('El mensaje debe ser un byte entre 0 y 255')
 mensaje_actual = mensaje

def establecer_ruedas(velocidad_base, correccion=0, direccion='adelante'):
 establecer_mensaje(codificar_ruedas(velocidad_base, correccion, direccion))

def establecer_giro(direccion, velocidad_base):
 establecer_mensaje(codificar_giro(direccion, velocidad_base))

def establecer_accesorios(velocidad_garra, velocidad_pala, direccion='adelante'):
 establecer_mensaje(codificar_accesorios(velocidad_garra, velocidad_pala, direccion))

def establecer_parada_global():
 establecer_mensaje(MENSAJE_DETENER)

def interseccion_derecha():
 ib.pixel = COLOR_INTERSECCION_DERECHA
 print('Interseccion solamente hacia la derecha.')

def interseccion_izquierda():
 ib.pixel = COLOR_INTERSECCION_IZQUIERDA
 print('Interseccion solamente hacia la izquierda.')

def interseccion_T():
 ib.pixel = COLOR_INTERSECCION_T
 print('Interseccion tipo T.')

def indicar_tipo_interseccion(tipo):
 if tipo == 'derecha':
  interseccion_derecha()
 elif tipo == 'izquierda':
  interseccion_izquierda()
 elif tipo == 'T':
  interseccion_T()
 else:
  ib.pixel = COLOR_ERROR

def checksum(data):
 c = 255
 for b in data:
  c ^= b
 return c & 255

def open_uart(baud):
 global uart
 if uart:
  uart.deinit()
 uart = busio.UART(tx=TX_PIN, rx=RX_PIN, baudrate=baud, timeout=0.005, receiver_buffer_size=64)
 time.sleep(0.05)

def send_raw(data):
 uart.write(bytes(data))

def send_msg(data):
 paquete = bytearray(data)
 paquete.append(checksum(paquete))
 send_raw(paquete)

def wait_for_hub_idle():
 global uart
 if uart:
  uart.deinit()
  uart = None
 rx = digitalio.DigitalInOut(RX_PIN)
 rx.direction = digitalio.Direction.INPUT
 tx = digitalio.DigitalInOut(TX_PIN)
 tx.direction = digitalio.Direction.OUTPUT
 tx.value = False
 idle_start = time.monotonic()
 while True:
  if rx.value is False:
   idle_start = time.monotonic()
  if time.monotonic() - idle_start > 0.1:
   break
  time.sleep(0.001)
 tx.value = True
 time.sleep(0.1)
 tx.value = False
 time.sleep(0.1)
 rx.deinit()
 tx.deinit()

def send_init_sequence():
 open_uart(BAUD_INICIAL)
 send_raw([0])
 time.sleep(0.01)
 send_msg([64, 29])
 send_msg([73, 0, 0])
 send_msg([82] + list(struct.pack('<I', BAUD_DATOS)))
 send_msg([95, 0, 0, 0, 16, 0, 0, 0, 16])
 time.sleep(0.01)
 send_msg([152, 0, 77, 79, 84, 79, 82, 0, 0, 0])
 send_msg([153, 1] + list(struct.pack('<f', 0.0)) + list(struct.pack('<f', 120.0)))
 send_msg([153, 2] + list(struct.pack('<f', 0.0)) + list(struct.pack('<f', 100.0)))
 send_msg([153, 3] + list(struct.pack('<f', 0.0)) + list(struct.pack('<f', 120.0)))
 send_msg([152, 4, 99, 109, 100, 0, 0, 0, 0, 0])
 send_msg([136, 5, 16, 0])
 send_msg([144, 128, 1, 0, 3, 0])
 send_raw([4])
 time.sleep(0.005)

def wait_for_ack():
 start = time.monotonic()
 while time.monotonic() - start < 2.0:
  data = uart.read(16)
  if data:
   print('RX init:', list(data))
   if 4 in data:
    return True
  time.sleep(0.005)
 return False

def send_control_data():
 paquete = bytearray([192, mensaje_actual & 255])
 paquete.append(checksum(paquete))
 send_raw(paquete)

def procesar_comunicacion():
 global connected
 global last_nack
 global advertencia_nack_mostrada
 data = uart.read(64)
 if data and 2 in data:
  last_nack = time.monotonic()
  advertencia_nack_mostrada = False
  send_control_data()
 demora = time.monotonic() - last_nack
 if demora > TIMEOUT_NACK_ADVERTENCIA:
  if not advertencia_nack_mostrada:
   print('Advertencia: NACK demorado.')
   advertencia_nack_mostrada = True
 if demora > TIMEOUT_NACK_DESCONEXION:
  print('Timeout NACK real. Se perdio el enlace LPF2.')
  connected = False
 return connected

def mantener_comunicacion(segundos):
 fin = time.monotonic() + segundos
 while connected and time.monotonic() < fin:
  procesar_comunicacion()
  time.sleep(0.001)
 return connected

def confirmar_parada(cambiar_color=True):
 establecer_parada_global()
 if cambiar_color:
  ib.pixel = COLOR_DETENERSE
 if not mantener_comunicacion(TIEMPO_CONFIRMACION_PARADA):
  raise RuntimeError('Se perdio el enlace al enviar la parada')

def conectar_spike():
 global connected
 global last_nack
 global mensaje_actual
 global advertencia_nack_mostrada
 connected = False
 mensaje_actual = MENSAJE_DETENER
 advertencia_nack_mostrada = False
 print('Esperando hub idle...')
 wait_for_hub_idle()
 print('Enviando inicializacion LPF2...')
 send_init_sequence()
 if not wait_for_ack():
  print('No se recibio ACK.')
  return False
 print('ACK recibido. Cambiando UART a', BAUD_DATOS)
 open_uart(BAUD_DATOS)
 connected = True
 last_nack = time.monotonic()
 return True

def leer_nivel_digital(sensor):
 return 1 if sensor.value else 0

def nivel_es_negro(nivel):
 if SENSOR_NEGRO_ES_LOW:
  return nivel == 0
 return nivel == 1

def leer_sensores_linea():
 nivel_ei = leer_nivel_digital(sensor_externo_izquierdo)
 nivel_ci = leer_nivel_digital(sensor_centro_izquierdo)
 nivel_c = leer_nivel_digital(sensor_centro)
 nivel_cd = leer_nivel_digital(sensor_centro_derecho)
 nivel_ed = leer_nivel_digital(sensor_externo_derecho)
 return (nivel_ei, nivel_ci, nivel_c, nivel_cd, nivel_ed, nivel_es_negro(nivel_ei), nivel_es_negro(nivel_ci), nivel_es_negro(nivel_c), nivel_es_negro(nivel_cd), nivel_es_negro(nivel_ed))

def correccion_desde_sensores(externo_izquierdo, centro_izquierdo, centro, centro_derecho, externo_derecho):
 if externo_izquierdo or externo_derecho:
  return None
 if centro_derecho and (not centro_izquierdo):
  return -CORRECCION_LINEA * SIGNO_CORRECCION_LINEA
 if centro_izquierdo and (not centro_derecho):
  return CORRECCION_LINEA * SIGNO_CORRECCION_LINEA
 return None

def calibrar_giroscopio(cantidad_muestras=40):
 global offset_giroscopio_z
 if cantidad_muestras <= 0:
  raise ValueError('La cantidad de muestras debe ser mayor que cero')
 establecer_parada_global()
 ib.pixel = COLOR_CALIBRANDO
 suma_z = 0.0
 print('Calibrando giroscopio. No mover el carrito.')
 for _ in range(cantidad_muestras):
  if not procesar_comunicacion():
   raise RuntimeError('Se perdio el enlace durante la calibracion')
  _, _, gz = imu.gyro
  suma_z += math.degrees(gz)
  time.sleep(0.003)
 offset_giroscopio_z = suma_z / cantidad_muestras
 print('Offset Z:', offset_giroscopio_z, 'grados/s')
 return offset_giroscopio_z

def actualizar_rumbo(rumbo_actual, tiempo_anterior):
 if offset_giroscopio_z is None:
  raise RuntimeError('El giroscopio no ha sido calibrado')
 tiempo_actual = time.monotonic()
 dt = tiempo_actual - tiempo_anterior
 if dt <= 0 or dt > 0.1:
  return (rumbo_actual, tiempo_actual, 0.0)
 _, _, gz = imu.gyro
 velocidad_angular_z = math.degrees(gz)
 velocidad_angular_z -= offset_giroscopio_z
 velocidad_angular_z *= SIGNO_GIROSCOPIO
 if abs(velocidad_angular_z) < ZONA_MUERTA_GIRO:
  velocidad_angular_z = 0.0
 rumbo_actual += velocidad_angular_z * dt
 rumbo_actual = normalizar_angulo(rumbo_actual)
 return (rumbo_actual, tiempo_actual, velocidad_angular_z)

def calcular_correccion_giroscopio(rumbo_actual, rumbo_objetivo):
 error_rumbo = normalizar_angulo(rumbo_objetivo - rumbo_actual)
 if abs(error_rumbo) < ERROR_RUMBO_MINIMO:
  return (0, error_rumbo)
 correccion_continua = KP_CORRECCION * error_rumbo * SIGNO_CORRECCION
 correccion = cuantizar_correccion(correccion_continua)
 if correccion == 0:
  correccion = 2 if correccion_continua > 0 else -2
 return (correccion, error_rumbo)

def convertir_correccion_a_direccion(correccion_logica, direccion_movimiento):
 bit_direccion = convertir_direccion(direccion_movimiento)
 if bit_direccion == DIRECCION_ATRAS:
  return -correccion_logica
 return correccion_logica

def aplicar_control_rumbo(rumbo_actual, rumbo_objetivo, velocidad_base, direccion_movimiento, tiempo_anterior, correccion_infrarroja=None):
 rumbo_actual, tiempo_actual, velocidad_angular_z = actualizar_rumbo(rumbo_actual, tiempo_anterior)
 correccion_gyro, error_rumbo = calcular_correccion_giroscopio(rumbo_actual, rumbo_objetivo)
 if correccion_infrarroja is None:
  correccion_logica = correccion_gyro
  fuente = 'giroscopio'
 else:
  correccion_logica = correccion_infrarroja
  fuente = 'infrarrojo'
 correccion_enviada = convertir_correccion_a_direccion(correccion_logica, direccion_movimiento)
 establecer_ruedas(velocidad_base, correccion_enviada, direccion=direccion_movimiento)
 return (rumbo_actual, tiempo_actual, correccion_logica, correccion_enviada, error_rumbo, velocidad_angular_z, fuente)

def _mover_tiempo_con_giroscopio(segundos, velocidad_base, direccion_movimiento, color_led):
 validar_segundos(segundos)
 validar_velocidad(velocidad_base, 'velocidad_base')
 if velocidad_base == 0:
  detenerse(segundos)
  return
 if offset_giroscopio_z is None:
  raise RuntimeError('El giroscopio no ha sido calibrado')
 ib.pixel = color_led
 rumbo_actual = 0.0
 rumbo_objetivo = 0.0
 tiempo_anterior = time.monotonic()
 fin = tiempo_anterior + segundos
 establecer_ruedas(velocidad_base, 0, direccion=direccion_movimiento)
 try:
  while connected and time.monotonic() < fin:
   if not procesar_comunicacion():
    raise RuntimeError('Se perdio el enlace durante el movimiento')
   rumbo_actual, tiempo_anterior, _, _, _, _, _ = aplicar_control_rumbo(rumbo_actual, rumbo_objetivo, velocidad_base, direccion_movimiento, tiempo_anterior, correccion_infrarroja=None)
   if not procesar_comunicacion():
    raise RuntimeError('Se perdio el enlace durante el movimiento')
   time.sleep(0.001)
 except Exception:
  establecer_parada_global()
  if connected:
   mantener_comunicacion(TIEMPO_CONFIRMACION_PARADA)
  raise
 confirmar_parada(cambiar_color=True)

def avance(segundos, velocidad):
 _mover_tiempo_con_giroscopio(segundos, velocidad, DIRECCION_ADELANTE, COLOR_AVANCE)

def reversa(segundos, velocidad):
 _mover_tiempo_con_giroscopio(segundos, velocidad, DIRECCION_ATRAS, COLOR_REVERSA)

def detenerse(segundos):
 validar_segundos(segundos)
 establecer_parada_global()
 ib.pixel = COLOR_DETENERSE
 if not mantener_comunicacion(segundos):
  raise RuntimeError('Se perdio el enlace durante detenerse()')

def ejecutar_accesorios(segundos, velocidad_garra, velocidad_pala, direccion='adelante', color_led=COLOR_GARRA_PALA):
 validar_segundos(segundos)
 establecer_accesorios(velocidad_garra, velocidad_pala, direccion)
 ib.pixel = color_led
 if not mantener_comunicacion(segundos):
  establecer_parada_global()
  raise RuntimeError('Se perdio el enlace durante accesorios')
 confirmar_parada(cambiar_color=True)

def mover_garra(segundos, velocidad, direccion='adelante'):
 ejecutar_accesorios(segundos, velocidad_garra=velocidad, velocidad_pala=0, direccion=direccion, color_led=COLOR_GARRA)

def mover_pala(segundos, velocidad, direccion='adelante'):
 ejecutar_accesorios(segundos, velocidad_garra=0, velocidad_pala=velocidad, direccion=direccion, color_led=COLOR_PALA)

def mover_garra_pala(segundos, velocidad_garra, velocidad_pala, direccion='adelante'):
 ejecutar_accesorios(segundos, velocidad_garra, velocidad_pala, direccion, color_led=COLOR_GARRA_PALA)

def calcular_velocidad_giro(error_angulo, velocidad_base):
 error_angulo = abs(error_angulo)
 if error_angulo > 35:
  return velocidad_base
 if error_angulo > 15:
  return min(velocidad_base, 20)
 return 10

def girar(direccion, angulo, velocidad_base):
 if offset_giroscopio_z is None:
  raise RuntimeError('El giroscopio no ha sido calibrado')
 if not isinstance(direccion, str):
  raise ValueError('direccion debe ser texto')
 direccion = direccion.strip().lower()
 convertir_direccion_giro(direccion)
 if not isinstance(angulo, (int, float)):
  raise ValueError('angulo debe ser numerico')
 if angulo <= 0 or angulo > 360:
  raise ValueError('angulo debe estar entre 0 y 360 grados')
 validar_velocidad(velocidad_base, 'velocidad_base')
 if velocidad_base == 0:
  raise ValueError('velocidad_base debe ser al menos 10')
 ib.pixel = COLOR_GIRO
 tiempo_inicio = time.monotonic()
 tiempo_anterior = tiempo_inicio
 ultimo_diagnostico = 0.0
 tiempo_estable = None
 factor_velocidad = max(1.0, 30.0 / velocidad_base)
 tiempo_maximo = max(5.0, angulo / 90.0 * TIEMPO_MAXIMO_GIRO_90 * factor_velocidad)
 angulo_medido = 0.0
 direccion_actual = direccion
 comando_detenido = False
 establecer_giro(direccion_actual, velocidad_base)
 print('Girando', direccion, '| Angulo objetivo:', angulo, '| Velocidad:', velocidad_base)
 try:
  while True:
   if not procesar_comunicacion():
    raise RuntimeError('Se perdio el enlace durante girar()')
   tiempo_actual = time.monotonic()
   dt = tiempo_actual - tiempo_anterior
   tiempo_anterior = tiempo_actual
   _, _, gz = imu.gyro
   velocidad_angular_z = (math.degrees(gz) - offset_giroscopio_z) * SIGNO_GIROSCOPIO
   if abs(velocidad_angular_z) < ZONA_MUERTA_GIRO:
    velocidad_angular_z = 0.0
   if 0 < dt <= 0.1:
    incremento = abs(velocidad_angular_z) * dt
    if direccion_actual == direccion:
     angulo_medido += incremento
    else:
     angulo_medido -= incremento
   error_angulo = angulo - angulo_medido
   if MOSTRAR_DIAGNOSTICO_GIRO:
    if tiempo_actual - ultimo_diagnostico >= INTERVALO_DIAGNOSTICO_GIRO:
     print('Giro:', direccion_actual, '| GZ:', round(velocidad_angular_z, 2), '| Angulo:', round(angulo_medido, 2), '| Error:', round(error_angulo, 2), '| Byte:', mensaje_actual)
     ultimo_diagnostico = tiempo_actual
   if abs(error_angulo) <= TOLERANCIA_ANGULO_GIRO:
    if not comando_detenido:
     establecer_parada_global()
     comando_detenido = True
     tiempo_estable = None
    if abs(velocidad_angular_z) <= VELOCIDAD_ANGULAR_DETENIDA:
     if tiempo_estable is None:
      tiempo_estable = tiempo_actual
     elif tiempo_actual - tiempo_estable >= TIEMPO_ESTABLE_GIRO:
      if abs(angulo - angulo_medido) <= TOLERANCIA_ANGULO_GIRO:
       break
      comando_detenido = False
      tiempo_estable = None
    else:
     tiempo_estable = None
   else:
    tiempo_estable = None
    if error_angulo > 0:
     nueva_direccion = direccion
    else:
     nueva_direccion = direccion_giro_opuesta(direccion)
    velocidad_giro = calcular_velocidad_giro(error_angulo, velocidad_base)
    direccion_actual = nueva_direccion
    establecer_giro(direccion_actual, velocidad_giro)
    comando_detenido = False
   if not procesar_comunicacion():
    raise RuntimeError('Se perdio el enlace durante girar()')
   if tiempo_actual - tiempo_inicio > tiempo_maximo:
    raise RuntimeError('Tiempo maximo excedido durante girar(); ultimo angulo medido: ' + str(round(angulo_medido, 2)))
   time.sleep(0.001)
 except Exception:
  establecer_parada_global()
  if connected:
   mantener_comunicacion(TIEMPO_CONFIRMACION_PARADA)
  raise
 confirmar_parada(cambiar_color=True)
 print('Giro terminado', '| Objetivo:', angulo, '| Medido:', round(angulo_medido, 2))
 return angulo_medido

def clasificar_interseccion(externo_izquierdo_visto, externo_derecho_visto):
 if externo_izquierdo_visto and externo_derecho_visto:
  return 'T'
 if externo_izquierdo_visto:
  return 'izquierda'
 if externo_derecho_visto:
  return 'derecha'
 return 'desconocida'

def _mover_hasta_interseccion(numero_interseccion, velocidad_base, direccion_movimiento):
 if not isinstance(numero_interseccion, int):
  raise ValueError('numero_interseccion debe ser entero')
 if numero_interseccion <= 0:
  raise ValueError('numero_interseccion debe ser mayor que cero')
 validar_velocidad(velocidad_base, 'velocidad_base')
 if velocidad_base == 0:
  raise ValueError('velocidad_base debe ser al menos 10')
 if offset_giroscopio_z is None:
  raise RuntimeError('El giroscopio no ha sido calibrado')
 bit_direccion = convertir_direccion(direccion_movimiento)
 es_reversa = bit_direccion == DIRECCION_ATRAS
 rumbo_actual = 0.0
 rumbo_objetivo = 0.0
 tiempo_anterior = time.monotonic()
 ultimo_diagnostico_sensores = 0.0
 contador_intersecciones = 0
 tipo_interseccion = None
 muestras_interseccion = 0
 muestras_liberacion = 0
 interseccion_activa = False
 externo_derecho_visto = False
 externo_izquierdo_visto = False
 nivel_ei, nivel_ci, nivel_c, nivel_cd, nivel_ed, ext_izq, cen_izq, centro, cen_der, ext_der = leer_sensores_linea()
 interseccion_activa = False
 if es_reversa:
  ib.pixel = COLOR_REVERSA_HASTA
  texto_movimiento = 'Reversa'
 else:
  ib.pixel = COLOR_AVANCE_HASTA
  texto_movimiento = 'Avance'
 establecer_ruedas(velocidad_base, 0, direccion=bit_direccion)
 print(texto_movimiento, 'hasta la interseccion', numero_interseccion, '| Velocidad base:', velocidad_base)
 try:
  while contador_intersecciones < numero_interseccion:
   if not procesar_comunicacion():
    raise RuntimeError('Se perdio la conexion durante ' + ('reversa_hasta()' if es_reversa else 'avance_hasta()'))
   nivel_ei, nivel_ci, nivel_c, nivel_cd, nivel_ed, ext_izq, cen_izq, centro, cen_der, ext_der = leer_sensores_linea()
   ahora = time.monotonic()
   if MOSTRAR_DIAGNOSTICO_SENSORES:
    if ahora - ultimo_diagnostico_sensores >= INTERVALO_DIAGNOSTICO_SENSORES:
     print('Sensores: {}{}{}{}{} '.format(nivel_ei, nivel_ci, nivel_c, nivel_cd, nivel_ed).replace('0', '-').replace('1', '▤'))
     ultimo_diagnostico_sensores = ahora
   interseccion_confirmada = False
   if interseccion_activa:
    if not ext_der and (not ext_izq):
     muestras_liberacion += 1
     if muestras_liberacion >= MUESTRAS_LIBERACION_INTERSECCION:
      interseccion_activa = False
      muestras_liberacion = 0
      muestras_interseccion = 0
      externo_derecho_visto = False
      externo_izquierdo_visto = False
      ib.pixel = COLOR_REVERSA_HASTA if es_reversa else COLOR_AVANCE_HASTA
    else:
     muestras_liberacion = 0
   elif ext_der or ext_izq:
    muestras_interseccion += 1
    externo_derecho_visto = externo_derecho_visto or ext_der
    externo_izquierdo_visto = externo_izquierdo_visto or ext_izq
    if muestras_interseccion >= MUESTRAS_CONFIRMACION_INTERSECCION:
     interseccion_confirmada = True
     interseccion_activa = True
     muestras_interseccion = 0
     muestras_liberacion = 0
     contador_intersecciones += 1
     tipo_interseccion = clasificar_interseccion(externo_izquierdo_visto, externo_derecho_visto)
     indicar_tipo_interseccion(tipo_interseccion)
     print('Interseccion:', contador_intersecciones, '| Tipo:', tipo_interseccion, '| Movimiento:', 'reversa' if es_reversa else 'avance')
     print('Sensores: {}{}{}{}{} '.format(nivel_ei, nivel_ci, nivel_c, nivel_cd, nivel_ed).replace('0', '-').replace('1', '▤'))
   else:
    muestras_interseccion = 0
    externo_derecho_visto = False
    externo_izquierdo_visto = False
   if interseccion_confirmada and contador_intersecciones >= numero_interseccion:
    confirmar_parada(cambiar_color=False)
    return tipo_interseccion
   correccion_ir = correccion_desde_sensores(ext_izq, cen_izq, centro, cen_der, ext_der)
   rumbo_actual, tiempo_anterior, correccion_logica, correccion_enviada, error_rumbo, velocidad_angular_z, fuente = aplicar_control_rumbo(rumbo_actual, rumbo_objetivo, velocidad_base, bit_direccion, tiempo_anterior, correccion_infrarroja=correccion_ir)
   if MOSTRAR_DIAGNOSTICO_CONTROL:
    print('Fuente:', fuente, '| Error gyro:', round(error_rumbo, 2), '| Correccion logica:', correccion_logica, '| Correccion enviada:', correccion_enviada)
   if not procesar_comunicacion():
    raise RuntimeError('Se perdio la conexion durante ' + ('reversa_hasta()' if es_reversa else 'avance_hasta()'))
   time.sleep(0.001)
 except Exception:
  establecer_parada_global()
  if connected:
   mantener_comunicacion(TIEMPO_CONFIRMACION_PARADA)
  raise
 confirmar_parada(cambiar_color=False)
 return tipo_interseccion

def avance_hasta(numero_interseccion, velocidad_base=VELOCIDAD_BASE):
 return _mover_hasta_interseccion(numero_interseccion, velocidad_base, DIRECCION_ADELANTE)

def reversa_hasta(numero_interseccion, velocidad_base=VELOCIDAD_BASE):
 return _mover_hasta_interseccion(numero_interseccion, velocidad_base, DIRECCION_ATRAS)

def esperar_boton_inicio():
 establecer_parada_global()
 limpiar_eventos_boton()
 ib.pixel = COLOR_ESPERANDO_BOTON
 print('Handshake completado.')
 print('Presione y suelte el boton BOOT para iniciar.')
 while connected:
  if not procesar_comunicacion():
   return False
  if boton_presionado():
   if not mantener_comunicacion(0.05):
    return False
   return True
  time.sleep(0.001)
 return False
__all__ = ('avance', 'reversa', 'detenerse', 'girar', 'avance_hasta', 'reversa_hasta', 'mover_garra', 'mover_pala', 'mover_garra_pala', 'calibrar_giroscopio', 'iniciar')

def iniciar(programa_usuario):
 global connected
 print('Iniciando biblioteca LPF2: ruedas, garra, pala y 5 sensores...')
 while True:
  if not conectar_spike():
   ib.pixel = COLOR_ERROR
   time.sleep(1.0)
   continue
  while connected:
   try:
    if not esperar_boton_inicio():
     break
    calibrar_giroscopio()
    programa_usuario()
    confirmar_parada(cambiar_color=True)
    print('Secuencia finalizada.')
   except KeyboardInterrupt:
    establecer_parada_global()
    ib.pixel = COLOR_APAGADO
    if connected:
     mantener_comunicacion(TIEMPO_CONFIRMACION_PARADA)
    raise
   except Exception as error:
    establecer_parada_global()
    ib.pixel = COLOR_ERROR
    if connected:
     mantener_comunicacion(TIEMPO_CONFIRMACION_PARADA)
     print('Error:', error)
     print('El enlace LPF2 sigue activo. Se vuelve a esperar el boton.')
     continue
    print('Error:', error)
    print('Enlace perdido; se realizara un nuevo handshake.')
    break