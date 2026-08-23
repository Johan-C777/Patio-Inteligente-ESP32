(function () {
  "use strict";

  var INTERVALO_ESTADO_MS = 1500;

  var elTicker = document.getElementById("ticker-comando");
  var elPuntoConexion = document.getElementById("punto-conexion");
  var elTextoConexion = document.getElementById("texto-conexion");
  var elIp = document.getElementById("ip-esp32");
  var elJsonEstado = document.getElementById("json-estado");
  var elBarraRiego = document.getElementById("barra-riego");

  var btnMic = document.getElementById("btn-mic");
  var etiquetaMic = document.getElementById("etiqueta-mic");
  var elVozFrase = document.getElementById("voz-frase");
  var elVozComando = document.getElementById("voz-comando");
  var elVozResultado = document.getElementById("voz-resultado");

  var ETIQUETAS_ESTADO = {
    puerta: "estado-puerta",
    silla: "estado-silla",
    fuente: "estado-fuente",
    riego: "estado-riego",
    color: "estado-color",
    modo: "estado-modo"
  };

  function escaparHtml(texto) {
    var div = document.createElement("div");
    div.textContent = texto;
    return div.innerHTML;
  }

  function marcarBotonActivo(comando) {
    document.querySelectorAll("[data-comando]").forEach(function (boton) {
      boton.classList.toggle(
        "activo",
        boton.getAttribute("data-comando") === comando
      );
    });
  }

  function mostrarBarraRiego() {
    elBarraRiego.style.display = "block";
    var relleno = elBarraRiego.querySelector(".relleno");
    relleno.style.animation = "none";
    void relleno.offsetWidth;
    relleno.style.animation = "vaciar-riego 5s linear forwards";

    setTimeout(function () {
      elBarraRiego.style.display = "none";
    }, 5200);
  }

  function marcarConectado() {
    elPuntoConexion.classList.add("conectado");
    elTextoConexion.textContent = "ESP32 conectado ✅";
    elIp.textContent = location.host;
  }

  function marcarDesconectado() {
    elPuntoConexion.classList.remove("conectado");
    elTextoConexion.textContent = "ESP32 sin respuesta ❌";
  }

  function formatearValor(valor) {
    if (typeof valor === "boolean") return valor ? "si" : "no";
    return String(valor);
  }

  function renderizarEstado(datos) {
    for (var campo in ETIQUETAS_ESTADO) {
      var elemento = document.getElementById(ETIQUETAS_ESTADO[campo]);
      if (elemento && campo in datos) {
        elemento.textContent = formatearValor(datos[campo]);
      }
    }

    elJsonEstado.textContent = JSON.stringify(datos, null, 2);
  }

  function actualizarEstado() {
    return PatioAPI.obtenerEstado()
      .then(function (datos) {
        marcarConectado();
        renderizarEstado(datos);
      })
      .catch(function () {
        marcarDesconectado();
      });
  }

  function enviarComando(comando, origenTexto) {
    marcarBotonActivo(comando);
    elTicker.innerHTML =
      '<span class="marca">&raquo;</span> Enviando: <b>' +
      escaparHtml(comando) +
      "</b> ...";

    return PatioAPI.enviarComando(comando)
      .then(function (datos) {
        var clase = datos.ok ? "ok" : "error";
        elTicker.innerHTML =
          '<span class="marca">&raquo;</span> ' +
          (origenTexto ? escaparHtml(origenTexto) + " &middot; " : "") +
          '<span class="' + clase + '">' +
          escaparHtml(datos.message || "") +
          "</span>";

        if (comando === "regar" && datos.ok) {
          mostrarBarraRiego();
        }

        if (datos.estado) {
          renderizarEstado(datos.estado);
        } else {
          actualizarEstado();
        }

        return datos;
      })
      .catch(function () {
        elTicker.innerHTML =
          '<span class="marca">&raquo;</span> <span class="error">No se pudo contactar al ESP32.</span>';
        marcarDesconectado();
        throw new Error("ESP32 sin respuesta");
      });
  }

  function configurarBotones() {
    document.querySelectorAll("[data-comando]").forEach(function (boton) {
      boton.addEventListener("click", function () {
        enviarComando(boton.getAttribute("data-comando"));
      });
    });
  }

  function configurarVoz() {
    var escuchando = false;

    var reconocimiento = PatioVoice.crearReconocedor({
      onStart: function () {
        escuchando = true;
        btnMic.classList.add("escuchando");
        etiquetaMic.textContent = "Escuchando...";
        elVozFrase.textContent = "--";
        elVozComando.textContent = "--";
        elVozResultado.textContent = "--";
        elVozResultado.className = "valor";
      },

      onEnd: function () {
        escuchando = false;
        btnMic.classList.remove("escuchando");
        etiquetaMic.textContent = "Hablar";
      },

      onError: function (error) {
        elVozResultado.textContent = "Error de reconocimiento (" + error + ")";
        elVozResultado.className = "valor error";
      },

      onResult: function (frase, comando) {
        elVozFrase.textContent = frase;

        if (!comando) {
          elVozComando.textContent = "(sin coincidencia)";
          elVozResultado.textContent = "Frase no reconocida. Intenta de nuevo.";
          elVozResultado.className = "valor error";
          return;
        }

        elVozComando.textContent = comando;
        elVozResultado.textContent = "Enviando al ESP32...";
        elVozResultado.className = "valor";

        enviarComando(comando, "🎙️ voz")
          .then(function (datos) {
            elVozResultado.textContent = datos.ok ? "Ejecutado" : (datos.message || "Error");
            elVozResultado.className = datos.ok ? "valor ok" : "valor error";
          })
          .catch(function () {
            elVozResultado.textContent = "ESP32 sin respuesta";
            elVozResultado.className = "valor error";
          });
      }
    });

    if (!reconocimiento) {
      btnMic.disabled = true;
      etiquetaMic.textContent = "Voz no disponible en este navegador";
      return;
    }

    btnMic.addEventListener("click", function () {
      if (escuchando) {
        reconocimiento.stop();
        return;
      }

      try {
        reconocimiento.start();
      } catch (error) {
        elVozResultado.textContent = "No se pudo iniciar el microfono";
        elVozResultado.className = "valor error";
      }
    });
  }

  configurarBotones();
  configurarVoz();
  actualizarEstado();
  setInterval(actualizarEstado, INTERVALO_ESTADO_MS);
})();
