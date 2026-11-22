"use strict";

const afirmar = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const prueba = require("node:test");
const vm = require("node:vm");

function crearNodo(etiqueta, documento, extras = {}) {
    const escuchadores = new Map();
    const atributos = new Map(Object.entries(extras.atributos || {}));
    return {
        tagName: etiqueta.toUpperCase(), value: "", hidden: false, open: false,
        disabled: false, readOnly: false, isConnected: true, scrollTop: 0,
        children: [], dataset: {}, textContent: "", className: "", ...extras, atributos,
        setAttribute(nombre, valor) { this.atributos.set(nombre, String(valor)); },
        getAttribute(nombre) { return this.atributos.get(nombre) ?? null; },
        hasAttribute(nombre) { return this.atributos.has(nombre); },
        addEventListener(tipo, funcion) {
            if (!escuchadores.has(tipo)) escuchadores.set(tipo, []);
            escuchadores.get(tipo).push(funcion);
        },
        dispatchEvent(evento) {
            for (const funcion of escuchadores.get(evento.type) || []) funcion(evento);
        },
        click() { this.dispatchEvent({ type: "click", target: this, preventDefault() {}, stopPropagation() {} }); },
        focus() { documento.activeElement = this; },
        select() {},
        append(...nodos) { this.children.push(...nodos); },
        replaceChildren(...nodos) { this.children = [...nodos]; },
        get firstElementChild() { return this.children[0] || null; },
    };
}

function crearCampo(documento, opciones = {}) {
    const valor = opciones.valor ?? "";
    const campo = crearNodo(opciones.tipoElemento || "INPUT", documento, {
        value: valor, selectionStart: valor.length, selectionEnd: valor.length,
        maxLength: -1, dataset: { ...(opciones.dataset || {}) }, atributos: opciones.atributos,
    });
    campo.matches = selector => selector.includes(campo.tagName.toLowerCase());
    campo.closest = selector => (opciones.dentroDialogo && selector.includes(".simbolos-dialogo") ? {} : null);
    campo.getClientRects = () => [{}];
    campo.setRangeText = (reemplazo, inicio, fin) => {
        campo.value = campo.value.slice(0, inicio) + reemplazo + campo.value.slice(fin);
        campo.selectionStart = campo.selectionEnd = inicio + reemplazo.length;
    };
    campo.setSelectionRange = (inicio, fin) => { campo.selectionStart = inicio; campo.selectionEnd = fin; };
    return campo;
}

function crearDialogo(documento) {
    const dialogo = crearNodo("dialog", documento, {
        getBoundingClientRect: () => ({ left: 100, right: 500, top: 100, bottom: 400 }),
        showModal() { this.open = true; },
        close() { if (this.open) { this.open = false; this.dispatchEvent({ type: "close" }); } },
    });
    const busqueda = crearCampo(documento, { dentroDialogo: true });
    const grupo = crearNodo("select", documento);
    const lista = crearNodo("div", documento);
    const estado = crearNodo("p", documento);
    const mas = crearNodo("button", documento, { hidden: true });
    const campoCopia = crearCampo(documento, { dentroDialogo: true });
    const copia = crearNodo("label", documento, { hidden: true, querySelector: () => campoCopia });
    const mapa = {
        ".simbolos-cuerpo": crearNodo("div", documento), 'input[type="search"]': busqueda,
        "select": grupo, ".simbolos-lista": lista, '[role="status"]': estado,
        "[data-mas-simbolos]": mas, "[data-copia-simbolo]": copia,
    };
    dialogo.querySelector = selector => mapa[selector] || null;
    return { dialogo, busqueda, grupo, lista, estado, mas, copia };
}

function cargarSelector(documento, copiados) {
    const contexto = vm.createContext({
        window: {}, document: documento,
        navigator: { clipboard: { writeText: async texto => { copiados.push(texto); } } },
        Event: class { constructor(tipo, cfg = {}) { this.type = tipo; this.bubbles = Boolean(cfg.bubbles); } },
        Option: class { constructor(texto, valor) { this.text = texto; this.value = valor; } },
    });
    const base = path.join(__dirname, "../src/frontend/recursos/js");
    vm.runInContext(fs.readFileSync(path.join(base, "nucleo/escritura/catalogo_simbolos.js"), "utf8"), contexto);
    vm.runInContext(fs.readFileSync(path.join(base, "nucleo/escritura/selector_simbolos.js"), "utf8"), contexto);
    return contexto;
}

function crearAccionesFiltrado(eventosDocumento, partes) {
    const abrirEn = objetivo => {
        objetivo.focus();
        for (const manejador of eventosDocumento.get("focusin") || []) manejador({ target: objetivo });
        for (const manejador of eventosDocumento.get("keydown") || []) {
            manejador({ ctrlKey: true, shiftKey: true, code: "Space", target: objetivo, preventDefault() {}, stopPropagation() {} });
        }
    };
    const buscar = texto => { partes.busqueda.value = texto; partes.busqueda.dispatchEvent({ type: "input" }); };
    const signosVisibles = () => {
        while (!partes.mas.hidden) partes.mas.click();
        return partes.lista.children.map(boton => boton.children[0].textContent);
    };
    return { abrirEn, buscar, signosVisibles };
}

function crearEntornoFiltrado(moduloInicial = "") {
    let moduloActual = moduloInicial;
    const eventosDocumento = new Map();
    const copiados = [];
    const documento = {
        activeElement: null, body: { append() {} },
        addEventListener(tipo, funcion) {
            if (!eventosDocumento.has(tipo)) eventosDocumento.set(tipo, []);
            eventosDocumento.get(tipo).push(funcion);
        },
        createElement: etiqueta => crearNodo(etiqueta, documento),
        querySelector: selector => (selector === 'meta[name="scalaris-modulo"]' && moduloActual
            ? { getAttribute: nombre => (nombre === "content" ? moduloActual : null) } : null),
    };
    const partes = crearDialogo(documento);
    documento.getElementById = id => (id === "plantilla-simbolos"
        ? { content: { firstElementChild: { cloneNode: () => partes.dialogo } } } : null);
    const contexto = cargarSelector(documento, copiados);
    return {
        documento, ...partes, copiados, contexto, ...crearAccionesFiltrado(eventosDocumento, partes),
        fijarModulo: nuevo => { moduloActual = nuevo; },
    };
}

prueba("oculta simbolos incompatibles y categorias vacias en cada perfil", () => {
    const entorno = crearEntornoFiltrado();
    const expectativas = [
        ["funcion", ["√", "⁰", "π", "ℯ", "¼", "∞", "∫"], ["ᵀ", "⊕", "₀"], ["", "Operadores", "Raíces, potencias y subíndices", "Fracciones", "Letras griegas", "Cálculo y geometría"]],
        ["matriz", ["−", "×", "·", "⋅", "∙", "ᵀ", "½"], ["√", "π", "∞", "₀"], ["", "Operadores", "Raíces, potencias y subíndices", "Fracciones", "Cálculo y geometría"]],
        ["numero", ["−", "⁄", "∕", "¼", "½"], ["×", "√", "π", "ᵀ", "∞"], ["", "Operadores", "Fracciones", "Cálculo y geometría"]],
        ["ecuacion", ["−", "⁄", "∕", "¼"], ["√", "⁰", "ᵀ", "∞"], ["", "Operadores", "Raíces, potencias y subíndices", "Fracciones", "Letras griegas", "Cálculo y geometría"]],
        ["real", ["−", "√", "π", "‰", "°"], ["∞", "ᵀ", "∫"], ["", "Operadores", "Raíces, potencias y subíndices", "Fracciones", "Letras griegas", "Cálculo y geometría"]],
        ["base", ["−"], ["×", "√", "π", "½", "∞"], ["", "Operadores"]],
    ];
    for (const [perfil, incluidos, excluidos, grupos] of expectativas) {
        const campo = crearCampo(entorno.documento, { dataset: { simbolos: perfil } });
        entorno.abrirEn(campo);
        const visibles = entorno.signosVisibles();
        for (const simbolo of incluidos) afirmar.ok(visibles.includes(simbolo), `${perfil} incluye ${simbolo}`);
        for (const simbolo of excluidos) afirmar.ok(!visibles.includes(simbolo), `${perfil} oculta ${simbolo}`);
        afirmar.deepEqual(entorno.grupo.children.map(opcion => opcion.value), grupos);
        afirmar.equal(entorno.grupo.disabled, false);
        entorno.dialogo.close();
    }
});

prueba("deshabilita categorias y orienta al usuario en perfiles romano y entero", () => {
    const entorno = crearEntornoFiltrado("romanos");
    const campoRomano = crearCampo(entorno.documento, { dataset: { simbolos: "romano" } });
    entorno.abrirEn(campoRomano);
    afirmar.equal(entorno.lista.children.length, 0);
    afirmar.equal(entorno.grupo.disabled, true);
    afirmar.deepEqual(entorno.grupo.children.map(opcion => opcion.value), [""]);
    afirmar.equal(entorno.estado.textContent, "Este campo solo admite números romanos (I, V, X, L, C, D, M).");
    entorno.dialogo.close();

    const campoEntero = crearCampo(entorno.documento, { dataset: { simbolos: "entero" } });
    entorno.abrirEn(campoEntero);
    afirmar.equal(entorno.lista.children.length, 0);
    afirmar.equal(entorno.grupo.disabled, true);
    afirmar.equal(entorno.estado.textContent, "Este campo solo admite números enteros positivos.");
    entorno.dialogo.close();
});

prueba("restringe la busqueda Unicode en perfiles acotados y la conserva en texto", () => {
    const entorno = crearEntornoFiltrado("metodos_abiertos");
    const campoFuncion = crearCampo(entorno.documento, { dataset: { simbolos: "funcion" } });
    entorno.abrirEn(campoFuncion);
    entorno.buscar("U+221E");
    afirmar.deepEqual(entorno.signosVisibles(), ["∞"]);
    entorno.buscar("");
    afirmar.ok(entorno.estado.textContent.startsWith("Se muestran "));
    entorno.buscar("U+03C0");
    afirmar.deepEqual(entorno.signosVisibles(), ["π"]);
    entorno.buscar("U+2605");
    afirmar.equal(entorno.lista.children.length, 0);
    entorno.dialogo.close();

    const campoGlosa = crearCampo(entorno.documento, { tipoElemento: "TEXTAREA", dataset: { simbolos: "texto" } });
    entorno.abrirEn(campoGlosa);
    entorno.buscar("U+221E");
    afirmar.deepEqual(entorno.signosVisibles(), ["∞"]);
    entorno.buscar("U+2605");
    afirmar.deepEqual(entorno.signosVisibles(), ["★"]);
});

prueba("usa el modulo activo sin foco y alterna limpiamente entre campos", async () => {
    const entorno = crearEntornoFiltrado("matrices");
    const boton = crearNodo("button", entorno.documento);
    entorno.abrirEn(boton);
    const visiblesMatrices = entorno.signosVisibles();
    afirmar.ok(visiblesMatrices.includes("ᵀ"));
    afirmar.ok(visiblesMatrices.includes("½"));
    afirmar.ok(!visiblesMatrices.includes("√"));
    afirmar.ok(!visiblesMatrices.includes("∞"));
    const botonTranspuesta = entorno.lista.children.find(opcion => opcion.children[0].textContent === "ᵀ");
    afirmar.equal(botonTranspuesta.children[2].textContent, "Copiar");
    botonTranspuesta.click();
    await new Promise(resolver => setImmediate(resolver));
    afirmar.deepEqual(entorno.copiados, ["ᵀ"]);

    entorno.fijarModulo("bases");
    entorno.abrirEn(boton);
    afirmar.deepEqual(entorno.signosVisibles(), ["−"]);
    entorno.dialogo.close();

    entorno.fijarModulo("romanos");
    const glosa = crearCampo(entorno.documento, { tipoElemento: "TEXTAREA", dataset: { simbolos: "texto" } });
    entorno.abrirEn(glosa);
    afirmar.ok(entorno.signosVisibles().includes("∞"));
    entorno.dialogo.close();

    glosa.isConnected = false;
    entorno.abrirEn(boton);
    afirmar.equal(entorno.lista.children.length, 0);
    afirmar.equal(entorno.estado.textContent, "Este campo solo admite números romanos (I, V, X, L, C, D, M).");
    entorno.dialogo.close();

    entorno.fijarModulo("inicio");
    entorno.abrirEn(boton);
    afirmar.ok(entorno.signosVisibles().includes("∞"));
});
