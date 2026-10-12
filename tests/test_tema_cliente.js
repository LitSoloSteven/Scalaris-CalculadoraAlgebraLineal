"use strict";

const afirmar = require("node:assert/strict");
const prueba = require("node:test");
const { cargarAssetCliente } = require("./comun_cliente_javascript.js");
const { crearTemaSimulado, cargarTemaCompleto } = require("./comun_tema_cliente.js");

prueba("los temas anteriores conservan equivalencias antes de cargar los estilos", () => {
    for (const [almacenado, esperado] of [["claro", "papel"], ["aqua", "marea"], ["oscuro", "medianoche"]]) {
        const cliente = crearTemaSimulado(almacenado);
        cargarAssetCliente("inicializacion_tema.js", cliente.contexto);
        afirmar.equal(cliente.atributos.get("data-theme"), esperado);
        afirmar.equal(cliente.almacen.get("theme"), esperado);
        afirmar.equal(cliente.documento.documentElement.style.colorScheme, esperado === "medianoche" ? "dark" : "light");
        afirmar.equal(JSON.stringify(cliente.ventana.scalaris.graficos), JSON.stringify(cliente.graficos));
    }
});

prueba("el tema inicial conserva valores canónicos desconocidos y ausencia", () => {
    for (const [almacenado, esperado] of [[null, "papel"], ["marea", "marea"], ["desconocido", "desconocido"]]) {
        const cliente = crearTemaSimulado(almacenado);
        cargarTemaCompleto(cliente);
        afirmar.equal(cliente.atributos.get("data-theme"), esperado);
        afirmar.equal(cliente.almacen.get("theme") ?? null, almacenado);
        afirmar.equal(cliente.logotipo.src, "original");
        afirmar.deepEqual(Object.keys(cliente.ventana.scalaris.tema), ["aplicar", "establecer"]);
    }
});

prueba("aplicar tema cambia atributos logotipo almacenamiento y figuras", () => {
    const cliente = crearTemaSimulado();
    cargarTemaCompleto(cliente);
    const llamadas = [];
    cliente.ventana.scalaris.actualizarTemaPlotly = tema => llamadas.push(tema);
    cliente.ventana.scalaris.tema.aplicar("medianoche");
    afirmar.equal(cliente.atributos.get("data-theme"), "medianoche");
    afirmar.equal(cliente.documento.documentElement.style.colorScheme, "dark");
    afirmar.equal(cliente.logotipo.src, "/assets/LogoClaro.png");
    afirmar.equal(cliente.almacen.get("theme"), "medianoche");
    afirmar.equal(cliente.temporizadores[0].espera, 50);
    cliente.temporizadores[0].manejador();
    afirmar.deepEqual(llamadas, ["medianoche"]);
    cliente.ventana.scalaris.tema.aplicar("papel");
    afirmar.equal(cliente.logotipo.src, "/assets/LogoOscuro.png");
    afirmar.equal(cliente.documento.documentElement.style.colorScheme, "light");
});

prueba("sin transición nativa el cambio de tema es inmediato", () => {
    const cliente = crearTemaSimulado();
    cargarTemaCompleto(cliente);
    cliente.ventana.scalaris.tema.establecer("marea");
    afirmar.equal(cliente.atributos.get("data-theme"), "marea");
    afirmar.equal(cliente.animaciones.length, 0);
});

prueba("la transición nativa conserva fotogramas duración y curva", async () => {
    const cliente = crearTemaSimulado();
    cargarTemaCompleto(cliente);
    cliente.documento.startViewTransition = cambiar => { cambiar(); return { ready: Promise.resolve() }; };
    cliente.ventana.scalaris.tema.establecer("medianoche");
    await Promise.resolve();
    afirmar.equal(cliente.atributos.get("data-theme"), "medianoche");
    afirmar.equal(cliente.animaciones.length, 1);
    afirmar.equal(JSON.stringify(cliente.animaciones[0].fotogramas), '[{"opacity":0},{"opacity":1}]');
    afirmar.equal(cliente.animaciones[0].opciones.duration, 240);
    afirmar.equal(cliente.animaciones[0].opciones.easing, "cubic-bezier(0.32, 0.72, 0, 1)");
    afirmar.equal(cliente.animaciones[0].opciones.pseudoElement, "::view-transition-new(root)");
});

prueba("el rechazo de la transición vuelve a aplicar el tema", async () => {
    const cliente = crearTemaSimulado();
    cargarTemaCompleto(cliente);
    const rechazo = new Error("transición simulada");
    cliente.documento.startViewTransition = () => ({ ready: Promise.reject(rechazo) });
    cliente.ventana.scalaris.tema.establecer("marea");
    await Promise.resolve();
    await Promise.resolve();
    afirmar.equal(cliente.atributos.get("data-theme"), "marea");
    afirmar.equal(cliente.animaciones.length, 0);
});

prueba("la preparación de Glosa conserva selección y límite de escritorio", () => {
    for (const [ancho, almacenado, esperado] of [[1024, "open", "open"], [1023, "open", "closed"], [1200, "closed", "closed"], [1200, null, "closed"]]) {
        const cliente = crearTemaSimulado(null, ancho);
        if (almacenado !== null) cliente.almacen.set("scalaris:glosa", almacenado);
        cargarAssetCliente("inicializacion_glosa.js", cliente.contexto);
        afirmar.equal(cliente.atributos.get("data-glosa"), esperado);
    }
});

prueba("el fallo de almacenamiento de Glosa conserva el atributo anterior", () => {
    const cliente = crearTemaSimulado();
    cliente.atributos.set("data-glosa", "open");
    cliente.almacenamiento.getItem = () => { throw new Error("almacenamiento simulado"); };
    afirmar.doesNotThrow(() => cargarAssetCliente("inicializacion_glosa.js", cliente.contexto));
    afirmar.equal(cliente.atributos.get("data-glosa"), "open");
});

prueba("la activación por teclado aplica el tema sin transición", () => {
    const cliente = crearTemaSimulado();
    cargarTemaCompleto(cliente);
    cargarAssetCliente("interacciones_globales.js", cliente.contexto);
    cliente.documento.startViewTransition = () => { throw new Error("no debe iniciar transición"); };
    cliente.eventos.get("keydown")();
    afirmar.doesNotThrow(() => cliente.ventana.scalaris.tema.establecer("marea"));
    afirmar.equal(cliente.atributos.get("data-theme"), "marea");
    afirmar.equal(cliente.animaciones.length, 0);
});

prueba("la preferencia de movimiento reducido aplica el tema sin transición", () => {
    const cliente = crearTemaSimulado();
    cargarTemaCompleto(cliente);
    cargarAssetCliente("interacciones_globales.js", cliente.contexto);
    cliente.ventana.matchMedia = consulta => ({ matches: consulta === '(prefers-reduced-motion: reduce)' });
    cliente.documento.startViewTransition = () => { throw new Error("no debe iniciar transición"); };
    afirmar.doesNotThrow(() => cliente.ventana.scalaris.tema.establecer("medianoche"));
    afirmar.equal(cliente.atributos.get("data-theme"), "medianoche");
    afirmar.equal(cliente.animaciones.length, 0);
});

prueba("el rechazo de una transición antigua no sobrescribe la última selección", async () => {
    const cliente = crearTemaSimulado();
    cargarTemaCompleto(cliente);
    const rechazos = [];
    cliente.documento.startViewTransition = cambiar => {
        cambiar();
        return { ready: new Promise((resolver, rechazar) => rechazos.push(rechazar)) };
    };
    cliente.ventana.scalaris.tema.establecer("marea");
    cliente.ventana.scalaris.tema.establecer("medianoche");
    afirmar.equal(cliente.atributos.get("data-theme"), "medianoche");
    rechazos[0](new Error("primera transición simulada"));
    await Promise.resolve();
    await Promise.resolve();
    afirmar.equal(cliente.atributos.get("data-theme"), "medianoche");
    afirmar.equal(cliente.almacen.get("theme"), "medianoche");
    afirmar.equal(cliente.logotipo.src, "/assets/LogoClaro.png");
});

prueba("un cambio directo invalida el callback diferido de una transición anterior", async () => {
    const cliente = crearTemaSimulado();
    cargarTemaCompleto(cliente);
    let cambioPendiente;
    let resolverPendiente;
    cliente.documento.startViewTransition = cambiar => {
        cambioPendiente = cambiar;
        return { ready: new Promise(resolver => { resolverPendiente = resolver; }) };
    };
    cliente.ventana.scalaris.tema.establecer("marea");
    cliente.ventana.scalaris.tema.aplicar("medianoche");
    cambioPendiente();
    resolverPendiente();
    await Promise.resolve();
    afirmar.equal(cliente.atributos.get("data-theme"), "medianoche");
    afirmar.equal(cliente.animaciones.length, 0);
});

prueba("la actualización diferida de figuras ignora selecciones anteriores", () => {
    const cliente = crearTemaSimulado();
    cargarTemaCompleto(cliente);
    const llamadas = [];
    cliente.ventana.scalaris.actualizarTemaPlotly = tema => llamadas.push(tema);
    cliente.ventana.scalaris.tema.aplicar("marea");
    cliente.ventana.scalaris.tema.aplicar("medianoche");
    cliente.temporizadores[0].manejador();
    afirmar.deepEqual(llamadas, []);
    cliente.temporizadores[1].manejador();
    afirmar.deepEqual(llamadas, ["medianoche"]);
    afirmar.equal(cliente.atributos.get("data-theme"), "medianoche");
});
