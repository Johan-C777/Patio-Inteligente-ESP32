(function (global) {
  "use strict";

  var API_COMANDO = "/api/command";
  var API_ESTADO = "/api/status";

  function validarRespuesta(respuesta) {
    if (!respuesta.ok) {
      throw new Error("HTTP " + respuesta.status);
    }
    return respuesta.json();
  }

  function enviarComando(comando) {
    return fetch(API_COMANDO, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command: comando })
    }).then(validarRespuesta);
  }

  function obtenerEstado() {
    return fetch(API_ESTADO, { cache: "no-store" })
      .then(validarRespuesta);
  }

  global.PatioAPI = {
    enviarComando: enviarComando,
    obtenerEstado: obtenerEstado
  };
})(window);
