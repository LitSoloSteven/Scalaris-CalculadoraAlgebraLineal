"use strict";

const afirmar = require("node:assert/strict");
const prueba = require("node:test");
const maquinaVirtual = require("node:vm");
const { crearEntradaSimulada, crearCalculadoraSimulada } = require("./comun_cliente_javascript.js");

prueba("inserta en la selección de la última celda enfocada", () => {
    const primera = crearEntradaSimulada("1234");
    const enfocada = crearEntradaSimulada("5678", [1, 3]);
    const cliente = crearCalculadoraSimulada(primera);
    cliente.eventos.get("focusin")({ target: enfocada });
    cliente.ventana.scalaris.calculadora.insertarSimbolo("90");
    afirmar.equal(enfocada.value, "5908");
    afirmar.equal(enfocada.selectionStart, 3);
    afirmar.equal(enfocada.selectionEnd, 3);
    afirmar.equal(primera.value, "1234");
    afirmar.equal(enfocada.eventos.length, 1);
    afirmar.equal(enfocada.eventos[0].type, "input");
    afirmar.equal(enfocada.eventos[0].bubbles, true);
});

prueba("una celda desconectada deja paso a la primera disponible", () => {
    const primera = crearEntradaSimulada("1");
    const desconectada = crearEntradaSimulada("9");
    desconectada.isConnected = false;
    const cliente = crearCalculadoraSimulada(primera);
    cliente.eventos.get("focusin")({ target: desconectada });
    cliente.ventana.scalaris.calculadora.insertarSimbolo("2");
    afirmar.equal(primera.value, "12");
    afirmar.equal(primera.enfocada, true);
    afirmar.equal(desconectada.value, "9");
});

prueba("la limpieza vacía la celda y conserva la emisión del evento", () => {
    const entrada = crearEntradaSimulada("-123");
    const cliente = crearCalculadoraSimulada(entrada);
    cliente.ventana.scalaris.calculadora.insertarSimbolo("C");
    afirmar.equal(entrada.value, "");
    afirmar.equal(entrada.eventos.length, 1);
});

prueba("alterna signos positivos negativos y ausentes sin rellenar vacíos", () => {
    for (const [valor, esperado] of [["-12", "12"], ["+12", "-12"], ["12", "-12"], ["", ""]]) {
        const entrada = crearEntradaSimulada(valor);
        const cliente = crearCalculadoraSimulada(entrada);
        cliente.ventana.scalaris.calculadora.insertarSimbolo("±");
        afirmar.equal(entrada.value, esperado);
        afirmar.equal(entrada.selectionStart, esperado.length);
        afirmar.equal(entrada.selectionEnd, esperado.length);
    }
});

prueba("borra el carácter anterior la selección o nada al inicio", () => {
    for (const [seleccion, esperado, posicion] of [[[2, 2], "134", 1], [[1, 3], "14", 1], [[0, 0], "1234", 0]]) {
        const entrada = crearEntradaSimulada("1234", seleccion);
        const cliente = crearCalculadoraSimulada(entrada);
        cliente.ventana.scalaris.calculadora.insertarSimbolo("⌫");
        afirmar.equal(entrada.value, esperado);
        afirmar.equal(entrada.selectionStart, posicion);
        afirmar.equal(entrada.selectionEnd, posicion);
        afirmar.equal(entrada.eventos.length, 1);
    }
});

prueba("las entradas ajenas no desplazan la celda enfocada", () => {
    const entrada = crearEntradaSimulada("1");
    const ajena = crearEntradaSimulada("9");
    ajena.closest = () => null;
    const cliente = crearCalculadoraSimulada();
    cliente.eventos.get("focusin")({ target: entrada });
    cliente.eventos.get("focusin")({ target: ajena });
    cliente.eventos.get("focusin")({ target: null });
    cliente.ventana.scalaris.calculadora.insertarSimbolo("2");
    afirmar.equal(entrada.value, "12");
    afirmar.equal(ajena.value, "9");
});

prueba("sin símbolo o sin celda disponible no modifica contenido", () => {
    const entrada = crearEntradaSimulada("1");
    const cliente = crearCalculadoraSimulada(entrada);
    cliente.ventana.scalaris.calculadora.insertarSimbolo("");
    afirmar.equal(entrada.value, "1");
    afirmar.equal(entrada.enfocada, false);
    afirmar.equal(entrada.eventos.length, 0);
    const vacia = crearCalculadoraSimulada();
    afirmar.doesNotThrow(() => vacia.ventana.scalaris.calculadora.insertarSimbolo("2"));
});

prueba("las funciones y el estado privado permanecen fuera del ámbito global", () => {
    const cliente = crearCalculadoraSimulada();
    for (const nombre of ["insertarSimbolo", "alternarSigno", "ultimaEntradaEnfocada"]) {
        afirmar.equal(maquinaVirtual.runInContext(`typeof ${nombre}`, cliente.contexto), "undefined");
    }
    afirmar.deepEqual(Object.keys(cliente.ventana.scalaris.calculadora), ["insertarSimbolo"]);
});
