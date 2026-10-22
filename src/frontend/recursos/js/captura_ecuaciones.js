/** Configuración de navegación, pegado y foco de ecuaciones. */
'use strict';

window.scalaris.capturas.registrarCaptura('ecuaciones', {
  tipo: 'ecuaciones',
  atributos: { fila: 'ecuacionesFila', columna: 'ecuacionesColumna' },
  claseResaltado: 'cuadricula-resaltado-cruzado',
  prepararTexto: texto => texto.replace(/\s+$/, '')
});
