/** Registro y limpieza de eventos y selecciones de las capturas. */
'use strict';

{
  const configuraciones = new Map();
  const registros = new Map();

  function crearRegistro(configuracion) {
    const registro = { configuracion, temporizadorSeleccion: null, controlesResaltados: new Set() };
    registro.manejadores = {
      keydown: evento => window.scalaris.navegacionCaptura.navegarCaptura(evento, registro),
      paste: evento => window.scalaris.pegadoCaptura.pegarCaptura(evento, registro),
      focusin: evento => window.scalaris.focoCaptura.resaltarCaptura(evento, registro),
      focusout: evento => window.scalaris.focoCaptura.desenfocarCaptura(evento, registro)
    };
    Object.entries(registro.manejadores).forEach(([nombre, manejador]) => document.addEventListener(nombre, manejador));
    return registro;
  }

  function retirarRegistro(nombre) {
    const registro = registros.get(nombre);
    if (!registro) return;
    Object.entries(registro.manejadores).forEach(([evento, manejador]) => document.removeEventListener(evento, manejador));
    window.scalaris.navegacionCaptura.cancelarSeleccion(registro);
    window.scalaris.focoCaptura.limpiarResaltado(registro);
    registros.delete(nombre);
  }

  /** Sustituye un adaptador y retira sus manejadores y temporizadores anteriores. */
  function registrarCaptura(nombre, configuracion) {
    retirarRegistro(nombre);
    configuraciones.set(nombre, configuracion);
    registros.set(nombre, crearRegistro(configuracion));
  }

  /** Desmonta una captura y elimina su configuración de restauración. */
  function retirarCaptura(nombre) {
    retirarRegistro(nombre);
    configuraciones.delete(nombre);
  }

  function suspenderCapturas() {
    Array.from(registros.keys()).forEach(retirarRegistro);
  }

  function restaurarCapturas() {
    configuraciones.forEach(function restaurarRegistro(configuracion, nombre) {
      if (!registros.has(nombre)) registros.set(nombre, crearRegistro(configuracion));
    });
  }

  function inicializarRegistro() {
    window.addEventListener('pagehide', suspenderCapturas);
    window.addEventListener('pageshow', restaurarCapturas);
    window.scalaris.capturas = { registrarCaptura, retirarCaptura };
  }

  if (!window.scalaris.capturas) inicializarRegistro();
}
