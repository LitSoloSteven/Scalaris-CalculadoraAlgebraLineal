/** Configuración de navegación, pegado y foco de matrices. */
'use strict';

window.scalaris.capturas.registrarCaptura('matrices', {
  tipo: 'matrices',
  atributos: { fila: 'matrizFila', columna: 'matrizColumna', grupo: 'matrizIdentificador' },
  claseResaltado: 'cuadricula-resaltado-cruzado',
  prepararTexto: texto => texto.trim()
});
