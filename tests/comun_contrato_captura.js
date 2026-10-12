"use strict";

const sistemaArchivos = require("node:fs");
const { crearCapturaSimulada, agregarEntradaCaptura, cargarCapturas, emitirEventoCaptura } = require("./comun_captura_cliente.js");

/** Ejecuta acciones del adaptador usando atributos producidos por NiceGUI. */
function observarContratoVectores(propiedades) {
    const cliente = crearCapturaSimulada();
    const entradas = propiedades.map(propiedad => {
        const datos = Object.fromEntries(Object.entries(propiedad)
            .filter(([nombre]) => nombre.startsWith("data-"))
            .map(([nombre, valor]) => [nombre.slice(5).replace(/-([a-z])/g, (_, letra) => letra.toUpperCase()), valor]));
        return agregarEntradaCaptura(cliente, datos);
    });
    cargarCapturas(cliente);
    entradas[0].focus();
    const teclado = emitirEventoCaptura(cliente, "keydown", { key: "Enter" });
    const destino = entradas.indexOf(cliente.documento.activeElement);
    entradas[0].focus();
    const pegado = emitirEventoCaptura(cliente, "paste", { clipboardData: { getData: () => "1;2;3" } });
    return {
        destino, cancelaciones: [teclado.cancelaciones, pegado.cancelaciones],
        valores: entradas.map(entrada => entrada.value), eventos: entradas.map(entrada => entrada.eventos.length),
    };
}

const propiedades = JSON.parse(sistemaArchivos.readFileSync(0, "utf8"));
process.stdout.write(JSON.stringify(observarContratoVectores(propiedades)));
