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

prueba('la salida de una fila se restaura sin animar su vecina', async () => {
  let cancelada = false, animacionesVecina = 0;
  const fila = { entradas: [], querySelectorAll() { return this.entradas; },
    contains: entrada => fila.entradas.includes(entrada),
    animate: (_, opciones) => {
      afirmar.equal(opciones.duration, 340);
      return { finished: Promise.resolve(), cancel() { cancelada = true; } };
    } };
  fila.entradas = Array.from({ length: 3 }, () => ({ closest: selector => selector.startsWith('[data-') ? fila : null }));
  const vecina = { animate() { animacionesVecina++; } };
  const contenedor = { children: [fila, vecina] };
  fila.parentElement = contenedor;
  vecina.parentElement = contenedor;
  const ventana = { scalaris: { movimiento: movimiento() } };
  const contexto = vm.createContext({ window: ventana, document: {} });
  cargarAssetCliente('cuadricula_compartida.js', contexto);
  const cuadricula = ventana.scalaris.cuadricula;
  await cuadricula.animarSalidaCeldas(fila.entradas);
  afirmar.equal(cancelada, false);
  cuadricula.restaurarCeldas(fila.entradas);
  afirmar.equal(cancelada, true);
  afirmar.equal(animacionesVecina, 0);
  afirmar.equal(contenedor.children[1], vecina);
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
