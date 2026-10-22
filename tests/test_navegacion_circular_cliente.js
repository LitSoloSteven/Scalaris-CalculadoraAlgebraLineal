'use strict';

const afirmar = require('node:assert/strict');
const prueba = require('node:test');
const vm = require('node:vm');
const { cargarAssetCliente } = require('./comun_cliente_javascript.js');
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
function crearCliente(almacen = new Map(), url = DESTINO) {
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

prueba('el enlace se conserva nativo y su origen se consume una sola vez', async () => {
    const almacen = new Map();
    const salida = crearCliente(almacen, 'https://scalaris.test/matrices');
    const clic = crearClic();
    salir(salida, clic);
    afirmar.equal(clic.defaultPrevented, undefined);
    afirmar.equal(JSON.parse(almacen.get(CLAVE)).x, 125);
    const entrada = crearCliente(almacen);
    await revelar(entrada);
    afirmar.equal(almacen.size, 0);
    const animacion = entrada.animaciones[0];
    afirmar.equal(animacion.fotogramas.clipPath[0], 'circle(0px at 125px 35px)');
    afirmar.equal(animacion.fotogramas.clipPath[1], `circle(${Math.hypot(675, 565)}px at 125px 35px)`);
    afirmar.equal(animacion.opciones.pseudoElement, '::view-transition-new(root)');
});

prueba('el teclado usa el centro del enlace y limita el origen a la ventana', async () => {
    const almacen = new Map();
    salir(crearCliente(almacen, 'https://scalaris.test/matrices'), crearClic({ detail: 0 }));
    const entrada = crearCliente(almacen);
    await revelar(entrada);
    afirmar.equal(entrada.animaciones[0].fotogramas.clipPath[0], 'circle(0px at 160px 40px)');
    salir(crearCliente(almacen, 'https://scalaris.test/matrices'), crearClic({ clientX: -5, clientY: 900 }));
    const limitada = crearCliente(almacen);
    await revelar(limitada);
    afirmar.equal(limitada.animaciones[0].fotogramas.clipPath[0], 'circle(0px at 0px 600px)');
});

prueba('no registra enlaces externos, descargas, fragmentos ni activaciones modificadas', () => {
    const excluidos = [
        crearClic({ button: 1 }), ...['ctrlKey', 'metaKey', 'shiftKey', 'altKey'].map(tecla => crearClic({ [tecla]: true })),
        crearClic({ defaultPrevented: true }), crearClic({}, { target: '_blank' }),
        crearClic({}, { href: 'https://externo.test/' }), crearClic({}, { href: DESTINO + '#fragmento' }),
        crearClic({}, { hasAttribute: () => true }), crearClic({ target: { closest: () => null } }),
    ];
    excluidos.forEach(clic => {
        const cliente = crearCliente();
        salir(cliente, clic);
        afirmar.equal(cliente.almacen.size, 0);
    });
});

prueba('un enlace cancelado posteriormente o con otro destino no persiste coordenadas', () => {
    const cliente = crearCliente(new Map(), 'https://scalaris.test/matrices');
    const clic = crearClic();
    cliente.clics.get('click')(clic);
    clic.defaultPrevented = true;
    cliente.eventos.get('pageswap')({ viewTransition: crearTransicion().transicion,
        activation: { navigationType: 'push', entry: { url: DESTINO } } });
    afirmar.equal(cliente.almacen.size, 0);
    salir(cliente, crearClic({}, { href: 'https://scalaris.test/inversa' }));
    afirmar.equal(cliente.almacen.size, 0);
});

prueba('historial, recarga y registros viejos o de otro documento usan el centro', async () => {
    for (const caso of ['traverse', 'reload', 'viejo', 'otra-salida', 'otro-destino']) {
        const almacen = new Map();
        salir(crearCliente(almacen, 'https://scalaris.test/matrices'));
        const cliente = crearCliente(almacen);
        if (caso === 'traverse' || caso === 'reload') cliente.ventana.navigation.activation.navigationType = caso;
        const registro = JSON.parse(almacen.get(CLAVE));
        if (caso === 'viejo') registro.instante -= 9000;
        if (caso === 'otra-salida') registro.salida = 'otro';
        if (caso === 'otro-destino') registro.destino += '?otro';
        almacen.set(CLAVE, JSON.stringify(registro));
        await revelar(cliente);
        afirmar.equal(cliente.animaciones[0].fotogramas.clipPath[0], 'circle(0px at 400px 300px)');
        afirmar.equal(almacen.size, 0);
    }
});

prueba('espera al montaje y dos cuadros; termina y limpia recursos sin repetir la entrada', async () => {
    const cliente = crearCliente();
    cliente.documento.montado = false;
    const control = await revelar(cliente);
    afirmar.equal(cliente.animaciones[0].pausada, true);
    afirmar.equal(cliente.animaciones[0].reproducida, undefined);
    cliente.documento.montado = true;
    cliente.observadores[0].funcion();
    avanzarCuadro(cliente); avanzarCuadro(cliente);
    afirmar.equal(cliente.animaciones[0].reproducida, true);
    control.finalizar(); await Promise.resolve();
    afirmar.equal(cliente.animaciones[0].cancelada, true);
    afirmar.equal(cliente.atributos.has('data-navegacion-circular'), false);
    afirmar.equal(cliente.atributos.has('data-vista-revelada'), true);
    afirmar.equal(cliente.temporizadores.size, 0);
    afirmar.equal(cliente.cuadros.size, 0);
});

prueba('el plazo de montaje evita retener la transición si falta contenido', async () => {
    const cliente = crearCliente();
    cliente.documento.montado = false;
    await revelar(cliente);
    [...cliente.temporizadores.values()][0]();
    afirmar.equal(cliente.animaciones[0].reproducida, true);
    afirmar.equal(cliente.observadores[0].desconectado, true);
});

prueba('navegaciones rápidas cancelan la espera anterior sin limpiar la nueva', async () => {
    const cliente = crearCliente();
    const anterior = await revelar(cliente);
    const siguiente = await revelar(cliente);
    afirmar.equal(anterior.transicion.omitida, true);
    afirmar.equal(cliente.animaciones[0].cancelada, true);
    anterior.finalizar(); await Promise.resolve();
    afirmar.equal(cliente.atributos.has('data-navegacion-circular'), true);
    siguiente.finalizar(); await Promise.resolve();
    afirmar.equal(cliente.atributos.has('data-navegacion-circular'), false);
});

prueba('movimiento reducido, cambio de preferencia y API ausente mantienen navegación normal', async () => {
    const cliente = crearCliente();
    cliente.preferencia.matches = true;
    const control = await revelar(cliente);
    afirmar.equal(control.transicion.omitida, true);
    afirmar.equal(cliente.animaciones.length, 0);
    cliente.preferencia.matches = false;
    const activa = await revelar(cliente);
    cliente.preferencia.matches = true;
    cliente.eventos.get('preferencia')();
    afirmar.equal(activa.transicion.omitida, true);
    afirmar.equal(cliente.animaciones[0].cancelada, true);
    cliente.eventos.get('pagereveal')({});
    afirmar.equal(cliente.atributos.has('data-navegacion-circular'), false);
});

prueba('un fallo de animación libera la transición y un almacenamiento corrupto usa el centro', async () => {
    const cliente = crearCliente(new Map([[CLAVE, '{invalido']]));
    cliente.raiz.animate = () => { throw new Error('No disponible'); };
    const control = await revelar(cliente);
    await Promise.resolve();
    afirmar.equal(control.transicion.omitida, true);
    afirmar.equal(cliente.atributos.has('data-navegacion-circular'), false);
    afirmar.equal(cliente.almacen.size, 0);
});
