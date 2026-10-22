/** Distribución de texto tabular o vectorial entre entradas de captura. */
'use strict';

{
  function pegarValores(texto, origen, configuracion) {
    const celdas = window.scalaris.capturaCeldas;
    if (configuracion.tipo === 'vectores') {
      texto.split(/[\n\t,;]+/).forEach(function asignarComponente(valor, indice) {
        celdas.asignarCelda({ ...origen, indice: origen.indice + indice }, configuracion, valor);
      });
      return;
    }
    texto.split('\n').forEach(function asignarFila(fila, indiceFila) {
      fila.split('\t').forEach(function asignarColumna(valor, indiceColumna) {
        const destino = { ...origen, fila: origen.fila + indiceFila, columna: origen.columna + indiceColumna };
        celdas.asignarCelda(destino, configuracion, valor);
      });
    });
  }

  /** Conserva el recorte del adaptador y emite un cambio por celda existente. */
  function pegarCaptura(evento, registro) {
    const configuracion = registro.configuracion;
    const entrada = evento.target;
    const celdas = window.scalaris.capturaCeldas;
    if (!celdas.perteneceCaptura(entrada, configuracion)) return;
    evento.preventDefault();
    const portapapeles = evento.clipboardData || window.clipboardData;
    const texto = configuracion.prepararTexto(portapapeles.getData('text'));
    pegarValores(texto, celdas.leerCoordenadas(entrada, configuracion), configuracion);
  }

  window.scalaris.pegadoCaptura = { pegarCaptura };
}
