"use strict";

const afirmar = require("node:assert/strict");
const prueba = require("node:test");
const maquinaVirtual = require("node:vm");
const { cargarAssetCliente } = require("./comun_cliente_javascript.js");

/** Simula la inserción diferida del menú y los cambios del atributo de tema. */
function crearSelector(temaInicial, montar = true) {
    let tema = temaInicial, notificar;
    const eventos = new Map(), llamadas = [];
    const opciones = ["papel", "marea", "medianoche"].map(nombre => {
        const atributos = new Map([["data-tema-opcion", nombre], ["aria-checked", "false"]]);
        return {
            getBoundingClientRect: () => ({ left: 30, top: 40, width: 100, height: 50 }),
            getAttribute: atributo => atributos.get(atributo),
            setAttribute: (atributo, valor) => atributos.set(atributo, valor),
        };
    });
    let montadas = montar ? opciones : [];
    const documento = {
        addEventListener: (nombre, funcion) => eventos.set(nombre, funcion),
        documentElement: { getAttribute: () => tema },
        querySelectorAll: () => montadas,
    };
    const contexto = maquinaVirtual.createContext({
        document: documento,
        window: { scalaris: { tema: { establecer: (...argumentos) => llamadas.push(argumentos) } } },
        MutationObserver: class {
            constructor(manejador) { notificar = manejador; }
            observe() {}
        },
    });
    cargarAssetCliente("selector_tema.js", contexto);
    return {
        opciones, eventos, llamadas,
        cambiar: valor => { tema = valor; notificar(); },
        montar: () => { montadas = opciones; notificar(); },
    };
}

/** Devuelve las opciones que anuncian selección a lectores de pantalla. */
function seleccionadas(cliente) {
    return cliente.opciones.filter(opcion => opcion.getAttribute("aria-checked") === "true")
        .map(opcion => opcion.getAttribute("data-tema-opcion"));
}

prueba("el menú restaura exactamente una selección en los tres temas", () => {
    for (const tema of ["papel", "marea", "medianoche"]) {
        afirmar.deepEqual(seleccionadas(crearSelector(tema)), [tema]);
    }
});

prueba("la selección usa únicamente el evento actual y el centro del control con teclado", () => {
    const cliente = crearSelector('papel');
    const seleccionar = cliente.eventos.get('click');
    const evento = { button: 0, detail: 1, clientX: 66, clientY: 77,
        target: { closest: () => cliente.opciones[1] } };
    seleccionar(evento);
    afirmar.equal(JSON.stringify(cliente.llamadas[0]), '["marea",{"x":66,"y":77}]');
    seleccionar({ ...evento, detail: 0 });
    afirmar.equal(JSON.stringify(cliente.llamadas[1]), '["marea",{"x":80,"y":65}]');
    seleccionar({ ...evento, button: 1 });
    afirmar.equal(cliente.llamadas.length, 2);
});

prueba("un menú insertado después de cargar los recursos refleja el tema vigente", () => {
    const cliente = crearSelector("medianoche", false);
    cliente.montar();
    afirmar.deepEqual(seleccionadas(cliente), ["medianoche"]);
    cliente.cambiar("papel");
    afirmar.deepEqual(seleccionadas(cliente), ["papel"]);
    cliente.cambiar("marea");
    afirmar.deepEqual(seleccionadas(cliente), ["marea"]);
});

prueba("un valor ausente o ajeno marca el tema base sin acumular selecciones", () => {
    const cliente = crearSelector(null);
    afirmar.deepEqual(seleccionadas(cliente), ["papel"]);
    cliente.cambiar("medianoche");
    cliente.cambiar("desconocido");
    afirmar.deepEqual(seleccionadas(cliente), ["papel"]);
});
