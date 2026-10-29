'use strict';
const prueba = require('node:test');
const afirmar = require('node:assert/strict');
const { crearCuadriculaSimulada } = require('./comun_cuadricula_cliente');

/** Simula una animación con cancelación observable y propiedades base visibles. */
function crearControl(terminacion = Promise.resolve()) {
    const animaciones = [];
    return { animaciones, animate: (fotogramas, opciones) => {
        const animacion = { fotogramas, opciones, finished: terminacion, cancelada: false,
            cancel() { this.cancelada = true; } };
        animaciones.push(animacion);
        return animacion;
    } };
}

prueba('entrada retira fill forwards y el fallo de salida devuelve visibilidad', async () => {
    const cliente = crearCuadriculaSimulada();
    const control = crearControl();
    const entrada = { closest: () => control };
    await cliente.ventana.scalaris.cuadricula.animarEntradaCeldas([entrada]);
    afirmar.equal(control.animaciones[0].cancelada, true);
    control.animate = () => { throw new Error('Web Animations no disponible'); };
    await afirmar.doesNotReject(cliente.ventana.scalaris.cuadricula.animarSalidaCeldas([entrada]));
    const rechazado = crearControl(Promise.reject(new Error('salida interrumpida')));
    await cliente.ventana.scalaris.cuadricula.animarSalidaCeldas([{ closest: () => rechazado }]);
    afirmar.equal(rechazado.animaciones[0].cancelada, true);
});

prueba('repetir sobre una celda cancela la animación anterior y deduplica controles', async () => {
    const cliente = crearCuadriculaSimulada();
    const control = crearControl();
    const entrada = { closest: () => control };
    const api = cliente.ventana.scalaris.cuadricula;
    await api.animarSalidaCeldas([entrada, entrada]);
    afirmar.equal(control.animaciones.length, 1);
    await api.animarEntradaCeldas([entrada]);
    afirmar.equal(control.animaciones.length, 2);
    afirmar.equal(control.animaciones[0].cancelada, true);
    afirmar.equal(control.animaciones[1].cancelada, true);
});

prueba('2500 controles dispersos limitan las capas y usan solo transform y opacity', async () => {
    const cliente = crearCuadriculaSimulada();
    const controles = Array.from({ length: 2500 }, () => crearControl());
    await cliente.ventana.scalaris.cuadricula.animarEntradaCeldas(controles.map(control => ({ closest: () => control })));
    const animados = controles.filter(control => control.animaciones.length);
    afirmar.equal(animados.length, 10);
    afirmar.equal(animados[0].animaciones[0].opciones.duration, 450);
    afirmar.equal(animados[0].animaciones[0].opciones.delay, undefined);
    for (const control of animados) {
        for (const fotograma of control.animaciones[0].fotogramas) {
            afirmar.deepEqual(Object.keys(fotograma).sort(), ['opacity', 'transform']);
        }
    }
});

prueba('teclado y movimiento reducido no crean animaciones ni efectos persistentes', async () => {
    const cliente = crearCuadriculaSimulada();
    const control = crearControl();
    const entrada = { closest: () => control };
    const api = cliente.ventana.scalaris.cuadricula;
    await api.animarSalidaCeldas([entrada]);
    cliente.eventos.get('keydown')();
    await api.animarEntradaCeldas([entrada]);
    afirmar.equal(control.animaciones.length, 1);
    afirmar.equal(control.animaciones[0].cancelada, true);
    cliente.eventos.get('pointerdown')();
    cliente.ventana.matchMedia = () => ({ matches: true });
    await api.animarSalidaCeldas([entrada]);
    afirmar.equal(control.animaciones.length, 1);
});

prueba('el rechazo de una animación antigua no cancela la entrada que la sustituye', async () => {
    const cliente = crearCuadriculaSimulada();
    const animaciones = [];
    const control = { animate() {
        let resolver, rechazar;
        const finished = new Promise((fin, error) => { resolver = fin; rechazar = error; });
        const animacion = { finished, cancelada: false, resolver,
            cancel() { this.cancelada = true; rechazar(new Error('cancelada')); } };
        animaciones.push(animacion);
        return animacion;
    } };
    const celda = { closest: () => control };
    const api = cliente.ventana.scalaris.cuadricula;
    const salida = api.animarSalidaCeldas([celda]);
    const entrada = api.animarEntradaCeldas([celda]);
    await Promise.resolve(); await Promise.resolve();
    afirmar.equal(animaciones[0].cancelada, true);
    afirmar.equal(animaciones[1].cancelada, false);
    animaciones[1].resolver();
    await Promise.all([salida, entrada]);
    afirmar.equal(animaciones[1].cancelada, true);
});
