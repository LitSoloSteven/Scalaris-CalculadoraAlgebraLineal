"use strict";

const prueba = require("node:test");
const afirmar = require("node:assert/strict");
const { crearCapturaSimulada, agregarEntradaCaptura, cargarCapturas, emitirEventoCaptura } = require("./comun_captura_cliente.js");

prueba("Enter en una matriz avanza una fila al cargar los tres adaptadores", () => {
    const cliente = crearCapturaSimulada();
    const entradas = [0, 1, 2].map(fila => agregarEntradaCaptura(cliente, {
        ecuacionesFila: String(fila), ecuacionesColumna: "0", matrizFila: String(fila), matrizColumna: "0", matrizIdentificador: "A",
    }));
    cargarCapturas(cliente);
    entradas[0].focus();
    const evento = emitirEventoCaptura(cliente, "keydown", { key: "Enter" });
    afirmar.equal(cliente.documento.activeElement, entradas[1]);
    afirmar.equal(evento.cancelaciones, 1);
});

prueba("Pegar en una matriz transmite un único evento de entrada por celda", () => {
    const cliente = crearCapturaSimulada();
    const entrada = agregarEntradaCaptura(cliente, { ecuacionesFila: "0", ecuacionesColumna: "0", matrizFila: "0", matrizColumna: "0", matrizIdentificador: "A" });
    cargarCapturas(cliente);
    entrada.focus();
    const evento = emitirEventoCaptura(cliente, "paste", { clipboardData: { getData: () => " 7 " } });
    afirmar.equal(entrada.value, "7");
    afirmar.equal(entrada.eventos.length, 1);
    afirmar.equal(evento.cancelaciones, 1);
});

prueba("los selectores de grupo delegan el escape al contrato CSS nativo", () => {
    const cliente = crearCapturaSimulada();
    cargarCapturas(cliente);
    const consultas = [];
    cliente.contexto.CSS.escape = valor => { consultas.push(valor); return "grupo_escapado"; };
    const configuracion = { tipo: "matrices", atributos: { fila: "matrizFila", columna: "matrizColumna", grupo: "matrizIdentificador" } };
    const selector = cliente.ventana.scalaris.capturaCeldas.selectorCelda({ fila: 1, columna: 2, grupo: 'A"\\\n' }, configuracion);
    afirmar.deepEqual(consultas, ['A"\\\n']);
    afirmar.equal(selector, 'input[data-matriz-identificador="grupo_escapado"][data-matriz-fila="1"][data-matriz-columna="2"]');
});
