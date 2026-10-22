/** Selectores y coordenadas de las entradas de captura. */
'use strict';

{
  window.scalaris = window.scalaris || {};

  /** Determina qué adaptador es responsable de una entrada. */
  function perteneceCaptura(entrada, configuracion) {
    if (!entrada || entrada.tagName !== 'INPUT') return false;
    const datos = entrada.dataset;
    if (configuracion.tipo === 'ecuaciones') {
      return datos.ecuacionesFila !== undefined && datos.matrizFila === undefined;
    }
    if (configuracion.tipo === 'matrices') {
      return datos.matrizFila !== undefined && datos.geometriaIndice === undefined;
    }
    return datos.geometriaIndice !== undefined;
  }

  /** Lee índices y orientación sin convertir los identificadores de grupo. */
  function leerCoordenadas(entrada, configuracion) {
    const atributos = configuracion.atributos;
    const datos = entrada.dataset;
    return {
      fila: parseInt(datos[atributos.fila], 10),
      columna: parseInt(datos[atributos.columna], 10),
      indice: parseInt(datos[atributos.indice], 10),
      orientacion: datos[atributos.orientacion],
      grupo: datos[atributos.grupo]
    };
  }

  function atributoHtml(nombre) {
    return 'data-' + nombre.replace(/[A-Z]/g, letra => '-' + letra.toLowerCase());
  }

  function selectorGrupo(coordenadas, configuracion) {
    const grupo = configuracion.atributos.grupo;
    return grupo ? '[' + atributoHtml(grupo) + '="' + CSS.escape(String(coordenadas.grupo)) + '"]' : '';
  }

  /** Construye el selector de una celda con su grupo escapado para CSS. */
  function selectorCelda(coordenadas, configuracion) {
    const atributos = configuracion.atributos;
    const grupo = selectorGrupo(coordenadas, configuracion);
    if (configuracion.tipo === 'vectores') {
      return 'input' + grupo + '[' + atributoHtml(atributos.indice) + '="' + coordenadas.indice + '"]';
    }
    return 'input' + grupo + '[' + atributoHtml(atributos.fila) + '="' + coordenadas.fila + '"]' +
      '[' + atributoHtml(atributos.columna) + '="' + coordenadas.columna + '"]';
  }

  /** Obtiene las celdas del grupo, respetando el panel de ecuaciones. */
  function obtenerGrupo(entrada, configuracion) {
    if (configuracion.tipo === 'ecuaciones') {
      const panel = entrada.closest('.panel-tarjeta');
      return panel ? Array.from(panel.querySelectorAll('input[data-ecuaciones-fila]')) : [];
    }
    const coordenadas = leerCoordenadas(entrada, configuracion);
    return Array.from(document.querySelectorAll('input' + selectorGrupo(coordenadas, configuracion)));
  }

  /** Escribe una celda y comunica el cambio mediante el evento nativo. */
  function asignarCelda(coordenadas, configuracion, valor) {
    const entrada = document.querySelector(selectorCelda(coordenadas, configuracion));
    if (!entrada) return;
    entrada.value = valor.trim();
    entrada.dispatchEvent(new Event('input', { bubbles: true }));
  }

  window.scalaris.capturaCeldas = {
    perteneceCaptura, leerCoordenadas, selectorCelda, obtenerGrupo, asignarCelda
  };
}
