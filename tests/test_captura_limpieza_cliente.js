"use strict";

const prueba = require("node:test");
const afirmar = require("node:assert/strict");
const { crearCapturaSimulada, agregarCeldasCaptura, cargarCapturas, emitirEventoCaptura, completarSelecciones } = require("./comun_captura_cliente.js");

prueba("reinyectar assets conserva un solo registro por adaptador y evento", () => {
    const cliente = crearCapturaSimulada();
    cargarCapturas(cliente);
    cargarCapturas(cliente);
    for (const nombre of ["keydown", "paste", "focusin", "focusout"]) {
        afirmar.equal(cliente.documento.manejadoresPorEvento.get(nombre).size, 3);
    }
    afirmar.equal(cliente.ventana.manejadoresPorEvento.get("pagehide").size, 1);
    afirmar.equal(cliente.ventana.manejadoresPorEvento.get("pageshow").size, 1);
});

prueba("retirar una captura cancela selección y resaltado sin afectar las otras", () => {
    const cliente = crearCapturaSimulada();
    const entradas = agregarCeldasCaptura(cliente, "matrices", [[0, 0], [1, 0]]);
    cargarCapturas(cliente);
    entradas[0].focus();
    emitirEventoCaptura(cliente, "focusin");
    emitirEventoCaptura(cliente, "keydown", { key: "Enter" });
    afirmar.equal(cliente.temporizadores.size, 1);
    cliente.ventana.scalaris.capturas.retirarCaptura("matrices");
    afirmar.equal(cliente.temporizadores.size, 0);
    afirmar.equal(cliente.documento.manejadoresPorEvento.get("keydown").size, 2);
    afirmar.equal(entradas[0].control.classList.contains("cuadricula-resaltado-cruzado"), false);
    cliente.ventana.emitir("pageshow", {});
    afirmar.equal(cliente.documento.manejadoresPorEvento.get("keydown").size, 2);
});

prueba("ocultar la página limpia recursos y volver restaura sin duplicarlos", () => {
    const cliente = crearCapturaSimulada();
    const entradas = agregarCeldasCaptura(cliente, "matrices", [[0, 0], [1, 0]]);
    cargarCapturas(cliente);
    entradas[0].focus();
    emitirEventoCaptura(cliente, "keydown", { key: "Enter" });
    cliente.ventana.emitir("pagehide", {});
    afirmar.equal(cliente.temporizadores.size, 0);
    afirmar.equal(cliente.documento.manejadoresPorEvento.get("keydown").size, 0);
    cliente.ventana.emitir("pageshow", {});
    cliente.ventana.emitir("pageshow", {});
    afirmar.equal(cliente.documento.manejadoresPorEvento.get("keydown").size, 3);
    entradas[0].focus();
    afirmar.equal(emitirEventoCaptura(cliente, "keydown", { key: "Enter" }).cancelaciones, 1);
});

prueba("navegar dos veces cancela la selección antigua y seleccionar requiere el foco", () => {
    const cliente = crearCapturaSimulada();
    const entradas = agregarCeldasCaptura(cliente, "matrices", [[0, 0], [1, 0], [2, 0]]);
    cargarCapturas(cliente);
    entradas[0].focus();
    emitirEventoCaptura(cliente, "keydown", { key: "Enter" });
    emitirEventoCaptura(cliente, "keydown", { key: "Enter" });
    afirmar.equal(cliente.temporizadores.size, 1);
    completarSelecciones(cliente);
    afirmar.equal(entradas[1].selecciones, 0);
    afirmar.equal(entradas[2].selecciones, 1);
    entradas[0].focus();
    emitirEventoCaptura(cliente, "keydown", { key: "Enter" });
    entradas[0].focus();
    completarSelecciones(cliente);
    afirmar.equal(entradas[1].selecciones, 0);
});

prueba("una entrada desmontada no recibe la selección pendiente", () => {
    const cliente = crearCapturaSimulada();
    const entradas = agregarCeldasCaptura(cliente, "ecuaciones", [[0, 0], [1, 0]]);
    cargarCapturas(cliente);
    entradas[0].focus();
    emitirEventoCaptura(cliente, "keydown", { key: "Enter" });
    entradas[1].isConnected = false;
    completarSelecciones(cliente);
    afirmar.equal(entradas[1].selecciones, 0);
});
