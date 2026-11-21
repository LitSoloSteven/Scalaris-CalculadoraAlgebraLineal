'use strict';

const afirmar = require('node:assert/strict');
const prueba = require('node:test');
const {
    DESTINO, CLAVE, crearCliente, crearTransicion, crearClic, salir, revelar, avanzarCuadro,
} = require('./comun_navegacion_circular_cliente.js');

function comprobarLimpieza(cliente, control) {
    afirmar.equal(control.transicion.omitida, true);
    afirmar.equal(cliente.atributos.has('data-navegacion-circular'), false);
    afirmar.equal(cliente.animaciones[0].cancelada, true);
    afirmar.equal(cliente.temporizadores.size, 0);
    afirmar.equal(cliente.cuadros.size, 0);
    afirmar(cliente.observadores.every(observador => observador.desconectado));
}

prueba('si falla play se libera la captura tanto al montar como al vencer el plazo', async () => {
    for (const montado of [true, false]) {
        const cliente = crearCliente();
        cliente.documento.montado = montado;
        const control = await revelar(cliente);
        cliente.animaciones[0].play = () => { throw new Error('Captura retirada'); };
        if (montado) {
            avanzarCuadro(cliente);
            avanzarCuadro(cliente);
        } else {
            [...cliente.temporizadores.values()][0]();
        }
        comprobarLimpieza(cliente, control);
    }
});

prueba('pagehide suelta la captura de entrada y conserva la captura de salida', async () => {
    const cliente = crearCliente();
    cliente.documento.montado = false;
    const entrada = await revelar(cliente);
    cliente.eventos.get('pagehide')();
    comprobarLimpieza(cliente, entrada);

    const salida = crearTransicion();
    cliente.eventos.get('pageswap')({ viewTransition: salida.transicion });
    cliente.eventos.get('pagehide')();
    afirmar.equal(salida.transicion.omitida, false);
});

prueba('un instante ausente, textual o futuro invalida el origen almacenado', async () => {
    for (const instante of [undefined, 'desconocido', String(Date.now()), Date.now() + 8000]) {
        const registro = { destino: DESTINO, salida: 'salida', instante, x: 25, y: 35 };
        const almacen = new Map([[CLAVE, JSON.stringify(registro)]]);
        const cliente = crearCliente(almacen);
        await revelar(cliente);
        afirmar.equal(cliente.animaciones[0].fotogramas.clipPath[0], 'circle(0px at 400px 300px)');
        afirmar.equal(almacen.size, 0);
    }
});

prueba('sin geometría compartida el teclado y el enlace conservan su navegación nativa', async () => {
    const almacen = new Map();
    const salida = crearCliente(almacen, 'https://scalaris.test/matrices', { sinRevelado: true });
    const clic = crearClic({ detail: 0 });
    salir(salida, clic);
    afirmar.equal(clic.defaultPrevented, undefined);
    const llegada = crearCliente(almacen, DESTINO, { sinRevelado: true });
    afirmar.equal(llegada.atributos.get('data-entrada'), 'teclado');
    const control = await revelar(llegada);
    afirmar.equal(control.transicion.omitida, true);
    afirmar.equal(llegada.animaciones.length, 0);
});
