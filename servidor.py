import socket
import json
import os
import config
from estado import estado
from comandos import procesar_comando

TIPOS_MIME = {
    ".html": "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
    ".json": "application/json",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml"
}

ARCHIVOS_FRONTEND = {
    "/": "index.html",
    "/index.html": "index.html",
    "/styles.css": "styles.css",
    "/api.js": "api.js",
    "/voice.js": "voice.js",
    "/app.js": "app.js"
}


def crear_servidor():
    servidor = socket.socket()
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(("0.0.0.0", config.HTTP_PORT))
    servidor.listen(4)
    servidor.settimeout(0.2)

    print("Servidor HTTP activo en puerto", config.HTTP_PORT)
    return servidor


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
    ).format(codigo, estados_http.get(codigo, ""), tipo, len(cuerpo))

    cliente.sendall(cabecera.encode("utf-8"))
    if cuerpo:
        cliente.sendall(cuerpo)


def enviar_json(cliente, datos, codigo=200):
    enviar_texto(cliente, json.dumps(datos), "application/json", codigo)


def tipo_mime(ruta):
    punto = ruta.rfind(".")
    extension = ruta[punto:].lower() if punto >= 0 else ""
    return TIPOS_MIME.get(extension, "application/octet-stream")


def enviar_archivo(cliente, nombre_archivo):
    ruta = config.FRONTEND_DIR + "/" + nombre_archivo

    try:
        tamano = os.stat(ruta)[6]
        tipo = tipo_mime(nombre_archivo)

        cabecera = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: {}; charset=utf-8\r\n"
            "Content-Length: {}\r\n"
            "Connection: close\r\n"
            "Cache-Control: no-cache\r\n"
            "\r\n"
        ).format(tipo, tamano)

        cliente.sendall(cabecera.encode("utf-8"))

        with open(ruta, "rb") as archivo:
            while True:
                bloque = archivo.read(config.TAMANO_CHUNK)
                if not bloque:
                    break
                cliente.sendall(bloque)

    except OSError:
        enviar_json(
            cliente,
            {"ok": False, "message": "Archivo frontend no encontrado: " + nombre_archivo},
            404
        )


def leer_solicitud(cliente):
    cliente.settimeout(1.5)
    datos = b""

    try:
        while b"\r\n\r\n" not in datos and len(datos) < config.TAMANO_MAX_SOLICITUD:
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
    ruta = partes[1].split("?", 1)[0]
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
        while len(cuerpo) < content_length and len(cuerpo) < config.TAMANO_MAX_SOLICITUD:
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
            enviar_json(cliente, {"ok": False, "message": "Solicitud invalida"}, 400)
            return

        if metodo == "OPTIONS":
            enviar_texto(cliente, "", "text/plain", 200)
            return

        if metodo == "GET" and ruta in ARCHIVOS_FRONTEND:
            enviar_archivo(cliente, ARCHIVOS_FRONTEND[ruta])
            return

        if metodo == "GET" and ruta == "/api/status":
            enviar_json(cliente, estado)
            return

        if metodo == "POST" and ruta == "/api/command":
            try:
                datos = json.loads(cuerpo.decode("utf-8")) if cuerpo else {}
            except ValueError:
                enviar_json(cliente, {"ok": False, "message": "JSON invalido"}, 400)
                return

            comando = datos.get("command", "")
            ok, mensaje = procesar_comando(comando)

            enviar_json(cliente, {
                "ok": ok,
                "command": comando,
                "message": mensaje,
                "estado": estado
            })
            return

        enviar_json(cliente, {"ok": False, "message": "Ruta no encontrada"}, 404)

    except Exception as error:
        print("Error atendiendo cliente:", error)
        try:
            enviar_json(cliente, {"ok": False, "message": "Error interno"}, 500)
        except Exception:
            pass


def atender_solicitud_pendiente(servidor):
    try:
        cliente, _ = servidor.accept()
    except OSError:
        return

    try:
        atender_cliente(cliente)
    finally:
        try:
            cliente.close()
        except Exception:
            pass
