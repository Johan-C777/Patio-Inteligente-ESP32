from machine import Pin, PWM
import time
import network
import socket
import json
import os

# Configuracion
WIFI_SSID = "CAMBIA_AQUI_TU_WIFI"
WIFI_PASSWORD = "CAMBIA_AQUI_TU_CLAVE"

USAR_AP_SI_FALLA = True
AP_SSID = "PatioInteligente"
AP_PASSWORD = "patio1234"

HTTP_PORT = 80
WIFI_TIMEOUT_S = 15

DURACION_RIEGO_MS = 5000
INTERVALO_FIESTA_MS = 500

BOMBA_ACTIVA_EN_ALTO = True
RGB_ANODO_COMUN = False

RUTA_INDEX = "index.html"
TAMANO_MAX_SOLICITUD = 4096
TAMANO_CHUNK = 1024

# Pines
PIN_SERVO_PUERTA = 13
PIN_SERVO_SILLA = 14
PIN_BOMBA_FUENTE = 25
PIN_BOMBA_RIEGO = 26
PIN_RGB_R = 18
PIN_RGB_G = 19
PIN_RGB_B = 21

# Posiciones
PUERTA_CERRADA = 0
PUERTA_ABIERTA = 90

SILLA_IZQUIERDA = 30
SILLA_CENTRO = 90
SILLA_DERECHA = 150

SERVO_FREQ = 50
SERVO_MIN_US = 500
SERVO_MAX_US = 2400
RGB_FREQ = 1000

# Hardware
servo_puerta = PWM(Pin(PIN_SERVO_PUERTA), freq=SERVO_FREQ)
servo_silla = PWM(Pin(PIN_SERVO_SILLA), freq=SERVO_FREQ)

bomba_fuente = Pin(PIN_BOMBA_FUENTE, Pin.OUT)
bomba_riego = Pin(PIN_BOMBA_RIEGO, Pin.OUT)

rgb_r = PWM(Pin(PIN_RGB_R), freq=RGB_FREQ)
rgb_g = PWM(Pin(PIN_RGB_G), freq=RGB_FREQ)
rgb_b = PWM(Pin(PIN_RGB_B), freq=RGB_FREQ)

# Estado
estado = {
    "puerta": "cerrada",
    "silla": "centro",
    "fuente": False,
    "riego": False,
    "color": "apagado",
    "modo": "normal"
}

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

# PWM
def aplicar_duty(canal, valor):
    try:
        canal.duty_u16(valor)
    except AttributeError:
        canal.duty(int(valor * 1023 / 65535))


def mover_servo(canal, angulo):
    angulo = max(0, min(180, angulo))
    pulso = SERVO_MIN_US + ((SERVO_MAX_US - SERVO_MIN_US) * angulo / 180)
    periodo = 1000000 // SERVO_FREQ
    duty = int(pulso * 65535 / periodo)
    aplicar_duty(canal, duty)


# Puerta
def abrir_puerta():
    mover_servo(servo_puerta, PUERTA_ABIERTA)
    estado["puerta"] = "abierta"
    estado["modo"] = "normal"
    return "Puerta abierta"


def cerrar_puerta():
    mover_servo(servo_puerta, PUERTA_CERRADA)
    estado["puerta"] = "cerrada"
    estado["modo"] = "normal"
    return "Puerta cerrada"


# Silla
def silla_izquierda():
    mover_servo(servo_silla, SILLA_IZQUIERDA)
    estado["silla"] = "izquierda"
    estado["modo"] = "normal"
    return "Silla a la izquierda"


def silla_centro():
    mover_servo(servo_silla, SILLA_CENTRO)
    estado["silla"] = "centro"
    estado["modo"] = "normal"
    return "Silla centrada"


def silla_derecha():
    mover_servo(servo_silla, SILLA_DERECHA)
    estado["silla"] = "derecha"
    estado["modo"] = "normal"
    return "Silla a la derecha"


# Bombas
def set_bomba(pin, encender):
    valor = 1 if encender else 0
    if not BOMBA_ACTIVA_EN_ALTO:
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
        if time.ticks_diff(time.ticks_ms(), riego_inicio) >= DURACION_RIEGO_MS:
            detener_riego()


# RGB
def duty_rgb(valor):
    duty = int(valor * 65535 / 255)
    return 65535 - duty if RGB_ANODO_COMUN else duty


def set_rgb(r, g, b):
    aplicar_duty(rgb_r, duty_rgb(r))
    aplicar_duty(rgb_g, duty_rgb(g))
    aplicar_duty(rgb_b, duty_rgb(b))


def detener_fiesta():
    global fiesta_activa
    fiesta_activa = False


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

    if time.ticks_diff(ahora, fiesta_ultimo_cambio) >= INTERVALO_FIESTA_MS:
        fiesta_indice = (fiesta_indice + 1) % len(SECUENCIA_FIESTA)
        nombre = SECUENCIA_FIESTA[fiesta_indice]
        set_rgb(*COLORES[nombre])
        estado["color"] = "fiesta-" + nombre
        fiesta_ultimo_cambio = ahora


# Modos
def modo_noche():
    detener_fiesta()
    cerrar_puerta()
    silla_centro()
    encender_fuente()
    detener_riego()
    set_rgb(0, 0, 60)

    estado["color"] = "azul tenue"
    estado["modo"] = "noche"

    return "Modo noche activado"


def modo_relajacion():
    detener_fiesta()
    silla_centro()
    encender_fuente()
    detener_riego()
    set_rgb(0, 90, 130)

    estado["color"] = "cian suave"
    estado["modo"] = "relajacion"

    return "Modo relajacion activado"


def modo_fiesta():
    global fiesta_activa, fiesta_indice, fiesta_ultimo_cambio

    encender_fuente()
    detener_riego()

    fiesta_activa = True
    fiesta_indice = 0
    fiesta_ultimo_cambio = time.ticks_ms()

    set_rgb(*COLORES[SECUENCIA_FIESTA[0]])

    estado["color"] = "fiesta-" + SECUENCIA_FIESTA[0]
    estado["modo"] = "fiesta"

    return "Modo fiesta activado"


def modo_salida():
    detener_fiesta()
    detener_riego()
    apagar_fuente()
    set_rgb(*COLORES["apagado"])
    cerrar_puerta()
    silla_centro()

    estado["color"] = "apagado"
    estado["modo"] = "salida"

    return "Modo salida activado"


# Comandos
TABLA_ACENTOS = {
    "\u00e1": "a",
    "\u00e9": "e",
    "\u00ed": "i",
    "\u00f3": "o",
    "\u00fa": "u",
    "\u00f1": "n",
    "\u00fc": "u"
}


def normalizar_texto(texto):
    texto = (texto or "").strip().lower()
    texto = "".join(TABLA_ACENTOS.get(c, c) for c in texto)

    while "  " in texto:
        texto = texto.replace("  ", " ")

    return texto


COMANDOS = {
    "abrir puerta": abrir_puerta,
    "cerrar puerta": cerrar_puerta,

    "silla izquierda": silla_izquierda,
    "silla centro": silla_centro,
    "silla derecha": silla_derecha,

    "encender fuente": encender_fuente,
    "apagar fuente": apagar_fuente,

    "regar": iniciar_riego,
    "detener riego": detener_riego,

    "luz roja": luz_roja,
    "luz verde": luz_verde,
    "luz azul": luz_azul,
    "luz blanca": luz_blanca,
    "luz morada": luz_morada,
    "apagar luces": apagar_luces,

    "modo noche": modo_noche,
    "modo relajacion": modo_relajacion,
    "modo fiesta": modo_fiesta,
    "modo salida": modo_salida
}


def procesar_comando(comando):
    comando = normalizar_texto(comando)
    funcion = COMANDOS.get(comando)

    if funcion is None:
        return False, "Comando no reconocido"

    try:
        mensaje = funcion()
        print("Comando:", comando, "->", mensaje)
        return True, mensaje
    except Exception as error:
        print("Error comando:", error)
        return False, "Error ejecutando comando"


# WiFi
def conectar_wifi():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)

    if sta.isconnected():
        return sta.ifconfig()[0]

    print("Conectando WiFi:", WIFI_SSID)
    sta.connect(WIFI_SSID, WIFI_PASSWORD)

    inicio = time.ticks_ms()

    while not sta.isconnected():
        if time.ticks_diff(time.ticks_ms(), inicio) >= WIFI_TIMEOUT_S * 1000:
            print("No fue posible conectar al WiFi")
            sta.active(False)
            return None

        time.sleep_ms(250)

    ip = sta.ifconfig()[0]
    print("WiFi conectado")
    print("IP:", ip)
    return ip


def crear_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)

    try:
        ap.config(essid=AP_SSID, password=AP_PASSWORD)
    except Exception:
        ap.config(essid=AP_SSID)

    time.sleep_ms(300)

    ip = ap.ifconfig()[0]
    print("Modo AP activo")
    print("Red:", AP_SSID)
    print("Clave:", AP_PASSWORD)
    print("IP:", ip)

    return ip


# HTTP
def enviar_texto(cliente, texto, tipo="text/plain", codigo=200):
    estados_http = {
        200: "OK",
        400: "Bad Request",
        404: "Not Found",
        500: "Internal Server Error"
    }

    cuerpo = texto.encode("utf-8")

    cabecera = (
        "HTTP/1.1 {} {}\r\n"
        "Content-Type: {}; charset=utf-8\r\n"
        "Content-Length: {}\r\n"
        "Connection: close\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        "Access-Control-Allow-Headers: Content-Type\r\n"
        "\r\n"
    ).format(
        codigo,
        estados_http.get(codigo, ""),
        tipo,
        len(cuerpo)
    )

    cliente.sendall(cabecera.encode("utf-8"))

    if cuerpo:
        cliente.sendall(cuerpo)


def enviar_json(cliente, datos, codigo=200):
    enviar_texto(
        cliente,
        json.dumps(datos),
        "application/json",
        codigo
    )


def enviar_index(cliente):
    try:
        tamano = os.stat(RUTA_INDEX)[6]

        cabecera = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            "Content-Length: {}\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).format(tamano)

        cliente.sendall(cabecera.encode("utf-8"))

        with open(RUTA_INDEX, "rb") as archivo:
            while True:
                bloque = archivo.read(TAMANO_CHUNK)

                if not bloque:
                    break

                cliente.sendall(bloque)

    except OSError:
        enviar_json(
            cliente,
            {
                "ok": False,
                "message": "No se encontro index.html en el ESP32"
            },
            404
        )


def leer_solicitud(cliente):
    cliente.settimeout(1.5)
    datos = b""

    try:
        while b"\r\n\r\n" not in datos and len(datos) < TAMANO_MAX_SOLICITUD:
            bloque = cliente.recv(512)

            if not bloque:
                break

            datos += bloque
    except OSError:
        pass

    if b"\r\n\r\n" not in datos:
        return None, None, b""

    cabecera, _, cuerpo = datos.partition(b"\r\n\r\n")
    lineas = cabecera.decode("utf-8", "ignore").split("\r\n")

    if not lineas:
        return None, None, b""

    partes = lineas[0].split(" ")

    if len(partes) < 2:
        return None, None, b""

    metodo = partes[0]
    ruta = partes[1]

    content_length = 0

    for linea in lineas[1:]:
        if ":" not in linea:
            continue

        clave, _, valor = linea.partition(":")

        if clave.strip().lower() == "content-length":
            try:
                content_length = int(valor.strip())
            except ValueError:
                content_length = 0

    try:
        while len(cuerpo) < content_length and len(cuerpo) < TAMANO_MAX_SOLICITUD:
            bloque = cliente.recv(512)

            if not bloque:
                break

            cuerpo += bloque
    except OSError:
        pass

    return metodo, ruta, cuerpo


def atender_cliente(cliente):
    try:
        metodo, ruta, cuerpo = leer_solicitud(cliente)

        if metodo is None:
            enviar_json(
                cliente,
                {"ok": False, "message": "Solicitud invalida"},
                400
            )
            return

        if metodo == "OPTIONS":
            enviar_texto(cliente, "", "text/plain", 200)
            return

        if metodo == "GET" and ruta in ("/", "/index.html"):
            enviar_index(cliente)
            return

        if metodo == "GET" and ruta == "/api/status":
            enviar_json(cliente, estado)
            return

        if metodo == "POST" and ruta == "/api/command":
            try:
                datos = json.loads(cuerpo.decode("utf-8")) if cuerpo else {}
            except ValueError:
                enviar_json(
                    cliente,
                    {"ok": False, "message": "JSON invalido"},
                    400
                )
                return

            comando = datos.get("command", "")
            ok, mensaje = procesar_comando(comando)

            enviar_json(
                cliente,
                {
                    "ok": ok,
                    "command": comando,
                    "message": mensaje,
                    "estado": estado
                }
            )
            return

        enviar_json(
            cliente,
            {"ok": False, "message": "Ruta no encontrada"},
            404
        )

    except Exception as error:
        print("Error HTTP:", error)

        try:
            enviar_json(
                cliente,
                {"ok": False, "message": "Error interno"},
                500
            )
        except Exception:
            pass

    finally:
        try:
            cliente.close()
        except Exception:
            pass


def crear_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(("0.0.0.0", HTTP_PORT))
    servidor.listen(4)
    servidor.settimeout(0.05)

    return servidor


# Principal
def inicializar():
    detener_fiesta()

    set_bomba(bomba_fuente, False)
    set_bomba(bomba_riego, False)

    mover_servo(servo_puerta, PUERTA_CERRADA)
    mover_servo(servo_silla, SILLA_CENTRO)

    set_rgb(*COLORES["apagado"])

    estado["puerta"] = "cerrada"
    estado["silla"] = "centro"
    estado["fuente"] = False
    estado["riego"] = False
    estado["color"] = "apagado"
    estado["modo"] = "normal"


def main():
    print()
    print("PATIO INTELIGENTE")
    print("-----------------")

    inicializar()

    ip = conectar_wifi()

    if ip is None and USAR_AP_SI_FALLA:
        ip = crear_ap()

    if ip is None:
        print("Sin conexion de red")
        return

    print("Abrir navegador en:")
    print("http://{}/".format(ip))

    servidor = crear_servidor()
    print("Servidor listo")

    try:
        while True:
            actualizar_riego()
            actualizar_fiesta()

            try:
                cliente, direccion = servidor.accept()
                atender_cliente(cliente)
            except OSError:
                pass

            time.sleep_ms(5)

    except KeyboardInterrupt:
        print("Programa detenido")

    finally:
        try:
            servidor.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
