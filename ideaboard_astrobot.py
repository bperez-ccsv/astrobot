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
_u = None
_c = False
_n = 0.0
_w = False
MODO_RUEDAS = 0
MODO_ACCESORIOS = 1
DIRECCION_ADELANTE = 0
DIRECCION_ATRAS = 1
CODIGO_GIRO_SOBRE_EJE = 7
MENSAJE_DETENER = 3
_m = MENSAJE_DETENER
keys = keypad.Keys((board.IO0,), value_when_pressed=False, pull=True)

def _a():
 evento = keys.events.get()
 return bool(evento and evento.released)

def _b():
 while keys.events.get() is not None:
  pass
sensor_externo_derecho = ib.DigitalIn(board.IO33, pull=ib.UP)
sensor_centro_derecho = ib.DigitalIn(board.IO32, pull=ib.UP)
sensor_centro = ib.DigitalIn(board.IO35, pull=ib.UP)
sensor_centro_izquierdo = ib.DigitalIn(board.IO34, pull=ib.UP)
sensor_externo_izquierdo = ib.DigitalIn(board.IO39, pull=ib.UP)
SENSOR_NEGRO_ES_LOW = False
CORRECCION_LINEA = 1
SIGNO_CORRECCION_LINEA = 1
MUESTRAS_CONFIRMACION_INTERSECCION = 1
MUESTRAS_LIBERACION_INTERSECCION = 3
MOSTRAR_DIAGNOSTICO_SENSORES = True
INTERVALO_DIAGNOSTICO_SENSORES = 0.3
i2c = board.I2C()
imu = LSM6DS3TRC(i2c, address=106)
_o = None
VELOCIDAD_BASE = 20
CIRCUNFERENCIA_RUEDA_CM = 17.6
CONTROL_DISTANCIA_INICIO = 255
CONTROL_DISTANCIA_PAUSA = 247
CONTROL_DISTANCIA_REANUDAR = 239
CONTROL_DISTANCIA_CANCELAR = 231
TIEMPO_PAQUETE_DISTANCIA = 0.1
MAX_GRADOS_DISTANCIA = (1 << 18) - 1
FACTOR_ESPERA_DISTANCIA = 1.25
MARGEN_ESPERA_DISTANCIA = 0.4
CORRECCION_MAXIMA = 3
KP_CORRECCION = 1.0
ERROR_RUMBO_MINIMO = 0.2
ZONA_MUERTA_GIRO = 0.05
SIGNO_GIROSCOPIO = 1.0
SIGNO_CORRECCION = 1
MOSTRAR_DIAGNOSTICO_CONTROL = False
INTERVALO_DIAGNOSTICO = 1.0
TOLERANCIA_ANGULO_GIRO = 1.5
VELOCIDAD_ANGULAR_DETENIDA = 3.0
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
COLOR_PAUSA = (255, 255, 0)

def _c(valor, minimo, maximo):
 return max(minimo, min(valor, maximo))

def _d(angulo):
 while angulo > 180:
  angulo -= 360
 while angulo < -180:
  angulo += 360
 return angulo

def _e(segundos):
 if not isinstance(segundos, (int, float)):
  raise ValueError('segundos debe ser numerico')
 if segundos < 0:
  raise ValueError('Los segundos no pueden ser negativos')

def _f(velocidad, nombre='velocidad'):
 if not isinstance(velocidad, int):
  raise ValueError(nombre + ' debe ser un numero entero')
 if velocidad < 0 or velocidad > 60:
  raise ValueError(nombre + ' debe estar entre 0 y 60')
 if velocidad % 10 != 0:
  raise ValueError(nombre + ' debe ser multiplo de 10')

def _g(correccion):
 if not isinstance(correccion, int):
  raise ValueError('La correccion debe ser un numero entero')
 if correccion < -3 or correccion > 3:
  raise ValueError('La correccion debe estar entre -3 y 3')

def _h(correccion):
 correccion = _c(float(correccion), -3.0, 3.0)
 magnitud = int(math.floor(abs(correccion) + 0.5))
 if correccion < 0:
  magnitud = -magnitud
 return int(_c(magnitud, -3, 3))

def _i(direccion):
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

def _j(direccion):
 if not isinstance(direccion, str):
  raise ValueError('direccion de giro debe ser texto')
 direccion = direccion.strip().lower()
 if direccion == 'izquierda':
  return DIRECCION_ATRAS
 if direccion == 'derecha':
  return DIRECCION_ADELANTE
 raise ValueError("direccion debe ser 'izquierda' o 'derecha'")

def _k(direccion):
 if direccion == 'izquierda':
  return 'derecha'
 return 'izquierda'

def _l(velocidad_base, correccion=0, direccion='adelante'):
 _f(velocidad_base, 'velocidad_base')
 _g(correccion)
 bit_direccion = _i(direccion)
 indice_velocidad = velocidad_base // 10
 indice_correccion = correccion + 3
 return MODO_RUEDAS << 7 | bit_direccion << 6 | indice_velocidad << 3 | indice_correccion

def _m(direccion, velocidad_base):
 _f(velocidad_base, 'velocidad_base')
 if velocidad_base == 0:
  raise ValueError('La velocidad del giro debe ser al menos 10')
 bit_direccion = _j(direccion)
 indice_velocidad = velocidad_base // 10
 return MODO_RUEDAS << 7 | bit_direccion << 6 | indice_velocidad << 3 | CODIGO_GIRO_SOBRE_EJE

def _n(velocidad_garra, velocidad_pala, direccion='adelante'):
 _f(velocidad_garra, 'velocidad_garra')
 _f(velocidad_pala, 'velocidad_pala')
 bit_direccion = _i(direccion)
 indice_garra = velocidad_garra // 10
 indice_pala = velocidad_pala // 10
 return MODO_ACCESORIOS << 7 | bit_direccion << 6 | indice_garra << 3 | indice_pala

def _o(mensaje):
 global _m
 if not isinstance(mensaje, int) or mensaje < 0 or mensaje > 255:
  raise ValueError('El mensaje debe ser un byte entre 0 y 255')
 _m = mensaje

def _p(velocidad_base, correccion=0, direccion='adelante'):
 _o(_l(velocidad_base, correccion, direccion))

def _q(direccion, velocidad_base):
 _o(_m(direccion, velocidad_base))

def _r(velocidad_garra, velocidad_pala, direccion='adelante'):
 _o(_n(velocidad_garra, velocidad_pala, direccion))

def _s():
 _o(MENSAJE_DETENER)

def interseccion_derecha():
 ib.pixel = COLOR_INTERSECCION_DERECHA
 print('Interseccion solamente hacia la derecha.')

def interseccion_izquierda():
 ib.pixel = COLOR_INTERSECCION_IZQUIERDA
 print('Interseccion solamente hacia la izquierda.')

def interseccion_T():
 ib.pixel = COLOR_INTERSECCION_T
 print('Interseccion tipo T.')

def _t(tipo):
 if tipo == 'derecha':
  interseccion_derecha()
 elif tipo == 'izquierda':
  interseccion_izquierda()
 elif tipo == 'T':
  interseccion_T()
 else:
  ib.pixel = COLOR_ERROR

def _u(data):
 c = 255
 for b in data:
  c ^= b
 return c & 255

def _v(baud):
 global _u
 if _u:
  _u.deinit()
 _u = busio.UART(tx=TX_PIN, rx=RX_PIN, baudrate=baud, timeout=0.005, receiver_buffer_size=64)
 time.sleep(0.05)

def _w(data):
 _u.write(bytes(data))

def _x(data):
 paquete = bytearray(data)
 paquete.append(_u(paquete))
 _w(paquete)

def _y():
 global _u
 if _u:
  _u.deinit()
  _u = None
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

def _z():
 _v(BAUD_INICIAL)
 _w([0])
 time.sleep(0.01)
 _x([64, 29])
 _x([73, 0, 0])
 _x([82] + list(struct.pack('<I', BAUD_DATOS)))
 _x([95, 0, 0, 0, 16, 0, 0, 0, 16])
 time.sleep(0.01)
 _x([152, 0, 77, 79, 84, 79, 82, 0, 0, 0])
 _x([153, 1] + list(struct.pack('<f', 0.0)) + list(struct.pack('<f', 120.0)))
 _x([153, 2] + list(struct.pack('<f', 0.0)) + list(struct.pack('<f', 100.0)))
 _x([153, 3] + list(struct.pack('<f', 0.0)) + list(struct.pack('<f', 120.0)))
 _x([152, 4, 99, 109, 100, 0, 0, 0, 0, 0])
 _x([136, 5, 16, 0])
 _x([144, 128, 1, 0, 3, 0])
 _w([4])
 time.sleep(0.005)

def _A():
 start = time.monotonic()
 while time.monotonic() - start < 2.0:
  data = _u.read(16)
  if data:
   print('RX init:', list(data))
   if 4 in data:
    return True
  time.sleep(0.005)
 return False

def _B():
 paquete = bytearray([192, _m & 255])
 paquete.append(_u(paquete))
 _w(paquete)

def _C():
 global _c
 global _n
 global _w
 data = _u.read(64)
 if data and 2 in data:
  _n = time.monotonic()
  _w = False
  _B()
 demora = time.monotonic() - _n
 if demora > TIMEOUT_NACK_ADVERTENCIA:
  if not _w:
   print('Advertencia: NACK demorado.')
   _w = True
 if demora > TIMEOUT_NACK_DESCONEXION:
  print('Timeout NACK real. Se perdio el enlace LPF2.')
  _c = False
 return _c

def _D(segundos):
 fin = time.monotonic() + segundos
 while _c and time.monotonic() < fin:
  _C()
  time.sleep(0.001)
 return _c

def _E(color_reanudar):
 if not _a():
  return 0.0
 mensaje_reanudar = _m
 inicio_pausa = time.monotonic()
 _s()
 ib.pixel = COLOR_PAUSA
 print('Programa pausado. Presione BOOT para continuar.')
 while _c:
  if not _C():
   raise RuntimeError('Se perdio el enlace durante la pausa')
  if _a():
   _o(mensaje_reanudar)
   ib.pixel = color_reanudar
   print('Programa reanudado.')
   return time.monotonic() - inicio_pausa
  time.sleep(0.001)
 raise RuntimeError('Se perdio el enlace durante la pausa')

def _F(segundos, color_reanudar):
 fin = time.monotonic() + segundos
 while _c and time.monotonic() < fin:
  if not _C():
   return False
  duracion_pausa = _E(color_reanudar)
  if duracion_pausa > 0:
   fin += duracion_pausa
  time.sleep(0.001)
 return _c

def _G(cambiar_color=True):
 _s()
 if cambiar_color:
  ib.pixel = COLOR_DETENERSE
 if not _D(TIEMPO_CONFIRMACION_PARADA):
  raise RuntimeError('Se perdio el enlace al enviar la parada')

def _H():
 global _c
 global _n
 global _m
 global _w
 _c = False
 _m = MENSAJE_DETENER
 _w = False
 print('Esperando hub idle...')
 _y()
 print('Enviando inicializacion LPF2...')
 _z()
 if not _A():
  print('No se recibio ACK.')
  return False
 print('ACK recibido. Cambiando UART a', BAUD_DATOS)
 _v(BAUD_DATOS)
 _c = True
 _n = time.monotonic()
 return True

def _I(sensor):
 return 1 if sensor.value else 0

def _J(nivel):
 if SENSOR_NEGRO_ES_LOW:
  return nivel == 0
 return nivel == 1

def _K():
 nivel_ei = _I(sensor_externo_izquierdo)
 nivel_ci = _I(sensor_centro_izquierdo)
 nivel_c = _I(sensor_centro)
 nivel_cd = _I(sensor_centro_derecho)
 nivel_ed = _I(sensor_externo_derecho)
 return (nivel_ei, nivel_ci, nivel_c, nivel_cd, nivel_ed, _J(nivel_ei), _J(nivel_ci), _J(nivel_c), _J(nivel_cd), _J(nivel_ed))

def _L(externo_izquierdo, centro_izquierdo, centro, centro_derecho, externo_derecho):
 if externo_izquierdo or externo_derecho:
  return None
 if centro_derecho and (not centro_izquierdo):
  return -CORRECCION_LINEA * SIGNO_CORRECCION_LINEA
 if centro_izquierdo and (not centro_derecho):
  return CORRECCION_LINEA * SIGNO_CORRECCION_LINEA
 return None

def calibrar_giroscopio(cantidad_muestras=40):
 global _o
 if cantidad_muestras <= 0:
  raise ValueError('La cantidad de muestras debe ser mayor que cero')
 _s()
 ib.pixel = COLOR_CALIBRANDO
 suma_z = 0.0
 print('Calibrando giroscopio. No mover el carrito.')
 for _ in range(cantidad_muestras):
  if not _C():
   raise RuntimeError('Se perdio el enlace durante la calibracion')
  _, _, gz = imu.gyro
  suma_z += math.degrees(gz)
  time.sleep(0.003)
 _o = suma_z / cantidad_muestras
 print('Offset Z:', _o, 'grados/s')
 return _o

def _M(rumbo_actual, tiempo_anterior):
 if _o is None:
  raise RuntimeError('El giroscopio no ha sido calibrado')
 tiempo_actual = time.monotonic()
 dt = tiempo_actual - tiempo_anterior
 if dt <= 0 or dt > 0.1:
  return (rumbo_actual, tiempo_actual, 0.0)
 _, _, gz = imu.gyro
 velocidad_angular_z = math.degrees(gz)
 velocidad_angular_z -= _o
 velocidad_angular_z *= SIGNO_GIROSCOPIO
 if abs(velocidad_angular_z) < ZONA_MUERTA_GIRO:
  velocidad_angular_z = 0.0
 rumbo_actual += velocidad_angular_z * dt
 rumbo_actual = _d(rumbo_actual)
 return (rumbo_actual, tiempo_actual, velocidad_angular_z)

def _N(rumbo_actual, rumbo_objetivo):
 error_rumbo = _d(rumbo_objetivo - rumbo_actual)
 if abs(error_rumbo) < ERROR_RUMBO_MINIMO:
  return (0, error_rumbo)
 correccion_continua = KP_CORRECCION * error_rumbo * SIGNO_CORRECCION
 correccion = _h(correccion_continua)
 if correccion == 0:
  correccion = 2 if correccion_continua > 0 else -2
 return (correccion, error_rumbo)

def _O(correccion_logica, direccion_movimiento):
 bit_direccion = _i(direccion_movimiento)
 if bit_direccion == DIRECCION_ATRAS:
  return -correccion_logica
 return correccion_logica

def _P(rumbo_actual, rumbo_objetivo, velocidad_base, direccion_movimiento, tiempo_anterior, correccion_infrarroja=None):
 rumbo_actual, tiempo_actual, velocidad_angular_z = _M(rumbo_actual, tiempo_anterior)
 correccion_gyro, error_rumbo = _N(rumbo_actual, rumbo_objetivo)
 if correccion_infrarroja is None:
  correccion_logica = correccion_gyro
  fuente = 'giroscopio'
 else:
  correccion_logica = correccion_infrarroja
  fuente = 'infrarrojo'
 correccion_enviada = _O(correccion_logica, direccion_movimiento)
 _p(velocidad_base, correccion_enviada, direccion=direccion_movimiento)
 return (rumbo_actual, tiempo_actual, correccion_logica, correccion_enviada, error_rumbo, velocidad_angular_z, fuente)

def _Q(segundos, velocidad_base, direccion_movimiento, color_led):
 _e(segundos)
 _f(velocidad_base, 'velocidad_base')
 if velocidad_base == 0:
  detenerse(segundos)
  return
 if _o is None:
  raise RuntimeError('El giroscopio no ha sido calibrado')
 ib.pixel = color_led
 rumbo_actual = 0.0
 rumbo_objetivo = 0.0
 tiempo_anterior = time.monotonic()
 fin = tiempo_anterior + segundos
 _p(velocidad_base, 0, direccion=direccion_movimiento)
 try:
  while _c and time.monotonic() < fin:
   if not _C():
    raise RuntimeError('Se perdio el enlace durante el movimiento')
   duracion_pausa = _E(color_led)
   if duracion_pausa > 0:
    fin += duracion_pausa
    tiempo_anterior = time.monotonic()
    continue
   rumbo_actual, tiempo_anterior, _, _, _, _, _ = _P(rumbo_actual, rumbo_objetivo, velocidad_base, direccion_movimiento, tiempo_anterior, correccion_infrarroja=None)
   if not _C():
    raise RuntimeError('Se perdio el enlace durante el movimiento')
   time.sleep(0.001)
 except Exception:
  _s()
  if _c:
   _D(TIEMPO_CONFIRMACION_PARADA)
  raise
 _G(cambiar_color=True)

def avance(segundos, velocidad):
 _Q(segundos, velocidad, DIRECCION_ADELANTE, COLOR_AVANCE)

def reversa(segundos, velocidad):
 _Q(segundos, velocidad, DIRECCION_ATRAS, COLOR_REVERSA)

def detenerse(segundos):
 _e(segundos)
 _s()
 ib.pixel = COLOR_DETENERSE
 if not _F(segundos, COLOR_DETENERSE):
  raise RuntimeError('Se perdio el enlace durante detenerse()')

def _R(distancia_cm):
 if not isinstance(distancia_cm, (int, float)):
  raise ValueError('distancia_cm debe ser numerica')
 if distancia_cm <= 0:
  raise ValueError('distancia_cm debe ser mayor que cero')
 if CIRCUNFERENCIA_RUEDA_CM <= 0:
  raise ValueError('CIRCUNFERENCIA_RUEDA_CM debe ser mayor que cero')

def _S(nibble):
 return 128 | (nibble & 15) << 3 | 7

def _T(direccion, velocidad, grados_objetivo):
 bit_direccion = _i(direccion)
 indice_velocidad = velocidad // 10
 metadata = bit_direccion << 3 | indice_velocidad
 paquetes = [CONTROL_DISTANCIA_INICIO, _S(metadata)]
 toggle = 1 - bit_direccion
 for desplazamiento in (15, 12, 9, 6, 3, 0):
  bloque = grados_objetivo >> desplazamiento & 7
  nibble = toggle << 3 | bloque
  paquetes.append(_S(nibble))
  toggle = 1 - toggle
 return paquetes

def _U(paquete):
 _o(paquete)
 if not _D(TIEMPO_PAQUETE_DISTANCIA):
  raise RuntimeError('Se perdio el enlace enviando distancia')

def _V(color_reanudar):
 if not _a():
  return 0.0
 inicio = time.monotonic()
 _U(CONTROL_DISTANCIA_PAUSA)
 ib.pixel = COLOR_PAUSA
 print('Movimiento por distancia pausado.')
 while _c:
  if not _C():
   raise RuntimeError('Se perdio el enlace durante la pausa')
  if _a():
   _U(CONTROL_DISTANCIA_REANUDAR)
   ib.pixel = color_reanudar
   print('Movimiento por distancia reanudado.')
   return time.monotonic() - inicio
  time.sleep(0.001)
 raise RuntimeError('Se perdio el enlace durante la pausa')

def _W(distancia_cm, velocidad, direccion, color_led):
 _R(distancia_cm)
 _f(velocidad, 'velocidad')
 if velocidad == 0:
  raise ValueError('velocidad debe ser al menos 10')
 rotaciones = distancia_cm / CIRCUNFERENCIA_RUEDA_CM
 grados_objetivo = int(round(rotaciones * 360.0))
 if grados_objetivo <= 0 or grados_objetivo > MAX_GRADOS_DISTANCIA:
  raise ValueError('La distancia solicitada excede el rango permitido')
 ib.pixel = color_led
 paquetes = _T(direccion, velocidad, grados_objetivo)
 print('Movimiento por distancia:', distancia_cm, 'cm', '| Rotaciones:', round(rotaciones, 3), '| Grados de motor:', grados_objetivo, '| Velocidad:', velocidad)
 try:
  for paquete in paquetes:
   _U(paquete)
  segundos_estimados = grados_objetivo / float(velocidad * 10)
  fin = time.monotonic() + segundos_estimados * FACTOR_ESPERA_DISTANCIA + MARGEN_ESPERA_DISTANCIA
  while _c and time.monotonic() < fin:
   if not _C():
    raise RuntimeError('Se perdio el enlace durante movimiento por distancia')
   pausa = _V(color_led)
   if pausa > 0:
    fin += pausa
   time.sleep(0.001)
 except Exception:
  try:
   _U(CONTROL_DISTANCIA_CANCELAR)
  except Exception:
   pass
  _s()
  if _c:
   _D(TIEMPO_CONFIRMACION_PARADA)
  raise
 _G(cambiar_color=True)

def avance_distancia(distancia_cm, velocidad=VELOCIDAD_BASE):
 _W(distancia_cm, velocidad, DIRECCION_ADELANTE, COLOR_AVANCE)

def reversa_distancia(distancia_cm, velocidad=VELOCIDAD_BASE):
 _W(distancia_cm, velocidad, DIRECCION_ATRAS, COLOR_REVERSA)

def _X(segundos, velocidad_garra, velocidad_pala, direccion='adelante', color_led=COLOR_GARRA_PALA):
 _e(segundos)
 _r(velocidad_garra, velocidad_pala, direccion)
 ib.pixel = color_led
 if not _F(segundos, color_led):
  _s()
  raise RuntimeError('Se perdio el enlace durante accesorios')
 _G(cambiar_color=True)

def mover_garra(segundos, velocidad, direccion='adelante'):
 _X(segundos, velocidad_garra=velocidad, velocidad_pala=0, direccion=direccion, color_led=COLOR_GARRA)

def mover_pala(segundos, velocidad, direccion='adelante'):
 _X(segundos, velocidad_garra=0, velocidad_pala=velocidad, direccion=direccion, color_led=COLOR_PALA)

def mover_garra_pala(segundos, velocidad_garra, velocidad_pala, direccion='adelante'):
 _X(segundos, velocidad_garra, velocidad_pala, direccion, color_led=COLOR_GARRA_PALA)

def _Y(error_angulo, velocidad_base):
 error_angulo = abs(error_angulo)
 if error_angulo > 35:
  return velocidad_base
 if error_angulo > 15:
  return min(velocidad_base, 20)
 return 10

def girar(direccion, angulo, velocidad_base):
 if _o is None:
  raise RuntimeError('El giroscopio no ha sido calibrado')
 if not isinstance(direccion, str):
  raise ValueError('direccion debe ser texto')
 direccion = direccion.strip().lower()
 _j(direccion)
 if not isinstance(angulo, (int, float)):
  raise ValueError('angulo debe ser numerico')
 if angulo <= 0 or angulo > 360:
  raise ValueError('angulo debe estar entre 0 y 360 grados')
 _f(velocidad_base, 'velocidad_base')
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
 _q(direccion_actual, velocidad_base)
 print('Girando', direccion, '| Angulo objetivo:', angulo, '| Velocidad:', velocidad_base)
 try:
  while True:
   if not _C():
    raise RuntimeError('Se perdio el enlace durante girar()')
   duracion_pausa = _E(COLOR_GIRO)
   if duracion_pausa > 0:
    tiempo_inicio += duracion_pausa
    tiempo_anterior = time.monotonic()
    tiempo_estable = None
    continue
   tiempo_actual = time.monotonic()
   dt = tiempo_actual - tiempo_anterior
   tiempo_anterior = tiempo_actual
   _, _, gz = imu.gyro
   velocidad_angular_z = (math.degrees(gz) - _o) * SIGNO_GIROSCOPIO
   if abs(velocidad_angular_z) < ZONA_MUERTA_GIRO:
    velocidad_angular_z = 0.0
   if 0 < dt <= 0.1:
    if comando_detenido and abs(velocidad_angular_z) <= VELOCIDAD_ANGULAR_DETENIDA:
     incremento = 0.0
    else:
     incremento = abs(velocidad_angular_z) * dt
    if direccion_actual == direccion:
     angulo_medido += incremento
    else:
     angulo_medido -= incremento
   error_angulo = angulo - angulo_medido
   if MOSTRAR_DIAGNOSTICO_GIRO:
    if tiempo_actual - ultimo_diagnostico >= INTERVALO_DIAGNOSTICO_GIRO:
     print('Giro:', direccion_actual, '| GZ:', round(velocidad_angular_z, 2), '| Angulo:', round(angulo_medido, 2), '| Error:', round(error_angulo, 2), '| Byte:', _m)
     ultimo_diagnostico = tiempo_actual
   if abs(error_angulo) <= TOLERANCIA_ANGULO_GIRO:
    if not comando_detenido:
     _s()
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
     nueva_direccion = _k(direccion)
    velocidad_giro = _Y(error_angulo, velocidad_base)
    direccion_actual = nueva_direccion
    _q(direccion_actual, velocidad_giro)
    comando_detenido = False
   if not _C():
    raise RuntimeError('Se perdio el enlace durante girar()')
   if tiempo_actual - tiempo_inicio > tiempo_maximo:
    raise RuntimeError('Tiempo maximo excedido durante girar(); ultimo angulo medido: ' + str(round(angulo_medido, 2)))
   time.sleep(0.001)
 except Exception:
  _s()
  if _c:
   _D(TIEMPO_CONFIRMACION_PARADA)
  raise
 _G(cambiar_color=True)
 print('Giro terminado', '| Objetivo:', angulo, '| Medido:', round(angulo_medido, 2))
 return angulo_medido

def _Z(externo_izquierdo_visto, externo_derecho_visto):
 if externo_izquierdo_visto and externo_derecho_visto:
  return 'T'
 if externo_izquierdo_visto:
  return 'izquierda'
 if externo_derecho_visto:
  return 'derecha'
 return 'desconocida'

def _x52(numero_interseccion, velocidad_base, direccion_movimiento):
 if not isinstance(numero_interseccion, int):
  raise ValueError('numero_interseccion debe ser entero')
 if numero_interseccion <= 0:
  raise ValueError('numero_interseccion debe ser mayor que cero')
 _f(velocidad_base, 'velocidad_base')
 if velocidad_base == 0:
  raise ValueError('velocidad_base debe ser al menos 10')
 bit_direccion = _i(direccion_movimiento)
 es_reversa = bit_direccion == DIRECCION_ATRAS
 color_movimiento = COLOR_REVERSA_HASTA if es_reversa else COLOR_AVANCE_HASTA
 texto_movimiento = 'Reversa' if es_reversa else 'Avance'
 ultimo_diagnostico_sensores = 0.0
 contador_intersecciones = 0
 tipo_interseccion = None
 muestras_interseccion = 0
 muestras_liberacion = 0
 interseccion_activa = False
 externo_derecho_visto = False
 externo_izquierdo_visto = False
 ib.pixel = color_movimiento
 _p(velocidad_base, 0, direccion=bit_direccion)
 print(texto_movimiento, 'hasta la interseccion', numero_interseccion, '| Velocidad base:', velocidad_base, '| Control: infrarrojos')
 try:
  while contador_intersecciones < numero_interseccion:
   if not _C():
    raise RuntimeError('Se perdio la conexion durante ' + ('reversa_hasta()' if es_reversa else 'avance_hasta()'))
   if _E(color_movimiento) > 0:
    ultimo_diagnostico_sensores = time.monotonic()
    continue
   nivel_ei, nivel_ci, nivel_c, nivel_cd, nivel_ed, ext_izq, cen_izq, centro, cen_der, ext_der = _K()
   ahora = time.monotonic()
   if MOSTRAR_DIAGNOSTICO_SENSORES and ahora - ultimo_diagnostico_sensores >= INTERVALO_DIAGNOSTICO_SENSORES:
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
      ib.pixel = color_movimiento
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
     tipo_interseccion = _Z(externo_izquierdo_visto, externo_derecho_visto)
     _t(tipo_interseccion)
     print('Interseccion:', contador_intersecciones, '| Tipo:', tipo_interseccion, '| Movimiento:', 'reversa' if es_reversa else 'avance')
   else:
    muestras_interseccion = 0
    externo_derecho_visto = False
    externo_izquierdo_visto = False
   if interseccion_confirmada and contador_intersecciones >= numero_interseccion:
    _G(cambiar_color=False)
    return tipo_interseccion
   correccion_logica = _L(ext_izq, cen_izq, centro, cen_der, ext_der)
   if correccion_logica is None:
    correccion_logica = 0
   correccion_enviada = _O(correccion_logica, bit_direccion)
   _p(velocidad_base, correccion_enviada, direccion=bit_direccion)
   if not _C():
    raise RuntimeError('Se perdio la conexion durante ' + ('reversa_hasta()' if es_reversa else 'avance_hasta()'))
   time.sleep(0.001)
 except Exception:
  _s()
  if _c:
   _D(TIEMPO_CONFIRMACION_PARADA)
  raise
 _G(cambiar_color=False)
 return tipo_interseccion

def avance_hasta(numero_interseccion, velocidad_base=VELOCIDAD_BASE):
 return _x52(numero_interseccion, velocidad_base, DIRECCION_ADELANTE)

def reversa_hasta(numero_interseccion, velocidad_base=VELOCIDAD_BASE):
 return _x52(numero_interseccion, velocidad_base, DIRECCION_ATRAS)

def _x53():
 _s()
 _b()
 ib.pixel = COLOR_ESPERANDO_BOTON
 print('Handshake completado.')
 print('Presione y suelte el boton BOOT para iniciar.')
 while _c:
  if not _C():
   return False
  if _a():
   if not _D(0.05):
    return False
   return True
  time.sleep(0.001)
 return False
__all__ = ('avance', 'reversa', 'detenerse', 'girar', 'avance_hasta', 'reversa_hasta', 'avance_distancia', 'reversa_distancia', 'mover_garra', 'mover_pala', 'mover_garra_pala', 'calibrar_giroscopio', 'iniciar')

def iniciar(programa_usuario):
 global _c
 print('Iniciando biblioteca LPF2: ruedas, garra, pala y 5 sensores...')
 while True:
  if not _H():
   ib.pixel = COLOR_ERROR
   time.sleep(1.0)
   continue
  while _c:
   try:
    if not _x53():
     break
    calibrar_giroscopio()
    programa_usuario()
    _G(cambiar_color=True)
    print('Secuencia finalizada.')
   except KeyboardInterrupt:
    _s()
    ib.pixel = COLOR_APAGADO
    if _c:
     _D(TIEMPO_CONFIRMACION_PARADA)
    raise
   except Exception as error:
    _s()
    ib.pixel = COLOR_ERROR
    if _c:
     _D(TIEMPO_CONFIRMACION_PARADA)
     print('Error:', error)
     print('El enlace LPF2 sigue activo. Se vuelve a esperar el boton.')
     continue
    print('Error:', error)
    print('Enlace perdido; se realizara un nuevo handshake.')
    break