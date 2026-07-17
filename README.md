# Guía rápida de uso

## 1. Archivo que debe modificar el usuario

El usuario solamente debe editar el archivo `code.py`.

La estructura básica es:

```python
from ideaboard_astrobot import *


def programa_usuario():
    # Escriba aquí las acciones del robot.
    avance_hasta(numero_interseccion=3, velocidad_base=40)
    girar(direccion="izquierda", angulo=90, velocidad_base=20)


# No modificar esta línea.
iniciar(programa_usuario)
```

La biblioteca `ideaboard_astrobot.py` no debe modificarse.

Al iniciar el sistema:

1. IdeaBoard completa la conexión con SPIKE.
2. El LED se ilumina azul y espera el botón BOOT.
3. El usuario presiona y suelta el botón BOOT.
4. El giroscopio se calibra automáticamente.
5. Se ejecuta `programa_usuario()`.
6. Al finalizar, el robot se detiene y vuelve a esperar el botón.

---

## 2. Reglas generales

- Las velocidades permitidas son: `10`, `20`, `30`, `40`, `50` y `60`.
- Los tiempos se indican en segundos y pueden incluir decimales, por ejemplo: `0.5`, `1.5` o `2`.
- Las direcciones de giro son `"izquierda"` y `"derecha"`.
- Para la garra pueden usarse `"abrir"` y `"cerrar"`.
- Para la pala pueden usarse `"subir"` y `"bajar"`.

---

## 3. Funciones de movimiento

### Avanzar durante un tiempo

```python
avance(segundos, velocidad)
```

Ejemplo:

```python
avance(segundos=2, velocidad=30)
```

El robot avanza durante 2 segundos a velocidad 30. Esta función utiliza el giroscopio para mantener el rumbo y no utiliza los sensores infrarrojos.

### Retroceder durante un tiempo

```python
reversa(segundos, velocidad)
```

Ejemplo:

```python
reversa(segundos=1.5, velocidad=20)
```

El robot retrocede durante 1.5 segundos a velocidad 20. Utiliza solamente el giroscopio.

### Detener el robot

```python
detenerse(segundos)
```

Ejemplo:

```python
detenerse(segundos=1)
```

El robot permanece detenido durante 1 segundo.

### Girar usando el giroscopio

```python
girar(direccion, angulo, velocidad_base)
```

Ejemplos:

```python
girar(direccion="derecha", angulo=90, velocidad_base=20)
girar(direccion="izquierda", angulo=45, velocidad_base=20)
```

El ángulo se indica en grados. La función utiliza el giroscopio y no utiliza los sensores infrarrojos.

---

## 4. Movimiento hasta una intersección

### Avanzar hasta una intersección

```python
avance_hasta(numero_interseccion, velocidad_base)
```

Ejemplo:

```python
avance_hasta(numero_interseccion=2, velocidad_base=30)
```

El robot avanza y se detiene en la segunda intersección detectada.

### Retroceder hasta una intersección

```python
reversa_hasta(numero_interseccion, velocidad_base)
```

Ejemplo:

```python
reversa_hasta(numero_interseccion=1, velocidad_base=20)
```

El robot retrocede y se detiene en la primera intersección detectada.

Estas dos funciones utilizan:

- El giroscopio para mantener el rumbo general.
- Los sensores centrales para corregir la posición sobre la línea.
- Los sensores externos para detectar intersecciones.

Ambas funciones retornan el tipo de intersección:

- `"izquierda"`
- `"derecha"`
- `"T"`

---

## 5. Garra y pala

### Mover la garra

```python
mover_garra(segundos, velocidad, direccion)
```

Ejemplos:

```python
mover_garra(segundos=1, velocidad=30, direccion="abrir")
mover_garra(segundos=1, velocidad=30, direccion="cerrar")
```

### Mover la pala

```python
mover_pala(segundos, velocidad, direccion)
```

Ejemplos:

```python
mover_pala(segundos=1, velocidad=20, direccion="subir")
mover_pala(segundos=1, velocidad=20, direccion="bajar")
```

Después de moverse, la pala mantiene su posición automáticamente mediante el control realizado por SPIKE.

### Mover garra y pala simultáneamente

```python
mover_garra_pala(
    segundos,
    velocidad_garra,
    velocidad_pala,
    direccion
)
```

Ejemplo:

```python
mover_garra_pala(segundos=1, velocidad_garra=30, velocidad_pala=20, direccion="adelante")
```

La misma dirección se aplica a ambos mecanismos.

---

## 6. Calibración manual del giroscopio

El giroscopio se calibra automáticamente antes de ejecutar `programa_usuario()`.

También puede recalibrarse durante el programa:

```python
calibrar_giroscopio()
```

El robot debe permanecer completamente quieto mientras el LED está naranja.

---

## 7. Ejemplo completo

```python
from ideaboard_astrobot import *


	
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


iniciar(programa_usuario)
```

---

## 8. Colores del LED de IdeaBoard

El LED cambia de color para indicar qué está haciendo el robot.

| Estado o función | Color del LED |
|---|---|
| Esperando que se presione el botón BOOT | Azul |
| Calibrando el giroscopio | Naranja |
| `avance_hasta()` | Verde |
| `reversa_hasta()` | Celeste |
| `avance()` | Turquesa |
| `reversa()` | Azul oscuro |
| `girar()` | Morado |
| `detenerse()` | Blanco |
| Moviendo la garra | Naranja |
| Moviendo la pala | Verde claro |
| Moviendo la garra y la pala al mismo tiempo | Rosado |
| Intersección hacia la derecha | Amarillo |
| Intersección hacia la izquierda | Fucsia |
| Intersección tipo T | Rojo |
| Error | Rojo |
| Sistema apagado | Apagado |

Cuando el LED está rojo, observe la consola para distinguir si el robot detectó una intersección tipo T o si ocurrió un error.
