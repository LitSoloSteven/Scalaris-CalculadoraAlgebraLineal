"use strict";

const afirmar = require("node:assert/strict");
const prueba = require("node:test");
const maquinaVirtual = require("node:vm");
const { cargarAssetCliente } = require("./comun_cliente_javascript.js");

/** Carga el recurso real con politicas y reinicios observables, sin temporizadores. */
function crearCambioSimulado() {
    const clases = new Set();
    const operaciones = [];
    const estado = { permitido: true, panel: true };
    const panel = {
        classList: {
            remove: clase => { operaciones.push("retirar"); clases.delete(clase); },
            add: clase => { operaciones.push("iniciar"); clases.add(clase); },
        },
        get offsetWidth() { operaciones.push("medir"); return 320; },
    };
    const ventana = { scalaris: { movimiento: { permitido: () => estado.permitido } } };
    const contexto = maquinaVirtual.createContext({
        window: ventana, document: { querySelector: () => estado.panel ? panel : null },
    });
    cargarAssetCliente("sistemas_metodo.js", contexto);
    return { clases, operaciones, estado, cambiar: ventana.scalaris.animarCambioMetodo };
}

prueba("los cambios rapidos reinician una unica transicion sin esperas", () => {
    const cliente = crearCambioSimulado();
    for (let indice = 0; indice < 20; indice += 1) cliente.cambiar();
    afirmar.deepEqual([...cliente.clases], ["sistemas-cambio-metodo"]);
    afirmar.equal(cliente.operaciones.length, 60);
    afirmar.deepEqual(cliente.operaciones.slice(-3), ["retirar", "medir", "iniciar"]);
});

prueba("teclado o movimiento reducido retiran la animacion activa inmediatamente", () => {
    const cliente = crearCambioSimulado();
    cliente.cambiar();
    cliente.estado.permitido = false;
    cliente.cambiar();
    afirmar.equal(cliente.clases.size, 0);
    afirmar.deepEqual(cliente.operaciones, ["retirar", "medir", "iniciar", "retirar"]);
});

prueba("un mensaje recibido tras desmontar la vista no anima otro contenido", () => {
    const cliente = crearCambioSimulado();
    cliente.estado.panel = false;
    afirmar.doesNotThrow(cliente.cambiar);
    afirmar.equal(cliente.operaciones.length, 0);
});
