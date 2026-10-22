"use strict";
const afirmar = require("node:assert/strict");
const prueba = require("node:test");
const { crearGlosaSimulada, pulsarGlosa } = require("./comun_glosa_cliente.js");

for (const inverso of [false, true]) {
    prueba(`el diálogo mantiene Tab circular con dirección inversa=${inverso}`, () => {
        const cliente = crearGlosaSimulada();
        cliente.panel.inert = false;
        cliente.documento.querySelectorAll = () => [cliente.panel];
        cliente.documento.activeElement = cliente.controles[inverso ? 0 : 1];
        afirmar.equal(pulsarGlosa(cliente, "Tab", inverso).defaultPrevented, true);
        afirmar.equal(cliente.documento.activeElement, cliente.controles[inverso ? 1 : 0]);
    });
}

prueba("el diálogo vacío conserva el foco y no captura Escape", () => {
    const cliente = crearGlosaSimulada();
    cliente.documento.querySelectorAll = () => [cliente.panel];
    cliente.panel.inert = false;
    cliente.controles.forEach(control => { control.disabled = true; });
    afirmar.equal(pulsarGlosa(cliente, "Tab").defaultPrevented, true);
    afirmar.equal(cliente.documento.activeElement, cliente.panel);
    afirmar.equal(pulsarGlosa(cliente, "Escape").defaultPrevented, false);
});

prueba("el diálogo superior tiene prioridad sobre Glosa y otros diálogos", () => {
    const cliente = crearGlosaSimulada();
    cliente.ventana.scalaris.glosa.abrir({ origen: "teclado" });
    const controlDialogo = { ...cliente.controles[0], focus() { cliente.documento.activeElement = this; } };
    const dialogo = {
        closest: () => null,
        getClientRects: () => [{}], querySelectorAll: () => [controlDialogo],
        contains: elemento => elemento === controlDialogo,
    };
    cliente.documento.querySelectorAll = () => [cliente.panel, dialogo];
    afirmar.equal(pulsarGlosa(cliente, "Tab").defaultPrevented, true);
    afirmar.equal(cliente.documento.activeElement, controlDialogo);
    pulsarGlosa(cliente, "Escape");
    afirmar.equal(cliente.ventana.scalaris.glosa.estaAbierto(), true);
});

prueba("un diálogo oculto o inerte no desplaza al diálogo visible", () => {
    const cliente = crearGlosaSimulada();
    cliente.panel.inert = false;
    cliente.documento.querySelectorAll = () => [cliente.panel,
        { getClientRects: () => [] },
        { getClientRects: () => [{}], closest: () => ({ inert: true }) }];
    afirmar.equal(cliente.ventana.scalaris.focoModal.dialogoActivo(), cliente.panel);
});
