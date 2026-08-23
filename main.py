import time
import actuadores
import red
import servidor


def iniciar():
    actuadores.inicializar_hardware()

    ip = red.iniciar_red()
    if ip is None:
        print("No hay conexion de red disponible")
        return

    http = servidor.crear_servidor()
    print("Patio Inteligente listo en http://{}/".format(ip))

    while True:
        actuadores.actualizar_riego()
        actuadores.actualizar_fiesta()
        servidor.atender_solicitud_pendiente(http)
        time.sleep_ms(10)


try:
    iniciar()
except KeyboardInterrupt:
    print("Programa detenido")
except Exception as error:
    print("Error principal:", error)
