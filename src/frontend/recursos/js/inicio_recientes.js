(function () {
  'use strict';

  window.scalaris = window.scalaris || {};

  var CLAVE = 'scalaris:recientes';
  var LIMITE_MAXIMO = 4;

  function leerRecientes() {
    try {
      var datoBruto = localStorage.getItem(CLAVE);
      var lista = datoBruto ? JSON.parse(datoBruto) : [];
      if (!Array.isArray(lista)) return { valido: false, identificadores: [] };
      return {
        valido: true,
        identificadores: lista.filter(function (elemento) { return typeof elemento === 'string'; })
      };
    } catch (_) { return { valido: false, identificadores: [] }; }
  }

  function registrarVisita(identificador) {
    if (typeof identificador !== 'string' || !identificador) return;
    try {
      var identificadores = leerRecientes().identificadores.filter(function (elemento) { return elemento !== identificador; });
      identificadores.unshift(identificador);
      localStorage.setItem(CLAVE, JSON.stringify(identificadores.slice(0, LIMITE_MAXIMO)));
    } catch (_) {}
  }

  window.scalaris.recientes = {
    leer: leerRecientes,
    registrar: registrarVisita
  };
})();
