"use strict";

const sistemaArchivos = require("node:fs");
const rutas = require("node:path");
const maquinaVirtual = require("node:vm");

/** Carga un asset del repositorio en el contexto simulado indicado. */
function cargarAssetCliente(nombre, contexto) {
    const ruta = rutas.join(__dirname, "../src/frontend/recursos/js", nombre);
    const codigo = sistemaArchivos.readFileSync(ruta, "utf8");
    maquinaVirtual.runInContext(codigo, contexto);
}

/** Crea una celda con selección, foco y eventos observables. */
function crearEntradaSimulada(valor, seleccion = [valor.length, valor.length]) {
    return {
        value: valor, tagName: "INPUT", isConnected: true,
        selectionStart: seleccion[0], selectionEnd: seleccion[1],
        eventos: [], enfocada: false,
        closest: () => true,
        focus() { this.enfocada = true; },
        setSelectionRange(inicio, fin) { this.selectionStart = inicio; this.selectionEnd = fin; },
        dispatchEvent(evento) { this.eventos.push(evento); },
    };
}

/** Crea un documento y carga el teclado numérico con sus eventos reales. */
function crearCalculadoraSimulada(primeraEntrada = null) {
    const eventos = new Map();
    const ventana = {};
    const documento = {
        addEventListener: (nombre, manejador) => eventos.set(nombre, manejador),
        querySelector: () => primeraEntrada,
    };
    const contexto = maquinaVirtual.createContext({ window: ventana, document: documento, Event });
    cargarAssetCliente("calculadora.js", contexto);
    return { ventana, eventos, contexto };
}

module.exports = { cargarAssetCliente, crearEntradaSimulada, crearCalculadoraSimulada };
