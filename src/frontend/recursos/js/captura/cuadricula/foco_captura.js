/** Resaltado de fila, columna o componente dentro de cada captura. */
'use strict';

{
  function coincideCoordenada(entrada, activa, configuracion) {
    const atributos = configuracion.atributos;
    if (configuracion.tipo === 'vectores') {
      return entrada.dataset[atributos.indice] === activa.dataset[atributos.indice];
    }
    return entrada.dataset[atributos.fila] === activa.dataset[atributos.fila] ||
      entrada.dataset[atributos.columna] === activa.dataset[atributos.columna];
  }

  /** Actualiza clases de los controles y conserva el fondo de la captura. */
  function resaltarCaptura(evento, registro) {
    const entrada = evento.target;
    const configuracion = registro.configuracion;
    const celdas = window.scalaris.capturaCeldas;
    if (!celdas.perteneceCaptura(entrada, configuracion)) return;
    limpiarResaltado(registro);
    celdas.obtenerGrupo(entrada, configuracion).forEach(function resaltarControl(celda) {
      const control = celda.closest('.q-field__control');
      if (!control) return;
      if (coincideCoordenada(celda, entrada, configuracion)) {
        control.classList.add(configuracion.claseResaltado);
        registro.controlesResaltados.add(control);
      } else control.classList.remove(configuracion.claseResaltado);
    });
  }

  /** Retira también el resaltado cuando se desmonta el registro. */
  function limpiarResaltado(registro) {
    registro.controlesResaltados.forEach(control => control.classList.remove(registro.configuracion.claseResaltado));
    registro.controlesResaltados.clear();
  }

  /** Retira la señal al abandonar una entrada del adaptador correspondiente. */
  function desenfocarCaptura(evento, registro) {
    if (window.scalaris.capturaCeldas.perteneceCaptura(evento.target, registro.configuracion)) limpiarResaltado(registro);
  }

  window.scalaris.focoCaptura = { resaltarCaptura, limpiarResaltado, desenfocarCaptura };
}
