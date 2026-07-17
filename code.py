from ideaboard_astrobot import *


# ==========================================================
# PROGRAMA DEL USUARIO
# ==========================================================

"""
Funciones disponibles:

	avance(segundos, velocidad)
	reversa(segundos, velocidad)
	detenerse(segundos)
	
	girar(direccion, angulo, velocidad_base

	avance_hasta(numero_interseccion, velocidad_base)
	reversa_hasta(numero_interseccion, velocidad_base)

	mover_garra(segundos, velocidad, direccion)
	mover_pala(segundos, velocidad, direccion)
	mover_garra_pala(segundos, vel_garra, vel_pala, direccion)
	
	calibrar_giroscopio()
"""
	
def pasos_inicio_punto1():
    reversa(segundos=1.5, velocidad=20)
    avance(segundos=1, velocidad=20)
    girar(direccion="derecha", angulo=90, velocidad_base=20)
    reversa(segundos=1, velocidad=20)
    calibrar_giroscopio()
    avance(segundos=1.3, velocidad=30)

def pasos_punto1_punto2():
    avance_hasta(numero_interseccion=3, velocidad_base=40)
    girar(direccion="izquierda", angulo=90, velocidad_base=20)
    mover_pala(segundos=1, velocidad=10, direccion="bajar")
    detenerse(segundos=1)

def programa_usuario():

    pasos_inicio_punto1()
    pasos_punto1_punto2()



# No modificar esta linea.
iniciar(programa_usuario)
