# 🌿 Patio Inteligente con ESP32

Sistema de automatización para una maqueta de patio inteligente desarrollado con **ESP32**, **MicroPython**, una interfaz web en **HTML/CSS/JavaScript** y control mediante **Wi-Fi y comandos de voz**.

El proyecto permite controlar distintos elementos del patio desde un computador o celular conectado a la misma red.

---

## ⚙️ Funcionalidades

El sistema permite controlar:

* 🚪 **Puerta inteligente**

  * Abrir
  * Cerrar

* 🪑 **Silla orientable**

  * Izquierda
  * Centro
  * Derecha

* ⛲ **Fuente de agua**

  * Encender
  * Apagar

* 🌱 **Regadera automática**

  * Activación manual
  * Apagado automático después de aproximadamente 5 segundos

* 🌈 **Iluminación RGB**

  * Rojo
  * Verde
  * Azul
  * Blanco
  * Morado
  * Apagado

* 🎛️ **Modos automáticos**

  * Modo noche
  * Modo relajación
  * Modo fiesta
  * Modo salida

* 🎙️ **Control por voz**

  * Reconocimiento de comandos desde la interfaz web

---

## 🧠 Arquitectura del sistema

```text
             Usuario
                │
        ┌───────┴───────┐
        │               │
       PC            Celular
        │               │
        └───────┬───────┘
                │
          Interfaz HTML
        Botones + Voz
                │
              Wi-Fi
                │
                ▼
              ESP32
           MicroPython
                │
     ┌──────────┼──────────┐
     │          │          │
   Servos     Bombas      RGB
     │          │          │
 Puerta      Fuente    Iluminación
 Silla       Regadera
```

La interfaz web envía comandos al servidor HTTP ejecutado directamente en el ESP32.

Ejemplo:

```text
Usuario pulsa "Abrir puerta"
        ↓
index.html
        ↓
POST /api/command
        ↓
main.py
        ↓
procesar_comando()
        ↓
abrir_puerta()
        ↓
Servo GPIO 13
```

---

## 🔌 Asignación de GPIO

| Elemento       |    GPIO |
| -------------- | ------: |
| Servo puerta   | GPIO 13 |
| Servo silla    | GPIO 14 |
| Bomba fuente   | GPIO 25 |
| Bomba regadera | GPIO 26 |
| RGB rojo       | GPIO 18 |
| RGB verde      | GPIO 19 |
| RGB azul       | GPIO 21 |

> ⚠️ Las bombas **no deben conectarse directamente al ESP32**.
> Deben utilizar un MOSFET, transistor o módulo de potencia adecuado.

Todos los módulos deben compartir una referencia común de **GND**.

---

## 📦 Estructura del repositorio

```text
Patio-Inteligente-ESP32/
│
├── main.py
├── index.html
├── diagram.json
└── README.md
```

### `main.py`

Programa principal ejecutado por el ESP32 mediante MicroPython.

Incluye:

* control de servomotores;
* control de bombas;
* PWM para RGB;
* modos automáticos;
* conexión Wi-Fi;
* servidor HTTP;
* API de comandos;
* estado del sistema.

### `index.html`

Interfaz web responsive que permite controlar el sistema desde PC o celular.

Incluye:

* botones de control;
* visualización del estado;
* control RGB;
* modos automáticos;
* reconocimiento de voz.

### `diagram.json`

Archivo correspondiente al circuito utilizado durante la simulación en **Wokwi**.

---

## 🌐 Comunicación

El ESP32 funciona como servidor web.

La interfaz utiliza principalmente dos rutas:

### Estado del sistema

```http
GET /api/status
```

Devuelve información como:

```json
{
  "puerta": "cerrada",
  "silla": "centro",
  "fuente": false,
  "riego": false,
  "color": "apagado",
  "modo": "normal"
}
```

### Enviar comandos

```http
POST /api/command
```

Ejemplo:

```json
{
  "command": "abrir puerta"
}
```

Todos los comandos terminan pasando por una función central:

```python
procesar_comando()
```

De esta forma, los botones y el control por voz utilizan la misma lógica de control.

---

## 🎙️ Comandos disponibles

### Puerta

```text
abrir puerta
cerrar puerta
```

### Silla

```text
silla izquierda
silla centro
silla derecha
```

### Fuente

```text
encender fuente
apagar fuente
```

### Regadera

```text
regar
detener riego
```

### Iluminación

```text
luz roja
luz verde
luz azul
luz blanca
luz morada
apagar luces
```

### Modos

```text
modo noche
modo relajacion
modo fiesta
modo salida
```

---

## 🎛️ Modos automáticos

| Modo          | Funcionamiento                                                                   |
| ------------- | -------------------------------------------------------------------------------- |
| 🌙 Noche      | Cierra la puerta, centra la silla, enciende la fuente y activa iluminación tenue |
| 🧘 Relajación | Centra la silla, enciende la fuente y activa iluminación azul/cian               |
| 🎉 Fiesta     | Enciende la fuente y ejecuta una secuencia automática de colores RGB             |
| 🚪 Salida     | Detiene riego, apaga fuente y luces, cierra puerta y centra la silla             |

---

## 💻 Configuración del ESP32

El proyecto utiliza **MicroPython**.

Para cargar los archivos se recomienda utilizar **Thonny**.

Los archivos que deben almacenarse dentro del ESP32 son:

```text
main.py
index.html
```

---

## 📡 Configuración Wi-Fi

Dentro de `main.py` se deben modificar:

```python
WIFI_SSID = "NOMBRE_DE_LA_RED"
WIFI_PASSWORD = "CONTRASEÑA"
```

Al iniciar, el ESP32 intentará conectarse a esa red.

Cuando la conexión sea exitosa, la consola mostrará una dirección IP similar a:

```text
WiFi conectado
IP: 192.168.1.XX
```

Desde un computador o celular conectado a la misma red se debe abrir:

```text
http://192.168.1.XX/
```

---

## 📶 Modo de respaldo

Si el ESP32 no puede conectarse a la red configurada, el programa puede crear una red propia:

```text
PatioInteligente
```

Contraseña:

```text
patio1234
```

Después de conectarse a esta red se puede acceder a la IP indicada por el ESP32.

---

## 🧪 Simulación

El control de los actuadores fue verificado mediante **Wokwi**.

Durante la simulación:

* dos servomotores representan puerta y silla;
* dos LEDs representan las bombas de fuente y regadera;
* un LED RGB representa la iluminación del patio.

El archivo:

```text
diagram.json
```

contiene las conexiones utilizadas en la simulación.

---

## 🛠️ Software utilizado

* MicroPython
* Thonny
* Wokwi
* HTML
* CSS
* JavaScript
* GitHub

---

## 📱 Uso

1. Encender el ESP32.
2. Esperar la conexión Wi-Fi.
3. Consultar la IP mostrada en Thonny.
4. Abrir la IP desde el navegador.
5. Utilizar los botones de la interfaz o el botón de micrófono.
6. Verificar la respuesta de los actuadores.

---

## 👥 Integrantes

**Universidad Militar Nueva Granada**
Ingeniería Mecatrónica

* Johan Andrés Canchala
* Luis Miguel Ruiz

---

## 📚 Proyecto académico

Proyecto desarrollado como aplicación de sistemas embebidos, automatización, programación en Python, comunicación Wi-Fi e integración de interfaces hombre-máquina mediante ESP32.
