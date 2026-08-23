import actuadores
import modos

TABLA_ACENTOS = {
    "á": "a",
    "é": "e",
    "í": "i",
    "ó": "o",
    "ú": "u",
    "ñ": "n",
    "ü": "u"
}


def normalizar_texto(texto):
    texto = (texto or "").strip().lower()
    texto = "".join(TABLA_ACENTOS.get(c, c) for c in texto)

    while "  " in texto:
        texto = texto.replace("  ", " ")

    return texto


COMANDOS = {
    "abrir puerta": actuadores.abrir_puerta,
    "cerrar puerta": actuadores.cerrar_puerta,
    "silla izquierda": actuadores.silla_izquierda,
    "silla centro": actuadores.silla_centro,
    "silla derecha": actuadores.silla_derecha,
    "encender fuente": actuadores.encender_fuente,
    "apagar fuente": actuadores.apagar_fuente,
    "regar": actuadores.iniciar_riego,
    "detener riego": actuadores.detener_riego,
    "luz roja": actuadores.luz_roja,
    "luz verde": actuadores.luz_verde,
    "luz azul": actuadores.luz_azul,
    "luz blanca": actuadores.luz_blanca,
    "luz morada": actuadores.luz_morada,
    "apagar luces": actuadores.apagar_luces,
    "modo noche": modos.modo_noche,
    "modo relajacion": modos.modo_relajacion,
    "modo fiesta": modos.modo_fiesta,
    "modo salida": modos.modo_salida
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
