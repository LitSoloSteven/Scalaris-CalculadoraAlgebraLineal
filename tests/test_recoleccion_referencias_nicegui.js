'use strict';
const prueba = require('node:test');
const afirmar = require('node:assert/strict');
const vm = require('node:vm');
const { cargarAssetCliente } = require('./comun_cliente_javascript.js');

prueba('la referencia NiceGUI se cancela y conserva la prioridad de visibilidad', async () => {
  const caja = { left: 0, top: 0, width: 10, height: 10, right: 10, bottom: 10 };
  let visibilidad = 'visible', prioridad = 'important';
  const estilo = { getPropertyValue: () => visibilidad, getPropertyPriority: () => prioridad,
    setProperty: (_, valor, fuerza = '') => { visibilidad = valor; prioridad = fuerza; },
    removeProperty: () => { visibilidad = ''; prioridad = ''; } };
  const entrada = { value: '7', style: estilo, closest: () => null, getBoundingClientRect: () => caja };
  const raiz = { querySelectorAll: () => [entrada] };
  const boton = { getBoundingClientRect: () => caja, querySelector: () => null,
    classList: { add() {}, remove() {} } };
  const tareas = new Set();
  const movimiento = { permitido: () => true, curva: () => 'curva',
    duracion: token => ({ '--dur-panel': 450, '--stagger-step': 75, '--stagger-max': 600 })[token] };
  const ventana = { innerWidth: 100, innerHeight: 100, getComputedStyle: () => ({}),
    getElement: id => id === 12 ? { $refs: { qRef: { $el: raiz } } } : null, scalaris: { movimiento } };
  const documento = { getElementById: id => id === 'boton-limpiar-principal' ? boton : null,
    createElement: () => ({ style: {}, remove() {} }), body: { appendChild() {} } };
  const contexto = vm.createContext({ window: ventana, document: documento,
    setTimeout: funcion => { tareas.add(funcion); return funcion; }, clearTimeout: funcion => tareas.delete(funcion) });
  cargarAssetCliente('recoleccion_basura.js', contexto);
  const espera = ventana.scalaris.animarRecoleccionBasura([12]);
  afirmar.equal(visibilidad, 'hidden');
  ventana.scalaris.terminarRecoleccionBasura();
  await espera;
  afirmar.equal(visibilidad, 'visible');
  afirmar.equal(prioridad, 'important');
  afirmar.equal(tareas.size, 0);
  afirmar.equal(entrada.value, '7');
});
