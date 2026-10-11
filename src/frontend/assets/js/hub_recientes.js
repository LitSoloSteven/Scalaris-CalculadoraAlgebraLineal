/**
 * Scalaris - Almacenamiento y registro de visitas recientes en el Hub
 */
(function () {
  'use strict';

  window.scalaris = window.scalaris || {};

  var CLAVE = 'scalaris:recent';
  var LIMITE_MAX = 4;

  function leerRecientes() {
    try {
      var datoBruto = localStorage.getItem(CLAVE);
      var lista = datoBruto ? JSON.parse(datoBruto) : [];
      if (!Array.isArray(lista)) return { ok: false, ids: [] };
      return {
        ok: true,
        ids: lista.filter(function (elem) { return typeof elem === 'string'; })
      };
    } catch (_) { return { ok: false, ids: [] }; }
  }

  function registrarVisita(id) {
    if (typeof id !== 'string' || !id) return;
    try {
      var ids = leerRecientes().ids.filter(function (elem) { return elem !== id; });
      ids.unshift(id);
      localStorage.setItem(CLAVE, JSON.stringify(ids.slice(0, LIMITE_MAX)));
    } catch (_) {}
  }

  window.scalaris.recientes = {
    leer: leerRecientes,
    registrar: registrarVisita
  };
})();
