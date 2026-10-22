"use strict";

const prueba = require("node:test");
const afirmar = require("node:assert/strict");
const { crearCapturaSimulada, agregarCeldasCaptura, agregarEntradaCaptura, cargarCapturas, emitirEventoCaptura } = require("./comun_captura_cliente.js");
const RESALTADO = "cuadricula-resaltado-cruzado";

for (const [tipo, esperado] of [["ecuaciones", ["", "1", "2", "3"]], ["matrices", ["1", "123", "2", "3"]]]) {
    prueba(`${tipo}: pegado tabular conserva su recorte y omite celdas ausentes`, () => {
        const cliente = crearCapturaSimulada();
        const entradas = agregarCeldasCaptura(cliente, tipo, [[0, 0], [0, 1], [1, 0], [1, 1]]);
        const [ajena] = agregarCeldasCaptura(cliente, "matrices", [[0, 0]], "B");
        cargarCapturas(cliente);
        entradas[0].focus();
        const evento = emitirEventoCaptura(cliente, "paste", { clipboardData: { getData: () => "\t1\n 2 \t3\t4\n" } });
        afirmar.deepEqual(entradas.map(entrada => entrada.value), esperado);
        afirmar.equal(ajena.value, "123");
        afirmar.equal(ajena.eventos.length, 0);
        afirmar.equal(evento.cancelaciones, 1);
        afirmar.equal(entradas[0].eventos[0].type, "input");
        afirmar.equal(entradas[0].eventos[0].bubbles, true);
    });
}

prueba("el pegado vectorial admite separadores mixtos y conserva texto sin interpretarlo", () => {
    const cliente = crearCapturaSimulada();
    const entradas = agregarCeldasCaptura(cliente, "vectores", [[0, "columna"], [1, "columna"], [2, "columna"], [3, "columna"]]);
    cargarCapturas(cliente);
    entradas[1].focus();
    emitirEventoCaptura(cliente, "paste", { clipboardData: { getData: () => " 1,;\n2\t<img src=x> \n5" } });
    afirmar.deepEqual(entradas.map(entrada => entrada.value), ["123", "1", "2", "<img src=x>"]);
    afirmar.deepEqual(entradas.map(entrada => entrada.eventos.length), [0, 1, 1, 1]);
});

for (const tipo of ["ecuaciones", "matrices", "vectores"]) {
    prueba(`${tipo}: el portapapeles vacío escribe una celda vacía con un evento`, () => {
        const cliente = crearCapturaSimulada();
        const [entrada] = agregarCeldasCaptura(cliente, tipo, [[0, tipo === "vectores" ? "fila" : 0]]);
        cargarCapturas(cliente);
        entrada.focus();
        cliente.ventana.clipboardData = { getData: () => "  " };
        emitirEventoCaptura(cliente, "paste");
        afirmar.equal(entrada.value, "");
        afirmar.equal(entrada.eventos.length, 1);
    });
}

for (const tipo of ["ecuaciones", "matrices"]) {
    prueba(`${tipo}: el foco resalta una cruz y limpia al salir`, () => {
        const cliente = crearCapturaSimulada();
        const entradas = agregarCeldasCaptura(cliente, tipo, [[0, 0], [0, 1], [1, 0], [1, 1]]);
        cargarCapturas(cliente);
        entradas[0].focus();
        emitirEventoCaptura(cliente, "focusin");
        afirmar.deepEqual(entradas.map(entrada => entrada.control.classList.contains(RESALTADO)), [true, true, true, false]);
        emitirEventoCaptura(cliente, "focusout");
        afirmar.equal(entradas.some(entrada => entrada.control.classList.contains(RESALTADO)), false);
    });
}

prueba("el resaltado de ecuaciones respeta su panel y se retira al cambiar de panel", () => {
    const cliente = crearCapturaSimulada();
    const primera = agregarEntradaCaptura(cliente, { ecuacionesFila: "0", ecuacionesColumna: "0" }, "1", "primero");
    const segunda = agregarEntradaCaptura(cliente, { ecuacionesFila: "0", ecuacionesColumna: "0" }, "2", "segundo");
    cargarCapturas(cliente);
    primera.focus();
    emitirEventoCaptura(cliente, "focusin");
    afirmar.equal(primera.control.classList.contains(RESALTADO), true);
    afirmar.equal(segunda.control.classList.contains(RESALTADO), false);
    segunda.focus();
    emitirEventoCaptura(cliente, "focusin");
    afirmar.equal(primera.control.classList.contains(RESALTADO), false);
    afirmar.equal(segunda.control.classList.contains(RESALTADO), true);
});

prueba("el resaltado vectorial coincide solo por componente dentro de su grupo", () => {
    const cliente = crearCapturaSimulada();
    const entradas = agregarCeldasCaptura(cliente, "vectores", [[0, "fila"], [1, "fila"]], "u");
    const [ajena] = agregarCeldasCaptura(cliente, "vectores", [[0, "fila"]], "v");
    cargarCapturas(cliente);
    entradas[0].focus();
    emitirEventoCaptura(cliente, "focusin");
    afirmar.deepEqual(entradas.map(entrada => entrada.control.classList.contains(RESALTADO)), [true, false]);
    afirmar.equal(ajena.control.classList.contains(RESALTADO), false);
});
