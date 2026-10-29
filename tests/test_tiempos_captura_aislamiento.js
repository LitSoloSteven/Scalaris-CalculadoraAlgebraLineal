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

prueba('la recolección selecciona solo la captura más cercana al botón', async () => {
  const caja = { left: 0, top: 0, width: 10, height: 10, bottom: 10, right: 10 };
  const entrada = valor => ({ value: valor, closest: () => null, getBoundingClientRect: () => caja });
  const propia = entrada('propia'), ajena = entrada('ajena');
  const ambito = { querySelectorAll: () => [propia] };
  const boton = { parentElement: ambito, getBoundingClientRect: () => caja,
    querySelector: () => null, classList: { add() {}, remove() {} } };
  const clones = [];
  const movimiento = { permitido: () => true, curva: () => 'curva',
    duracion: token => ({ '--dur-panel': 450, '--stagger-step': 75, '--stagger-max': 600 })[token] };
  const ventana = { innerWidth: 100, innerHeight: 100, getComputedStyle: () => ({}), scalaris: { movimiento } };
  const documento = { querySelectorAll: () => [propia, ajena], getElementById: () => boton,
    createElement: () => ({ style: {}, remove() {} }), body: { appendChild: clon => clones.push(clon) } };
  const contexto = vm.createContext({ window: ventana, document: documento, setTimeout: funcion => funcion() });
  cargarAssetCliente('recoleccion_basura.js', contexto);
  await ventana.scalaris.animarRecoleccionBasura();
  afirmar.deepEqual(clones.map(clon => clon.textContent), ['propia']);
  afirmar.equal(ajena.value, 'ajena');
});
