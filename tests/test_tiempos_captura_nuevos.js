'use strict';
const prueba = require('node:test');
const afirmar = require('node:assert/strict');
const vm = require('node:vm');
const { cargarAssetCliente } = require('./comun_cliente_javascript.js');

function movimiento() {
  const tokens = { '--dur-panel': 450, '--dur-panel-exit': 340, '--dur-didactic': 900,
    '--stagger-step': 75, '--stagger-max': 600 };
  return { permitido: () => true, duracion: nombre => tokens[nombre], curva: () => 'curva' };
}

prueba('una fila completa se anima como capa sin ocultar su contenedor', async () => {
  const animaciones = [];
  const fila = { entradas: [], querySelectorAll() { return this.entradas; },
    contains: entrada => fila.entradas.includes(entrada),
    animate: (_, opciones) => { animaciones.push(opciones); return { finished: Promise.resolve(), cancel() {} }; } };
  fila.entradas = Array.from({ length: 20 }, () => ({
    closest: selector => selector.startsWith('[data-') ? fila : null,
  }));
  const ventana = { scalaris: { movimiento: movimiento() } };
  const contexto = vm.createContext({ window: ventana, document: {} });
  cargarAssetCliente('cuadricula_compartida.js', contexto);
  await ventana.scalaris.cuadricula.animarEntradaCeldas(fila.entradas);
  afirmar.equal(animaciones.length, 1);
  afirmar.equal(animaciones[0].duration, 450);
  afirmar.equal(animaciones[0].easing, 'curva');
});

prueba('texto largo termina con un número acotado de temporizadores', () => {
  let ahora = 0, cantidad = 0;
  const pendientes = [];
  const fragmento = { textContent: '' }, cursor = { style: {} };
  const elemento = { querySelector: selector => selector === '.escritura-texto' ? fragmento : cursor,
    addEventListener() {}, removeEventListener() {} };
  const ventana = { scalaris: { movimiento: movimiento() } };
  const contexto = vm.createContext({ window: ventana, document: { getElementById: () => elemento },
    Date: { now: () => ahora }, clearTimeout() {},
    setTimeout: (funcion, espera) => { cantidad++; pendientes.push({ funcion, espera }); return cantidad; } });
  cargarAssetCliente('escritura_progresiva.js', contexto);
  ventana.scalaris.efectoMaquinaEscribir('texto', 'x'.repeat(10000), 18);
  while (pendientes.length) { const tarea = pendientes.shift(); ahora += tarea.espera; tarea.funcion(); }
  afirmar.equal(ahora, 900);
  afirmar.equal(fragmento.textContent.length, 10000);
  afirmar.ok(cantidad <= 12);
});

prueba('la recolección conserva los valores hasta que la captura los limpie', async () => {
  const rectangulo = { left: 0, top: 0, width: 50, height: 40, bottom: 40, right: 50 };
  const entradas = Array.from({ length: 15 }, (_, indice) => ({ value: String(indice + 1), style: {},
    closest: () => null, getBoundingClientRect: () => rectangulo }));
  const clones = [];
  const boton = { getBoundingClientRect: () => rectangulo, querySelector: () => null,
    classList: { add() {}, remove() {} } };
  const ventana = { innerWidth: 320, innerHeight: 760, getComputedStyle: () => ({}),
    scalaris: { movimiento: movimiento() } };
  const documento = { querySelectorAll: () => entradas, getElementById: () => boton,
    createElement: () => ({ style: {}, remove() {} }), body: { appendChild: clon => clones.push(clon) } };
  const contexto = vm.createContext({ window: ventana, document: documento, setTimeout: funcion => funcion() });
  cargarAssetCliente('recoleccion_basura.js', contexto);
  await ventana.scalaris.animarRecoleccionBasura();
  afirmar.equal(clones.length, 8);
  afirmar.deepEqual(entradas.map(entrada => entrada.value), Array.from({ length: 15 }, (_, indice) => String(indice + 1)));
});
