/** Adaptador de la unión de fila y columna a las animaciones compartidas. */
'use strict';
{
  window.scalaris.cuadricula.animarRedimensionCuadrada = async function (selector, modo) {
    if (modo === 'Entrada') await window.Vue?.nextTick?.();
    const entradas = Array.from(document.querySelectorAll(selector));
    const animar = modo === 'Salida' ? 'animarSalidaCeldas' : 'animarEntradaCeldas';
    return window.scalaris.cuadricula[animar](entradas);
  };
}
