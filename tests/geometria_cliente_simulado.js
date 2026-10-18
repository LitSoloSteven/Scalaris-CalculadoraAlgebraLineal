/* El DOM simulado verifica contratos de cliente sin atribuirle una revisión visual. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const codigo = fs.readFileSync(process.argv[2], 'utf8');
const elementos = new Map();
const oyentes = new Set();
const solicitudes = new Map();
const llamadas = [];
let siguienteSolicitud = 0;
let observadorActual;

function crearCelda() {
  const atributos = new Map();
  const clases = new Set();
  const control = { classList: { add: valor => clases.add(valor), remove: valor => clases.delete(valor) } };
  return {
    atributos, clases,
    setAttribute: (clave, valor) => atributos.set(clave, valor),
    removeAttribute: clave => atributos.delete(clave),
    closest: () => control,
    focus() { this.enfocada = true; },
    scrollIntoView(opciones) { this.desplazamiento = opciones; }
  };
}

const grafica = { isConnected: true };
const envoltura = { querySelector: () => grafica };
const celda = crearCelda();
const ajena = crearCelda();
ajena.atributos.set('aria-invalid', 'true');
const aviso = { textContent: '' };
const etiqueta = { textContent: '' };
const deslizador = {
  value: '1',
  matches: () => true,
  getAttribute: () => 'figura',
  setAttribute(clave, valor) { this[clave] = valor; },
  closest: () => ({ querySelector: () => etiqueta })
};
elementos.set('figura', envoltura);
elementos.set('geometria-error-cuadro-figura', aviso);

const entorno = {
  window: {
    Plotly: { restyle(elemento, datos, indices) { llamadas.push({ elemento, datos, indices }); return Promise.resolve(); } }
  },
  document: {
    documentElement: {},
    getElementById: clave => elementos.get(clave),
    querySelector: selector => selector === '#celda' ? celda : ajena,
    addEventListener(tipo, oyente) { if (tipo === 'input') oyentes.add(oyente); },
    removeEventListener(tipo, oyente) { oyentes.delete(oyente); }
  },
  MutationObserver: class {
    constructor(funcion) { this.funcion = funcion; observadorActual = this; }
    observe() { this.activo = true; }
    disconnect() { this.activo = false; }
  },
  requestAnimationFrame(funcion) { const indice = ++siguienteSolicitud; solicitudes.set(indice, funcion); return indice; },
  cancelAnimationFrame(indice) { solicitudes.delete(indice); },
};

function comprobarDeslizadorDosDimensiones() {
  vm.runInNewContext(codigo, entorno);
  entorno.window.scalaris.geometria.registrar('figura', [
    { escalar_por_u: [0, 0], escalar_por_u_mas_v: [0, 1], escalar_exacto: '0' },
    { escalar_por_u: [1, 2], escalar_por_u_mas_v: [3, 4], escalar_exacto: '1/2' }
  ]);
  Array.from(oyentes)[0]({ target: deslizador });
  assert.equal(etiqueta.textContent, '1/2');
  assert.equal(deslizador['aria-valuetext'], '1/2');
  assert.equal(llamadas.length, 0);
  const programada = Array.from(solicitudes.values())[0];
  solicitudes.clear();
  programada();
  assert.equal(llamadas.length, 1);
  assert.equal(JSON.stringify(llamadas[0].datos.x), '[[0,1],[0,3]]');
  assert.equal(JSON.stringify(llamadas[0].indices), '[0,2]');
}

function comprobarCuadroTresDimensiones() {
  entorno.window.scalaris.geometria.registrar('figura', [{ escalar_por_u: [1, 2, 3], escalar_por_u_mas_v: [4, 5, 6], escalar_exacto: '1' }]);
  llamadas.length = 0;
  entorno.window.scalaris.geometria.establecerCuadro('figura', 0);
  assert.equal(llamadas.length, 4);
  assert.equal(JSON.stringify(llamadas.map(llamada => llamada.indices)), '[[0],[1],[4],[5]]');
  assert.equal(JSON.stringify(llamadas[2].datos.z), '[[0,6]]');
}

function comprobarMarcadoYFoco() {
  entorno.window.scalaris.geometria.marcarInvalido('#celda');
  assert.equal(celda.atributos.get('aria-invalid'), 'true');
  assert.equal(celda.clases.has('geometria-celda-error'), true);
  entorno.window.scalaris.geometria.marcarInvalido(null);
  assert.equal(celda.atributos.has('aria-invalid'), false);
  assert.equal(celda.clases.size, 0);
  assert.equal(ajena.atributos.get('aria-invalid'), 'true');
  entorno.window.scalaris.geometria.enfocarCelda('#celda');
  assert.equal(celda.enfocada, true);
  assert.equal(celda.desplazamiento.behavior, 'instant');
}

function comprobarLimpiezaYRecarga() {
  elementos.delete('figura');
  observadorActual.funcion();
  llamadas.length = 0;
  entorno.window.scalaris.geometria.establecerCuadro('figura', 0);
  assert.equal(llamadas.length, 0);
  elementos.set('figura', envoltura);
  entorno.window.scalaris.geometria.registrar('figura', [
    { escalar_por_u: [0, 0], escalar_por_u_mas_v: [0, 1], escalar_exacto: '0' },
    { escalar_por_u: [1, 2], escalar_por_u_mas_v: [3, 4], escalar_exacto: '1' }
  ]);
  Array.from(oyentes)[0]({ target: deslizador });
  assert.equal(solicitudes.size, 1);
  const anterior = observadorActual;
  vm.runInNewContext(codigo, entorno);
  assert.equal(anterior.activo, false);
  assert.equal(solicitudes.size, 0);
  assert.equal(oyentes.size, 1);
  entorno.window.scalaris.geometria.limpiar();
  assert.equal(oyentes.size, 0);
  assert.equal(observadorActual.activo, false);
}

function comprobarRegistroAntesDeMontar() {
  vm.runInNewContext(codigo, entorno);
  elementos.delete('figura');
  entorno.window.scalaris.geometria.registrar('figura', [{ escalar_por_u: [1, 2], escalar_por_u_mas_v: [3, 4], escalar_exacto: '1' }]);
  observadorActual.funcion();
  elementos.set('figura', envoltura);
  observadorActual.funcion();
  llamadas.length = 0;
  entorno.window.scalaris.geometria.establecerCuadro('figura', 0);
  assert.equal(llamadas.length, 1);
  entorno.window.scalaris.geometria.limpiar();
}

function comprobarRegistroConCuadroPendiente() {
  vm.runInNewContext(codigo, entorno);
  const cliente = entorno.window.scalaris.geometria;
  cliente.registrar('figura', [
    { escalar_por_u: [0, 0], escalar_por_u_mas_v: [0, 1], escalar_exacto: '0' },
    { escalar_por_u: [1, 2], escalar_por_u_mas_v: [3, 4], escalar_exacto: '1' }
  ]);
  Array.from(oyentes)[0]({ target: deslizador });
  const antigua = Array.from(solicitudes.values())[0];
  assert.equal(solicitudes.size, 1);
  cliente.registrar('figura', [{ escalar_por_u: [5, 6], escalar_por_u_mas_v: [7, 8], escalar_exacto: '0' }]);
  assert.equal(solicitudes.size, 0);
  llamadas.length = 0;
  antigua();
  assert.equal(llamadas.length, 0);
  cliente.limpiar();
}

async function comprobarFalloVisible() {
  vm.runInNewContext(codigo, entorno);
  entorno.window.scalaris.geometria.registrar('figura', [{ escalar_por_u: [1, 2], escalar_por_u_mas_v: [3, 4], escalar_exacto: '1' }]);
  entorno.window.Plotly.restyle = () => { throw new Error('Fallo simulado'); };
  entorno.window.scalaris.geometria.establecerCuadro('figura', 0);
  assert.equal(aviso.textContent, 'No pudimos actualizar el parámetro. Vuelve a mover el control.');
  entorno.window.Plotly.restyle = () => Promise.resolve();
  entorno.window.scalaris.geometria.establecerCuadro('figura', 0);
  await new Promise(completar => setImmediate(completar));
  assert.equal(aviso.textContent, '');
  entorno.window.scalaris.geometria.limpiar();
}

comprobarDeslizadorDosDimensiones();
comprobarCuadroTresDimensiones();
comprobarMarcadoYFoco();
comprobarLimpiezaYRecarga();
comprobarRegistroAntesDeMontar();
comprobarRegistroConCuadroPendiente();
comprobarFalloVisible().catch(error => { process.stderr.write(String(error)); process.exitCode = 1; });
