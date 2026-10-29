'use strict';
const prueba = require('node:test');
const afirmar = require('node:assert/strict');
const vm = require('node:vm');
const { cargarAssetCliente } = require('./comun_cliente_javascript.js');

function crearMatriz(falloObservador = false) {
  const animaciones = [], observadores = [];
  const contenedor = {
    entradas: [], parentElement: {}, matches: selector => selector === '.cuadricula-contenido',
    querySelectorAll() { return this.entradas; }, contains(entrada) { return this.entradas.includes(entrada); },
    animate(fotogramas, opciones) {
      const animacion = { fotogramas, opciones, finished: Promise.resolve(), cancelada: false,
        cancel() { this.cancelada = true; } };
      animaciones.push(animacion);
      return animacion;
    }
  };
  for (let indice = 0; indice < 20; indice++) {
    const fila = { entradas: [], querySelectorAll() { return this.entradas; },
      contains(entrada) { return this.entradas.includes(entrada); } };
    for (let columna = 0; columna < 20; columna++) {
      const entrada = { closest(selector) {
        if (selector.startsWith('[data-')) return fila;
        if (selector === '.cuadricula-contenido') return contenedor;
        return null;
      } };
      fila.entradas.push(entrada);
      contenedor.entradas.push(entrada);
    }
  }
  class Observador {
    constructor(callback) { this.callback = callback; this.desconectado = false; observadores.push(this); }
    observe() { if (falloObservador) throw new Error('observador indisponible'); }
    disconnect() { this.desconectado = true; }
  }
  const movimiento = { permitido: () => true, duracion: token => token === '--dur-panel' ? 450 : 340,
    curva: () => 'curva' };
  const ventana = { scalaris: { movimiento } };
  cargarAssetCliente('cuadricula_compartida.js', vm.createContext({ window: ventana, MutationObserver: Observador }));
  return { contenedor, animaciones, observadores, api: ventana.scalaris.cuadricula };
}

prueba('una matriz grande completa entra y sale como una sola capa', async () => {
  const { contenedor, animaciones, observadores, api } = crearMatriz();
  const entradas = [...contenedor.entradas];
  await api.animarEntradaCeldas(entradas);
  afirmar.equal(animaciones.length, 1);
  afirmar.equal(animaciones[0].opciones.duration, 450);
  afirmar.equal(animaciones[0].cancelada, true);
  await api.animarSalidaCeldas(entradas);
  afirmar.equal(animaciones.length, 2);
  afirmar.equal(animaciones[1].opciones.duration, 340);
  afirmar.equal(animaciones[1].cancelada, false);
  contenedor.entradas = [];
  observadores[0].callback();
  afirmar.equal(animaciones[1].cancelada, true);
  afirmar.equal(observadores[0].desconectado, true);
});

prueba('una selección parcial nunca oculta el resto de la matriz', async () => {
  const { contenedor, animaciones, api } = crearMatriz();
  await api.animarSalidaCeldas(contenedor.entradas.slice(0, -20));
  afirmar.equal(animaciones.length, 0);
});

prueba('restaurar o sustituir una salida desconecta su observador', async () => {
  const { contenedor, animaciones, observadores, api } = crearMatriz();
  const entradas = [...contenedor.entradas];
  await api.animarSalidaCeldas(entradas);
  api.restaurarCeldas(entradas);
  afirmar.equal(animaciones[0].cancelada, true);
  afirmar.equal(observadores[0].desconectado, true);
  await api.animarSalidaCeldas(entradas);
  await api.animarEntradaCeldas(entradas);
  afirmar.equal(animaciones[1].cancelada, true);
  afirmar.equal(observadores[1].desconectado, true);
});

prueba('desmontar el contenedor completo también libera su observador', async () => {
  const { contenedor, animaciones, observadores, api } = crearMatriz();
  await api.animarSalidaCeldas([...contenedor.entradas]);
  contenedor.isConnected = false;
  observadores[0].callback();
  afirmar.equal(animaciones[0].cancelada, true);
  afirmar.equal(observadores[0].desconectado, true);
});

prueba('un fallo al observar devuelve la capa a su estado visible', async () => {
  const { contenedor, animaciones, observadores, api } = crearMatriz(true);
  await api.animarSalidaCeldas([...contenedor.entradas]);
  afirmar.equal(animaciones[0].cancelada, true);
  afirmar.equal(observadores[0].desconectado, true);
});
