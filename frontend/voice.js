(function (global) {
  "use strict";

  function normalizarTexto(texto) {
    return (texto || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  function contiene(texto, palabra) {
    return texto.indexOf(palabra) !== -1;
  }

  function interpretarComando(fraseOriginal) {
    var t = normalizarTexto(fraseOriginal);

    if (contiene(t, "puerta")) {
      if (contiene(t, "abr")) return "abrir puerta";
      if (contiene(t, "cerr") || contiene(t, "cierr")) return "cerrar puerta";
    }

    if (contiene(t, "silla")) {
      if (contiene(t, "izquierda")) return "silla izquierda";
      if (contiene(t, "derecha")) return "silla derecha";
      if (contiene(t, "centro")) return "silla centro";
    }

    if (contiene(t, "fuente")) {
      if (contiene(t, "apag")) return "apagar fuente";
      if (contiene(t, "enciend") || contiene(t, "activ") || contiene(t, "prend")) {
        return "encender fuente";
      }
    }

    if (contiene(t, "riego") || contiene(t, "regadera") || contiene(t, "regar")) {
      if (contiene(t, "deten") || contiene(t, "para") || contiene(t, "apag")) {
        return "detener riego";
      }
      return "regar";
    }

    if (contiene(t, "luz") || contiene(t, "luces")) {
      if (contiene(t, "apag")) return "apagar luces";
      if (contiene(t, "roja") || contiene(t, "rojo")) return "luz roja";
      if (contiene(t, "verde")) return "luz verde";
      if (contiene(t, "azul")) return "luz azul";
      if (contiene(t, "blanca") || contiene(t, "blanco")) return "luz blanca";
      if (contiene(t, "morada") || contiene(t, "morado") || contiene(t, "purpura")) {
        return "luz morada";
      }
    }

    if (contiene(t, "modo")) {
      if (contiene(t, "noche")) return "modo noche";
      if (contiene(t, "relaj")) return "modo relajacion";
      if (contiene(t, "fiesta")) return "modo fiesta";
      if (contiene(t, "salida")) return "modo salida";
    }

    return null;
  }

  function crearReconocedor(eventos) {
    var Motor = global.SpeechRecognition || global.webkitSpeechRecognition;

    if (!Motor) {
      return null;
    }

    var reconocimiento = new Motor();
    reconocimiento.lang = "es-CO";
    reconocimiento.continuous = false;
    reconocimiento.interimResults = false;
    reconocimiento.maxAlternatives = 1;

    reconocimiento.onstart = function () {
      if (eventos.onStart) eventos.onStart();
    };

    reconocimiento.onend = function () {
      if (eventos.onEnd) eventos.onEnd();
    };

    reconocimiento.onerror = function (evento) {
      if (eventos.onError) eventos.onError(evento.error);
    };

    reconocimiento.onresult = function (evento) {
      var frase = evento.results[0][0].transcript;
      var comando = interpretarComando(frase);
      if (eventos.onResult) eventos.onResult(frase, comando);
    };

    return reconocimiento;
  }

  global.PatioVoice = {
    interpretarComando: interpretarComando,
    crearReconocedor: crearReconocedor
  };
})(window);
