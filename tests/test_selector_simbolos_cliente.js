"use strict";

const afirmar = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const prueba = require("node:test");
const vm = require("node:vm");

function crearNodoSimulado(etiqueta, documento, extras = {}) {
    const escuchadores = new Map();
    const atributos = new Map(Object.entries(extras.atributos || {}));
    return {
        tagName: etiqueta.toUpperCase(), value: "", hidden: false, open: false,
        disabled: false, readOnly: false, isConnected: true, scrollTop: 0,
        children: [], dataset: {}, textContent: "", className: "", ...extras, atributos,
        setAttribute(nombre, valor) { this.atributos.set(nombre, String(valor)); },
        getAttribute(nombre) { return this.atributos.get(nombre) ?? null; },
        hasAttribute(nombre) { return this.atributos.has(nombre); },
        addEventListener(tipo, fn) {
            if (!escuchadores.has(tipo)) escuchadores.set(tipo, []);
            escuchadores.get(tipo).push(fn);
        },
        dispatchEvent(evento) {
            for (const fn of escuchadores.get(evento.type) || []) fn(evento);
        },
        click() { this.dispatchEvent({ type: "click", target: this, preventDefault() {}, stopPropagation() {} }); },
        focus() { documento.activeElement = this; this.enfocado = true; },
        select() { this.seleccionado = true; },
        append(...nodos) { this.children.push(...nodos); },
        replaceChildren(...nodos) { this.children = [...nodos]; },
        get firstElementChild() { return this.children[0] || null; },
    };
}

function crearCampoSimulado(documento, opciones = {}) {
    const valor = opciones.valor ?? "";
    const seleccion = opciones.seleccion || [valor.length, valor.length];
    const campo = crearNodoSimulado(opciones.tipoElemento || "INPUT", documento, {
        value: valor, selectionStart: seleccion[0], selectionEnd: seleccion[1],
        maxLength: opciones.maxLength ?? -1, disabled: Boolean(opciones.disabled),
        readOnly: Boolean(opciones.readOnly), isConnected: opciones.isConnected ?? true,
        dataset: { ...(opciones.dataset || {}) }, atributos: opciones.atributos,
    });
    campo.matches = selector => selector.includes(campo.tagName.toLowerCase());
    campo.closest = selector => {
        if (opciones.dentroDialogo && selector.includes(".simbolos-dialogo")) return {};
        return opciones.inert && selector.includes("[inert]") ? {} : null;
    };
    campo.getClientRects = () => (opciones.visible === false ? [] : [{}]);
    campo.setRangeText = (reemplazo, inicio, fin) => {
        campo.value = campo.value.slice(0, inicio) + reemplazo + campo.value.slice(fin);
        campo.selectionStart = campo.selectionEnd = inicio + reemplazo.length;
    };
    campo.setSelectionRange = (inicio, fin) => { campo.selectionStart = inicio; campo.selectionEnd = fin; };
    return campo;
}

function crearDialogoSimulado(documento) {
    const dialogo = crearNodoSimulado("dialog", documento, {
        getBoundingClientRect: () => ({ left: 100, right: 500, top: 100, bottom: 400 }),
        showModal() { this.open = true; },
        close() { if (this.open) { this.open = false; this.dispatchEvent({ type: "close" }); } },
    });
    const cuerpo = crearNodoSimulado("div", documento, { scrollTop: 120 });
    const busqueda = crearCampoSimulado(documento, { dentroDialogo: true });
    const grupo = crearNodoSimulado("select", documento, { add() {} });
    const lista = crearNodoSimulado("div", documento);
    const estado = crearNodoSimulado("p", documento);
    const mas = crearNodoSimulado("button", documento, { hidden: true });
    const campoCopia = crearCampoSimulado(documento, { dentroDialogo: true });
    const copia = crearNodoSimulado("label", documento, { hidden: true, querySelector: () => campoCopia });
    const mapa = {
        ".simbolos-cuerpo": cuerpo, 'input[type="search"]': busqueda, "select": grupo,
        ".simbolos-lista": lista, '[role="status"]': estado, "[data-mas-simbolos]": mas,
        "[data-copia-simbolo]": copia,
    };
    dialogo.querySelector = selector => mapa[selector] || null;
    return { dialogo, cuerpo, busqueda, grupo, lista, estado, mas, copia, campoCopia };
}

function cargarScriptsSelector(documento, navigatorSimulado) {
    const contexto = vm.createContext({
        window: {}, document: documento, navigator: navigatorSimulado,
        Event: class { constructor(tipo, cfg = {}) { this.type = tipo; this.bubbles = Boolean(cfg.bubbles); } },
        Option: class { constructor(t, v) { this.text = t; this.value = v; } },
    });
    const base = path.join(__dirname, "../src/frontend/recursos/js");
    vm.runInContext(fs.readFileSync(path.join(base, "catalogo_simbolos.js"), "utf8"), contexto);
    vm.runInContext(fs.readFileSync(path.join(base, "selector_simbolos.js"), "utf8"), contexto);
}

function crearAccionesEntorno(eventosDocumento, partes) {
    const emitirDocumento = (tipo, datos) => {
        const ev = {
            type: tipo, defaultPrevented: false,
            preventDefault() { this.defaultPrevented = true; },
            stopPropagation() { this.propagacionDetenida = true; }, ...datos,
        };
        for (const fn of eventosDocumento.get(tipo) || []) fn(ev);
        return ev;
    };
    const abrirEn = campo => {
        campo.focus();
        emitirDocumento("focusin", { target: campo });
        return emitirDocumento("keydown", { ctrlKey: true, shiftKey: true, code: "Space", target: campo });
    };
    const buscarYElegir = (consulta, simbolo) => {
        partes.busqueda.value = consulta;
        partes.busqueda.dispatchEvent({ type: "input" });
        const boton = partes.lista.children.find(op => op.children[0]?.textContent === simbolo);
        afirmar.ok(boton);
        boton.click();
        return boton;
    };
    return { emitirDocumento, abrirEn, buscarYElegir };
}

function crearEntornoSelector(opciones = {}) {
    const eventosDocumento = new Map();
    const portapapelesCopiado = [];
    const documento = {
        activeElement: null, body: { append() {} },
        addEventListener(tipo, fn) {
            if (!eventosDocumento.has(tipo)) eventosDocumento.set(tipo, []);
            eventosDocumento.get(tipo).push(fn);
        },
        createElement: etiqueta => crearNodoSimulado(etiqueta, documento),
    };
    const partes = crearDialogoSimulado(documento);
    documento.getElementById = id => (id === "plantilla-simbolos"
        ? { content: { firstElementChild: { cloneNode: () => partes.dialogo } } } : null);
    cargarScriptsSelector(documento, {
        clipboard: {
            writeText: async texto => {
                if (opciones.fallarPortapapeles) throw new Error("Sin permiso");
                portapapelesCopiado.push(texto);
            },
        },
    });
    const acciones = crearAccionesEntorno(eventosDocumento, partes);
    return { documento, ...partes, eventosDocumento, portapapelesCopiado, ...acciones };
}

prueba("no registra listener de clic para boton visible y abre con Ctrl+Mayus+Espacio", () => {
    const entorno = crearEntornoSelector();
    afirmar.equal(entorno.eventosDocumento.has("click"), false);
    const campo = crearCampoSimulado(entorno.documento, { dataset: { simbolos: "funcion" }, valor: "x" });
    const evento = entorno.abrirEn(campo);
    afirmar.equal(evento.defaultPrevented, true);
    afirmar.equal(entorno.dialogo.open, true);
    afirmar.equal(entorno.documento.activeElement, entorno.busqueda);
    afirmar.equal(entorno.cuerpo.scrollTop, 0);
});

prueba("inserta raiz cuadrada y simbolo no evaluable en funcion cerrando el dialogo", () => {
    const entorno = crearEntornoSelector();
    const campo = crearCampoSimulado(entorno.documento, {
        dataset: { simbolos: "funcion" }, valor: "x+", seleccion: [2, 2],
    });
    entorno.abrirEn(campo);
    entorno.buscarYElegir("cuadrada", "√");
    afirmar.equal(campo.value, "x+√()");
    afirmar.equal(entorno.dialogo.open, false);
    afirmar.equal(entorno.documento.activeElement, campo);
    afirmar.deepEqual([campo.selectionStart, campo.selectionEnd], [4, 4]);

    campo.value = "x+1";
    campo.setSelectionRange(0, 3);
    entorno.abrirEn(campo);
    entorno.buscarYElegir("cuadrada", "√");
    afirmar.equal(campo.value, "√(x+1)");
    afirmar.deepEqual([campo.selectionStart, campo.selectionEnd], [6, 6]);

    entorno.abrirEn(campo);
    entorno.busqueda.value = "Infinito";
    entorno.busqueda.dispatchEvent({ type: "input" });
    afirmar.equal(entorno.lista.children.length, 0);
    afirmar.equal(campo.value, "√(x+1)");
    entorno.dialogo.close();
});

prueba("inserta y cierra en perfiles matriz, numero, ecuacion y texto generico", () => {
    const entorno = crearEntornoSelector();
    const campoMatriz = crearCampoSimulado(entorno.documento, { dataset: { simbolos: "matriz" }, valor: "A" });
    entorno.abrirEn(campoMatriz);
    entorno.buscarYElegir("Transpuesta", "ᵀ");
    afirmar.equal(campoMatriz.value, "Aᵀ");
    afirmar.equal(entorno.dialogo.open, false);

    const campoNumero = crearCampoSimulado(entorno.documento, { dataset: { soloNumerico: "true" }, valor: "" });
    entorno.abrirEn(campoNumero);
    const botonNumero = entorno.buscarYElegir("1/2", "½");
    afirmar.equal(botonNumero.children[2].textContent, "Insertar 1/2");
    afirmar.equal(campoNumero.value, "1/2");

    const campoEcuacion = crearCampoSimulado(entorno.documento, {
        atributos: { "data-ecuaciones-indice": "0" }, valor: "2x",
    });
    entorno.abrirEn(campoEcuacion);
    entorno.buscarYElegir("Signo menos", "−");
    afirmar.equal(campoEcuacion.value, "2x-");

    const campoTexto = crearCampoSimulado(entorno.documento, { tipoElemento: "TEXTAREA", valor: "Nota " });
    entorno.abrirEn(campoTexto);
    entorno.buscarYElegir("Infinito", "∞");
    afirmar.equal(campoTexto.value, "Nota ∞");
});

prueba("conserva cursor tras saneado en input, prioriza compatibles y respeta maxLength", () => {
    const entorno = crearEntornoSelector();
    const campoNumero = crearCampoSimulado(entorno.documento, { dataset: { soloNumerico: "true" }, valor: "1" });
    campoNumero.addEventListener("input", () => {
        campoNumero.value = campoNumero.value.replace(/[^0-9+-]/g, "");
        campoNumero.setSelectionRange(campoNumero.value.length, campoNumero.value.length);
    });
    entorno.abrirEn(campoNumero);
    entorno.busqueda.value = "Infinito";
    entorno.busqueda.dispatchEvent({ type: "input" });
    afirmar.equal(entorno.lista.children.length, 0);
    entorno.buscarYElegir("1/2", "½");
    afirmar.equal(campoNumero.value, "112");
    afirmar.deepEqual([campoNumero.selectionStart, campoNumero.selectionEnd], [3, 3]);

    const campoCorto = crearCampoSimulado(entorno.documento, {
        dataset: { simbolos: "funcion" }, valor: "x", maxLength: 1,
    });
    const botonPagina = crearNodoSimulado("button", entorno.documento);
    entorno.emitirDocumento("focusin", { target: campoCorto });
    botonPagina.focus();
    entorno.emitirDocumento("keydown", { ctrlKey: true, shiftKey: true, code: "Space", target: botonPagina });
    afirmar.equal(entorno.lista.children[0].children[2].textContent, "Insertar");
    entorno.busqueda.value = "Infinito";
    entorno.busqueda.dispatchEvent({ type: "input" });
    afirmar.equal(entorno.lista.children.length, 0);
    entorno.buscarYElegir("pi minúscula", "π");
    afirmar.equal(entorno.dialogo.open, true);
    afirmar.equal(entorno.estado.textContent, "El símbolo no cabe en el campo o el campo ya no está disponible.");
});

prueba("excluye campos ocultos o sin dataset y respalda portapapeles sin campo", async () => {
    const entorno = crearEntornoSelector();
    entorno.emitirDocumento("focusin", { target: crearCampoSimulado(entorno.documento, { visible: false }) });
    entorno.emitirDocumento("focusin", { target: crearCampoSimulado(entorno.documento, { inert: true }) });
    entorno.emitirDocumento("focusin", { target: entorno.busqueda });
    entorno.emitirDocumento("focusin", { target: { matches: () => true } });

    const boton = crearNodoSimulado("button", entorno.documento);
    entorno.emitirDocumento("keydown", { ctrlKey: true, shiftKey: true, code: "Space", target: boton });
    const opcion = entorno.buscarYElegir("Infinito", "∞");
    afirmar.equal(opcion.children[2].textContent, "Copiar");
    await new Promise(resolver => setImmediate(resolver));
    afirmar.deepEqual(entorno.portapapelesCopiado, ["∞"]);
    afirmar.equal(entorno.dialogo.open, false);

    const entornoError = crearEntornoSelector({ fallarPortapapeles: true });
    entornoError.emitirDocumento("keydown", { ctrlKey: true, shiftKey: true, code: "Space", target: boton });
    entornoError.buscarYElegir("Infinito", "∞");
    await new Promise(resolver => setImmediate(resolver));
    afirmar.equal(entornoError.copia.hidden, false);
    afirmar.equal(entornoError.campoCopia.value, "∞");
});

prueba("cierra con Escape sin propagar y con pulsacion exterior sin cerrar por arrastre", () => {
    const entorno = crearEntornoSelector();
    const campo = crearCampoSimulado(entorno.documento, { dataset: { simbolos: "funcion" }, valor: "" });
    entorno.abrirEn(campo);
    const ev = {
        type: "keydown", key: "Escape", target: entorno.busqueda,
        preventDefault() { this.cancelado = true; }, stopPropagation() { this.detenido = true; },
    };
    entorno.dialogo.dispatchEvent(ev);
    afirmar.equal(ev.cancelado && ev.detenido && !entorno.dialogo.open, true);

    entorno.abrirEn(campo);
    entorno.dialogo.dispatchEvent({ type: "pointerdown", clientX: 250, clientY: 250 });
    entorno.dialogo.dispatchEvent({ type: "pointerup", clientX: 20, clientY: 20 });
    afirmar.equal(entorno.dialogo.open, true);
    entorno.dialogo.dispatchEvent({ type: "pointerdown", clientX: 20, clientY: 20 });
    entorno.dialogo.dispatchEvent({ type: "pointerup", clientX: 25, clientY: 25 });
    afirmar.equal(entorno.dialogo.open, false);
});
