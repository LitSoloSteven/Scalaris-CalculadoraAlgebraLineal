"use strict";
const afirmar = require("node:assert/strict");
const prueba = require("node:test");
const { crearPresentacion } = require("./comun_presentacion_cliente.js");

prueba("la primera visita encadena las animaciones y después libera el inicio", async () => {
    const cliente = crearPresentacion({ tema: "medianoche" });
    await cliente.reloj.avanzar(1949);
    afirmar.equal(cliente.animaciones.length, 7);
    afirmar.equal(cliente.montado(), true);
    afirmar.equal(cliente.atributos.has("data-inicio-pendiente"), true);
    afirmar.equal(cliente.imagen.src, "/assets/LogoClaro.png");
    await cliente.reloj.avanzar(1982);
    afirmar.equal(cliente.montado(), false);
    afirmar.equal(cliente.atributos.has("data-inicio-pendiente"), false);
    afirmar.equal(cliente.reloj.tareas.size, 0);
    afirmar(cliente.animaciones.every(animacion => animacion.cancelada));
    afirmar.equal(cliente.ventana.oyentes.size, 0);
    afirmar.deepEqual([...cliente.documento.oyentes.keys()].sort(), ["focusin", "keydown", "mouseover", "pointerdown"]);
});

prueba("reinyectar, recargar o regresar al inicio no reproduce otra presentación", async () => {
    const cliente = crearPresentacion();
    cliente.cargar("presentacion.js");
    await cliente.reloj.avanzar(1982);
    afirmar.equal(cliente.animaciones.length, 7);
    const recarga = crearPresentacion({ almacen: cliente.almacen });
    await recarga.reloj.avanzar(32);
    afirmar.equal(recarga.animaciones.length, 0);
    afirmar.equal(recarga.montado(), false);
    afirmar.equal(recarga.atributos.has("data-inicio-pendiente"), false);
});

prueba("entrar por otra ruta o una consulta consume la presentación sin mostrarla", async () => {
    for (const opciones of [{ ruta: "/algebra-lineal/vectores" }, { consulta: "?glosa=1" }]) {
        const directo = crearPresentacion(opciones);
        afirmar.equal(directo.montado(), false);
        const vuelta = crearPresentacion({ almacen: directo.almacen });
        await vuelta.reloj.avanzar(32);
        afirmar.equal(vuelta.animaciones.length, 0);
    }
});

prueba("la alternativa reducida solo anima opacidad y termina a los 120 ms", async () => {
    const cliente = crearPresentacion({ reducido: true });
    await cliente.reloj.avanzar(119);
    afirmar.equal(cliente.montado(), true);
    afirmar.equal(cliente.animaciones.length, 1);
    afirmar(cliente.animaciones[0].fotogramas.every(f => Object.keys(f).join() === "opacity"));
    await cliente.reloj.avanzar(152);
    afirmar.equal(cliente.montado(), false);
    afirmar.equal(cliente.reloj.tareas.size, 0);
});

prueba("contenido tardío espera al montaje y a dos fotogramas visibles", async () => {
    const cliente = crearPresentacion({ contenido: false });
    await cliente.reloj.avanzar(3100);
    afirmar.equal(cliente.montado(), false);
    afirmar.equal(cliente.atributos.has("data-inicio-pendiente"), true);
    cliente.montarContenido();
    await cliente.reloj.avanzar(3132);
    afirmar.equal(cliente.atributos.has("data-inicio-pendiente"), false);
    afirmar(cliente.observadores.every(observador => !observador.activo));
});

prueba("fallos de imagen, animación o almacenamiento dejan libre la aplicación", async () => {
    for (const opciones of [{ imagenFallida: true }, { animacionFallida: true }, { almacenBloqueado: true }]) {
        const cliente = crearPresentacion(opciones);
        await cliente.reloj.avanzar(64);
        afirmar.equal(cliente.montado(), false);
        afirmar.equal(cliente.atributos.has("data-inicio-pendiente"), false);
        afirmar.equal(cliente.reloj.tareas.size, 0);
    }
});

prueba("abandonar la página cancela la escena y la entrada pendiente", async () => {
    const cliente = crearPresentacion();
    await cliente.reloj.avanzar(200);
    cliente.ventana.emitir("pagehide");
    await cliente.reloj.avanzar(5000);
    afirmar.equal(cliente.montado(), false);
    afirmar.equal(cliente.reloj.tareas.size, 0);
    afirmar.equal(cliente.atributos.has("data-inicio-pendiente"), false);
    afirmar(cliente.animaciones.every(animacion => animacion.cancelada));
});

prueba("la salida de emergencia retira animaciones que no resuelven", async () => {
    const cliente = crearPresentacion({ animacionCongelada: true });
    await cliente.reloj.avanzar(3832);
    afirmar.equal(cliente.montado(), false);
    afirmar.equal(cliente.atributos.has("data-inicio-pendiente"), false);
    afirmar.equal(cliente.reloj.tareas.size, 0);
    afirmar(cliente.animaciones.every(animacion => animacion.cancelada));
});

prueba("si falta alguno de los recursos la presentación no deja oculto el contenido", async () => {
    for (const opciones of [{ sinEntrada: true }, { sinPresentacion: true }]) {
        const cliente = crearPresentacion(opciones);
        await cliente.reloj.avanzar(3000);
        afirmar.equal(cliente.montado(), false);
        afirmar.equal(cliente.atributos.has("data-inicio-pendiente"), false);
        afirmar.equal(cliente.reloj.tareas.size, 0);
    }
});

prueba("teclado, puntero, ocultación y cambio a movimiento reducido cancelan la escena", async () => {
    for (const motivo of ["keydown", "pointerdown", "visibilitychange", "change"]) {
        const cliente = crearPresentacion();
        await cliente.reloj.avanzar(200);
        cliente.documento.hidden = true;
        if (motivo === "change") cliente.preferencia.emitir(motivo, { matches: true });
        else cliente.documento.emitir(motivo);
        await cliente.reloj.avanzar(232);
        afirmar.equal(cliente.montado(), false);
        afirmar.equal(cliente.reloj.tareas.size, 0);
        afirmar.equal(cliente.atributos.has("data-inicio-pendiente"), false);
    }
});
