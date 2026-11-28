"use strict";

const afirmar = require("node:assert/strict");
const prueba = require("node:test");
const { createContext } = require("node:vm");
const { cargarAssetCliente } = require("./comun_cliente_javascript.js");

function montarConfiguracion(tema) {
    const eventos = new Map();
    const documento = {activeElement: null, documentElement: {getAttribute: () => tema},
        addEventListener: (nombre, accion) => eventos.set(nombre, accion)};
    const selectorOpcion = "[data-tema-opcion]";
    const menu = {querySelectorAll: () => opciones, contains: opcion => opciones.includes(opcion)};
    const opciones = ["papel", "marea", "medianoche"].map(nombre => {
        const atributos = new Map([["data-tema-opcion", nombre]]);
        const opcion = {
            getAttribute: atributo => atributos.get(atributo),
            setAttribute: (atributo, valor) => atributos.set(atributo, valor),
            closest: selector => selector === selectorOpcion ? opcion : menu,
            focus: () => { documento.activeElement = opcion; },
        };
        return opcion;
    });
    documento.querySelectorAll = () => opciones;
    const contexto = createContext({document: documento, window: {scalaris: {}},
        MutationObserver: class { observe() {} }});
    cargarAssetCliente("nucleo/tema/selector_tema.js", contexto);
    return {documento, eventos, opciones};
}

prueba("Configuración deja una opción tabulable y mueve el foco sin seleccionar el tema", () => {
    const {documento, eventos, opciones} = montarConfiguracion("marea");
    afirmar.deepEqual(opciones.map(opcion => opcion.tabIndex), [-1, 0, -1]);
    const mover = eventos.get("keydown");
    opciones[1].focus();

    for (const [tecla, indice] of [["ArrowDown", 2], ["ArrowDown", 0], ["ArrowUp", 2], ["Home", 0], ["End", 2]]) {
        let gestionado = false;
        mover({key: tecla, target: documento.activeElement, preventDefault: () => { gestionado = true; }});
        afirmar.equal(gestionado, true);
        afirmar.equal(documento.activeElement, opciones[indice]);
        afirmar.deepEqual(opciones.map(opcion => opcion.tabIndex), opciones.map((_, i) => i === indice ? 0 : -1));
        afirmar.deepEqual(opciones.map(opcion => opcion.getAttribute("aria-checked")), ["false", "true", "false"]);
    }
});

prueba("las flechas fuera del menú de Configuración conservan su comportamiento", () => {
    const {eventos} = montarConfiguracion("papel");
    const opcion = {closest: () => null};
    eventos.get("keydown")({key: "ArrowDown", target: {closest: () => opcion},
        preventDefault: () => afirmar.fail("No debe capturar la tecla de otro control")});
});
