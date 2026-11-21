'use strict';

const afirmar = require('node:assert/strict');
const prueba = require('node:test');
const { cargarAssetCliente } = require('./comun_cliente_javascript.js');
const { crearPresentacion } = require('./comun_presentacion_cliente.js');
const { crearTemaSimulado, simularTransicion } = require('./comun_tema_cliente.js');

prueba('redimensionar la ventana libera una máscara ya medida', async () => {
    for (const instante of [930, 1700]) {
        const cliente = crearPresentacion();
        await cliente.reloj.avanzar(instante);
        afirmar.equal(cliente.montado(), true);
        cliente.ventana.innerWidth = 320;
        cliente.ventana.emitir('resize');
        afirmar.equal(cliente.montado(), false);
        afirmar.equal(cliente.ventana.oyentes.size, 0);
        afirmar.equal(cliente.reloj.tareas.size, 0);
    }
});

prueba('si falla el audio un gesto real sigue retirando la presentación', async () => {
    const cliente = crearPresentacion();
    await cliente.reloj.avanzar(200);
    cliente.ventana.scalaris.sonido = { reproducir: () => { throw new Error('Audio indisponible'); } };
    cliente.documento.emitir('keydown', { isTrusted: true });
    afirmar.equal(cliente.montado(), false);
    afirmar.equal(cliente.reloj.tareas.size, 0);
});

prueba('si falta el directorio cliente la portada queda visible al terminar el anillo', async () => {
    const cliente = crearPresentacion({ sinEntrada: true });
    await cliente.reloj.avanzar(900);
    afirmar.equal(cliente.montado(), false);
    afirmar.equal(cliente.ventana.scalaris.presentacion.activa, false);
    afirmar.equal(cliente.reloj.tareas.size, 0);
    afirmar.equal(cliente.atributos.has('data-vista-revelada'), true);
});

prueba('si falta la geometría compartida el tema se aplica sin captura', () => {
    const cliente = crearTemaSimulado('papel');
    for (const archivo of ['inicializacion_tema.js', 'interacciones_globales.js', 'tema.js']) {
        cargarAssetCliente(archivo, cliente.contexto);
    }
    let capturas = 0;
    cliente.documento.startViewTransition = cambiar => {
        capturas++;
        return simularTransicion(cambiar);
    };
    cliente.ventana.scalaris.tema.establecer('marea');
    afirmar.equal(cliente.atributos.get('data-tema'), 'marea');
    afirmar.equal(cliente.almacen.get('tema'), 'marea');
    afirmar.equal(capturas, 0);
});
