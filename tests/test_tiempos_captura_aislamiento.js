'use strict';
const prueba = require('node:test');
const afirmar = require('node:assert/strict');
const vm = require('node:vm');
const { cargarAssetCliente } = require('./comun_cliente_javascript.js');

prueba('un callback en cola no reanuda una escritura saltada', () => {
  let clic, tarea;
  const texto = { textContent: '' }, cursor = { style: {} };
  const elemento = { querySelector: selector => selector === '.escritura-texto' ? texto : cursor,
    addEventListener: (_, funcion) => { clic = funcion; }, removeEventListener() {} };
  const movimiento = { permitido: () => true, duracion: token => token === '--dur-didactic' ? 900 : 75 };
  const ventana = { scalaris: { movimiento } };
  const contexto = vm.createContext({ window: ventana, document: { getElementById: () => elemento },
    Date: { now: () => 0 }, setTimeout: funcion => { tarea = funcion; return 1; }, clearTimeout() {} });
  cargarAssetCliente('escritura_progresiva.js', contexto);
  ventana.scalaris.efectoMaquinaEscribir('texto', 'Contenido completo', 18);
  clic();
  tarea();
  afirmar.equal(texto.textContent, 'Contenido completo');
});
