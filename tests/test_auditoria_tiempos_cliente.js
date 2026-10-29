'use strict';
const prueba = require('node:test');
const afirmar = require('node:assert/strict');
const { analizarTiempos } = require('./comun_auditoria_tiempos.js');

prueba('detecta duraciones literales aun con fotogramas anidados y constantes', () => {
  for (const codigo of [
    'elemento.animate([{opacity:0},{opacity:1}], 180)',
    'elemento.animate(crearFotogramas(), 180)',
    'const t = 180\nelemento.animate(f, {duration:t})',
    "elemento.animate(f, {easing:'cubic-bezier(0,0,0,1)'})",
  ]) afirmar.notEqual(analizarTiempos(codigo).length, 0, codigo);
  afirmar.deepEqual(analizarTiempos("elemento.animate(f, {duration: movimiento.duracion('--dur-view')})"), []);
});
