'use strict';
const prueba = require('node:test');
const afirmar = require('node:assert/strict');
const vm = require('node:vm');
const { cargarAssetCliente } = require('./comun_cliente_javascript.js');

prueba('una desconexión restaura los campos y cancela los temporizadores', async () => {
  const caja = { left: 0, top: 0, width: 10, height: 10, right: 10, bottom: 10 };
  let visible = '', desconectar;
  const estilo = { getPropertyValue: () => visible, getPropertyPriority: () => '',
    setProperty: (_, valor) => { visible = valor; }, removeProperty: () => { visible = ''; } };
  const entrada = { value: '9', style: estilo, closest: () => null, getBoundingClientRect: () => caja };
  const raiz = { querySelectorAll: () => [entrada] };
  const boton = { getBoundingClientRect: () => caja, querySelector: () => null, classList: { add() {}, remove() {} } };
  const tareas = new Set();
  const movimiento = { permitido: () => true, curva: () => 'curva',
    duracion: token => ({ '--dur-panel': 450, '--stagger-step': 75, '--stagger-max': 600 })[token] };
  const ventana = { innerWidth: 100, innerHeight: 100, getComputedStyle: () => ({}),
    socket: { on: (_, funcion) => { desconectar = funcion; }, off: () => { desconectar = null; } },
    scalaris: { movimiento } };
  const documento = { getElementById: id => id === 'captura' ? raiz : boton,
    createElement: () => ({ style: {}, remove() {} }), body: { appendChild() {} } };
  const contexto = vm.createContext({ window: ventana, document: documento,
    setTimeout: funcion => { tareas.add(funcion); return funcion; }, clearTimeout: funcion => tareas.delete(funcion) });
  cargarAssetCliente('recoleccion_basura.js', contexto);
  const espera = ventana.scalaris.animarRecoleccionBasura(['captura']);
  afirmar.equal(visible, 'hidden');
  desconectar();
  await espera;
  afirmar.equal(visible, '');
  afirmar.equal(tareas.size, 0);
  afirmar.equal(desconectar, null);
  afirmar.equal(entrada.value, '9');
});
