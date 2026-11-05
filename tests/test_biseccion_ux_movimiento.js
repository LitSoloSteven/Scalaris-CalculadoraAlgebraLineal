"use strict";

const afirmar = require("node:assert/strict");
const prueba = require("node:test");
const { createContext } = require("node:vm");
const { cargarAssetCliente } = require("./comun_cliente_javascript.js");

function entorno() {
    const nodos = new Map();
    const reducido = { matches: false, addEventListener() {} };
    const tokens = { "--dur-panel": 450, "--dur-panel-exit": 340, "--dur-view": 600 };
    const ventana = {
        matchMedia: () => reducido, addEventListener() {},
        scalaris: { movimiento: { duracion: token => tokens[token], curva: () => "cubic-bezier(0.32, 0.72, 0, 1)" } },
    };
    const contexto = createContext({
        window: ventana, getComputedStyle: nodo => nodo.estiloActual,
        document: { documentElement: { dataset: { entrada: "puntero" } }, getElementById: id => nodos.get(id) },
        MutationObserver: class {
            observe() {}
            disconnect() {}
        },
    });
    cargarAssetCliente("movimiento_biseccion.js", contexto);
    return { contexto, ventana, nodos, reducido, movimiento: ventana.scalaris.movimientoBiseccion };
}

function nodoAnimado() {
    const animaciones = [];
    return {
        dataset: {}, isConnected: true, animaciones, getClientRects: () => [1],
        estiloActual: { opacity: "0.6", transform: "matrix(1, 0, 0, 1, 0, 4)" },
        style: { removeProperty() { delete this.willChange; } },
        animate(fotogramas, opciones) {
            const promesa = Promise.withResolvers();
            const animacion = { fotogramas, opciones, finished: promesa.promise, resolver: promesa.resolve,
                cancel: () => promesa.reject(new Error("Cancelada")) };
            animaciones.push(animacion);
            return animacion;
        },
    };
}

prueba("invertir una tarea conserva sus nodos y libera solo su transición vigente", async () => {
    const { movimiento, nodos } = entorno();
    const intervalo = nodoAnimado();
    const busqueda = nodoAnimado();
    nodos.set("intervalo", intervalo);
    nodos.set("busqueda", busqueda);
    const botonIntervalo = { getAttribute: () => "intervalo" };
    const botonBusqueda = { getAttribute: () => "busqueda" };
    movimiento.cambiarModo({ detail: 1, currentTarget: botonBusqueda }, botonIntervalo);
    afirmar.equal(intervalo.inert, true);
    afirmar.equal(busqueda.animaciones[0].opciones.duration, 450);
    afirmar.equal(intervalo.animaciones[0].opciones.duration, 340);
    movimiento.cambiarModo({ detail: 1, currentTarget: botonIntervalo }, botonBusqueda);
    await Promise.resolve();
    afirmar.equal(intervalo.inert, false);
    afirmar.equal(busqueda.inert, true);
    afirmar.equal(intervalo.animaciones[1].fotogramas[0].transform, intervalo.estiloActual.transform);
    intervalo.animaciones[1].resolver();
    busqueda.animaciones[1].resolver();
    await Promise.resolve();
    afirmar.equal(intervalo.style.willChange, undefined);
    afirmar.equal(busqueda.dataset.biseccionTransicion, undefined);
});

prueba("la entrada por teclado o con movimiento reducido no promociona una capa", () => {
    const { movimiento, reducido } = entorno();
    const nodo = nodoAnimado();
    afirmar.equal(movimiento.esPuntero({ detail: 0 }), false);
    movimiento.entrada(nodo, false);
    reducido.matches = true;
    movimiento.entrada(nodo, true);
    afirmar.equal(nodo.animaciones.length, 0);
    afirmar.equal(nodo.style.willChange, undefined);
});

prueba("una fórmula lenta no se transfiere después de solicitar otra", async () => {
    const { contexto, ventana, nodos } = entorno();
    cargarAssetCliente("paso_biseccion.js", contexto);
    const conversion = Promise.withResolvers();
    ventana.MathJax = {
        tex2chtmlPromise: latex => latex === "primera" ? conversion.promise : Promise.resolve({ latex }),
        startup: { document: { updateDocument() {} } },
    };
    const cuerpo = nodoAnimado();
    const formula = { replaceChildren(contenido) { this.contenido = contenido; } };
    cuerpo.contains = elemento => elemento === formula;
    nodos.set("cuerpo", cuerpo);
    nodos.set("formula", formula);
    const paso = ventana.scalaris.pasoBiseccion;
    const primera = paso.preparar({ cuerpo: "cuerpo", revision: 1, latex: "primera" });
    await Promise.resolve();
    const segunda = paso.preparar({ cuerpo: "cuerpo", revision: 2, latex: "segunda" });
    conversion.resolve({ latex: "primera" });
    afirmar.equal(await primera, false);
    afirmar.equal(await segunda, true);
    paso.publicar({ identificador: "formula", cuerpo: "cuerpo", revision: 2, puntero: true, token: "--dur-panel" });
    afirmar.equal(formula.contenido.latex, "segunda");
    afirmar.equal(cuerpo.animaciones[0].opciones.duration, 450);
});
