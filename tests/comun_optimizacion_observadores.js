"use strict";
const maquinaVirtual = require('node:vm');
const archivos = require('node:fs');
const rutas = require('node:path');
const recursos = rutas.resolve(__dirname, '../src/frontend/recursos/js');

/** Monta el script real con contadores de consultas y una cola de fotogramas simulados. */
function crearObservador(nombre) {
    const observadores = [], fotogramas = [], contadores = { consultas: 0 };
    const raiz = { getAttribute: () => 'papel' };
    const documento = { documentElement: raiz, fonts: { ready: Promise.resolve() },
        addEventListener() {}, querySelector: () => null,
        querySelectorAll() { contadores.consultas++; return []; } };
    const contexto = maquinaVirtual.createContext({ document: documento, window: { scalaris: {} },
        MutationObserver: class { constructor(funcion) { observadores.push(funcion); } observe() {} },
        ResizeObserver: class { observe() {} },
        requestAnimationFrame: funcion => fotogramas.push(funcion), setTimeout, clearTimeout });
    const recursoObservacion = rutas.join(recursos, 'observacion_dom.js');
    if (archivos.existsSync(recursoObservacion)) {
        maquinaVirtual.runInContext(archivos.readFileSync(recursoObservacion, 'utf8'), contexto);
    }
    maquinaVirtual.runInContext(archivos.readFileSync(rutas.join(recursos, nombre), 'utf8'), contexto);
    return { contadores, observadores, fotogramas, raiz, contexto };
}

/** Devuelve una mutación de entrada sin elementos de navegación, tema o gráficos. */
function mutacionEntrada() {
    const entrada = { nodeType: 1, matches: () => false, querySelector: () => null };
    return { type: 'childList', target: entrada, addedNodes: [entrada], removedNodes: [] };
}

/** Cuenta consultas completas para lotes de mutación repartidos en fotogramas. */
function medirConsultas(nombre, cantidad = 100) {
    const cliente = crearObservador(nombre);
    cliente.contadores.consultas = 0;
    for (let indice = 0; indice < cantidad; indice++) {
        cliente.observadores[0]([mutacionEntrada()]);
        cliente.fotogramas.splice(0).forEach(funcion => funcion());
    }
    return cliente.contadores.consultas;
}

module.exports = { crearObservador, mutacionEntrada, medirConsultas };
