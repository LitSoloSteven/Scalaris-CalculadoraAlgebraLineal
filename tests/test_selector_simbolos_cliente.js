"use strict";

const afirmar = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const prueba = require("node:test");
const vm = require("node:vm");

function crearNodoSimulado(etiqueta, documento, extras = {}) {
    const escuchadores = new Map();
    const nodo = {
        tagName: etiqueta.toUpperCase(),
        value: "",
        hidden: false,
        open: false,
        disabled: false,
        readOnly: false,
        isConnected: true,
        scrollTop: 0,
        children: [],
        atributos: new Map(),
        dataset: {},
        textContent: "",
        className: "",
        ...extras,
        setAttribute(nombre, valor) {
            this.atributos.set(nombre, String(valor));
        },
        getAttribute(nombre) {
            return this.atributos.get(nombre) ?? null;
        },
        hasAttribute(nombre) {
            return this.atributos.has(nombre);
        },
        addEventListener(tipo, manejador) {
            if (!escuchadores.has(tipo)) escuchadores.set(tipo, []);
            escuchadores.get(tipo).push(manejador);
        },
        dispatchEvent(evento) {
            for (const manejador of escuchadores.get(evento.type) || []) {
                manejador(evento);
            }
        },
        click() {
            this.dispatchEvent({ type: "click", target: this, preventDefault() {}, stopPropagation() {} });
        },
        focus() {
            documento.activeElement = this;
            this.enfocado = true;
        },
        select() {
            this.seleccionado = true;
        },
        append(...elementos) {
            for (const elemento of elementos) {
                elemento.parentNode = this;
                this.children.push(elemento);
            }
        },
        replaceChildren(...elementos) {
            this.children = [];
            this.append(...elementos);
        },
        get firstElementChild() {
            return this.children[0] || null;
        },
    };
    return nodo;
}

function crearCampoSimulado(documento, opciones = {}) {
    const tipoElemento = opciones.tipoElemento || "INPUT";
    const atributos = new Map(Object.entries(opciones.atributos || {}));
    const campo = crearNodoSimulado(tipoElemento, documento, {
        value: opciones.valor ?? "",
        selectionStart: opciones.seleccion ? opciones.seleccion[0] : (opciones.valor ?? "").length,
        selectionEnd: opciones.seleccion ? opciones.seleccion[1] : (opciones.valor ?? "").length,
        maxLength: opciones.maxLength ?? -1,
        disabled: Boolean(opciones.disabled),
        readOnly: Boolean(opciones.readOnly),
        isConnected: opciones.isConnected ?? true,
        dataset: { ...(opciones.dataset || {}) },
        atributos,
    });
    campo.matches = selector => {
        if (campo.tagName === "TEXTAREA") return selector.includes("textarea");
        if (campo.tagName === "INPUT") return selector.includes("input");
        return false;
    };
    campo.closest = selector => {
        if (opciones.dentroDialogo && selector.includes(".simbolos-dialogo")) return {};
        if (opciones.inert && selector.includes("[inert]")) return {};
        return null;
    };
    campo.getClientRects = () => (opciones.visible === false ? [] : [{}]);
    campo.setRangeText = (reemplazo, inicio, fin, modo) => {
        campo.value = campo.value.slice(0, inicio) + reemplazo + campo.value.slice(fin);
        if (modo === "end") {
            campo.selectionStart = inicio + reemplazo.length;
            campo.selectionEnd = inicio + reemplazo.length;
        }
    };
    campo.setSelectionRange = (inicio, fin) => {
        campo.selectionStart = inicio;
        campo.selectionEnd = fin;
    };
    return campo;
}

function crearEntornoSelector(opciones = {}) {
    const eventosDocumento = new Map();
    const portapapelesCopiado = [];
    const documento = {
        activeElement: null,
        body: { append() {} },
        addEventListener(tipo, manejador) {
            if (!eventosDocumento.has(tipo)) eventosDocumento.set(tipo, []);
            eventosDocumento.get(tipo).push(manejador);
        },
        createElement(etiqueta) {
            return crearNodoSimulado(etiqueta, documento);
        },
    };

    const dialogo = crearNodoSimulado("dialog", documento, {
        getBoundingClientRect: () => ({ left: 100, right: 500, top: 100, bottom: 400 }),
        showModal() {
            this.open = true;
        },
        close() {
            if (!this.open) return;
            this.open = false;
            this.dispatchEvent({ type: "close" });
        },
    });
    const cuerpo = crearNodoSimulado("div", documento, { scrollTop: 120 });
    const busqueda = crearCampoSimulado(documento, { dentroDialogo: true });
    const grupo = crearNodoSimulado("select", documento, {
        opciones: [],
        add(opcion) { this.opciones.push(opcion); },
    });
    const lista = crearNodoSimulado("div", documento);
    const estado = crearNodoSimulado("p", documento);
    const mas = crearNodoSimulado("button", documento, { hidden: true });
    const campoCopia = crearCampoSimulado(documento, { dentroDialogo: true });
    const copia = crearNodoSimulado("label", documento, {
        hidden: true,
        querySelector: () => campoCopia,
    });

    const mapaSelectores = {
        ".simbolos-cuerpo": cuerpo,
        'input[type="search"]': busqueda,
        "select": grupo,
        ".simbolos-lista": lista,
        '[role="status"]': estado,
        "[data-mas-simbolos]": mas,
        "[data-copia-simbolo]": copia,
    };
    dialogo.querySelector = selector => mapaSelectores[selector] || null;
    documento.getElementById = id => (id === "plantilla-simbolos"
        ? { content: { firstElementChild: { cloneNode: () => dialogo } } }
        : null);

    const navigatorSimulado = {
        clipboard: {
            writeText: async texto => {
                if (opciones.fallarPortapapeles) throw new Error("Sin permiso");
                portapapelesCopiado.push(texto);
            },
        },
    };
    const ventana = {};
    const contexto = vm.createContext({
        window: ventana,
        document: documento,
        navigator: navigatorSimulado,
        Event: class EventSimulado {
            constructor(tipo, config = {}) {
                this.type = tipo;
                this.bubbles = Boolean(config.bubbles);
            }
        },
        Option: class OptionSimulado {
            constructor(texto, valor) {
                this.text = texto;
                this.value = valor;
            }
        },
    });
    const rutaCatalogo = path.join(__dirname, "../src/frontend/recursos/js/catalogo_simbolos.js");
    const rutaSelector = path.join(__dirname, "../src/frontend/recursos/js/selector_simbolos.js");
    vm.runInContext(fs.readFileSync(rutaCatalogo, "utf8"), contexto);
    vm.runInContext(fs.readFileSync(rutaSelector, "utf8"), contexto);

    function emitirDocumento(tipo, datosEvento) {
        const evento = {
            type: tipo,
            defaultPrevented: false,
            preventDefault() { this.defaultPrevented = true; },
            stopPropagation() { this.propagacionDetenida = true; },
            ...datosEvento,
        };
        for (const manejador of eventosDocumento.get(tipo) || []) {
            manejador(evento);
        }
        return evento;
    }

    function abrirEn(campo) {
        campo.focus();
        emitirDocumento("focusin", { target: campo });
        return emitirDocumento("keydown", {
            ctrlKey: true, shiftKey: true, altKey: false, metaKey: false,
            isComposing: false, repeat: false, code: "Space", key: " ", target: campo,
        });
    }

    function buscarYElegir(textoBusqueda, simboloObjetivo) {
        busqueda.value = textoBusqueda;
        busqueda.dispatchEvent({ type: "input" });
        const boton = lista.children.find(opcion => opcion.children[0]?.textContent === simboloObjetivo);
        afirmar.ok(boton, `No se encontró la opción para ${simboloObjetivo}`);
        return { boton, promesa: boton.click() };
    }

    return {
        documento, dialogo, cuerpo, busqueda, grupo, lista, estado, mas, copia, campoCopia,
        eventosDocumento, portapapelesCopiado, emitirDocumento, abrirEn, buscarYElegir,
    };
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
    afirmar.equal(campo.selectionStart, 4);
    afirmar.equal(campo.selectionEnd, 4);

    campo.value = "x+1";
    campo.setSelectionRange(0, 3);
    entorno.abrirEn(campo);
    entorno.buscarYElegir("cuadrada", "√");
    afirmar.equal(campo.value, "√(x+1)");
    afirmar.equal(campo.selectionStart, 6);
    afirmar.equal(campo.selectionEnd, 6);

    entorno.abrirEn(campo);
    entorno.buscarYElegir("Infinito", "∞");
    afirmar.equal(campo.value, "√(x+1)∞");
    afirmar.equal(entorno.dialogo.open, false);
});

prueba("inserta y cierra en perfiles matriz, numero, ecuacion y texto generico", () => {
    const entorno = crearEntornoSelector();

    const campoMatriz = crearCampoSimulado(entorno.documento, {
        dataset: { simbolos: "matriz" }, valor: "A",
    });
    entorno.abrirEn(campoMatriz);
    entorno.buscarYElegir("Transpuesta", "ᵀ");
    afirmar.equal(campoMatriz.value, "Aᵀ");
    afirmar.equal(entorno.dialogo.open, false);

    const campoNumero = crearCampoSimulado(entorno.documento, {
        dataset: { soloNumerico: "true" }, valor: "",
    });
    entorno.abrirEn(campoNumero);
    const opcionNumero = entorno.buscarYElegir("1/2", "½");
    afirmar.equal(opcionNumero.boton.children[2].textContent, "Insertar 1/2");
    afirmar.equal(campoNumero.value, "1/2");
    afirmar.equal(entorno.dialogo.open, false);

    const campoEcuacion = crearCampoSimulado(entorno.documento, {
        atributos: { "data-ecuaciones-indice": "0" }, valor: "2x",
    });
    entorno.abrirEn(campoEcuacion);
    entorno.buscarYElegir("Signo menos", "−");
    afirmar.equal(campoEcuacion.value, "2x-");
    afirmar.equal(entorno.dialogo.open, false);

    const campoTexto = crearCampoSimulado(entorno.documento, {
        tipoElemento: "TEXTAREA", valor: "Nota ",
    });
    entorno.abrirEn(campoTexto);
    entorno.buscarYElegir("Infinito", "∞");
    afirmar.equal(campoTexto.value, "Nota ∞");
    afirmar.equal(entorno.dialogo.open, false);
});

prueba("conserva la posicion del cursor resultante tras saneado en evento input", () => {
    const entorno = crearEntornoSelector();
    const campoNumero = crearCampoSimulado(entorno.documento, {
        dataset: { soloNumerico: "true" }, valor: "1",
    });
    campoNumero.addEventListener("input", () => {
        campoNumero.value = campoNumero.value.replace(/[^0-9/+-]/g, "");
        campoNumero.setSelectionRange(campoNumero.value.length, campoNumero.value.length);
    });

    entorno.abrirEn(campoNumero);
    entorno.buscarYElegir("Infinito", "∞");

    afirmar.equal(campoNumero.value, "1");
    afirmar.equal(entorno.dialogo.open, false);
    afirmar.equal(entorno.documento.activeElement, campoNumero);
    afirmar.equal(campoNumero.selectionStart, 1);
    afirmar.equal(campoNumero.selectionEnd, 1);
});

prueba("prioriza simbolos compatibles y etiqueta los incompatibles como solo texto", () => {
    const entorno = crearEntornoSelector();
    const campoFuncion = crearCampoSimulado(entorno.documento, {
        dataset: { simbolos: "funcion" }, valor: "",
    });
    entorno.abrirEn(campoFuncion);

    entorno.busqueda.value = "";
    entorno.busqueda.dispatchEvent({ type: "input" });
    afirmar.equal(entorno.lista.children[0].children[2].textContent, "Insertar");

    entorno.buscarYElegir("Infinito", "∞");
    const opcionInfinito = entorno.lista.children.find(opcion => opcion.children[0]?.textContent === "∞");
    afirmar.equal(opcionInfinito.children[2].textContent, "Insertar · solo texto");
});

prueba("mantiene abierto el dialogo si maxLength impide insertar y usa ultimo campo visible", () => {
    const entorno = crearEntornoSelector();
    const campoCorto = crearCampoSimulado(entorno.documento, {
        dataset: { simbolos: "funcion" }, valor: "x", maxLength: 1,
    });
    const botonPagina = crearNodoSimulado("button", entorno.documento);

    entorno.emitirDocumento("focusin", { target: campoCorto });
    botonPagina.focus();
    entorno.emitirDocumento("keydown", {
        ctrlKey: true, shiftKey: true, altKey: false, metaKey: false,
        isComposing: false, repeat: false, code: "Space", key: " ", target: botonPagina,
    });

    afirmar.equal(entorno.dialogo.open, true);
    entorno.buscarYElegir("Infinito", "∞");
    afirmar.equal(campoCorto.value, "x");
    afirmar.equal(entorno.dialogo.open, true);
    afirmar.equal(entorno.estado.textContent, "El símbolo no cabe en el campo o el campo ya no está disponible.");
});

prueba("excluye campos ocultos, inert y el buscador interno; respalda portapapeles sin campo", async () => {
    const entorno = crearEntornoSelector();
    const campoOculto = crearCampoSimulado(entorno.documento, { visible: false, valor: "oculto" });
    const campoInerte = crearCampoSimulado(entorno.documento, { inert: true, valor: "inerte" });

    entorno.emitirDocumento("focusin", { target: campoOculto });
    entorno.emitirDocumento("focusin", { target: campoInerte });
    entorno.emitirDocumento("focusin", { target: entorno.busqueda });

    const boton = crearNodoSimulado("button", entorno.documento);
    entorno.emitirDocumento("keydown", {
        ctrlKey: true, shiftKey: true, altKey: false, metaKey: false,
        isComposing: false, repeat: false, code: "Space", key: " ", target: boton,
    });

    afirmar.equal(entorno.dialogo.open, true);
    const { boton: opcion } = entorno.buscarYElegir("Infinito", "∞");
    afirmar.equal(opcion.children[2].textContent, "Copiar");
    await new Promise(resolver => setImmediate(resolver));
    afirmar.deepEqual(entorno.portapapelesCopiado, ["∞"]);
    afirmar.equal(entorno.dialogo.open, false);

    const entornoError = crearEntornoSelector({ fallarPortapapeles: true });
    entornoError.emitirDocumento("keydown", {
        ctrlKey: true, shiftKey: true, altKey: false, metaKey: false,
        isComposing: false, repeat: false, code: "Space", key: " ", target: boton,
    });
    entornoError.buscarYElegir("Infinito", "∞");
    await new Promise(resolver => setImmediate(resolver));
    afirmar.equal(entornoError.copia.hidden, false);
    afirmar.equal(entornoError.campoCopia.value, "∞");
    afirmar.equal(entornoError.campoCopia.seleccionado, true);
});

prueba("cierra con Escape sin propagar y con pulsacion exterior sin cerrar por arrastre", () => {
    const entorno = crearEntornoSelector();
    const campo = crearCampoSimulado(entorno.documento, { dataset: { simbolos: "funcion" }, valor: "" });

    entorno.abrirEn(campo);
    const eventoEscape = {
        type: "keydown", key: "Escape", target: entorno.busqueda,
        defaultPrevented: false, propagacionDetenida: false,
        preventDefault() { this.defaultPrevented = true; },
        stopPropagation() { this.propagacionDetenida = true; },
    };
    entorno.dialogo.dispatchEvent(eventoEscape);
    afirmar.equal(eventoEscape.defaultPrevented, true);
    afirmar.equal(eventoEscape.propagacionDetenida, true);
    afirmar.equal(entorno.dialogo.open, false);

    entorno.abrirEn(campo);
    entorno.dialogo.dispatchEvent({ type: "pointerdown", clientX: 250, clientY: 250 });
    entorno.dialogo.dispatchEvent({ type: "pointerup", clientX: 20, clientY: 20 });
    afirmar.equal(entorno.dialogo.open, true);

    entorno.dialogo.dispatchEvent({ type: "pointerdown", clientX: 20, clientY: 20 });
    entorno.dialogo.dispatchEvent({ type: "pointerup", clientX: 25, clientY: 25 });
    afirmar.equal(entorno.dialogo.open, false);
});
