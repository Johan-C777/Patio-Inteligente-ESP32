from machine import Pin, PWM
import time
import config
from estado import estado

servo_puerta = None
servo_silla = None
bomba_fuente = None
bomba_riego = None
rgb_r = None
rgb_g = None
rgb_b = None

riego_activo = False
riego_inicio = 0

fiesta_activa = False
fiesta_indice = 0
fiesta_ultimo_cambio = 0

COLORES = {
    "rojo": (255, 0, 0),
    "verde": (0, 255, 0),
    "azul": (0, 0, 255),
    "blanco": (255, 255, 255),
    "morado": (170, 0, 255),
    "apagado": (0, 0, 0)
}

SECUENCIA_FIESTA = ("rojo", "verde", "azul", "blanco", "morado")


def inicializar_hardware():
    global servo_puerta, servo_silla
    global bomba_fuente, bomba_riego
    global rgb_r, rgb_g, rgb_b

    servo_puerta = PWM(Pin(config.PIN_SERVO_PUERTA), freq=config.SERVO_FREQ)
    servo_silla = PWM(Pin(config.PIN_SERVO_SILLA), freq=config.SERVO_FREQ)

    bomba_fuente = Pin(config.PIN_BOMBA_FUENTE, Pin.OUT)
    bomba_riego = Pin(config.PIN_BOMBA_RIEGO, Pin.OUT)

    rgb_r = PWM(Pin(config.PIN_RGB_R), freq=config.RGB_FREQ)
    rgb_g = PWM(Pin(config.PIN_RGB_G), freq=config.RGB_FREQ)
    rgb_b = PWM(Pin(config.PIN_RGB_B), freq=config.RGB_FREQ)

    set_bomba(bomba_fuente, False)
    set_bomba(bomba_riego, False)
    set_rgb(0, 0, 0)
    mover_servo(servo_puerta, config.PUERTA_CERRADA)
    mover_servo(servo_silla, config.SILLA_CENTRO)

    estado.update({
        "puerta": "cerrada",
        "silla": "centro",
        "fuente": False,
        "riego": False,
        "color": "apagado",
        "modo": "normal"
    })


def aplicar_duty(canal, valor):
    try:
        canal.duty_u16(valor)
    except AttributeError:
        canal.duty(int(valor * 1023 / 65535))


def mover_servo(canal, angulo):
    angulo = max(0, min(180, angulo))
    pulso = config.SERVO_MIN_US + (
        (config.SERVO_MAX_US - config.SERVO_MIN_US) * angulo / 180
    )
    periodo = 1000000 // config.SERVO_FREQ
    duty = int(pulso * 65535 / periodo)
    aplicar_duty(canal, duty)


def abrir_puerta():
    mover_servo(servo_puerta, config.PUERTA_ABIERTA)
    estado["puerta"] = "abierta"
    estado["modo"] = "normal"
    return "Puerta abierta"


def cerrar_puerta():
    mover_servo(servo_puerta, config.PUERTA_CERRADA)
    estado["puerta"] = "cerrada"
    estado["modo"] = "normal"
    return "Puerta cerrada"


def silla_izquierda():
    mover_servo(servo_silla, config.SILLA_IZQUIERDA)
    estado["silla"] = "izquierda"
    estado["modo"] = "normal"
    return "Silla a la izquierda"


def silla_centro():
    mover_servo(servo_silla, config.SILLA_CENTRO)
    estado["silla"] = "centro"
    estado["modo"] = "normal"
    return "Silla centrada"


def silla_derecha():
    mover_servo(servo_silla, config.SILLA_DERECHA)
    estado["silla"] = "derecha"
    estado["modo"] = "normal"
    return "Silla a la derecha"


def set_bomba(pin, encender):
    valor = 1 if encender else 0
    if not config.BOMBA_ACTIVA_EN_ALTO:
        valor = 1 - valor
    pin.value(valor)


def encender_fuente():
    set_bomba(bomba_fuente, True)
    estado["fuente"] = True
    estado["modo"] = "normal"
    return "Fuente encendida"


def apagar_fuente():
    set_bomba(bomba_fuente, False)
    estado["fuente"] = False
    estado["modo"] = "normal"
    return "Fuente apagada"


def iniciar_riego():
    global riego_activo, riego_inicio
    set_bomba(bomba_riego, True)
    riego_activo = True
    riego_inicio = time.ticks_ms()
    estado["riego"] = True
    estado["modo"] = "normal"
    return "Riego activado por 5 segundos"


def detener_riego():
    global riego_activo
    set_bomba(bomba_riego, False)
    riego_activo = False
    estado["riego"] = False
    return "Riego detenido"


def actualizar_riego():
    if riego_activo:
        transcurrido = time.ticks_diff(time.ticks_ms(), riego_inicio)
        if transcurrido >= config.DURACION_RIEGO_MS:
            detener_riego()


def duty_rgb(valor):
    duty = int(valor * 65535 / 255)
    return 65535 - duty if config.RGB_ANODO_COMUN else duty


def set_rgb(r, g, b):
    aplicar_duty(rgb_r, duty_rgb(r))
    aplicar_duty(rgb_g, duty_rgb(g))
    aplicar_duty(rgb_b, duty_rgb(b))


def establecer_rgb(r, g, b, nombre, modo="normal"):
    detener_fiesta()
    set_rgb(r, g, b)
    estado["color"] = nombre
    estado["modo"] = modo


def detener_fiesta():
    global fiesta_activa
    fiesta_activa = False


def iniciar_fiesta():
    global fiesta_activa, fiesta_indice, fiesta_ultimo_cambio

    fiesta_activa = True
    fiesta_indice = 0
    fiesta_ultimo_cambio = time.ticks_ms()

    nombre = SECUENCIA_FIESTA[0]
    set_rgb(*COLORES[nombre])
    estado["color"] = "fiesta-" + nombre


def cambiar_luz(nombre):
    detener_fiesta()
    set_rgb(*COLORES[nombre])
    estado["color"] = nombre
    estado["modo"] = "normal"

    if nombre == "apagado":
        return "Luces apagadas"
    return "Luz {} activada".format(nombre)


def luz_roja():
    return cambiar_luz("rojo")


def luz_verde():
    return cambiar_luz("verde")


def luz_azul():
    return cambiar_luz("azul")


def luz_blanca():
    return cambiar_luz("blanco")


def luz_morada():
    return cambiar_luz("morado")


def apagar_luces():
    return cambiar_luz("apagado")


def actualizar_fiesta():
    global fiesta_indice, fiesta_ultimo_cambio

    if not fiesta_activa:
        return

    ahora = time.ticks_ms()
    transcurrido = time.ticks_diff(ahora, fiesta_ultimo_cambio)

    if transcurrido >= config.INTERVALO_FIESTA_MS:
        fiesta_indice = (fiesta_indice + 1) % len(SECUENCIA_FIESTA)
        nombre = SECUENCIA_FIESTA[fiesta_indice]
        set_rgb(*COLORES[nombre])
        estado["color"] = "fiesta-" + nombre
        fiesta_ultimo_cambio = ahora
