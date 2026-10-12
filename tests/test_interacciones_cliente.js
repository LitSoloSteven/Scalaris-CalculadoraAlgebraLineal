"use strict";

const afirmar = require("node:assert/strict");
const prueba = require("node:test");
const sistemaArchivos = require("node:fs");
const rutas = require("node:path");
const maquinaVirtual = require("node:vm");
const { cargarAssetCliente } = require("./comun_cliente_javascript.js");

const ARCHIVOS_CLIENTE = JSON.parse(sistemaArchivos.readFileSync(
    rutas.join(__dirname, "../src/frontend/assets/catalogo_interacciones.json"), "utf8",
));

/** Ejecuta los assets reales en un documento simulado con eventos y temporizadores observables. */
function crearClienteSimulado() {
    const atributos = new Map();
    const eventos = new Map();
    const elementos = new Map();
    const temporizadores = [];
    const documento = {
        documentElement: {
            setAttribute: (nombre, valor) => atributos.set(nombre, valor),
            getAttribute: nombre => atributos.get(nombre),
        },
        addEventListener: (nombre, manejador) => eventos.set(nombre, manejador),
        getElementById: nombre => elementos.get(nombre),
        querySelector: () => null,
        querySelectorAll: () => [],
    };
    const ventana = { innerWidth: 800, innerHeight: 600, matchMedia: () => ({ matches: false }) };
    const contexto = maquinaVirtual.createContext({
        window: ventana, document: documento, Date,
        setTimeout: (manejador, espera) => temporizadores.push({ manejador, espera }),
        clearTimeout: identificador => { if (identificador) temporizadores[identificador - 1].cancelado = true; },
    });
    for (const archivo of ARCHIVOS_CLIENTE) {
        cargarAssetCliente(archivo, contexto);
    }
    return { ventana, documento, eventos, elementos, temporizadores, contexto };
}

prueba("las entradas conservan teclado, puntero, movimiento reducido y posición de clic", () => {
    const cliente = crearClienteSimulado();
    afirmar.equal(cliente.ventana.scalaris.movimiento.permitido(), true);
    cliente.eventos.get("keydown")();
    afirmar.equal(cliente.ventana.scalaris.movimiento.permitido(), false);
    cliente.eventos.get("pointerdown")();
    afirmar.equal(cliente.ventana.scalaris.movimiento.permitido(), true);
    cliente.ventana.matchMedia = () => ({ matches: true });
    afirmar.equal(cliente.ventana.scalaris.movimiento.permitido(), false);
    cliente.eventos.get("click")({ clientX: 25, clientY: 70 });
    afirmar.equal(cliente.ventana.scalaris.ultimoClic.x, 25);
    afirmar.equal(cliente.ventana.scalaris.ultimoClic.y, 70);
});

prueba("la ayuda de celda muestra el valor completo y se retira al caber", () => {
    const cliente = crearClienteSimulado();
    const objetivo = {
        value: "12345678901234567890", scrollWidth: 300, clientWidth: 100,
        matches: () => true, hasAttribute: () => objetivo.title !== undefined,
        removeAttribute: nombre => { delete objetivo[nombre]; },
    };
    cliente.eventos.get("mouseover")({ target: objetivo });
    afirmar.equal(objetivo.title, objetivo.value);
    objetivo.scrollWidth = 50;
    cliente.eventos.get("focusin")({ target: objetivo });
    afirmar.equal(objetivo.title, undefined);
});

prueba("el renderizado MathJax mantiene la selección de elementos y la espera", () => {
    const cliente = crearClienteSimulado();
    cliente.ventana.scalaris.renderizarMathJax(["salida"]);
    afirmar.equal(cliente.temporizadores.length, 1);
    afirmar.equal(cliente.temporizadores[0].espera, 100);
    const elemento = {};
    const llamadas = [];
    cliente.elementos.set("salida", elemento);
    cliente.ventana.MathJax = {
        typesetClear: elementos => llamadas.push(elementos),
        typesetPromise: elementos => { llamadas.push(elementos); return Promise.resolve(); },
    };
    cliente.temporizadores[0].manejador();
    afirmar.equal(llamadas.length, 2);
    afirmar.equal(llamadas[0][0], elemento);
    afirmar.equal(llamadas[1][0], elemento);
});

prueba("la escritura con movimiento reducido inserta texto sin interpretar HTML", () => {
    const cliente = crearClienteSimulado();
    const elemento = { innerHTML: "contenido original", textContent: "" };
    cliente.elementos.set("salida", elemento);
    cliente.ventana.matchMedia = () => ({ matches: true });
    cliente.ventana.scalaris.efectoMaquinaEscribir("salida", "<img src=x onerror=alert(1)>");
    afirmar.equal(elemento.textContent, "<img src=x onerror=alert(1)>");
    afirmar.equal(elemento.innerHTML, "contenido original");
    afirmar.equal(cliente.temporizadores.length, 0);
});

prueba("el tema Plotly actualiza solo figuras conectadas con disposición disponible", () => {
    const cliente = crearClienteSimulado();
    const activa = { isConnected: true, _fullLayout: {} };
    const desconectada = { isConnected: false, _fullLayout: {} };
    const pendiente = { isConnected: true };
    const llamadas = [];
    cliente.documento.querySelectorAll = () => [activa, desconectada, pendiente];
    cliente.ventana.scalaris.graficos = { texto: { marea: "color-texto" }, cuadricula: { marea: "color-cuadricula" } };
    cliente.ventana.Plotly = {
        relayout: (figura, opciones) => { llamadas.push({ figura, opciones }); return Promise.resolve(); },
    };
    cliente.contexto.Plotly = cliente.ventana.Plotly;
    cliente.ventana.scalaris.actualizarTemaPlotly("marea");
    afirmar.equal(llamadas.length, 1);
    afirmar.equal(llamadas[0].figura, activa);
    afirmar.equal(llamadas[0].opciones["font.color"], "color-texto");
    afirmar.equal(llamadas[0].opciones["scene.xaxis.gridcolor"], "color-cuadricula");
});

prueba("el clic de salto impide que callbacks pendientes dupliquen el texto", () => {
    const cliente = crearClienteSimulado();
    const fragmento = { textContent: "" };
    const cursor = { style: {} };
    const elemento = {
        querySelector: selector => selector === ".tw-text" ? fragmento : cursor,
        addEventListener: (nombre, manejador) => cliente.eventos.set("clic_escritura", manejador),
        removeEventListener: () => cliente.eventos.delete("clic_escritura"),
    };
    cliente.elementos.set("salida", elemento);
    cliente.ventana.scalaris.efectoMaquinaEscribir("salida", "ABC", 1);
    afirmar.equal(fragmento.textContent, "A");
    cliente.eventos.get("clic_escritura")();
    afirmar.equal(fragmento.textContent, "ABC");
    cliente.temporizadores[0].manejador();
    afirmar.equal(fragmento.textContent, "ABC");
    afirmar.equal(cursor.style.display, "none");
    afirmar.equal(cliente.eventos.has("clic_escritura"), false);
    afirmar.equal(cliente.temporizadores[0].cancelado, true);
});
