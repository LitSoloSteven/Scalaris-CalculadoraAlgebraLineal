"use strict";

const afirmar = require("node:assert/strict");
const prueba = require("node:test");
const maquinaVirtual = require("node:vm");
const { cargarAssetCliente } = require("./comun_cliente_javascript.js");

prueba("el puente consulta los tokens vigentes en cada llamada", () => {
    const valores = new Map([
        ["--dur-panel", "450ms"],
        ["--dur-med", "240ms"],
        ["--ease-std", " cubic-bezier(0.32, 0.72, 0, 1) "],
    ]);
    const documento = { documentElement: {}, addEventListener() {} };
    const ventana = {};
    const contexto = maquinaVirtual.createContext({
        window: ventana,
        document: documento,
        getComputedStyle: () => ({ getPropertyValue: nombre => valores.get(nombre) || "" }),
    });
    cargarAssetCliente("interacciones_globales.js", contexto);
    const movimiento = ventana.scalaris.movimiento;
    afirmar.equal(movimiento.duracion("--dur-panel"), 450);
    afirmar.equal(movimiento.medio, 240);
    afirmar.equal(movimiento.curva(), "cubic-bezier(0.32, 0.72, 0, 1)");
    valores.set("--dur-panel", "600ms");
    afirmar.equal(movimiento.duracion("--dur-panel"), 600);
    afirmar.ok(Number.isNaN(movimiento.duracion("--inexistente")));
});
