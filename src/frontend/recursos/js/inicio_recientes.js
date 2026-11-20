{
  'use strict';

  window.scalaris = window.scalaris || {};

  const CLAVE = 'scalaris:recientes';
  const LIMITE_MAXIMO = 4;
  const LIMITE_LECTURA = 16;
  const LIMITE_IDENTIFICADOR = 64;
  const LIMITE_ALMACENAMIENTO = 2048;

  function esIdentificadorValido(elemento) {
    return typeof elemento === 'string' && elemento.trim().length > 0 && elemento.length <= LIMITE_IDENTIFICADOR;
  }

  function leerRecientes() {
    try {
      const datoBruto = localStorage.getItem(CLAVE);
      if (datoBruto && datoBruto.length > LIMITE_ALMACENAMIENTO) return { valido: false, identificadores: [] };
      const lista = datoBruto ? JSON.parse(datoBruto) : [];
      if (!Array.isArray(lista)) return { valido: false, identificadores: [] };
      return {
        valido: true,
        identificadores: lista.slice(0, LIMITE_LECTURA).filter(esIdentificadorValido)
      };
    } catch (_) { return { valido: false, identificadores: [] }; }
  }

  function registrarVisita(identificador) {
    if (!esIdentificadorValido(identificador)) return;
    try {
      const identificadores = leerRecientes().identificadores.filter(elemento => elemento !== identificador);
      identificadores.unshift(identificador);
      localStorage.setItem(CLAVE, JSON.stringify(identificadores.slice(0, LIMITE_MAXIMO)));
    } catch (_) {}
  }

  window.scalaris.recientes = {
    leer: leerRecientes,
    registrar: registrarVisita
  };
}
