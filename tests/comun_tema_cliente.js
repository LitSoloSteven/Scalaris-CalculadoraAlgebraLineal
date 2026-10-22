"use strict";

const maquinaVirtual = require("node:vm");
const { cargarAssetCliente } = require("./comun_cliente_javascript.js");

/** Observa el estado visual y la limpieza de las animaciones de tema. */
function crearRaizTema(atributos, animaciones) {
    return {
        style: {},
        setAttribute: (nombre, valor) => atributos.set(nombre, valor),
        getAttribute: nombre => atributos.get(nombre),
        hasAttribute: nombre => atributos.has(nombre),
        removeAttribute: nombre => atributos.delete(nombre),
        animate: (fotogramas, opciones) => {
            const animacion = { fotogramas, opciones, finished: Promise.resolve(), cancel() { this.cancelada = true; } };
            animaciones.push(animacion);
            return animacion;
        },
    };
}

/** Simula atributos de tema, almacenamiento, logotipos y temporizadores. */
function crearTemaSimulado(temaInicial = null, ancho = 1200) {
    const atributos = new Map(), eventos = new Map();
    const almacen = new Map(temaInicial === null ? [] : [["tema", temaInicial]]);
    const logotipo = { src: "original" }, temporizadores = [], animaciones = [];
    const graficos = { texto: { papel: "texto" }, cuadricula: { papel: "cuadricula" } };
    const raiz = crearRaizTema(atributos, animaciones);
    const documento = {
        documentElement: raiz,
        getElementById: () => ({ textContent: JSON.stringify(graficos) }),
        addEventListener: (nombre, manejador) => eventos.set(nombre, manejador),
        querySelector: () => null,
        querySelectorAll: () => [logotipo],
    };
    const ventana = {
        innerWidth: ancho, innerHeight: 800,
        matchMedia: consulta => ({ matches: consulta === '(min-width: 1024px)' && ancho >= 1024,
            addEventListener: (_, funcion) => eventos.set('preferenciaTema', funcion) }),
        addEventListener: (nombre, manejador) => eventos.set(nombre, manejador),
    };
    const almacenamiento = {
        getItem: nombre => almacen.get(nombre) ?? null,
        setItem: (nombre, valor) => almacen.set(nombre, valor),
    };
    const contexto = maquinaVirtual.createContext({
        window: ventana, document: documento, localStorage: almacenamiento,
        setTimeout: (manejador, espera) => temporizadores.push({ manejador, espera }),
    });
    return {
        ventana, documento, contexto, atributos, almacen, logotipo,
        temporizadores, animaciones, almacenamiento, graficos, eventos,
    };
}

/** Carga los dos momentos de inicialización en el orden de la cabecera real. */
function cargarTemaCompleto(cliente) {
    cargarAssetCliente("inicializacion_tema.js", cliente.contexto);
    cargarAssetCliente("tema.js", cliente.contexto);
}

/** Conserva pendientes las capturas hasta que la prueba decida finalizarlas. */
function simularTransicion(cambiar, ready = Promise.resolve()) {
    cambiar?.();
    return { ready, finished: new Promise(() => {}), updateCallbackDone: Promise.resolve(),
        skipTransition() { this.omitida = true; } };
}

module.exports = { crearTemaSimulado, cargarTemaCompleto, simularTransicion };
