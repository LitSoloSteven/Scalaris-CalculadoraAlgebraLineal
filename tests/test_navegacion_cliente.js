"use strict";

const afirmar = require("node:assert/strict");
const prueba = require("node:test");
const maquinaVirtual = require("node:vm");
const { cargarAssetCliente } = require("./comun_cliente_javascript.js");

/** Simula una lista desplazable sin API para desplazar la página o mover el foco. */
function crearLista() {
    const atributos = new Set(), eventos = new Map(), documentoEventos = new Map();
    const centro = { toggleAttribute: (nombre, activo) => activo ? atributos.add(nombre) : atributos.delete(nombre) };
    const lista = {
        scrollLeft: 0, clientWidth: 200, scrollWidth: 800,
        closest: () => centro,
        getBoundingClientRect: () => ({ left: 50, right: 250 }),
        addEventListener: (nombre, manejador) => eventos.set(nombre, manejador),
        querySelector: () => activo,
    };
    const activo = crearEnlace(lista, 500);
    const documento = {
        documentElement: {}, fonts: { ready: Promise.resolve() },
        querySelector: () => activo, querySelectorAll: () => [lista],
        addEventListener: (nombre, manejador) => documentoEventos.set(nombre, manejador),
    };
    const contexto = maquinaVirtual.createContext({
        document: documento, window: { scalaris: {} },
        MutationObserver: class { observe() {} },
        ResizeObserver: class { observe() {} },
    });
    cargarAssetCliente("navegacion_herramientas.js", contexto);
    return { lista, activo, atributos, eventos, documentoEventos, documento, contexto };
}

/** Calcula la posición del enlace a partir del desplazamiento real de su lista. */
function crearEnlace(lista, posicion) {
    return {
        closest: selector => selector === ".navegacion-elementos" ? lista : null,
        getBoundingClientRect: () => ({ left: 50 + posicion - lista.scrollLeft, right: 170 + posicion - lista.scrollLeft }),
    };
}

prueba("la ruta activa queda visible desplazando solamente su lista", () => {
    const cliente = crearLista();
    afirmar.equal(cliente.lista.scrollLeft, 428);
    afirmar.equal(cliente.atributos.has("data-opciones-antes"), true);
    afirmar.equal(cliente.atributos.has("data-opciones-despues"), true);
});

prueba("el foco revela el enlace anterior sin invocar foco ni scrollIntoView", () => {
    const cliente = crearLista();
    const primero = crearEnlace(cliente.lista, 0);
    cliente.documentoEventos.get("focusin")({ target: { closest: () => primero } });
    afirmar.equal(cliente.lista.scrollLeft, -8);
});

prueba("los indicadores corresponden al inicio y al final del recorrido", () => {
    const cliente = crearLista();
    cliente.lista.scrollLeft = 0;
    cliente.eventos.get("scroll")();
    afirmar.equal(cliente.atributos.has("data-opciones-antes"), false);
    afirmar.equal(cliente.atributos.has("data-opciones-despues"), true);
    cliente.lista.scrollLeft = 600;
    cliente.eventos.get("scroll")();
    afirmar.equal(cliente.atributos.has("data-opciones-antes"), true);
    afirmar.equal(cliente.atributos.has("data-opciones-despues"), false);
});
