'use strict';

const afirmar = require('node:assert/strict');
const prueba = require('node:test');
const {
    DESTINO, CLAVE, crearTransicion, crearCliente, crearClic, salir, revelar, avanzarCuadro,
} = require('./comun_navegacion_circular_cliente.js');

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

prueba('el teclado omite la transición y el puntero limita el origen a la ventana', async () => {
    const almacen = new Map();
    const teclado = crearCliente(almacen, 'https://scalaris.test/matrices');
    salir(teclado, crearClic({ detail: 0 }));
    afirmar.equal(almacen.has(CLAVE), false);
    const llegada = crearCliente(almacen);
    afirmar.equal(llegada.atributos.get('data-entrada'), 'teclado');
    const transicion = await revelar(llegada);
    afirmar.equal(transicion.transicion.omitida, true);
    afirmar.equal(llegada.animaciones.length, 0);
    salir(crearCliente(almacen, 'https://scalaris.test/matrices'), crearClic({ clientX: -5, clientY: 900 }));
    const limitada = crearCliente(almacen);
    await revelar(limitada);
    afirmar.equal(limitada.animaciones[0].fotogramas.clipPath[0], 'circle(0px at 0px 600px)');
});

prueba('un clic de teclado cancelado no afecta una navegación posterior con puntero', () => {
    const almacen = new Map();
    const salida = crearCliente(almacen, 'https://scalaris.test/matrices');
    salida.clics.get('click')(crearClic({ detail: 0 }));
    salida.clics.get('click')(crearClic());
    const entrada = crearCliente(almacen);
    afirmar.notEqual(entrada.atributos.get('data-entrada'), 'teclado');
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

prueba('al volver al inicio el directorio libera la captura antes del vencimiento', async () => {
    const cliente = crearCliente(new Map(), 'https://scalaris.test/');
    const encontrados = new Set(['.inicio-cabecera', 'main']);
    cliente.documento.querySelector = selector => encontrados.has(selector);
    await revelar(cliente);
    afirmar.equal(cliente.cuadros.size, 0);
    encontrados.add('.inicio-directorio[data-directorio-listo] .inicio-enlace[href]');
    cliente.observadores[0].funcion();
    avanzarCuadro(cliente); avanzarCuadro(cliente);
    afirmar.equal(cliente.animaciones[0].reproducida, true);
    afirmar.equal(cliente.temporizadores.size, 0);
});

prueba('la presentación activa tiene prioridad sobre la captura de navegación', async () => {
    const cliente = crearCliente(new Map(), 'https://scalaris.test/');
    cliente.ventana.scalaris.presentacion = { activa: true };
    const control = await revelar(cliente);
    afirmar.equal(control.transicion.omitida, true);
    afirmar.equal(cliente.animaciones.length, 0);
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
