'use strict';
const { test } = require('node:test');
const comprobar = require('node:assert/strict');
const { crearPresentacion } = require('./comun_presentacion_cliente.js');

test('la presentación solicita una sola señal al comenzar la animación', async () => {
    const cliente = crearPresentacion();
    const sonidos = [];
    cliente.ventana.scalaris.sonido = { reproducir: nombre => sonidos.push(nombre) };
    await cliente.reloj.avanzar(0);
    comprobar.deepEqual(sonidos, ['entrada']);
    await cliente.reloj.avanzar(3000);
    comprobar.deepEqual(sonidos, ['entrada']);
    comprobar.equal(cliente.montado(), false);
    comprobar.equal(cliente.reloj.tareas.size, 0);
});

test('silencio o bloqueo de autoplay no retrasan ni dejan pendiente la entrada', async () => {
    const cliente = crearPresentacion();
    let intentos = 0;
    cliente.ventana.scalaris.sonido = { reproducir: () => { intentos++; return false; } };
    await cliente.reloj.avanzar(3000);
    comprobar.equal(intentos, 1);
    comprobar.equal(cliente.montado(), false);
    comprobar.equal(cliente.reloj.tareas.size, 0);
    cliente.documento.emitir('pointerdown', { isTrusted: true });
    comprobar.equal(intentos, 1);
});

test('entrada ya vista, ruta ajena o cancelación anterior al montaje no suenan', async () => {
    for (const opciones of [{ ruta: '/algebra-lineal/vectores' },
        { almacen: new Map([['presentacion-mostrada', '1']]) }, { imagenFallida: true }]) {
        const cliente = crearPresentacion(opciones);
        const sonidos = [];
        cliente.ventana.scalaris.sonido = { reproducir: nombre => sonidos.push(nombre) };
        await cliente.reloj.avanzar(3000);
        comprobar.deepEqual(sonidos, []);
    }
    const cancelado = crearPresentacion();
    const sonidos = [];
    cancelado.ventana.scalaris.sonido = { reproducir: nombre => sonidos.push(nombre) };
    cancelado.documento.emitir('pointerdown', { isTrusted: true });
    await cancelado.reloj.avanzar(3000);
    comprobar.deepEqual(sonidos, []);
});
