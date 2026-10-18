"use strict";
const maquinaVirtual = require("node:vm");
const { cargarAssetCliente } = require("./comun_cliente_javascript.js");

/** Crea un elemento con atributos, visibilidad y foco observables. */
function crearElementoGlosa(documento, opciones = {}) {
    const atributos = new Map();
    return {
        isConnected: true, tabIndex: 0, inert: false, parentElement: null, ...opciones,
        atributos, style: { setProperty() {}, removeProperty() {} },
        classList: { contains: () => false },
        getAttribute: nombre => atributos.get(nombre),
        setAttribute: (nombre, valor) => atributos.set(nombre, valor),
        removeAttribute: nombre => atributos.delete(nombre),
        hasAttribute: nombre => atributos.has(nombre),
        focus() { if (!this.disabled && !this.inert && !this.invisible && !this.oculto) documento.activeElement = this; },
        closest() { return this.inert || this.oculto ? this : null; },
        matches() { return !!this.disabled; },
        getClientRects() { return this.invisible ? [] : [{}]; },
    };
}

/** Monta los dos assets reales con un panel, controles y eventos de documento. */
function crearGlosaSimulada(modo = "superposicion") {
    const eventos = new Map();
    const documento = { addEventListener: (nombre, manejar) => {
        eventos.set(nombre, [...(eventos.get(nombre) || []), manejar]);
    }, dispatchEvent() {} };
    const raiz = crearElementoGlosa(documento);
    raiz.setAttribute("data-glosa", "cerrado");
    const origen = crearElementoGlosa(documento);
    const controles = [crearElementoGlosa(documento), crearElementoGlosa(documento)];
    const panel = crearElementoGlosa(documento, { tabIndex: -1,
        querySelector: () => controles[1], querySelectorAll: () => controles,
        contains: elemento => elemento === panel || controles.includes(elemento) });
    documento.documentElement = raiz;
    documento.body = { children: [panel, origen] };
    panel.parentElement = documento.body;
    documento.activeElement = origen;
    documento.getElementById = () => panel;
    documento.querySelector = selector => selector === ".glosa-boton-flotante" ? origen : null;
    documento.querySelectorAll = selector => selector === "[data-glosa-inactivo]" ? [origen] : [];
    const ventana = { addEventListener() {}, matchMedia: () => ({ matches: false }) };
    const contexto = maquinaVirtual.createContext({ window: ventana, document: documento,
        getComputedStyle: () => ({ getPropertyValue: () => modo }),
        history: { pushState() {}, back() {} }, localStorage: { setItem() {} },
        requestAnimationFrame: manejar => manejar(), CustomEvent: function () {} });
    cargarAssetCliente("foco_modal.js", contexto);
    cargarAssetCliente("glosa_foco.js", contexto);
    cargarAssetCliente("glosa_panel_lateral.js", contexto);
    return { ventana, documento, panel, controles, origen, eventos, raiz };
}

/** Despacha un evento de tecla por todos los manejadores reales registrados. */
function pulsarGlosa(cliente, tecla, inverso = false) {
    const evento = { key: tecla, shiftKey: inverso, target: cliente.documento.activeElement,
        defaultPrevented: false, preventDefault() { this.defaultPrevented = true; } };
    cliente.eventos.get("keydown").forEach(manejar => manejar(evento));
    return evento;
}

module.exports = { crearGlosaSimulada, crearElementoGlosa, pulsarGlosa };
