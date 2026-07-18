from hub import port
import device
import motor
import time


# ==========================================================
# PUERTOS
# ==========================================================

PUERTO_IDEABOARD      = port.E
MOTOR_RUEDA_IZQUIERDA = port.F
MOTOR_RUEDA_DERECHA    = port.B
MOTOR_GARRA            = port.C
MOTOR_PALA            = port.D


# ==========================================================
# SENTIDOS FISICOS
# ==========================================================

# Ajustar solamente estos signos si un motor gira al reves.
SENTIDO_MOTOR_RUEDA_IZQUIERDA = -1
SENTIDO_MOTOR_RUEDA_DERECHA = 1
SENTIDO_MOTOR_GARRA = 1
SENTIDO_MOTOR_PALA = -1

# La pala conserva la posicion mediante motor.HOLD.
FACTOR_GRADOS_POR_SEGUNDO = 10


# ==========================================================
# PROTOCOLO DE 8 BITS
# ==========================================================

MODO_RUEDAS = 0
MODO_ACCESORIOS = 1

DIRECCION_ADELANTE = 0
DIRECCION_ATRAS = 1

CODIGO_GIRO_SOBRE_EJE = 7
MENSAJE_DETENER = 0b00000011

MOSTRAR_DIAGNOSTICO = True

ultimo_byte = None
seguridad_desconexion_aplicada = False

# Protocolo de movimiento por distancia.
CONTROL_DISTANCIA_INICIO = 0xFF
CONTROL_DISTANCIA_PAUSA = 0xF7
CONTROL_DISTANCIA_REANUDAR = 0xEF
CONTROL_DISTANCIA_CANCELAR = 0xE7
recepcion_distancia_estado = 0
recepcion_distancia_direccion = 0
recepcion_distancia_velocidad = 0
recepcion_distancia_grados = 0
recepcion_distancia_bloques = 0
recepcion_distancia_toggle = 0

movimiento_distancia_activo = False
movimiento_distancia_pausado = False
distancia_objetivo_grados = 0
distancia_direccion = 0
distancia_velocidad = 0
distancia_correccion = 0
distancia_terminada = False
distancia_inicio_izquierda = 0
distancia_inicio_derecha = 0
distancia_izquierda_completa = False
distancia_derecha_completa = False


# ==========================================================
# ESTADO DE LA PALA
# ==========================================================

pala_en_movimiento = False
pala_manteniendo_posicion = False
posicion_pala = None


# ==========================================================
# FUNCIONES GENERALES
# ==========================================================


def limitar(valor, minimo, maximo):
    return max(minimo, min(valor, maximo))


def extraer_valor(datos):
    if datos is None:
        return None

    if isinstance(datos, (tuple, list)):
        if len(datos) == 0:
            return None

        return datos[0]

    return datos


def convertir_a_byte(valor_firmado):
    """
    SPIKE interpreta DATA8 como -128..127. El AND recupera los ocho
    bits originales enviados por IdeaBoard.
    """
    return int(valor_firmado) & 0xFF


def byte_a_binario(byte):
    """
    Convierte un byte a texto binario de ocho caracteres.

    Se implementa manualmente porque el firmware de SPIKE no incluye
    la funcion global format().
    """
    byte = int(byte) & 0xFF
    resultado = ""

    for posicion in range(7, -1, -1):
        if byte & (1 << posicion):
            resultado += "1"
        else:
            resultado += "0"

    return resultado


def decodificar_campos(byte):
    modo = (byte >> 7) & 0b1
    direccion = (byte >> 6) & 0b1
    campo_1 = (byte >> 3) & 0b111
    campo_2 = byte & 0b111

    return modo, direccion, campo_1, campo_2


# ==========================================================
# CONTROL BASICO DE MOTORES
# ==========================================================


def ejecutar_motor(puerto_motor, velocidad_logica, sentido_fisico):
    velocidad_logica = limitar(velocidad_logica, -100, 100)

    velocidad_dps = int(
        velocidad_logica
        * FACTOR_GRADOS_POR_SEGUNDO
        * sentido_fisico
    )

    if velocidad_dps == 0:
        motor.stop(puerto_motor)
    else:
        motor.run(puerto_motor, velocidad_dps)


def detener_motor_seguro(puerto_motor):
    try:
        motor.stop(puerto_motor)
    except Exception:
        pass


def detener_motor_manteniendo(puerto_motor):
    try:
        motor.stop(puerto_motor, stop=motor.HOLD)
        return True
    except Exception as error_hold:
        try:
            motor.stop(puerto_motor)
            return False
        except Exception:
            raise error_hold


def detener_ruedas():
    detener_motor_seguro(MOTOR_RUEDA_IZQUIERDA)
    detener_motor_seguro(MOTOR_RUEDA_DERECHA)


def detener_garra():
    detener_motor_seguro(MOTOR_GARRA)


def detener_pala_totalmente():
    global pala_en_movimiento
    global pala_manteniendo_posicion

    detener_motor_seguro(MOTOR_PALA)
    pala_en_movimiento = False
    pala_manteniendo_posicion = False


def detener_todo():
    """Detencion total, usada al iniciar o ante un error no recuperable."""
    detener_ruedas()
    detener_garra()
    detener_pala_totalmente()


# ==========================================================
# SOSTENIMIENTO DE LA PALA
# ==========================================================


def enviar_soltar_posicion_pala():
    """
    Equivalente al mensaje de bloques SoltarPosicionPala.
    Solo se usa antes de comenzar un nuevo movimiento del motor E.
    """
    global pala_manteniendo_posicion

    if pala_manteniendo_posicion:
        motor.stop(MOTOR_PALA)
        pala_manteniendo_posicion = False

        if MOSTRAR_DIAGNOSTICO:
            print("Evento: SoltarPosicionPala")


def enviar_mantener_posicion_pala():
    global pala_en_movimiento
    global pala_manteniendo_posicion
    global posicion_pala

    try:
        posicion_pala = motor.relative_position(MOTOR_PALA)
    except Exception:
        posicion_pala = None

    hold_disponible = detener_motor_manteniendo(MOTOR_PALA)
    pala_en_movimiento = False
    pala_manteniendo_posicion = True

    if MOSTRAR_DIAGNOSTICO:
        print(
            "Evento: MantenerPosicionPala",
            "| Posicion:", posicion_pala,
            "| Modo:", "HOLD" if hold_disponible else "BRAKE"
        )


def finalizar_movimiento_pala_si_corresponde():
    """
    El final del movimiento se identifica cuando llega un byte diferente.
    Antes de aplicar ese nuevo byte, se activa el sostenimiento.
    """
    if pala_en_movimiento:
        enviar_mantener_posicion_pala()


def detener_seguro_con_pala():
    """
    Detiene ruedas y garra. Si la pala estaba moviendose, activa el
    sostenimiento en vez de dejarla caer.
    """
    detener_ruedas()
    detener_garra()

    if pala_en_movimiento:
        try:
            enviar_mantener_posicion_pala()
        except Exception:
            detener_pala_totalmente()


# ==========================================================
# MOVIMIENTO POR DISTANCIA
# ==========================================================


def cancelar_movimiento_distancia():
    global movimiento_distancia_activo
    global movimiento_distancia_pausado
    global distancia_correccion
    global distancia_terminada

    detener_ruedas()
    movimiento_distancia_activo = False
    movimiento_distancia_pausado = False
    distancia_correccion = 0
    distancia_terminada = False



def aplicar_velocidades_movimiento_distancia():
    """Aplica velocidad base y corrección sin reiniciar los encoders."""
    if (
        not movimiento_distancia_activo
        or movimiento_distancia_pausado
        or distancia_terminada
    ):
        return

    signo = 1 if distancia_direccion == DIRECCION_ADELANTE else -1
    velocidad_izquierda = (
        distancia_velocidad - distancia_correccion
    ) * signo
    velocidad_derecha = (
        distancia_velocidad + distancia_correccion
    ) * signo

    if not distancia_izquierda_completa:
        ejecutar_motor(
            MOTOR_RUEDA_IZQUIERDA,
            velocidad_izquierda,
            SENTIDO_MOTOR_RUEDA_IZQUIERDA
        )

    if not distancia_derecha_completa:
        ejecutar_motor(
            MOTOR_RUEDA_DERECHA,
            velocidad_derecha,
            SENTIDO_MOTOR_RUEDA_DERECHA
        )


def iniciar_movimiento_distancia(direccion, velocidad, grados_objetivo):
    global movimiento_distancia_activo
    global movimiento_distancia_pausado
    global distancia_objetivo_grados
    global distancia_direccion
    global distancia_velocidad
    global distancia_correccion
    global distancia_terminada
    global distancia_inicio_izquierda
    global distancia_inicio_derecha
    global distancia_izquierda_completa
    global distancia_derecha_completa

    detener_garra()
    distancia_direccion = direccion
    distancia_velocidad = velocidad
    distancia_correccion = 0
    distancia_terminada = False
    distancia_objetivo_grados = grados_objetivo
    distancia_inicio_izquierda = motor.relative_position(
        MOTOR_RUEDA_IZQUIERDA
    )
    distancia_inicio_derecha = motor.relative_position(
        MOTOR_RUEDA_DERECHA
    )
    distancia_izquierda_completa = False
    distancia_derecha_completa = False
    movimiento_distancia_activo = True
    movimiento_distancia_pausado = False

    aplicar_velocidades_movimiento_distancia()

    print(
        "Distancia iniciada | Grados:", grados_objetivo,
        "| Velocidad:", velocidad,
        "| Direccion:",
        "adelante" if direccion == DIRECCION_ADELANTE else "atras",
        "| Control: encoder + correccion externa"
    )



def pausar_movimiento_distancia():
    global movimiento_distancia_pausado

    if (
        movimiento_distancia_activo
        and not movimiento_distancia_pausado
        and not distancia_terminada
    ):
        detener_ruedas()
        movimiento_distancia_pausado = True
        print("Distancia pausada")



def reanudar_movimiento_distancia():
    global movimiento_distancia_pausado

    if (
        movimiento_distancia_activo
        and movimiento_distancia_pausado
        and not distancia_terminada
    ):
        movimiento_distancia_pausado = False
        aplicar_velocidades_movimiento_distancia()
        print("Distancia reanudada")



def actualizar_movimiento_distancia():
    global distancia_izquierda_completa
    global distancia_derecha_completa
    global distancia_terminada

    if (
        not movimiento_distancia_activo
        or movimiento_distancia_pausado
        or distancia_terminada
    ):
        return

    actual_izquierda = motor.relative_position(MOTOR_RUEDA_IZQUIERDA)
    actual_derecha = motor.relative_position(MOTOR_RUEDA_DERECHA)
    recorrido_izquierda = abs(
        actual_izquierda - distancia_inicio_izquierda
    )
    recorrido_derecha = abs(
        actual_derecha - distancia_inicio_derecha
    )

    if (
        not distancia_izquierda_completa
        and recorrido_izquierda >= distancia_objetivo_grados
    ):
        motor.stop(MOTOR_RUEDA_IZQUIERDA)
        distancia_izquierda_completa = True

    if (
        not distancia_derecha_completa
        and recorrido_derecha >= distancia_objetivo_grados
    ):
        motor.stop(MOTOR_RUEDA_DERECHA)
        distancia_derecha_completa = True

    if distancia_izquierda_completa and distancia_derecha_completa:
        detener_ruedas()
        distancia_terminada = True
        print("Distancia terminada | Grados:", distancia_objetivo_grados)



def actualizar_correccion_movimiento_distancia(
    direccion,
    indice_velocidad,
    indice_correccion
):
    """
    Actualiza las velocidades diferenciales sin reiniciar el objetivo.

    Retorna None cuando el byte debe procesarse como una orden normal.
    """
    global distancia_velocidad
    global distancia_correccion

    if not movimiento_distancia_activo:
        return None

    if indice_correccion == CODIGO_GIRO_SOBRE_EJE:
        return None

    # Una orden de velocidad cero cierra la sesión de distancia.
    if indice_velocidad == 0:
        cancelar_movimiento_distancia()
        return {"modo": "distancia_finalizada_por_ideaboard"}

    # Un cambio de dirección corresponde a una nueva orden normal.
    if direccion != distancia_direccion:
        return None

    distancia_velocidad = indice_velocidad * 10
    distancia_correccion = indice_correccion - 3

    # Si los encoders ya terminaron, se conserva la parada aunque IdeaBoard
    # siga enviando correcciones durante su tiempo de espera conservador.
    if not distancia_terminada and not movimiento_distancia_pausado:
        aplicar_velocidades_movimiento_distancia()

    return {
        "modo": "distancia_correccion_gyro",
        "base": distancia_velocidad,
        "correccion": distancia_correccion,
        "terminada": distancia_terminada
    }


def es_paquete_control_distancia(byte):
    return (byte & 0x87) == 0x87


def procesar_control_distancia(byte):
    global recepcion_distancia_estado
    global recepcion_distancia_direccion
    global recepcion_distancia_velocidad
    global recepcion_distancia_grados
    global recepcion_distancia_bloques
    global recepcion_distancia_toggle

    if recepcion_distancia_estado == 0:
        if byte == CONTROL_DISTANCIA_INICIO:
            if movimiento_distancia_activo:
                cancelar_movimiento_distancia()
            recepcion_distancia_estado = 1
            return {"modo": "distancia_inicio"}

        if byte == CONTROL_DISTANCIA_PAUSA and movimiento_distancia_activo:
            pausar_movimiento_distancia()
            return {"modo": "distancia_pausa"}

        if byte == CONTROL_DISTANCIA_REANUDAR and movimiento_distancia_activo:
            reanudar_movimiento_distancia()
            return {"modo": "distancia_reanudar"}

        if byte == CONTROL_DISTANCIA_CANCELAR and movimiento_distancia_activo:
            cancelar_movimiento_distancia()
            return {"modo": "distancia_cancelar"}

        return None

    if not es_paquete_control_distancia(byte):
        recepcion_distancia_estado = 0
        return None

    nibble = (byte >> 3) & 0x0F

    if recepcion_distancia_estado == 1:
        direccion = (nibble >> 3) & 1
        indice_velocidad = nibble & 0x07
        if indice_velocidad < 1 or indice_velocidad > 6:
            recepcion_distancia_estado = 0
            raise ValueError("Velocidad de distancia invalida")

        recepcion_distancia_direccion = direccion
        recepcion_distancia_velocidad = indice_velocidad * 10
        recepcion_distancia_grados = 0
        recepcion_distancia_bloques = 0
        recepcion_distancia_toggle = 1 - direccion
        recepcion_distancia_estado = 2
        return {"modo": "distancia_metadata"}

    toggle = (nibble >> 3) & 1
    bloque = nibble & 0x07
    if toggle != recepcion_distancia_toggle:
        recepcion_distancia_estado = 0
        raise ValueError("Secuencia de distancia invalida")

    recepcion_distancia_grados = (recepcion_distancia_grados << 3) | bloque
    recepcion_distancia_bloques += 1
    recepcion_distancia_toggle = 1 - recepcion_distancia_toggle

    if recepcion_distancia_bloques >= 6:
        grados = recepcion_distancia_grados
        direccion = recepcion_distancia_direccion
        velocidad = recepcion_distancia_velocidad
        recepcion_distancia_estado = 0
        iniciar_movimiento_distancia(direccion, velocidad, grados)
        return {"modo": "distancia_ejecutando", "grados": grados, "velocidad": velocidad}

    return {"modo": "distancia_dato", "bloque": recepcion_distancia_bloques}


def aplicar_seguridad_desconexion():
    detener_ruedas()
    detener_garra()
    if pala_en_movimiento:
        try:
            enviar_mantener_posicion_pala()
        except Exception:
            detener_pala_totalmente()
    cancelar_movimiento_distancia()


# ==========================================================
# MODO RUEDAS
# ==========================================================


def aplicar_ruedas(direccion, indice_velocidad, indice_correccion):
    # Un comando de ruedas detiene la garra, pero NO detiene la pala si
    # esta aplicando el torque de sostenimiento.
    detener_garra()

    if indice_velocidad > 6:
        raise ValueError("Indice de velocidad de ruedas reservado")

    velocidad_base = indice_velocidad * 10

    if indice_correccion == CODIGO_GIRO_SOBRE_EJE:
        # Mapeo ajustado a la orientacion fisica usada en las versiones V5.
        if direccion == DIRECCION_ADELANTE:
            velocidad_a = velocidad_base
            velocidad_b = -velocidad_base
            modo_detallado = "giro_izquierda"
        else:
            velocidad_a = -velocidad_base
            velocidad_b = velocidad_base
            modo_detallado = "giro_derecha"

        correccion = None

    else:
        if indice_correccion > 6:
            raise ValueError("Indice de correccion invalido")

        correccion = indice_correccion - 3
        signo_direccion = (
            1 if direccion == DIRECCION_ADELANTE else -1
        )

        velocidad_a = (
            velocidad_base - correccion
        ) * signo_direccion

        velocidad_b = (
            velocidad_base + correccion
        ) * signo_direccion

        modo_detallado = (
            "ruedas_adelante"
            if direccion == DIRECCION_ADELANTE
            else "ruedas_atras"
        )

    ejecutar_motor(MOTOR_RUEDA_IZQUIERDA, velocidad_a, SENTIDO_MOTOR_RUEDA_IZQUIERDA)
    ejecutar_motor(MOTOR_RUEDA_DERECHA, velocidad_b, SENTIDO_MOTOR_RUEDA_DERECHA)

    return {
        "modo": modo_detallado,
        "base": velocidad_base,
        "correccion": correccion,
        "A": velocidad_a,
        "B": velocidad_b,
        "pala_sostenida": pala_manteniendo_posicion
    }


# ==========================================================
# MODO GARRA / PALA
# ==========================================================


def aplicar_accesorios(direccion, indice_garra, indice_pala):
    """
    Reglas de la pala:
    1. Si la pala se va a mover, llamar SoltarPosicionPala primero.
    2. Mover E y marcar pala_en_movimiento.
    3. Al llegar el siguiente byte, llamar MantenerPosicionPala.
    4. Si solamente se mueve la garra, no tocar E.
    """
    global pala_en_movimiento

    detener_ruedas()

    if indice_garra > 6:
        raise ValueError("Indice de velocidad de garra reservado")

    if indice_pala > 6:
        raise ValueError("Indice de velocidad de pala reservado")

    velocidad_garra = indice_garra * 10
    velocidad_pala = indice_pala * 10

    signo_direccion = (
        1 if direccion == DIRECCION_ADELANTE else -1
    )

    velocidad_c = velocidad_garra * signo_direccion
    velocidad_e = velocidad_pala * signo_direccion

    # La garra siempre sigue el paquete actual.
    ejecutar_motor(MOTOR_GARRA, velocidad_c, SENTIDO_MOTOR_GARRA)

    if velocidad_pala > 0:
        # Enviar SoltarPosicionPala antes de mover E.
        enviar_soltar_posicion_pala()

        ejecutar_motor(MOTOR_PALA, velocidad_e, SENTIDO_MOTOR_PALA)
        pala_en_movimiento = True
        estado_pala = "moviendo"

    else:
        # No llamar motor.stop(E). Si solo se mueve la garra, la pala
        # conserva el sostenimiento que ya tenia.
        estado_pala = (
            "manteniendo"
            if pala_manteniendo_posicion
            else "sin_movimiento"
        )

    return {
        "modo": (
            "accesorios_adelante"
            if direccion == DIRECCION_ADELANTE
            else "accesorios_atras"
        ),
        "C_garra": velocidad_c,
        "E_pala": velocidad_e,
        "estado_pala": estado_pala
    }


# ==========================================================
# APLICACION DEL BYTE
# ==========================================================


def aplicar_byte(byte):
    resultado_control = procesar_control_distancia(byte)

    if resultado_control is not None:
        return resultado_control

    finalizar_movimiento_pala_si_corresponde()
    modo, direccion, campo_1, campo_2 = decodificar_campos(byte)

    if movimiento_distancia_activo and modo == MODO_RUEDAS:
        resultado_distancia = actualizar_correccion_movimiento_distancia(
            direccion,
            campo_1,
            campo_2
        )

        if resultado_distancia is not None:
            return resultado_distancia

    # Cualquier orden incompatible cancela primero el movimiento por
    # distancia y luego se procesa normalmente.
    if movimiento_distancia_activo:
        cancelar_movimiento_distancia()

    if modo == MODO_RUEDAS:
        return aplicar_ruedas(direccion, campo_1, campo_2)

    return aplicar_accesorios(direccion, campo_1, campo_2)



# ==========================================================
# BUCLE PRINCIPAL
# ==========================================================


print("Esperando comandos LPF2 de 8 bits por el puerto D...")
detener_todo()

while True:
    try:
        actualizar_movimiento_distancia()
        datos = device.data(PUERTO_IDEABOARD)
        valor_firmado = extraer_valor(datos)

        if valor_firmado is not None:
            seguridad_desconexion_aplicada = False
            byte = convertir_a_byte(valor_firmado)

            if byte != ultimo_byte:
                resultado = aplicar_byte(byte)
                if MOSTRAR_DIAGNOSTICO:
                    print(
                        "Recibido:", valor_firmado,
                        "| Byte:", byte,
                        "| Bin:", byte_a_binario(byte),
                        "|", resultado
                    )
                ultimo_byte = byte

    except Exception as error:
        ultimo_byte = None
        errno = getattr(error, "errno", None)
        es_enodev = errno == 19 or "ENODEV" in str(error)

        if not seguridad_desconexion_aplicada:
            aplicar_seguridad_desconexion()
            seguridad_desconexion_aplicada = True
            if es_enodev:
                print("IdeaBoard desconectada. Motores en estado seguro.")
            else:
                print("Error de comunicacion o decodificacion:", error)

        time.sleep(0.10)

    time.sleep(0.02)