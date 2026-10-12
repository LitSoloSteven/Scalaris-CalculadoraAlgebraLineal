"use strict";

const { crearEntradaSimulada, cargarAssetCliente } = require("./comun_cliente_javascript.js");
const { crearTemaSimulado } = require("./comun_tema_cliente.js");

/** Simula las operaciones de clases que usa la API del documento. */
function crearListaClases() {
    const nombres = new Set();
    return {
        add: nombre => nombres.add(nombre),
        remove: nombre => nombres.delete(nombre),
        contains: nombre => nombres.has(nombre),
    };
}

/** Registra animaciones de un control y su promesa de finalización. */
function crearControlAnimado(finalizacion = Promise.resolve()) {
    const control = { classList: crearListaClases(), animaciones: [] };
    control.animate = (fotogramas, opciones) => {
        control.animaciones.push({ fotogramas, opciones });
        return { finished: finalizacion };
    };
    return control;
}

/** Crea una celda que permite observar foco, desplazamiento y finalización del aviso. */
function crearCeldaCuadricula(control = crearControlAnimado()) {
    const contenedor = { classList: crearListaClases(), offsetWidth: 100, eventos: [] };
    contenedor.addEventListener = (nombre, manejador, opciones) => contenedor.eventos.push({ nombre, manejador, opciones });
    const entrada = crearEntradaSimulada("1");
    entrada.closest = selector => selector === ".matrix-input" ? contenedor : control;
    entrada.desplazamientos = [];
    entrada.scrollIntoView = opciones => entrada.desplazamientos.push(opciones);
    return { entrada, contenedor, control };
}

/** Carga la política de movimiento y la cuadrícula en el orden de producción. */
function crearCuadriculaSimulada() {
    const cliente = crearTemaSimulado();
    cargarAssetCliente("interacciones_globales.js", cliente.contexto);
    cargarAssetCliente("cuadricula_compartida.js", cliente.contexto);
    return cliente;
}

module.exports = { crearListaClases, crearControlAnimado, crearCeldaCuadricula, crearCuadriculaSimulada };
