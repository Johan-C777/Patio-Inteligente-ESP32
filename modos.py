from estado import estado
import actuadores


def modo_noche():
    actuadores.detener_fiesta()
    actuadores.cerrar_puerta()
    actuadores.silla_centro()
    actuadores.encender_fuente()
    actuadores.detener_riego()
    actuadores.set_rgb(0, 0, 60)

    estado["color"] = "azul tenue"
    estado["modo"] = "noche"
    return "Modo noche activado"


def modo_relajacion():
    actuadores.detener_fiesta()
    actuadores.silla_centro()
    actuadores.encender_fuente()
    actuadores.detener_riego()
    actuadores.set_rgb(0, 90, 130)

    estado["color"] = "cian suave"
    estado["modo"] = "relajacion"
    return "Modo relajacion activado"


def modo_fiesta():
    actuadores.encender_fuente()
    actuadores.detener_riego()
    actuadores.iniciar_fiesta()

    estado["modo"] = "fiesta"
    return "Modo fiesta activado"


def modo_salida():
    actuadores.detener_fiesta()
    actuadores.detener_riego()
    actuadores.apagar_fuente()
    actuadores.set_rgb(0, 0, 0)
    actuadores.cerrar_puerta()
    actuadores.silla_centro()

    estado["color"] = "apagado"
    estado["modo"] = "salida"
    return "Modo salida activado"
