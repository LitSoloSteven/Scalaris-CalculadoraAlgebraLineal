/** Navegación de captura sin animación para acciones de teclado. */
'use strict';

{
  const DEMORA_SELECCION = 10;
  const DESPLAZAMIENTOS = {
    ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1], Enter: [1, 0]
  };

  function permiteNavegar(entrada, tecla) {
    if (!Object.hasOwn(DESPLAZAMIENTOS, tecla)) return false;
    if (tecla === 'ArrowLeft') return entrada.selectionStart === 0;
    if (tecla === 'ArrowRight') return entrada.selectionEnd === entrada.value.length;
    return true;
  }

  function desplazarCoordenadas(coordenadas, configuracion, tecla) {
    const [vertical, horizontal] = DESPLAZAMIENTOS[tecla];
    const destino = { ...coordenadas };
    if (configuracion.tipo === 'vectores') {
      const incremento = coordenadas.orientacion === 'columna' ? vertical : horizontal;
      destino.indice += tecla === 'Enter' ? 1 : incremento;
    } else {
      destino.fila += vertical;
      destino.columna += horizontal;
    }
    return destino;
  }

  /** Cancela una selección diferida que pertenece al registro indicado. */
  function cancelarSeleccion(registro) {
    if (registro.temporizadorSeleccion !== null) clearTimeout(registro.temporizadorSeleccion);
    registro.temporizadorSeleccion = null;
  }

  function enfocarDestino(entrada, registro) {
    cancelarSeleccion(registro);
    entrada.focus();
    registro.temporizadorSeleccion = setTimeout(function seleccionarDestino() {
      registro.temporizadorSeleccion = null;
      if (entrada.isConnected && document.activeElement === entrada) entrada.select();
    }, DEMORA_SELECCION);
  }

  /** Mueve el foco al destino existente y respeta el cursor horizontal. */
  function navegarCaptura(evento, registro) {
    const entrada = evento.target;
    const configuracion = registro.configuracion;
    const celdas = window.scalaris.capturaCeldas;
    if (!celdas.perteneceCaptura(entrada, configuracion) || !permiteNavegar(entrada, evento.key)) return;
    const coordenadas = celdas.leerCoordenadas(entrada, configuracion);
    const destino = desplazarCoordenadas(coordenadas, configuracion, evento.key);
    const siguiente = document.querySelector(celdas.selectorCelda(destino, configuracion));
    if (!siguiente) return;
    enfocarDestino(siguiente, registro);
    evento.preventDefault();
  }

  window.scalaris.navegacionCaptura = { navegarCaptura, cancelarSeleccion };
}
