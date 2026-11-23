"use strict";

const afirmar = require("node:assert/strict");
const prueba = require("node:test");
const maquinaVirtual = require("node:vm");
const { cargarAssetCliente } = require("./comun_cliente_javascript.js");

/** Carga el recurso con un historial y eventos de ventana observables. */
function prepararHistorial() {
    const eventos = new Map();
    const entradas = [];
    const emisiones = [];
    const ventana = {
        location: new URL("http://scalaris.test/algebra-lineal/metodos-iterativos?ejemplo=1#captura"),
        addEventListener: (nombre, manejador) => eventos.set(nombre, manejador),
        removeEventListener: nombre => eventos.delete(nombre),
    };
    ventana.history = {
        state: { seccion: "captura" },
        pushState(estado, _titulo, direccion) {
            entradas.push({ estado, direccion });
            ventana.location = direccion;
        },
    };
    const contexto = maquinaVirtual.createContext({
        window: ventana, URL, URLSearchParams, emitEvent: (...datos) => emisiones.push(datos),
    });
    cargarAssetCliente("herramientas/algebra/iterativos_historial.js", contexto);
    return { ventana, eventos, entradas, emisiones, historial: ventana.scalaris.historialIterativos };
}

prueba("el historial conserva la consulta y el fragmento y evita entradas duplicadas", () => {
    const { entradas, historial, ventana } = prepararHistorial();
    historial.guardar("gauss-seidel");
    historial.guardar("gauss-seidel");
    afirmar.equal(entradas.length, 1);
    afirmar.equal(entradas[0].estado, ventana.history.state);
    afirmar.equal(ventana.location.search, "?ejemplo=1&method=gauss-seidel");
    afirmar.equal(ventana.location.hash, "#captura");
});

prueba("solo la vista montada escucha el historial y conserva la escucha al volver de la caché", () => {
    const { historial, eventos, emisiones } = prepararHistorial();
    afirmar.equal(eventos.size, 0);
    historial.montar();
    eventos.get("popstate")();
    historial.guardar("gauss-seidel");
    eventos.get("popstate")();
    afirmar.deepEqual(emisiones, [
        ["iterativos-metodo-historial", null],
        ["iterativos-metodo-historial", "gauss-seidel"],
    ]);
    eventos.get("pagehide")({ persisted: true });
    afirmar.equal(eventos.size, 2);
    eventos.get("pagehide")({ persisted: false });
    afirmar.equal(eventos.size, 0);
});
