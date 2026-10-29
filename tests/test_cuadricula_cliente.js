"use strict";

const afirmar = require("node:assert/strict");
const prueba = require("node:test");
const { crearControlAnimado, crearCeldaCuadricula, crearCuadriculaSimulada } = require("./comun_cuadricula_cliente.js");

prueba("la entrada y la salida conservan fotogramas duración curva y espera", async () => {
    const cliente = crearCuadriculaSimulada();
    const celda = crearCeldaCuadricula();
    const api = cliente.ventana.scalaris.cuadricula;
    await api.animarEntradaCeldas([celda.entrada]);
    await api.animarSalidaCeldas([celda.entrada]);
    const animaciones = celda.control.animaciones;
    afirmar.equal(animaciones.length, 2);
    afirmar.deepEqual(JSON.parse(JSON.stringify(animaciones[0].fotogramas)), [
        { opacity: 0, transform: "scale(0.95) translateY(16px)" },
        { opacity: 1, transform: "scale(1) translateY(0)" },
    ]);
    afirmar.deepEqual(JSON.parse(JSON.stringify(animaciones[1].fotogramas)), [
        { opacity: 1, transform: "scale(1) translateY(0)" },
        { opacity: 0, transform: "scale(0.95) translateY(16px)" },
    ]);
    afirmar.equal(animaciones[0].opciones.duration, 450);
    afirmar.equal(animaciones[1].opciones.duration, 340);
    afirmar.equal(animaciones[0].opciones.easing, "cubic-bezier(0.32, 0.72, 0, 1)");
    afirmar.equal(animaciones[1].opciones.easing, animaciones[0].opciones.easing);
    afirmar.equal(animaciones[0].opciones.fill, "forwards");
});

prueba("la promesa espera la finalización del control", async () => {
    const cliente = crearCuadriculaSimulada();
    let finalizar;
    const finalizacion = new Promise(resolver => { finalizar = resolver; });
    const celda = crearCeldaCuadricula(crearControlAnimado(finalizacion));
    let completada = false;
    const espera = cliente.ventana.scalaris.cuadricula.animarEntradaCeldas([celda.entrada]).then(() => { completada = true; });
    await Promise.resolve();
    afirmar.equal(completada, false);
    finalizar();
    await espera;
    afirmar.equal(completada, true);
});

prueba("las celdas vacías sin control y las animaciones rechazadas completan la espera", async () => {
    const cliente = crearCuadriculaSimulada();
    const api = cliente.ventana.scalaris.cuadricula;
    await afirmar.doesNotReject(api.animarEntradaCeldas([]));
    await afirmar.doesNotReject(api.animarSalidaCeldas([{ closest: () => null }]));
    const celda = crearCeldaCuadricula(crearControlAnimado(Promise.reject(new Error("animación simulada"))));
    await afirmar.doesNotReject(api.animarSalidaCeldas([celda.entrada]));
    afirmar.equal(celda.control.animaciones.length, 1);
});

prueba("la modalidad de teclado y el movimiento reducido evitan animar celdas", async () => {
    const cliente = crearCuadriculaSimulada();
    const celda = crearCeldaCuadricula();
    const api = cliente.ventana.scalaris.cuadricula;
    cliente.eventos.get("keydown")();
    afirmar.equal(api.movimientoActivo(), false);
    await api.animarEntradaCeldas([celda.entrada]);
    cliente.eventos.get("pointerdown")();
    cliente.ventana.matchMedia = () => ({ matches: true });
    afirmar.equal(api.movimientoActivo(), false);
    await api.animarSalidaCeldas([celda.entrada]);
    afirmar.equal(celda.control.animaciones.length, 0);
});

prueba("los adaptadores de matriz y vector mantienen los selectores y las duraciones", async () => {
    const cliente = crearCuadriculaSimulada();
    const celda = crearCeldaCuadricula();
    const selectores = [];
    cliente.documento.querySelectorAll = selector => { selectores.push(selector); return [celda.entrada]; };
    const api = cliente.ventana.scalaris.cuadricula;
    await api.animarEntradaMatriz("A", "[data-target='izquierda']");
    await api.animarSalidaMatriz("B", "[data-target='derecha']");
    await api.animarEntradaVector(3);
    await api.animarSalidaVector(4);
    afirmar.deepEqual(selectores, [
        "input[data-matriz-identificador='A'][data-target='izquierda']",
        "input[data-matriz-identificador='B'][data-target='derecha']",
        "input[data-geometria-indice='3']", "input[data-geometria-indice='4']",
    ]);
    afirmar.deepEqual(celda.control.animaciones.map(animacion => animacion.opciones.duration), [450, 340, 450, 340]);
});

prueba("el aviso de error enfoca la celda y limpia su marca temporal", () => {
    const cliente = crearCuadriculaSimulada();
    const celda = crearCeldaCuadricula();
    let selector;
    cliente.documento.querySelector = valor => { selector = valor; return celda.entrada; };
    cliente.ventana.scalaris.cuadricula.sacudirCelda("A", 1, 2);
    afirmar.equal(selector, 'input[data-matriz-identificador="A"][data-matriz-fila="1"][data-matriz-columna="2"]');
    afirmar.equal(celda.entrada.enfocada, true);
    afirmar.equal(celda.entrada.desplazamientos[0].behavior, "smooth");
    afirmar.equal(celda.contenedor.classList.contains("movimiento-sacudida"), true);
    afirmar.equal(celda.control.classList.contains("cuadricula-error"), true);
    afirmar.equal(celda.contenedor.eventos[0].opciones.once, true);
    celda.contenedor.eventos[0].manejador();
    afirmar.equal(celda.contenedor.classList.contains("movimiento-sacudida"), false);
    afirmar.equal(cliente.temporizadores[0].espera, 1800);
    cliente.temporizadores[0].manejador();
    afirmar.equal(celda.control.classList.contains("cuadricula-error"), false);
});

prueba("el aviso de error iniciado por teclado conserva foco y marca sin movimiento", () => {
    const cliente = crearCuadriculaSimulada();
    const celda = crearCeldaCuadricula();
    cliente.documento.querySelector = () => celda.entrada;
    cliente.eventos.get("keydown")();
    cliente.ventana.scalaris.cuadricula.sacudirCelda("A", 0, 0);
    afirmar.equal(celda.entrada.enfocada, true);
    afirmar.equal(celda.entrada.desplazamientos[0].behavior, "auto");
    afirmar.equal(celda.control.classList.contains("cuadricula-error"), true);
    afirmar.equal(celda.contenedor.classList.contains("movimiento-sacudida"), false);
    afirmar.equal(celda.contenedor.eventos.length, 0);
});

prueba("el foco permite entradas directas contenedores y ausencia de elemento", () => {
    const cliente = crearCuadriculaSimulada();
    const celda = crearCeldaCuadricula();
    const api = cliente.ventana.scalaris.cuadricula;
    cliente.documento.getElementById = () => celda.entrada;
    api.enfocarElemento("directa");
    afirmar.equal(celda.entrada.enfocada, true);
    afirmar.equal(celda.entrada.desplazamientos[0].block, "center");
    celda.entrada.enfocada = false;
    cliente.documento.getElementById = () => ({ tagName: "DIV", querySelector: () => celda.entrada });
    api.enfocarElemento("contenedor");
    afirmar.equal(celda.entrada.enfocada, true);
    cliente.documento.getElementById = () => null;
    cliente.documento.querySelector = () => null;
    afirmar.doesNotThrow(() => api.enfocarElemento("ausente"));
    afirmar.doesNotThrow(() => api.sacudirCelda("ausente", 0, 0));
});

prueba("un aviso anterior no retira la marca del aviso más reciente", () => {
    const cliente = crearCuadriculaSimulada();
    const celda = crearCeldaCuadricula();
    cliente.documento.querySelector = () => celda.entrada;
    const api = cliente.ventana.scalaris.cuadricula;
    api.sacudirCelda("A", 0, 0);
    api.sacudirCelda("A", 0, 0);
    afirmar.equal(cliente.temporizadores.length, 2);
    cliente.temporizadores[0].manejador();
    afirmar.equal(celda.control.classList.contains("cuadricula-error"), true);
    cliente.temporizadores[1].manejador();
    afirmar.equal(celda.control.classList.contains("cuadricula-error"), false);
});
