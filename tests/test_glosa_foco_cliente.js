"use strict";
const afirmar = require("node:assert/strict");
const prueba = require("node:test");
const { crearGlosaSimulada, crearElementoGlosa, pulsarGlosa } = require("./comun_glosa_cliente.js");

for (const modo of ["hoja", "superposicion"]) {
    prueba(`Glosa ${modo} atrapa Tab y Shift+Tab y permite el recorrido interior`, () => {
        const cliente = crearGlosaSimulada(modo);
        cliente.ventana.scalaris.glosa.abrir({ origen: "teclado" });
        afirmar.equal(cliente.documento.activeElement, cliente.controles[1]);
        afirmar.equal(pulsarGlosa(cliente, "Tab").defaultPrevented, true);
        afirmar.equal(cliente.documento.activeElement, cliente.controles[0]);
        afirmar.equal(pulsarGlosa(cliente, "Tab").defaultPrevented, false);
        afirmar.equal(pulsarGlosa(cliente, "Tab", true).defaultPrevented, true);
        afirmar.equal(cliente.documento.activeElement, cliente.controles[1]);
    });
}

prueba("el modo lateral no atrapa Tab y Escape devuelve al disparador conectado", () => {
    const cliente = crearGlosaSimulada("desplazar");
    const disparador = crearElementoGlosa(cliente.documento);
    cliente.ventana.scalaris.glosa.abrir({ origen: "teclado", elemento_origen: disparador });
    afirmar.equal(pulsarGlosa(cliente, "Tab").defaultPrevented, false);
    pulsarGlosa(cliente, "Escape");
    afirmar.equal(cliente.documento.activeElement, disparador);
    afirmar.equal(cliente.ventana.scalaris.glosa.estaAbierto(), false);
});

prueba("el modal vacío mantiene foco en el panel y descarta controles ocultos o deshabilitados", () => {
    const cliente = crearGlosaSimulada();
    cliente.controles[0].disabled = true;
    cliente.controles[1].invisible = true;
    cliente.ventana.scalaris.glosa.abrir();
    afirmar.equal(cliente.documento.activeElement, cliente.panel);
    afirmar.equal(pulsarGlosa(cliente, "Tab").defaultPrevented, true);
    afirmar.equal(cliente.documento.activeElement, cliente.panel);
    afirmar.equal(pulsarGlosa(cliente, "Tab", true).defaultPrevented, true);
    afirmar.equal(cliente.documento.activeElement, cliente.panel);
});

prueba("el foco ajeno al modal se reconduce y cerrar restaura la interacción", () => {
    const cliente = crearGlosaSimulada();
    cliente.ventana.scalaris.glosa.abrir();
    afirmar.equal(cliente.origen.inert, true);
    cliente.documento.activeElement = cliente.origen;
    pulsarGlosa(cliente, "Tab");
    afirmar.equal(cliente.documento.activeElement, cliente.controles[0]);
    pulsarGlosa(cliente, "Escape");
    afirmar.equal(cliente.origen.inert, false);
    afirmar.equal(cliente.documento.activeElement, cliente.origen);
    afirmar.equal(pulsarGlosa(cliente, "Tab").defaultPrevented, false);
});

prueba("el cierre usa el flotante cuando el disparador ya no está conectado", () => {
    const cliente = crearGlosaSimulada();
    const disparador = crearElementoGlosa(cliente.documento, { isConnected: false });
    cliente.ventana.scalaris.glosa.abrir({ elemento_origen: disparador });
    cliente.ventana.scalaris.glosa.cerrar();
    afirmar.equal(cliente.documento.activeElement, cliente.origen);
});

for (const impedimento of ["disabled", "invisible", "oculto"]) {
    prueba(`el cierre usa el flotante si el disparador está ${impedimento}`, () => {
        const cliente = crearGlosaSimulada();
        const disparador = crearElementoGlosa(cliente.documento);
        cliente.ventana.scalaris.glosa.abrir({ elemento_origen: disparador });
        disparador[impedimento] = true;
        cliente.ventana.scalaris.glosa.cerrar();
        afirmar.equal(cliente.documento.activeElement, cliente.origen);
    });
}

prueba("reabrir con teclado durante una consulta enfoca el panel y omite el campo deshabilitado", () => {
    const cliente = crearGlosaSimulada();
    cliente.controles[1].disabled = true;
    cliente.ventana.scalaris.glosa.abrir({ origen: "teclado" });
    afirmar.equal(cliente.documento.activeElement, cliente.panel);
    pulsarGlosa(cliente, "Tab");
    afirmar.equal(cliente.documento.activeElement, cliente.controles[0]);
});

prueba("la apertura programática por teclado y movimiento reducido es instantánea", () => {
    for (const reduccion of [false, true]) {
        const cliente = crearGlosaSimulada();
        cliente.raiz.setAttribute("data-entrada", reduccion ? "puntero" : "teclado");
        cliente.ventana.matchMedia = consulta => ({ matches: reduccion && consulta.includes("reduced-motion") });
        const estados = [];
        const atributos = [];
        const establecer = cliente.raiz.setAttribute;
        cliente.raiz.setAttribute = (nombre, valor) => { atributos.push(nombre); establecer(nombre, valor); };
        cliente.documento.dispatchEvent = () => estados.push(cliente.raiz.getAttribute("data-glosa"));
        cliente.ventana.scalaris.glosa.abrir();
        afirmar.deepEqual(estados, ["abierto"]);
        afirmar.ok(atributos.includes("data-glosa-instantaneo"));
        afirmar.equal(cliente.ventana.scalaris.glosa.estaAbierto(), true);
    }
});
