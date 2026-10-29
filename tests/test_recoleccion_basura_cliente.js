"use strict";
const prueba = require("node:test");
const afirmar = require("node:assert/strict");
const archivos = require("node:fs");
const maquina = require("node:vm");
const ruta = require("node:path");
const fuente = archivos.readFileSync(ruta.join(__dirname,
    "../src/frontend/recursos/js/recoleccion_basura.js"), "utf8");

function crearCliente(permitido, cantidad = 1) {
    const rectangulo = { left: 0, top: 0, width: 50, height: 40, bottom: 40, right: 50 };
    const entradas = Array.from({ length: cantidad }, () => ({
        value: "<script>" + "9".repeat(10000), style: {
            getPropertyValue: () => "", getPropertyPriority: () => "", setProperty() {}, removeProperty() {},
        },
        closest: () => null, getBoundingClientRect: () => rectangulo,
    }));
    const clones = [];
    const icono = { textContent: "delete" };
    const boton = { getBoundingClientRect: () => rectangulo,
        querySelector: () => icono, classList: { add() {}, remove() {} } };
    const ventana = { innerWidth: 320, innerHeight: 760, getComputedStyle: () => ({}),
        scalaris: { movimiento: { permitido: () => permitido, curva: () => "curva",
            duracion: token => ({ "--dur-panel": 450, "--stagger-step": 75, "--stagger-max": 600 })[token] } } };
    const documento = {
        getElementById: id => id === "captura" ? { querySelectorAll: () => entradas } : boton,
        createElement: () => ({ style: {}, remove() {} }),
        body: { appendChild: clon => clones.push(clon) },
    };
    maquina.runInNewContext(fuente, { window: ventana, document: documento,
        setTimeout: ejecutar => ejecutar(), clearTimeout() {} });
    return { ventana, entradas, clones, icono };
}

prueba("teclado o movimiento reducido omiten clones y conservan la captura", async () => {
    const cliente = crearCliente(false);
    await cliente.ventana.scalaris.animarRecoleccionBasura();
    afirmar.equal(cliente.clones.length, 0);
    afirmar.ok(cliente.entradas[0].value.length > 10000);
});

prueba("sin política de movimiento disponible no se inicia la animación", async () => {
    const cliente = crearCliente(true);
    delete cliente.ventana.scalaris.movimiento;
    await cliente.ventana.scalaris.animarRecoleccionBasura();
    afirmar.equal(cliente.clones.length, 0);
});

prueba("el puntero recolecta como máximo ocho valores extensos de una matriz 50x50", async () => {
    const cliente = crearCliente(true, 2500);
    await cliente.ventana.scalaris.animarRecoleccionBasura(["captura"]);
    cliente.ventana.scalaris.terminarRecoleccionBasura();
    afirmar.equal(cliente.clones.length, 8);
    afirmar.ok(cliente.clones[0].textContent.startsWith("<script>"));
    afirmar.equal(cliente.clones[0].innerHTML, undefined);
    afirmar.ok(cliente.entradas[0].value.length > 10000);
    afirmar.ok(cliente.entradas[40].value.length > 10000);
    afirmar.equal(cliente.icono.textContent, "delete");
});
