'use strict';

const vm = require('node:vm');
const { cargarAssetCliente } = require('./comun_cliente_javascript.js');
const { estilosMovimiento } = require('./comun_tokens_movimiento.js');
const DESTINO = 'https://scalaris.test/vectores';
const CLAVE = 'scalaris:origen-navegacion';

/** Controla la finalización y el rechazo de una transición nativa. */
function crearTransicion() {
    let finalizar, rechazar;
    const transicion = {
        ready: Promise.resolve(),
        finished: new Promise((resolver, fallo) => { finalizar = resolver; rechazar = fallo; }),
        omitida: false,
        skipTransition() { this.omitida = true; finalizar(); },
    };
    return { transicion, finalizar, rechazar };
}

/** Observa la captura circular y su ciclo de reproducción sin crear capas reales. */
function crearRaiz(atributos, animaciones) {
    return {
        setAttribute: (nombre, valor) => atributos.set(nombre, valor),
        getAttribute: nombre => atributos.get(nombre),
        removeAttribute: nombre => atributos.delete(nombre),
        animate: (fotogramas, opciones) => {
            const animacion = {
                fotogramas, opciones, finished: new Promise(() => {}),
                pause() { this.pausada = true; }, play() { this.reproducida = true; },
                cancel() { this.cancelada = true; },
            };
            animaciones.push(animacion);
            return animacion;
        },
    };
}

/** Simula documentos independientes compartiendo únicamente el almacenamiento de sesión. */
function crearCliente(almacen = new Map(), url = DESTINO, { sinRevelado = false } = {}) {
    const eventos = new Map(), clics = new Map(), atributos = new Map();
    const animaciones = [], cuadros = new Map(), temporizadores = new Map(), observadores = [];
    let secuencia = 0;
    const preferencia = { matches: false, addEventListener: (_, funcion) => eventos.set('preferencia', funcion) };
    const raiz = crearRaiz(atributos, animaciones);
    const documento = {
        documentElement: raiz, montado: true,
        querySelector: selector => selector === 'base[target]' ? null : documento.montado,
        addEventListener: (nombre, funcion) => clics.set(nombre, funcion),
    };
    const ventana = {
        location: new URL(url), innerWidth: 800, innerHeight: 600,
        navigation: { activation: { navigationType: 'push', from: { key: 'salida' } } },
        matchMedia: () => preferencia, addEventListener: (nombre, funcion) => eventos.set(nombre, funcion),
    };
    const contexto = vm.createContext({
        window: ventana, document: documento, URL, Date, Number, Math,
        getComputedStyle: estilosMovimiento,
        performance: { getEntriesByType: () => [{ type: 'navigate' }] },
        sessionStorage: {
            getItem: clave => almacen.get(clave) || null,
            setItem: (clave, valor) => almacen.set(clave, valor), removeItem: clave => almacen.delete(clave),
        },
        MutationObserver: class {
            constructor(funcion) { this.funcion = funcion; observadores.push(this); }
            observe() {} disconnect() { this.desconectado = true; }
        },
        setTimeout: funcion => { temporizadores.set(++secuencia, funcion); return secuencia; },
        clearTimeout: id => temporizadores.delete(id),
        requestAnimationFrame: funcion => { cuadros.set(++secuencia, funcion); return secuencia; },
        cancelAnimationFrame: id => cuadros.delete(id),
    });
    cargarAssetCliente('interacciones_globales.js', contexto);
    if (!sinRevelado) cargarAssetCliente('revelado_circular.js', contexto);
    cargarAssetCliente('navegacion_circular.js', contexto);
    return { eventos, clics, atributos, animaciones, cuadros, temporizadores, observadores,
        preferencia, ventana, documento, contexto, raiz, almacen };
}

function crearClic(cambios = {}, propiedades = {}) {
    const enlace = {
        href: DESTINO, target: '', hasAttribute: () => false,
        getBoundingClientRect: () => ({ left: 100, top: 20, width: 120, height: 40 }),
        ...propiedades,
    };
    return { button: 0, detail: 1, clientX: 125, clientY: 35,
        target: { closest: () => enlace }, ...cambios };
}

function salir(cliente, evento = crearClic(), tipo = 'push') {
    cliente.clics.get('click')(evento);
    const { transicion } = crearTransicion();
    cliente.eventos.get('pageswap')({ viewTransition: transicion,
        activation: { navigationType: tipo, from: { key: 'salida' }, entry: { url: DESTINO } } });
}

async function revelar(cliente) {
    const control = crearTransicion();
    cliente.eventos.get('pagereveal')({ viewTransition: control.transicion });
    await Promise.resolve();
    return control;
}

function avanzarCuadro(cliente) {
    const pendientes = [...cliente.cuadros.values()];
    cliente.cuadros.clear();
    pendientes.forEach(funcion => funcion());
}

module.exports = { DESTINO, CLAVE, crearTransicion, crearCliente, crearClic, salir, revelar, avanzarCuadro };
