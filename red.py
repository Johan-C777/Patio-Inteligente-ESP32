import network
import time
import config


def conectar_wifi():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)

    if sta.isconnected():
        return sta.ifconfig()[0]

    print("Conectando WiFi:", config.WIFI_SSID)
    sta.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

    inicio = time.ticks_ms()

    while not sta.isconnected():
        if time.ticks_diff(time.ticks_ms(), inicio) >= config.WIFI_TIMEOUT_S * 1000:
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
        ap.config(essid=config.AP_SSID, password=config.AP_PASSWORD)
    except Exception:
        ap.config(essid=config.AP_SSID)

    time.sleep_ms(300)

    ip = ap.ifconfig()[0]
    print("Modo AP activo")
    print("Red:", config.AP_SSID)
    print("Clave:", config.AP_PASSWORD)
    print("IP:", ip)
    return ip


def iniciar_red():
    ip = conectar_wifi()

    if ip is None and config.USAR_AP_SI_FALLA:
        ip = crear_ap()

    return ip
