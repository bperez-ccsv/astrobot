import time
import math
import board
import busio
import digitalio
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
p0=digitalio.DigitalInOut(board.IO0)
p0.switch_to_input(pull=digitalio.Pull.UP)
p1=digitalio.DigitalInOut(board.IO27)
p1.switch_to_input(pull=digitalio.Pull.UP)
be=1
bc=1
bt=time.monotonic()

def _a():
 global be,bc,bt
 n=p0.value and p1.value
 t=time.monotonic()
 if n!=bc:
  bc=n;bt=t;return False
 if n!=be and t-bt>=.03:
  a=be;be=n;return not a and n
 return False

def _b():
 global be,bc,bt
 be=p0.value and p1.value
 bc=be
 bt=time.monotonic()
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
offset_giroscopio_z = None
VELOCIDAD_BASE = 20
CIRCUNFERENCIA_RUEDA_CM = 17.6
CAL_DISTANCIA_INTERCEPTO = -0.81422
CAL_DISTANCIA_COEF_DISTANCIA = 0.97808
CAL_DISTANCIA_COEF_VELOCIDAD = 0.059195
CONTROL_DISTANCIA_INICIO = 255
CONTROL_DISTANCIA_PAUSA = 247
CONTROL_DISTANCIA_REANUDAR = 239
CONTROL_DISTANCIA_CANCELAR = 231
TIEMPO_PAQUETE_DISTANCIA = 0.1
MAX_GRADOS_DISTANCIA = (1 << 18) - 1
FACTOR_ESPERA_DISTANCIA = 1.35
MARGEN_ESPERA_DISTANCIA = 0.6
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
 a = int(math.floor(abs(correccion) + 0.5))
 if correccion < 0:
  a = -a
 return int(_c(a, -3, 3))

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
 a = _i(direccion)
 c = velocidad_base // 10
 b = correccion + 3
 return MODO_RUEDAS << 7 | a << 6 | c << 3 | b

def _m(direccion, velocidad_base):
 _f(velocidad_base, 'velocidad_base')
 if velocidad_base == 0:
  raise ValueError('La velocidad del giro debe ser al menos 10')
 a = _j(direccion)
 b = velocidad_base // 10
 return MODO_RUEDAS << 7 | a << 6 | b << 3 | CODIGO_GIRO_SOBRE_EJE

def _n(velocidad_garra, velocidad_pala, direccion='adelante'):
 _f(velocidad_garra, 'velocidad_garra')
 _f(velocidad_pala, 'velocidad_pala')
 a = _i(direccion)
 b = velocidad_garra // 10
 c = velocidad_pala // 10
 return MODO_ACCESORIOS << 7 | a << 6 | b << 3 | c

def _o(mensaje):
 global mensaje_actual
 if not isinstance(mensaje, int) or mensaje < 0 or mensaje > 255:
  raise ValueError('El mensaje debe ser un byte entre 0 y 255')
 mensaje_actual = mensaje

def _p(velocidad_base, correccion=0, direccion='adelante'):
 _o(_l(velocidad_base, correccion, direccion))

def _q(direccion, velocidad_base):
 _o(_m(direccion, velocidad_base))

def _r(velocidad_garra, velocidad_pala, direccion='adelante'):
 _o(_n(velocidad_garra, velocidad_pala, direccion))

def _s():
 _o(MENSAJE_DETENER)

def _t():
 ib.pixel = COLOR_INTERSECCION_DERECHA
 print('Interseccion solamente hacia la derecha.')

def _u():
 ib.pixel = COLOR_INTERSECCION_IZQUIERDA
 print('Interseccion solamente hacia la izquierda.')

def _v():
 ib.pixel = COLOR_INTERSECCION_T
 print('Interseccion tipo T.')

def _w(tipo):
 if tipo == 'derecha':
  _t()
 elif tipo == 'izquierda':
  _u()
 elif tipo == 'T':
  _v()
 else:
  ib.pixel = COLOR_ERROR

def _x(data):
 b = 255
 for a in data:
  b ^= a
 return b & 255

def _y(baud):
 global uart
 if uart:
  uart.deinit()
 uart = busio.UART(tx=TX_PIN, rx=RX_PIN, baudrate=baud, timeout=0.005, receiver_buffer_size=64)
 time.sleep(0.05)

def _z(data):
 uart.write(bytes(data))

def _A(data):
 a = bytearray(data)
 a.append(_x(a))
 _z(a)

def _B():
 global uart
 if uart:
  uart.deinit()
  uart = None
 b = digitalio.DigitalInOut(RX_PIN)
 b.direction = digitalio.Direction.INPUT
 c = digitalio.DigitalInOut(TX_PIN)
 c.direction = digitalio.Direction.OUTPUT
 c.value = False
 a = time.monotonic()
 while True:
  if b.value is False:
   a = time.monotonic()
  if time.monotonic() - a > 0.1:
   break
  time.sleep(0.001)
 c.value = True
 time.sleep(0.1)
 c.value = False
 time.sleep(0.1)
 b.deinit()
 c.deinit()

def _C():
 _y(BAUD_INICIAL)
 _z([0])
 time.sleep(0.01)
 _A([64, 29])
 _A([73, 0, 0])
 _A([82] + list(struct.pack('<I', BAUD_DATOS)))
 _A([95, 0, 0, 0, 16, 0, 0, 0, 16])
 time.sleep(0.01)
 _A([152, 0, 77, 79, 84, 79, 82, 0, 0, 0])
 _A([153, 1] + list(struct.pack('<f', 0.0)) + list(struct.pack('<f', 120.0)))
 _A([153, 2] + list(struct.pack('<f', 0.0)) + list(struct.pack('<f', 100.0)))
 _A([153, 3] + list(struct.pack('<f', 0.0)) + list(struct.pack('<f', 120.0)))
 _A([152, 4, 99, 109, 100, 0, 0, 0, 0, 0])
 _A([136, 5, 16, 0])
 _A([144, 128, 1, 0, 3, 0])
 _z([4])
 time.sleep(0.005)

def _D():
 b = time.monotonic()
 while time.monotonic() - b < 2.0:
  a = uart.read(16)
  if a:
   print('RX init:', list(a))
   if 4 in a:
    return True
  time.sleep(0.005)
 return False

def _E():
 a = bytearray([192, mensaje_actual & 255])
 a.append(_x(a))
 _z(a)

def _F():
 global connected
 global last_nack
 global advertencia_nack_mostrada
 a = uart.read(64)
 if a and 2 in a:
  last_nack = time.monotonic()
  advertencia_nack_mostrada = False
  _E()
 b = time.monotonic() - last_nack
 if b > TIMEOUT_NACK_ADVERTENCIA:
  if not advertencia_nack_mostrada:
   print('Advertencia: NACK demorado.')
   advertencia_nack_mostrada = True
 if b > TIMEOUT_NACK_DESCONEXION:
  print('Timeout NACK real. Se perdio el enlace LPF2.')
  connected = False
 return connected

def _G(segundos):
 a = time.monotonic() + segundos
 while connected and time.monotonic() < a:
  _F()
  time.sleep(0.001)
 return connected

def _H(color_reanudar):
 if not _a():
  return 0.0
 b = mensaje_actual
 a = time.monotonic()
 _s()
 ib.pixel = COLOR_PAUSA
 print('Programa pausado. Presione BOOT o IO27 para continuar.')
 while connected:
  if not _F():
   raise RuntimeError('Se perdio el enlace durante la pausa')
  if _a():
   _o(b)
   ib.pixel = color_reanudar
   print('Programa reanudado.')
   return time.monotonic() - a
  time.sleep(0.001)
 raise RuntimeError('Se perdio el enlace durante la pausa')

def _I(segundos, color_reanudar):
 b = time.monotonic() + segundos
 while connected and time.monotonic() < b:
  if not _F():
   return False
  a = _H(color_reanudar)
  if a > 0:
   b += a
  time.sleep(0.001)
 return connected

def _J(cambiar_color=True):
 _s()
 if cambiar_color:
  ib.pixel = COLOR_DETENERSE
 if not _G(TIEMPO_CONFIRMACION_PARADA):
  raise RuntimeError('Se perdio el enlace al enviar la parada')

def _K():
 global connected
 global last_nack
 global mensaje_actual
 global advertencia_nack_mostrada
 connected = False
 mensaje_actual = MENSAJE_DETENER
 advertencia_nack_mostrada = False
 print('Esperando hub idle...')
 _B()
 print('Enviando inicializacion LPF2...')
 _C()
 if not _D():
  print('No se recibio ACK.')
  return False
 print('ACK recibido. Cambiando UART a', BAUD_DATOS)
 _y(BAUD_DATOS)
 connected = True
 last_nack = time.monotonic()
 return True

def _L(sensor):
 return 1 if sensor.value else 0

def _M(nivel):
 if SENSOR_NEGRO_ES_LOW:
  return nivel == 0
 return nivel == 1

def _N():
 e = _L(sensor_externo_izquierdo)
 c = _L(sensor_centro_izquierdo)
 a = _L(sensor_centro)
 b = _L(sensor_centro_derecho)
 d = _L(sensor_externo_derecho)
 return (e, c, a, b, d, _M(e), _M(c), _M(a), _M(b), _M(d))

def _O(externo_izquierdo, centro_izquierdo, centro, centro_derecho, externo_derecho):
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
 _s()
 ib.pixel = COLOR_CALIBRANDO
 c = 0.0
 print('Calibrando giroscopio. No mover el carrito.')
 for a in range(cantidad_muestras):
  if not _F():
   raise RuntimeError('Se perdio el enlace durante la calibracion')
  a, a, b = imu.gyro
  c += math.degrees(b)
  time.sleep(0.003)
 offset_giroscopio_z = c / cantidad_muestras
 print('Offset Z:', offset_giroscopio_z, 'grados/s')
 return offset_giroscopio_z

def _P(rumbo_actual, tiempo_anterior):
 if offset_giroscopio_z is None:
  raise RuntimeError('El giroscopio no ha sido calibrado')
 d = time.monotonic()
 b = d - tiempo_anterior
 if b <= 0 or b > 0.1:
  return (rumbo_actual, d, 0.0)
 a, a, c = imu.gyro
 e = math.degrees(c)
 e -= offset_giroscopio_z
 e *= SIGNO_GIROSCOPIO
 if abs(e) < ZONA_MUERTA_GIRO:
  e = 0.0
 rumbo_actual += e * b
 rumbo_actual = _d(rumbo_actual)
 return (rumbo_actual, d, e)

def _Q(rumbo_actual, rumbo_objetivo):
 c = _d(rumbo_objetivo - rumbo_actual)
 if abs(c) < ERROR_RUMBO_MINIMO:
  return (0, c)
 b = KP_CORRECCION * c * SIGNO_CORRECCION
 a = _h(b)
 if a == 0:
  a = 2 if b > 0 else -2
 return (a, c)

def _R(correccion_logica, direccion_movimiento):
 a = _i(direccion_movimiento)
 if a == DIRECCION_ATRAS:
  return -correccion_logica
 return correccion_logica

def _S(rumbo_actual, rumbo_objetivo, velocidad_base, direccion_movimiento, tiempo_anterior, correccion_infrarroja=None):
 rumbo_actual, f, g = _P(rumbo_actual, tiempo_anterior)
 b, d = _Q(rumbo_actual, rumbo_objetivo)
 if correccion_infrarroja is None:
  c = b
  e = 'giroscopio'
 else:
  c = correccion_infrarroja
  e = 'infrarrojo'
 a = _R(c, direccion_movimiento)
 _p(velocidad_base, a, direccion=direccion_movimiento)
 return (rumbo_actual, f, c, a, d, g, e)

def _T(segundos, velocidad_base, direccion_movimiento, color_led):
 _e(segundos)
 _f(velocidad_base, 'velocidad_base')
 if velocidad_base == 0:
  detenerse(segundos)
  return
 if offset_giroscopio_z is None:
  raise RuntimeError('El giroscopio no ha sido calibrado')
 ib.pixel = color_led
 d = 0.0
 e = 0.0
 f = time.monotonic()
 c = f + segundos
 _p(velocidad_base, 0, direccion=direccion_movimiento)
 try:
  while connected and time.monotonic() < c:
   if not _F():
    raise RuntimeError('Se perdio el enlace durante el movimiento')
   b = _H(color_led)
   if b > 0:
    c += b
    f = time.monotonic()
    continue
   d, f, a, a, a, a, a = _S(d, e, velocidad_base, direccion_movimiento, f, correccion_infrarroja=None)
   if not _F():
    raise RuntimeError('Se perdio el enlace durante el movimiento')
   time.sleep(0.001)
 except Exception:
  _s()
  if connected:
   _G(TIEMPO_CONFIRMACION_PARADA)
  raise
 _J(cambiar_color=True)

def avance(segundos, velocidad):
 _T(segundos, velocidad, DIRECCION_ADELANTE, COLOR_AVANCE)

def reversa(segundos, velocidad):
 _T(segundos, velocidad, DIRECCION_ATRAS, COLOR_REVERSA)

def detenerse(segundos):
 _e(segundos)
 _s()
 ib.pixel = COLOR_DETENERSE
 if not _I(segundos, COLOR_DETENERSE):
  raise RuntimeError('Se perdio el enlace durante detenerse()')

def _U(distancia_cm):
 if not isinstance(distancia_cm, (int, float)):
  raise ValueError('distancia_cm debe ser numerica')
 if distancia_cm <= 0:
  raise ValueError('distancia_cm debe ser mayor que cero')
 if CIRCUNFERENCIA_RUEDA_CM <= 0:
  raise ValueError('CIRCUNFERENCIA_RUEDA_CM debe ser mayor que cero')

def _V(distancia_objetivo_cm, velocidad):
 a = (distancia_objetivo_cm - CAL_DISTANCIA_INTERCEPTO - CAL_DISTANCIA_COEF_VELOCIDAD * velocidad) / CAL_DISTANCIA_COEF_DISTANCIA
 if a <= 0:
  raise ValueError('La combinacion de distancia y velocidad queda fuera del rango util del modelo de calibracion')
 return a

def _W(nibble):
 return 128 | (nibble & 15) << 3 | 7

def _X(direccion, velocidad, grados_objetivo):
 a = _i(direccion)
 d = velocidad // 10
 e = a << 3 | d
 g = [CONTROL_DISTANCIA_INICIO, _W(e)]
 h = 1 - a
 for c in (15, 12, 9, 6, 3, 0):
  b = grados_objetivo >> c & 7
  f = h << 3 | b
  g.append(_W(f))
  h = 1 - h
 return g

def _Y(paquete):
 _o(paquete)
 if not _G(TIEMPO_PAQUETE_DISTANCIA):
  raise RuntimeError('Se perdio el enlace enviando distancia')

def _Z(color_reanudar):
 if not _a():
  return 0.0
 a = time.monotonic()
 _Y(CONTROL_DISTANCIA_PAUSA)
 ib.pixel = COLOR_PAUSA
 print('Movimiento por distancia pausado.')
 while connected:
  if not _F():
   raise RuntimeError('Se perdio el enlace durante la pausa')
  if _a():
   _Y(CONTROL_DISTANCIA_REANUDAR)
   ib.pixel = color_reanudar
   print('Movimiento por distancia reanudado.')
   return time.monotonic() - a
  time.sleep(0.001)
 raise RuntimeError('Se perdio el enlace durante la pausa')

def _aa(distancia_cm, velocidad, direccion, color_led):
 _U(distancia_cm)
 _f(velocidad, 'velocidad')
 if velocidad == 0:
  raise ValueError('velocidad debe ser al menos 10')
 if offset_giroscopio_z is None:
  raise RuntimeError('El giroscopio no ha sido calibrado')
 d = _V(distancia_cm, velocidad)
 k = d / CIRCUNFERENCIA_RUEDA_CM
 g = int(round(k * 360.0))
 if g <= 0 or g > MAX_GRADOS_DISTANCIA:
  raise ValueError('La distancia solicitada excede el rango permitido')
 ib.pixel = color_led
 i = _X(direccion, velocidad, g)
 l = 0.0
 m = 0.0
 o = time.monotonic()
 print('Distancia solicitada:', round(distancia_cm, 3), 'cm', '| Distancia interna:', round(d, 3), 'cm', '| Rotaciones:', round(k, 3), '| Grados:', g, '| Velocidad:', velocidad, '| Control: calibracion + encoders + giroscopio')
 try:
  for h in i:
   _Y(h)
  _p(velocidad, 0, direccion=direccion)
  q = max(1, velocidad - CORRECCION_MAXIMA)
  n = g / float(q * 10)
  f = time.monotonic() + n * FACTOR_ESPERA_DISTANCIA + MARGEN_ESPERA_DISTANCIA
  while connected and time.monotonic() < f:
   if not _F():
    raise RuntimeError('Se perdio el enlace durante movimiento por distancia')
   j = _Z(color_led)
   if j > 0:
    f += j
    o = time.monotonic()
    continue
   l, o, c, b, e, p, a = _S(l, m, velocidad, direccion, o, correccion_infrarroja=None)
   if MOSTRAR_DIAGNOSTICO_CONTROL:
    print('Distancia + gyro', '| Rumbo:', round(l, 2), '| Error:', round(e, 2), '| Correccion:', b, '| Velocidad angular:', round(p, 2))
   if not _F():
    raise RuntimeError('Se perdio el enlace durante movimiento por distancia')
   time.sleep(0.001)
 except Exception:
  try:
   _Y(CONTROL_DISTANCIA_CANCELAR)
  except Exception:
   pass
  _s()
  if connected:
   _G(TIEMPO_CONFIRMACION_PARADA)
  raise
 _J(cambiar_color=True)

def avance_distancia(distancia_cm, velocidad=VELOCIDAD_BASE):
 _aa(distancia_cm, velocidad, DIRECCION_ADELANTE, COLOR_AVANCE)

def reversa_distancia(distancia_cm, velocidad=VELOCIDAD_BASE):
 _aa(distancia_cm, velocidad, DIRECCION_ATRAS, COLOR_REVERSA)

def _ab(segundos, velocidad_garra, velocidad_pala, direccion='adelante', color_led=COLOR_GARRA_PALA):
 _e(segundos)
 _r(velocidad_garra, velocidad_pala, direccion)
 ib.pixel = color_led
 if not _I(segundos, color_led):
  _s()
  raise RuntimeError('Se perdio el enlace durante accesorios')
 _J(cambiar_color=True)

def mover_garra(segundos, velocidad, direccion='adelante'):
 _ab(segundos, velocidad_garra=velocidad, velocidad_pala=0, direccion=direccion, color_led=COLOR_GARRA)

def mover_pala(segundos, velocidad, direccion='adelante'):
 _ab(segundos, velocidad_garra=0, velocidad_pala=velocidad, direccion=direccion, color_led=COLOR_PALA)

def mover_garra_pala(segundos, velocidad_garra, velocidad_pala, direccion='adelante'):
 _ab(segundos, velocidad_garra, velocidad_pala, direccion, color_led=COLOR_GARRA_PALA)

def _ac(error_angulo, velocidad_base):
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
 _j(direccion)
 if not isinstance(angulo, (int, float)):
  raise ValueError('angulo debe ser numerico')
 if angulo <= 0 or angulo > 360:
  raise ValueError('angulo debe estar entre 0 y 360 grados')
 _f(velocidad_base, 'velocidad_base')
 if velocidad_base == 0:
  raise ValueError('velocidad_base debe ser al menos 10')
 ib.pixel = COLOR_GIRO
 o = time.monotonic()
 m = o
 q = 0.0
 n = None
 h = max(1.0, 30.0 / velocidad_base)
 p = max(5.0, angulo / 90.0 * TIEMPO_MAXIMO_GIRO_90 * h)
 b = 0.0
 d = direccion
 c = False
 _q(d, velocidad_base)
 print('Girando', direccion, '| Angulo objetivo:', angulo, '| Velocidad:', velocidad_base)
 try:
  while True:
   if not _F():
    raise RuntimeError('Se perdio el enlace durante girar()')
   f = _H(COLOR_GIRO)
   if f > 0:
    o += f
    m = time.monotonic()
    n = None
    continue
   l = time.monotonic()
   e = l - m
   m = l
   a, a, i = imu.gyro
   r = (math.degrees(i) - offset_giroscopio_z) * SIGNO_GIROSCOPIO
   if abs(r) < ZONA_MUERTA_GIRO:
    r = 0.0
   if 0 < e <= 0.1:
    if c and abs(r) <= VELOCIDAD_ANGULAR_DETENIDA:
     j = 0.0
    else:
     j = abs(r) * e
    if d == direccion:
     b += j
    else:
     b -= j
   g = angulo - b
   if MOSTRAR_DIAGNOSTICO_GIRO:
    if l - q >= INTERVALO_DIAGNOSTICO_GIRO:
     print('Giro:', d, '| GZ:', round(r, 2), '| Angulo:', round(b, 2), '| Error:', round(g, 2), '| Byte:', mensaje_actual)
     q = l
   if abs(g) <= TOLERANCIA_ANGULO_GIRO:
    if not c:
     _s()
     c = True
     n = None
    if abs(r) <= VELOCIDAD_ANGULAR_DETENIDA:
     if n is None:
      n = l
     elif l - n >= TIEMPO_ESTABLE_GIRO:
      if abs(angulo - b) <= TOLERANCIA_ANGULO_GIRO:
       break
      c = False
      n = None
    else:
     n = None
   else:
    n = None
    if g > 0:
     k = direccion
    else:
     k = _k(direccion)
    s = _ac(g, velocidad_base)
    d = k
    _q(d, s)
    c = False
   if not _F():
    raise RuntimeError('Se perdio el enlace durante girar()')
   if l - o > p:
    raise RuntimeError('Tiempo maximo excedido durante girar(); ultimo angulo medido: ' + str(round(b, 2)))
   time.sleep(0.001)
 except Exception:
  _s()
  if connected:
   _G(TIEMPO_CONFIRMACION_PARADA)
  raise
 _J(cambiar_color=True)
 print('Giro terminado', '| Objetivo:', angulo, '| Medido:', round(b, 2))
 return b

def _ad(externo_izquierdo_visto, externo_derecho_visto):
 if externo_izquierdo_visto and externo_derecho_visto:
  return 'T'
 if externo_izquierdo_visto:
  return 'izquierda'
 if externo_derecho_visto:
  return 'derecha'
 return 'desconocida'

def _ae(numero_interseccion, velocidad_base, direccion_movimiento):
 if not isinstance(numero_interseccion, int):
  raise ValueError('numero_interseccion debe ser entero')
 if numero_interseccion <= 0:
  raise ValueError('numero_interseccion debe ser mayor que cero')
 _f(velocidad_base, 'velocidad_base')
 if velocidad_base == 0:
  raise ValueError('velocidad_base debe ser al menos 10')
 if offset_giroscopio_z is None:
  raise RuntimeError('El giroscopio no ha sido calibrado')
 b = _i(direccion_movimiento)
 m = b == DIRECCION_ATRAS
 B = 0.0
 C = 0.0
 E = time.monotonic()
 G = 0.0
 g = 0
 F = None
 u = 0
 v = 0
 s = False
 p = False
 q = False
 A, y, w, x, z, o, d, e, c, n = _N()
 s = False
 if m:
  ib.pixel = COLOR_REVERSA_HASTA
  D = 'Reversa'
 else:
  ib.pixel = COLOR_AVANCE_HASTA
  D = 'Avance'
 _p(velocidad_base, 0, direccion=b)
 print(D, 'hasta la interseccion', numero_interseccion, '| Velocidad base:', velocidad_base)
 try:
  while g < numero_interseccion:
   if not _F():
    raise RuntimeError('Se perdio la conexion durante ' + ('reversa_hasta()' if m else 'avance_hasta()'))
   f = COLOR_REVERSA_HASTA if m else COLOR_AVANCE_HASTA
   k = _H(f)
   if k > 0:
    E = time.monotonic()
    G = E
    continue
   A, y, w, x, z, o, d, e, c, n = _N()
   a = time.monotonic()
   if MOSTRAR_DIAGNOSTICO_SENSORES:
    if a - G >= INTERVALO_DIAGNOSTICO_SENSORES:
     print('Sensores: {}{}{}{}{} '.format(A, y, w, x, z).replace('0', '-').replace('1', '▤'))
     G = a
   t = False
   if s:
    if not n and (not o):
     v += 1
     if v >= MUESTRAS_LIBERACION_INTERSECCION:
      s = False
      v = 0
      u = 0
      p = False
      q = False
      ib.pixel = COLOR_REVERSA_HASTA if m else COLOR_AVANCE_HASTA
    else:
     v = 0
   elif n or o:
    u += 1
    p = p or n
    q = q or o
    if u >= MUESTRAS_CONFIRMACION_INTERSECCION:
     t = True
     s = True
     u = 0
     v = 0
     g += 1
     F = _ad(q, p)
     _w(F)
     print('Interseccion:', g, '| Tipo:', F, '| Movimiento:', 'reversa' if m else 'avance')
     print('Sensores: {}{}{}{}{} '.format(A, y, w, x, z).replace('0', '-').replace('1', '▤'))
   else:
    u = 0
    p = False
    q = False
   if t and g >= numero_interseccion:
    _J(cambiar_color=False)
    return F
   i = _O(o, d, e, c, n)
   B, E, j, h, l, H, r = _S(B, C, velocidad_base, b, E, correccion_infrarroja=i)
   if MOSTRAR_DIAGNOSTICO_CONTROL:
    print('Fuente:', r, '| Error gyro:', round(l, 2), '| Correccion logica:', j, '| Correccion enviada:', h)
   if not _F():
    raise RuntimeError('Se perdio la conexion durante ' + ('reversa_hasta()' if m else 'avance_hasta()'))
   time.sleep(0.001)
 except Exception:
  _s()
  if connected:
   _G(TIEMPO_CONFIRMACION_PARADA)
  raise
 _J(cambiar_color=False)
 return F

def avance_hasta(numero_interseccion, velocidad_base=VELOCIDAD_BASE):
 return _ae(numero_interseccion, velocidad_base, DIRECCION_ADELANTE)

def reversa_hasta(numero_interseccion, velocidad_base=VELOCIDAD_BASE):
 return _ae(numero_interseccion, velocidad_base, DIRECCION_ATRAS)

def _af():
 _s()
 _b()
 ib.pixel = COLOR_ESPERANDO_BOTON
 print('Handshake completado.')
 print('Presione y suelte BOOT o IO27 para iniciar.')
 while connected:
  if not _F():
   return False
  if _a():
   if not _G(0.05):
    return False
   return True
  time.sleep(0.001)
 return False
__all__ = ('avance', 'reversa', 'detenerse', 'girar', 'avance_hasta', 'reversa_hasta', 'avance_distancia', 'reversa_distancia', 'mover_garra', 'mover_pala', 'mover_garra_pala', 'calibrar_giroscopio', 'iniciar')

def iniciar(programa_usuario):
 global connected
 print('Iniciando biblioteca CCSV: version 260721.1325')
 while True:
  if not _K():
   ib.pixel = COLOR_ERROR
   time.sleep(1.0)
   continue
  while connected:
   try:
    if not _af():
     break
    calibrar_giroscopio()
    programa_usuario()
    _J(cambiar_color=True)
    print('Secuencia finalizada.')
   except KeyboardInterrupt:
    _s()
    ib.pixel = COLOR_APAGADO
    if connected:
     _G(TIEMPO_CONFIRMACION_PARADA)
    raise
   except Exception as a:
    _s()
    ib.pixel = COLOR_ERROR
    if connected:
     _G(TIEMPO_CONFIRMACION_PARADA)
     print('Error:', a)
     print('El enlace LPF2 sigue activo. Se vuelve a esperar el boton.')
     continue
    print('Error:', a)
    print('Enlace perdido; se realizara un nuevo handshake.')
    break