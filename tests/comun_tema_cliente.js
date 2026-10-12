"use strict";

const maquinaVirtual = require("node:vm");
const { cargarAssetCliente } = require("./comun_cliente_javascript.js");

/** Simula atributos de tema, almacenamiento, logotipos y temporizadores. */
function crearTemaSimulado(temaInicial = null, ancho = 1200) {
    const atributos = new Map();
    const eventos = new Map();
    const almacen = new Map(temaInicial === null ? [] : [["theme", temaInicial]]);
    const logotipo = { src: "original" };
    const temporizadores = [];
    const animaciones = [];
    const graficos = { texto: { papel: "texto" }, cuadricula: { papel: "cuadricula" } };
    const raiz = {
        style: {},
        setAttribute: (nombre, valor) => atributos.set(nombre, valor),
        getAttribute: nombre => atributos.get(nombre),
        animate: (fotogramas, opciones) => animaciones.push({ fotogramas, opciones }),
    };
    const documento = {
        documentElement: raiz,
        getElementById: () => ({ textContent: JSON.stringify(graficos) }),
        addEventListener: (nombre, manejador) => eventos.set(nombre, manejador),
        querySelector: () => null,
        querySelectorAll: () => [logotipo],
    };
    const ventana = {
        innerWidth: ancho, innerHeight: 800,
        matchMedia: consulta => ({ matches: consulta === '(min-width: 1024px)' && ancho >= 1024 }),
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

module.exports = { crearTemaSimulado, cargarTemaCompleto };
