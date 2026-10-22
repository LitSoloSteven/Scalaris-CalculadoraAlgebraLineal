"use strict";

const prueba = require("node:test");
const afirmar = require("node:assert/strict");
const { crearCapturaSimulada, agregarCeldasCaptura, cargarCapturas, emitirEventoCaptura, completarSelecciones } = require("./comun_captura_cliente.js");

for (const tipo of ["ecuaciones", "matrices"]) {
    for (const [tecla, esperado] of [["ArrowUp", 1], ["ArrowDown", 3], ["ArrowLeft", 0], ["ArrowRight", 4], ["Enter", 3], ["Tab", 2]]) {
        prueba(`${tipo}: ${tecla} conserva el destino y la selección diferida`, () => {
            const cliente = crearCapturaSimulada();
            const entradas = agregarCeldasCaptura(cliente, tipo, [[1, 0], [0, 1], [1, 1], [2, 1], [1, 2]]);
            cargarCapturas(cliente);
            entradas[2].selectionStart = 0;
            entradas[2].focus();
            const evento = emitirEventoCaptura(cliente, "keydown", { key: tecla });
            afirmar.equal(cliente.documento.activeElement, entradas[esperado]);
            afirmar.equal(evento.cancelaciones, tecla === "Tab" ? 0 : 1);
            afirmar.equal(entradas[esperado].selecciones, 0);
            if (tecla !== "Tab") afirmar.equal([...cliente.temporizadores.values()][0].demora, 10);
            completarSelecciones(cliente);
            afirmar.equal(entradas[esperado].selecciones, tecla === "Tab" ? 0 : 1);
        });
    }
}

for (const [orientacion, tecla, esperado] of [
    ["columna", "ArrowDown", 2], ["columna", "ArrowUp", 0], ["columna", "ArrowRight", 1],
    ["fila", "ArrowRight", 2], ["fila", "ArrowLeft", 0], ["fila", "ArrowDown", 1],
    ["otra", "ArrowRight", 2], ["columna", "Enter", 2], ["fila", "Enter", 2],
]) {
    prueba(`vectores: ${orientacion}/${tecla} conserva el eje y Enter`, () => {
        const cliente = crearCapturaSimulada();
        const entradas = agregarCeldasCaptura(cliente, "vectores", [[0, orientacion], [1, orientacion], [2, orientacion]]);
        cargarCapturas(cliente);
        entradas[1].selectionStart = 0;
        entradas[1].focus();
        const evento = emitirEventoCaptura(cliente, "keydown", { key: tecla });
        afirmar.equal(cliente.documento.activeElement, entradas[esperado]);
        afirmar.equal(evento.cancelaciones, 1);
        completarSelecciones(cliente);
        afirmar.equal(entradas[esperado].selecciones, 1);
    });
}

for (const [tecla, seleccion] of [["ArrowLeft", [1, 1]], ["ArrowRight", [1, 2]]]) {
    prueba(`${tecla} dentro del texto deja el cursor y el foco intactos`, () => {
        const cliente = crearCapturaSimulada();
        const entradas = agregarCeldasCaptura(cliente, "matrices", [[0, 0], [0, 1], [0, 2]]);
        cargarCapturas(cliente);
        entradas[1].setSelectionRange(...seleccion);
        entradas[1].focus();
        const evento = emitirEventoCaptura(cliente, "keydown", { key: tecla });
        afirmar.equal(cliente.documento.activeElement, entradas[1]);
        afirmar.equal(evento.cancelaciones, 0);
        afirmar.equal(cliente.temporizadores.size, 0);
    });
}

prueba("el borde sin destino y un objetivo ajeno no se cancelan", () => {
    const cliente = crearCapturaSimulada();
    const [entrada] = agregarCeldasCaptura(cliente, "ecuaciones", [[0, 0]]);
    cargarCapturas(cliente);
    entrada.focus();
    afirmar.equal(emitirEventoCaptura(cliente, "keydown", { key: "ArrowUp" }).cancelaciones, 0);
    afirmar.equal(emitirEventoCaptura(cliente, "keydown", { key: "Enter", target: { tagName: "TEXTAREA" } }).cancelaciones, 0);
    afirmar.equal(emitirEventoCaptura(cliente, "paste", { target: null }).cancelaciones, 0);
    afirmar.equal(cliente.temporizadores.size, 0);
});
