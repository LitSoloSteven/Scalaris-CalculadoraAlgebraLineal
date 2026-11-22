/** Configuración de navegación, pegado y foco de vectores geométricos. */
'use strict';

window.scalaris.capturas.registrarCaptura('vectores', {
  tipo: 'vectores',
  atributos: { indice: 'geometriaIndice', grupo: 'geometriaVector', orientacion: 'geometriaOrientacion' },
  claseResaltado: 'cuadricula-resaltado-cruzado',
  prepararTexto: texto => texto.trim()
});
