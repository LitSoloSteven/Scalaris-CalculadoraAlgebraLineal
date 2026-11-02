'use strict';
const { test } = require('node:test');
const comprobar = require('node:assert/strict');
const { readFileSync: leerArchivo } = require('node:fs');
const { runInNewContext: ejecutar } = require('node:vm');

function preparar(permitido) {
    const eventos = [];
    const clases = new Set();
    const tareas = [];
    const caja = { left: 0, top: 0, width: 10, height: 10, right: 10, bottom: 10 };
    const entrada = { value: '1', closest: () => null, getBoundingClientRect: () => caja,
        style: { getPropertyValue: () => '', getPropertyPriority: () => '', setProperty() {}, removeProperty() {} } };
    const boton = { getBoundingClientRect: () => caja, querySelector: () => null,
        classList: { add: nombre => clases.add(nombre), remove: nombre => clases.delete(nombre) } };
    const ventana = { innerWidth: 100, innerHeight: 100, getComputedStyle: () => ({}),
        scalaris: { movimiento: { permitido: () => permitido, curva: () => 'curva',
            duracion: token => ({ '--dur-panel': 450, '--stagger-step': 75, '--stagger-max': 600 })[token] },
        eventosSonoros: { limpiezaVuelo: () => eventos.push('vuelo'), limpiezaFinal: () => {
            comprobar.equal(clases.has('movimiento-compresion'), true);
            eventos.push('golpe');
            return true;
        } } } };
    const documento = { getElementById: nombre => nombre === 'captura' ? { querySelectorAll: () => [entrada] } : boton,
        body: { appendChild() {} }, createElement: () => ({ style: {}, remove() {} }) };
    ejecutar(leerArchivo('src/frontend/recursos/js/recoleccion_basura.js', 'utf8'), {
        window: ventana, document: documento, setTimeout: tarea => { tareas.push(tarea); return tareas.length; }, clearTimeout() {} });
    return { ventana, eventos, clases, tareas };
}

test('el golpe ocurre al empezar la compresion y se confirma sin duplicarlo al resolver', async () => {
    const caso = preparar(true);
    const espera = caso.ventana.scalaris.animarRecoleccionBasura(['captura']);
    comprobar.deepEqual(caso.eventos, ['vuelo']);
    caso.tareas.splice(0, 2).forEach(tarea => tarea());
    caso.tareas.shift()();
    comprobar.deepEqual(caso.eventos, ['vuelo', 'golpe']);
    comprobar.equal(caso.clases.has('movimiento-compresion'), true);
    caso.tareas.shift()();
    comprobar.equal(await espera, true);
    comprobar.deepEqual(caso.eventos, ['vuelo', 'golpe']);
    comprobar.equal(caso.clases.has('movimiento-compresion'), false);
    caso.ventana.scalaris.terminarRecoleccionBasura();
});

test('el modo sin movimiento no emite vuelo ni golpe y deja la senal al servidor', async () => {
    const caso = preparar(false);
    comprobar.equal(await caso.ventana.scalaris.animarRecoleccionBasura(['captura']), undefined);
    comprobar.deepEqual(caso.eventos, []);
    comprobar.equal(caso.tareas.length, 0);
});
