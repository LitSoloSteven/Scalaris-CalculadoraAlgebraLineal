'use strict';
const prueba = require('node:test');
const afirmar = require('node:assert/strict');
const vm = require('node:vm');
const { cargarAssetCliente } = require('./comun_cliente_javascript.js');

function cliente() {
  const caja = { left: 0, top: 0, width: 10, height: 10, right: 10, bottom: 10 };
  const crearEntrada = valor => ({ value: valor, style: { visibility: '',
    getPropertyValue() { return this.visibility; }, getPropertyPriority() { return ''; },
    setProperty(_, valor) { this.visibility = valor; }, removeProperty() { this.visibility = ''; } },
    closest: () => null, getBoundingClientRect: () => caja });
  const propias = Array.from({ length: 12 }, (_, indice) => crearEntrada(String(indice)));
  const ajena = crearEntrada('ajena');
  const ambito = { querySelectorAll: () => propias };
  const icono = { textContent: 'delete' };
  const boton = { getBoundingClientRect: () => caja, querySelector: () => icono,
    classList: { add() {}, remove() {} } };
  const tareas = [], clones = [];
  let tiempo = 0;
  const duraciones = { '--dur-panel': 450, '--stagger-step': 75, '--stagger-max': 600 };
  const ventana = { innerWidth: 100, innerHeight: 100, getComputedStyle: () => ({}),
    scalaris: { movimiento: { permitido: () => true, duracion: token => duraciones[token], curva: () => 'curva' } } };
  const documento = { getElementById: id => id === 'captura' ? ambito : id === 'boton-limpiar-principal' ? boton : null,
    createElement: () => ({ style: {}, remove() {} }), body: { appendChild: clon => clones.push(clon) } };
  const contexto = vm.createContext({ window: ventana, document: documento,
    setTimeout: (funcion, espera) => { const tarea = { funcion, momento: tiempo + espera }; tareas.push(tarea); return tarea; },
    clearTimeout: tarea => { const indice = tareas.indexOf(tarea); if (indice >= 0) tareas.splice(indice, 1); } });
  cargarAssetCliente('recoleccion_basura.js', contexto);
  return { ventana, propias, ajena, tareas, clones, avanzar() {
    tareas.sort((primera, segunda) => primera.momento - segunda.momento);
    const tarea = tareas.shift(); tiempo = tarea.momento; tarea.funcion(); return tiempo;
  } };
}

prueba('la captura explícita desaparece junta y otras capturas conservan sus valores', async () => {
  const simulacion = cliente();
  const promesa = simulacion.ventana.scalaris.animarRecoleccionBasura(['captura']);
  afirmar.equal(simulacion.clones.length, 8);
  afirmar.ok(simulacion.propias.every(entrada => entrada.style.visibility === 'hidden'));
  afirmar.equal(simulacion.ajena.style.visibility, '');
  let tiempo = 0;
  while (simulacion.tareas.length && tiempo < 1425) tiempo = simulacion.avanzar();
  await promesa;
  afirmar.equal(tiempo, 1425);
  afirmar.ok(simulacion.propias.every(entrada => entrada.style.visibility === 'hidden'));
  simulacion.ventana.scalaris.terminarRecoleccionBasura();
  afirmar.ok(simulacion.propias.every(entrada => entrada.style.visibility === ''));
  afirmar.equal(simulacion.propias[0].value, '0');
  afirmar.equal(simulacion.ajena.value, 'ajena');
});

prueba('sin ámbito explícito no se consultan ni animan capturas ajenas', async () => {
  const simulacion = cliente();
  await simulacion.ventana.scalaris.animarRecoleccionBasura(null);
  afirmar.equal(simulacion.clones.length, 0);
  afirmar.equal(simulacion.ajena.value, 'ajena');
});
