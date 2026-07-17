import time as _a
import math as _b
import board as _c
import busio as _d
import digitalio as _e
import keypad as _f
import struct as _g
from ideaboard import IdeaBoard as _h
from adafruit_lsm6ds.lsm6ds3trc import LSM6DS3TRC as _i
_j = _h()
_k = _c.IO26
_l = _c.IO25
_m = 2400
_n = 115200
_o = 0.5
_p = 2.0
_q = 0.15
_r = None
_s = False
_t = 0.0
_u = False
_v = 0
_w = 1
_x = 0
_y = 1
_z = 7
_aa = 3
_ab = _aa
_ac = _f.Keys((_c.IO0,), value_when_pressed=False, pull=True)

def _ad():
    evento = _ac.events.get()
    return bool(evento and evento.released)

def _ae():
    while _ac.events.get() is not None:
        pass
_af = _j.DigitalIn(_c.IO33, pull=_j.UP)
_ag = _j.DigitalIn(_c.IO32, pull=_j.UP)
_ah = _j.DigitalIn(_c.IO35, pull=_j.UP)
_ai = _j.DigitalIn(_c.IO34, pull=_j.UP)
_aj = _j.DigitalIn(_c.IO39, pull=_j.UP)
_ak = False
_al = 1
_am = -1
_an = 1
_ao = 3
_ap = True
_aq = 0.3
_ar = _c.I2C()
_as = _i(_ar, address=106)
_at = None
_au = 20
_av = 6
_aw = 1.0
_ax = 0.2
_ay = 0.05
_az = 1.0
_ba = -1
_bb = False
_bc = 1.0
_bd = 1.5
_be = 1.0
_bf = 0.1
_bg = 8.0
_bh = False
_bi = 0.5
_bj = (0, 0, 255)
_bk = (255, 80, 0)
_bl = (0, 255, 0)
_bm = (0, 120, 255)
_bn = (0, 255, 255)
_bo = (0, 80, 255)
_bp = (120, 0, 255)
_bq = (255, 255, 255)
_br = (255, 120, 0)
_bs = (120, 255, 0)
_bt = (255, 120, 255)
_bu = (255, 255, 0)
_bv = (255, 0, 255)
_bw = (255, 0, 0)
_bx = (255, 0, 0)
_by = (0, 0, 0)

def _bz(valor, minimo, maximo):
    return max(minimo, min(valor, maximo))

def _ca(angulo):
    while angulo > 180:
        angulo -= 360
    while angulo < -180:
        angulo += 360
    return angulo

def _cb(segundos):
    if not isinstance(segundos, (int, float)):
        raise ValueError('segundos debe ser numerico')
    if segundos < 0:
        raise ValueError('Los segundos no pueden ser negativos')

def _cc(velocidad, nombre='velocidad'):
    if not isinstance(velocidad, int):
        raise ValueError(nombre + ' debe ser un numero entero')
    if velocidad < 0 or velocidad > 60:
        raise ValueError(nombre + ' debe estar entre 0 y 60')
    if velocidad % 10 != 0:
        raise ValueError(nombre + ' debe ser multiplo de 10')

def _cd(correccion):
    if not isinstance(correccion, int):
        raise ValueError('La correccion debe ser un numero entero')
    if correccion < -3 or correccion > 3:
        raise ValueError('La correccion debe estar entre -3 y 3')

def _ce(correccion):
    correccion = _bz(float(correccion), -3.0, 3.0)
    magnitud = int(_b.floor(abs(correccion) + 0.5))
    if correccion < 0:
        magnitud = -magnitud
    return int(_bz(magnitud, -3, 3))

def _cf(direccion):
    if direccion == _x:
        return _x
    if direccion == _y:
        return _y
    if isinstance(direccion, str):
        direccion = direccion.strip().lower()
        if direccion in ('adelante', 'frente', 'subir', 'abrir'):
            return _x
        if direccion in ('atras', 'atrás', 'reversa', 'bajar', 'cerrar'):
            return _y
    raise ValueError("direccion debe ser 'adelante' o 'atras'")

def _cg(direccion):
    if not isinstance(direccion, str):
        raise ValueError('direccion de giro debe ser texto')
    direccion = direccion.strip().lower()
    if direccion == 'izquierda':
        return _x
    if direccion == 'derecha':
        return _y
    raise ValueError("direccion debe ser 'izquierda' o 'derecha'")

def _ch(direccion):
    if direccion == 'izquierda':
        return 'derecha'
    return 'izquierda'

def _ci(velocidad_base, correccion=0, direccion='adelante'):
    _cc(velocidad_base, 'velocidad_base')
    _cd(correccion)
    bit_direccion = _cf(direccion)
    indice_velocidad = velocidad_base // 10
    indice_correccion = correccion + 3
    return _v << 7 | bit_direccion << 6 | indice_velocidad << 3 | indice_correccion

def _cj(direccion, velocidad_base):
    _cc(velocidad_base, 'velocidad_base')
    if velocidad_base == 0:
        raise ValueError('La velocidad del giro debe ser al menos 10')
    bit_direccion = _cg(direccion)
    indice_velocidad = velocidad_base // 10
    return _v << 7 | bit_direccion << 6 | indice_velocidad << 3 | _z

def _ck(velocidad_garra, velocidad_pala, direccion='adelante'):
    _cc(velocidad_garra, 'velocidad_garra')
    _cc(velocidad_pala, 'velocidad_pala')
    bit_direccion = _cf(direccion)
    indice_garra = velocidad_garra // 10
    indice_pala = velocidad_pala // 10
    return _w << 7 | bit_direccion << 6 | indice_garra << 3 | indice_pala

def _cl(mensaje):
    global _ab
    if not isinstance(mensaje, int) or mensaje < 0 or mensaje > 255:
        raise ValueError('El mensaje debe ser un byte entre 0 y 255')
    _ab = mensaje

def _cm(velocidad_base, correccion=0, direccion='adelante'):
    _cl(_ci(velocidad_base, correccion, direccion))

def _cn(direccion, velocidad_base):
    _cl(_cj(direccion, velocidad_base))

def _co(velocidad_garra, velocidad_pala, direccion='adelante'):
    _cl(_ck(velocidad_garra, velocidad_pala, direccion))

def _cp():
    _cl(_aa)

def _cq():
    _j.pixel = _bu
    print('Interseccion solamente hacia la derecha.')

def _cr():
    _j.pixel = _bv
    print('Interseccion solamente hacia la izquierda.')

def _cs():
    _j.pixel = _bw
    print('Interseccion tipo T.')

def _ct(tipo):
    if tipo == 'derecha':
        _cq()
    elif tipo == 'izquierda':
        _cr()
    elif tipo == 'T':
        _cs()
    else:
        _j.pixel = _bx

def _cu(data):
    c = 255
    for b in data:
        c ^= b
    return c & 255

def _cv(baud):
    global _r
    if _r:
        _r.deinit()
    _r = _d.UART(tx=_k, rx=_l, baudrate=baud, timeout=0.005, receiver_buffer_size=64)
    _a.sleep(0.05)

def _cw(data):
    _r.write(bytes(data))

def _cx(data):
    paquete = bytearray(data)
    paquete.append(_cu(paquete))
    _cw(paquete)

def _cy():
    global _r
    if _r:
        _r.deinit()
        _r = None
    rx = _e.DigitalInOut(_l)
    rx.direction = _e.Direction.INPUT
    tx = _e.DigitalInOut(_k)
    tx.direction = _e.Direction.OUTPUT
    tx.value = False
    idle_start = _a.monotonic()
    while True:
        if rx.value is False:
            idle_start = _a.monotonic()
        if _a.monotonic() - idle_start > 0.1:
            break
        _a.sleep(0.001)
    tx.value = True
    _a.sleep(0.1)
    tx.value = False
    _a.sleep(0.1)
    rx.deinit()
    tx.deinit()

def _cz():
    _cv(_m)
    _cw([0])
    _a.sleep(0.01)
    _cx([64, 29])
    _cx([73, 0, 0])
    _cx([82] + list(_g.pack('<I', _n)))
    _cx([95, 0, 0, 0, 16, 0, 0, 0, 16])
    _a.sleep(0.01)
    _cx([152, 0, 77, 79, 84, 79, 82, 0, 0, 0])
    _cx([153, 1] + list(_g.pack('<f', 0.0)) + list(_g.pack('<f', 120.0)))
    _cx([153, 2] + list(_g.pack('<f', 0.0)) + list(_g.pack('<f', 100.0)))
    _cx([153, 3] + list(_g.pack('<f', 0.0)) + list(_g.pack('<f', 120.0)))
    _cx([152, 4, 99, 109, 100, 0, 0, 0, 0, 0])
    _cx([136, 5, 16, 0])
    _cx([144, 128, 1, 0, 3, 0])
    _cw([4])
    _a.sleep(0.005)

def _da():
    start = _a.monotonic()
    while _a.monotonic() - start < 2.0:
        data = _r.read(16)
        if data:
            print('RX init:', list(data))
            if 4 in data:
                return True
        _a.sleep(0.005)
    return False

def _db():
    paquete = bytearray([192, _ab & 255])
    paquete.append(_cu(paquete))
    _cw(paquete)

def _dc():
    global _s
    global _t
    global _u
    data = _r.read(64)
    if data and 2 in data:
        _t = _a.monotonic()
        _u = False
        _db()
    demora = _a.monotonic() - _t
    if demora > _o:
        if not _u:
            print('Advertencia: NACK demorado.')
            _u = True
    if demora > _p:
        print('Timeout NACK real. Se perdio el enlace LPF2.')
        _s = False
    return _s

def _dd(segundos):
    fin = _a.monotonic() + segundos
    while _s and _a.monotonic() < fin:
        _dc()
        _a.sleep(0.001)
    return _s

def _de(cambiar_color=True):
    _cp()
    if cambiar_color:
        _j.pixel = _bq
    if not _dd(_q):
        raise RuntimeError('Se perdio el enlace al enviar la parada')

def _df():
    global _s
    global _t
    global _ab
    global _u
    _s = False
    _ab = _aa
    _u = False
    print('Esperando hub idle...')
    _cy()
    print('Enviando inicializacion LPF2...')
    _cz()
    if not _da():
        print('No se recibio ACK.')
        return False
    print('ACK recibido. Cambiando UART a', _n)
    _cv(_n)
    _s = True
    _t = _a.monotonic()
    return True

def _dg(sensor):
    return 1 if sensor.value else 0

def _dh(nivel):
    if _ak:
        return nivel == 0
    return nivel == 1

def _di():
    nivel_ei = _dg(_aj)
    nivel_ci = _dg(_ai)
    nivel_c = _dg(_ah)
    nivel_cd = _dg(_ag)
    nivel_ed = _dg(_af)
    return (nivel_ei, nivel_ci, nivel_c, nivel_cd, nivel_ed, _dh(nivel_ei), _dh(nivel_ci), _dh(nivel_c), _dh(nivel_cd), _dh(nivel_ed))

def _dj(externo_izquierdo, centro_izquierdo, centro, centro_derecho, externo_derecho):
    if externo_izquierdo or externo_derecho:
        return None
    if centro_derecho and (not centro_izquierdo):
        return -_al * _am
    if centro_izquierdo and (not centro_derecho):
        return _al * _am
    return None

def calibrar_giroscopio(cantidad_muestras=40):
    global _at
    if cantidad_muestras <= 0:
        raise ValueError('La cantidad de muestras debe ser mayor que cero')
    _cp()
    _j.pixel = _bk
    suma_z = 0.0
    print('Calibrando giroscopio. No mover el carrito.')
    for _ in range(cantidad_muestras):
        if not _dc():
            raise RuntimeError('Se perdio el enlace durante la calibracion')
        _, _, gz = _as.gyro
        suma_z += _b.degrees(gz)
        _a.sleep(0.003)
    _at = suma_z / cantidad_muestras
    print('Offset Z:', _at, 'grados/s')
    return _at

def _dk(rumbo_actual, tiempo_anterior):
    if _at is None:
        raise RuntimeError('El giroscopio no ha sido calibrado')
    tiempo_actual = _a.monotonic()
    dt = tiempo_actual - tiempo_anterior
    if dt <= 0 or dt > 0.1:
        return (rumbo_actual, tiempo_actual, 0.0)
    _, _, gz = _as.gyro
    velocidad_angular_z = _b.degrees(gz)
    velocidad_angular_z -= _at
    velocidad_angular_z *= _az
    if abs(velocidad_angular_z) < _ay:
        velocidad_angular_z = 0.0
    rumbo_actual += velocidad_angular_z * dt
    rumbo_actual = _ca(rumbo_actual)
    return (rumbo_actual, tiempo_actual, velocidad_angular_z)

def _dl(rumbo_actual, rumbo_objetivo):
    error_rumbo = _ca(rumbo_objetivo - rumbo_actual)
    if abs(error_rumbo) < _ax:
        return (0, error_rumbo)
    correccion_continua = _aw * error_rumbo * _ba
    correccion = _ce(correccion_continua)
    if correccion == 0:
        correccion = 1 if correccion_continua > 0 else -1
    return (correccion, error_rumbo)

def _dm(correccion_logica, direccion_movimiento):
    bit_direccion = _cf(direccion_movimiento)
    if bit_direccion == _y:
        return -correccion_logica
    return correccion_logica

def _dn(rumbo_actual, rumbo_objetivo, velocidad_base, direccion_movimiento, tiempo_anterior, correccion_infrarroja=None):
    rumbo_actual, tiempo_actual, velocidad_angular_z = _dk(rumbo_actual, tiempo_anterior)
    correccion_gyro, error_rumbo = _dl(rumbo_actual, rumbo_objetivo)
    if correccion_infrarroja is None:
        correccion_logica = correccion_gyro
        fuente = 'giroscopio'
    else:
        correccion_logica = correccion_infrarroja
        fuente = 'infrarrojo'
    correccion_enviada = _dm(correccion_logica, direccion_movimiento)
    _cm(velocidad_base, correccion_enviada, direccion=direccion_movimiento)
    return (rumbo_actual, tiempo_actual, correccion_logica, correccion_enviada, error_rumbo, velocidad_angular_z, fuente)

def _do(segundos, velocidad_base, direccion_movimiento, color_led):
    _cb(segundos)
    _cc(velocidad_base, 'velocidad_base')
    if velocidad_base == 0:
        detenerse(segundos)
        return
    if _at is None:
        raise RuntimeError('El giroscopio no ha sido calibrado')
    _j.pixel = color_led
    rumbo_actual = 0.0
    rumbo_objetivo = 0.0
    tiempo_anterior = _a.monotonic()
    fin = tiempo_anterior + segundos
    _cm(velocidad_base, 0, direccion=direccion_movimiento)
    try:
        while _s and _a.monotonic() < fin:
            if not _dc():
                raise RuntimeError('Se perdio el enlace durante el movimiento')
            rumbo_actual, tiempo_anterior, _, _, _, _, _ = _dn(rumbo_actual, rumbo_objetivo, velocidad_base, direccion_movimiento, tiempo_anterior, correccion_infrarroja=None)
            if not _dc():
                raise RuntimeError('Se perdio el enlace durante el movimiento')
            _a.sleep(0.001)
    except Exception:
        _cp()
        if _s:
            _dd(_q)
        raise
    _de(cambiar_color=True)

def avance(segundos, velocidad):
    _do(segundos, velocidad, _x, _bn)

def reversa(segundos, velocidad):
    _do(segundos, velocidad, _y, _bo)

def detenerse(segundos):
    _cb(segundos)
    _cp()
    _j.pixel = _bq
    if not _dd(segundos):
        raise RuntimeError('Se perdio el enlace durante detenerse()')

def _dp(segundos, velocidad_garra, velocidad_pala, direccion='adelante', color_led=_bt):
    _cb(segundos)
    _co(velocidad_garra, velocidad_pala, direccion)
    _j.pixel = color_led
    if not _dd(segundos):
        _cp()
        raise RuntimeError('Se perdio el enlace durante accesorios')
    _de(cambiar_color=True)

def mover_garra(segundos, velocidad, direccion='adelante'):
    _dp(segundos, velocidad_garra=velocidad, velocidad_pala=0, direccion=direccion, color_led=_br)

def mover_pala(segundos, velocidad, direccion='adelante'):
    _dp(segundos, velocidad_garra=0, velocidad_pala=velocidad, direccion=direccion, color_led=_bs)

def mover_garra_pala(segundos, velocidad_garra, velocidad_pala, direccion='adelante'):
    _dp(segundos, velocidad_garra, velocidad_pala, direccion, color_led=_bt)

def _dq(error_angulo, velocidad_base):
    error_angulo = abs(error_angulo)
    if error_angulo > 35:
        return velocidad_base
    if error_angulo > 15:
        return min(velocidad_base, 20)
    return 10

def girar(direccion, angulo, velocidad_base):
    if _at is None:
        raise RuntimeError('El giroscopio no ha sido calibrado')
    if not isinstance(direccion, str):
        raise ValueError('direccion debe ser texto')
    direccion = direccion.strip().lower()
    _cg(direccion)
    if not isinstance(angulo, (int, float)):
        raise ValueError('angulo debe ser numerico')
    if angulo <= 0 or angulo > 360:
        raise ValueError('angulo debe estar entre 0 y 360 grados')
    _cc(velocidad_base, 'velocidad_base')
    if velocidad_base == 0:
        raise ValueError('velocidad_base debe ser al menos 10')
    _j.pixel = _bp
    tiempo_inicio = _a.monotonic()
    tiempo_anterior = tiempo_inicio
    ultimo_diagnostico = 0.0
    tiempo_estable = None
    factor_velocidad = max(1.0, 30.0 / velocidad_base)
    tiempo_maximo = max(5.0, angulo / 90.0 * _bg * factor_velocidad)
    angulo_medido = 0.0
    direccion_actual = direccion
    comando_detenido = False
    _cn(direccion_actual, velocidad_base)
    print('Girando', direccion, '| Angulo objetivo:', angulo, '| Velocidad:', velocidad_base)
    try:
        while True:
            if not _dc():
                raise RuntimeError('Se perdio el enlace durante girar()')
            tiempo_actual = _a.monotonic()
            dt = tiempo_actual - tiempo_anterior
            tiempo_anterior = tiempo_actual
            _, _, gz = _as.gyro
            velocidad_angular_z = (_b.degrees(gz) - _at) * _az
            if abs(velocidad_angular_z) < _ay:
                velocidad_angular_z = 0.0
            if 0 < dt <= 0.1:
                incremento = abs(velocidad_angular_z) * dt
                if direccion_actual == direccion:
                    angulo_medido += incremento
                else:
                    angulo_medido -= incremento
            error_angulo = angulo - angulo_medido
            if _bh:
                if tiempo_actual - ultimo_diagnostico >= _bi:
                    print('Giro:', direccion_actual, '| GZ:', round(velocidad_angular_z, 2), '| Angulo:', round(angulo_medido, 2), '| Error:', round(error_angulo, 2), '| Byte:', _ab)
                    ultimo_diagnostico = tiempo_actual
            if abs(error_angulo) <= _bd:
                if not comando_detenido:
                    _cp()
                    comando_detenido = True
                    tiempo_estable = None
                if abs(velocidad_angular_z) <= _be:
                    if tiempo_estable is None:
                        tiempo_estable = tiempo_actual
                    elif tiempo_actual - tiempo_estable >= _bf:
                        if abs(angulo - angulo_medido) <= _bd:
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
                    nueva_direccion = _ch(direccion)
                velocidad_giro = _dq(error_angulo, velocidad_base)
                direccion_actual = nueva_direccion
                _cn(direccion_actual, velocidad_giro)
                comando_detenido = False
            if not _dc():
                raise RuntimeError('Se perdio el enlace durante girar()')
            if tiempo_actual - tiempo_inicio > tiempo_maximo:
                raise RuntimeError('Tiempo maximo excedido durante girar(); ultimo angulo medido: ' + str(round(angulo_medido, 2)))
            _a.sleep(0.001)
    except Exception:
        _cp()
        if _s:
            _dd(_q)
        raise
    _de(cambiar_color=True)
    print('Giro terminado', '| Objetivo:', angulo, '| Medido:', round(angulo_medido, 2))
    return angulo_medido

def _dr(externo_izquierdo_visto, externo_derecho_visto):
    if externo_izquierdo_visto and externo_derecho_visto:
        return 'T'
    if externo_izquierdo_visto:
        return 'izquierda'
    if externo_derecho_visto:
        return 'derecha'
    return 'desconocida'

def _ds(numero_interseccion, velocidad_base, direccion_movimiento):
    if not isinstance(numero_interseccion, int):
        raise ValueError('numero_interseccion debe ser entero')
    if numero_interseccion <= 0:
        raise ValueError('numero_interseccion debe ser mayor que cero')
    _cc(velocidad_base, 'velocidad_base')
    if velocidad_base == 0:
        raise ValueError('velocidad_base debe ser al menos 10')
    if _at is None:
        raise RuntimeError('El giroscopio no ha sido calibrado')
    bit_direccion = _cf(direccion_movimiento)
    es_reversa = bit_direccion == _y
    rumbo_actual = 0.0
    rumbo_objetivo = 0.0
    tiempo_anterior = _a.monotonic()
    ultimo_diagnostico_sensores = 0.0
    contador_intersecciones = 0
    tipo_interseccion = None
    muestras_interseccion = 0
    muestras_liberacion = 0
    interseccion_activa = False
    externo_derecho_visto = False
    externo_izquierdo_visto = False
    nivel_ei, nivel_ci, nivel_c, nivel_cd, nivel_ed, ext_izq, cen_izq, centro, cen_der, ext_der = _di()
    interseccion_activa = False
    if es_reversa:
        _j.pixel = _bm
        texto_movimiento = 'Reversa'
    else:
        _j.pixel = _bl
        texto_movimiento = 'Avance'
    _cm(velocidad_base, 0, direccion=bit_direccion)
    print(texto_movimiento, 'hasta la interseccion', numero_interseccion, '| Velocidad base:', velocidad_base)
    try:
        while contador_intersecciones < numero_interseccion:
            if not _dc():
                raise RuntimeError('Se perdio la conexion durante ' + ('reversa_hasta()' if es_reversa else 'avance_hasta()'))
            nivel_ei, nivel_ci, nivel_c, nivel_cd, nivel_ed, ext_izq, cen_izq, centro, cen_der, ext_der = _di()
            ahora = _a.monotonic()
            if _ap:
                if ahora - ultimo_diagnostico_sensores >= _aq:
                    print('Sensores: {}{}{}{}{} '.format(nivel_ei, nivel_ci, nivel_c, nivel_cd, nivel_ed).replace('0', '-').replace('1', '▤'))
                    ultimo_diagnostico_sensores = ahora
            interseccion_confirmada = False
            if interseccion_activa:
                if not ext_der and (not ext_izq):
                    muestras_liberacion += 1
                    if muestras_liberacion >= _ao:
                        interseccion_activa = False
                        muestras_liberacion = 0
                        muestras_interseccion = 0
                        externo_derecho_visto = False
                        externo_izquierdo_visto = False
                        _j.pixel = _bm if es_reversa else _bl
                else:
                    muestras_liberacion = 0
            elif ext_der or ext_izq:
                muestras_interseccion += 1
                externo_derecho_visto = externo_derecho_visto or ext_der
                externo_izquierdo_visto = externo_izquierdo_visto or ext_izq
                if muestras_interseccion >= _an:
                    interseccion_confirmada = True
                    interseccion_activa = True
                    muestras_interseccion = 0
                    muestras_liberacion = 0
                    contador_intersecciones += 1
                    tipo_interseccion = _dr(externo_izquierdo_visto, externo_derecho_visto)
                    _ct(tipo_interseccion)
                    print('Interseccion:', contador_intersecciones, '| Tipo:', tipo_interseccion, '| Movimiento:', 'reversa' if es_reversa else 'avance')
                    print('Sensores: {}{}{}{}{} '.format(nivel_ei, nivel_ci, nivel_c, nivel_cd, nivel_ed).replace('0', '-').replace('1', '▤'))
            else:
                muestras_interseccion = 0
                externo_derecho_visto = False
                externo_izquierdo_visto = False
            if interseccion_confirmada and contador_intersecciones >= numero_interseccion:
                _de(cambiar_color=False)
                return tipo_interseccion
            correccion_ir = _dj(ext_izq, cen_izq, centro, cen_der, ext_der)
            rumbo_actual, tiempo_anterior, correccion_logica, correccion_enviada, error_rumbo, velocidad_angular_z, fuente = _dn(rumbo_actual, rumbo_objetivo, velocidad_base, bit_direccion, tiempo_anterior, correccion_infrarroja=correccion_ir)
            if _bb:
                print('Fuente:', fuente, '| Error gyro:', round(error_rumbo, 2), '| Correccion logica:', correccion_logica, '| Correccion enviada:', correccion_enviada)
            if not _dc():
                raise RuntimeError('Se perdio la conexion durante ' + ('reversa_hasta()' if es_reversa else 'avance_hasta()'))
            _a.sleep(0.001)
    except Exception:
        _cp()
        if _s:
            _dd(_q)
        raise
    _de(cambiar_color=False)
    return tipo_interseccion

def avance_hasta(numero_interseccion, velocidad_base=_au):
    return _ds(numero_interseccion, velocidad_base, _x)

def reversa_hasta(numero_interseccion, velocidad_base=_au):
    return _ds(numero_interseccion, velocidad_base, _y)

def _dt():
    _cp()
    _ae()
    _j.pixel = _bj
    print('Handshake completado.')
    print('Presione y suelte el boton BOOT para iniciar.')
    while _s:
        if not _dc():
            return False
        if _ad():
            if not _dd(0.05):
                return False
            return True
        _a.sleep(0.001)
    return False
__all__ = ('avance', 'reversa', 'detenerse', 'girar', 'avance_hasta', 'reversa_hasta', 'mover_garra', 'mover_pala', 'mover_garra_pala', 'calibrar_giroscopio', 'iniciar')

def iniciar(programa_usuario):
    global _s
    print('Iniciando robot IdeaBoard-SPIKE...')
    while True:
        if not _df():
            _j.pixel = _bx
            _a.sleep(1.0)
            continue
        while _s:
            try:
                if not _dt():
                    break
                calibrar_giroscopio()
                programa_usuario()
                _de(cambiar_color=True)
                print('Secuencia finalizada.')
            except KeyboardInterrupt:
                _cp()
                _j.pixel = _by
                if _s:
                    _dd(_q)
                raise
            except Exception as error:
                _cp()
                _j.pixel = _bx
                if _s:
                    _dd(_q)
                    print('Error:', error)
                    print('Se vuelve a esperar el boton.')
                    continue
                print('Error:', error)
                break