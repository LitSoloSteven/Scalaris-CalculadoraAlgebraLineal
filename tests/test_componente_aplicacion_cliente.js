'use strict';
const prueba = require('node:test');
const afirmar = require('node:assert/strict');
const maquinaVirtual = require('node:vm');
const { cargarAssetCliente } = require('./comun_cliente_javascript');

/** Carga el módulo real sin modificar su código y simula un montaje Plotly. */
async function crearEscenario(valores = [2, 4]) {
    const filas = valores.map((_, indice) => ({dataset: {componenteResultado: String(indice)},
        setAttribute(nombre, valor) {this[nombre] = valor;}, removeAttribute(nombre) {delete this[nombre];}}));
    const region = {isConnected: true, dataset: {componenteActiva: '-1'},
        querySelectorAll: selector => selector === '.js-plotly-plot' ? [grafico] : filas};
    const grafico = {isConnected: true, _fullLayout: {}, closest: () => region,
        data: [{}, {meta: {scalaris_proyeccion: valores}}]};
    const llamadas = [];
    const biblioteca = {restyle: async (_, cambios, indices) => llamadas.push(JSON.parse(JSON.stringify({cambios, indices})))};
    const documento = {getElementById: () => region};
    const ventana = {getElement: () => ({Plotly: biblioteca})};
    cargarAssetCliente('aplicacion_transformacion.js', maquinaVirtual.createContext({window: ventana, document: documento}));
    const modulo = ventana.scalaris.aplicacionTransformacion;
    return {region, grafico, filas, llamadas, modulo, biblioteca};
}

for (const valores of [[2, 4], [2, 4, 6], [0, 0]]) {
    prueba(`proyecta solo la componente activa en ${valores.length} ejes`, async () => {
        const cliente = await crearEscenario(valores);
        await cliente.modulo.actualizar('resultado', 1);
        const cambio = cliente.llamadas.at(-1);
        afirmar.deepEqual(cambio.indices, [1]);
        afirmar.deepEqual(cambio.cambios.x, [[0]]);
        afirmar.deepEqual(cambio.cambios.y, [[valores[1]]]);
        afirmar.equal(cambio.cambios.visible, true);
        afirmar.equal(cliente.filas[1]['aria-current'], 'true');
        afirmar.equal(cliente.filas[0]['aria-current'], undefined);
        await cliente.modulo.actualizar('resultado', -1);
        afirmar.equal(cliente.llamadas.at(-1).cambios.visible, false);
        afirmar.ok(cliente.filas.every(fila => !fila['aria-current']));
    });
}

prueba('montaje tardío recupera el último paso y no repite actualizaciones del mismo paso', async () => {
    const cliente = await crearEscenario();
    cliente.grafico._fullLayout = null;
    await cliente.modulo.actualizar('resultado', 1);
    afirmar.equal(cliente.llamadas.length, 0);
    cliente.grafico._fullLayout = {};
    await cliente.modulo.sincronizar(cliente.grafico);
    afirmar.equal(cliente.llamadas.length, 1);
    await cliente.modulo.actualizar('resultado', 1);
    await cliente.modulo.sincronizar(cliente.grafico);
    afirmar.equal(cliente.llamadas.length, 1);
});

prueba('navegación rápida conserva solo la selección más reciente', async () => {
    const cliente = await crearEscenario();
    await Promise.all([0, 1, 0].map(indice => cliente.modulo.actualizar('resultado', indice)));
    afirmar.equal(cliente.llamadas.length, 1);
    afirmar.deepEqual(cliente.llamadas[0].cambios.x, [[2]]);
    afirmar.deepEqual(cliente.llamadas[0].cambios.y, [[0]]);
    afirmar.equal(cliente.filas[0]['aria-current'], 'true');
});

prueba('retirar una escena antes de ejecutar su actualización cancela el trabajo pendiente', async () => {
    const cliente = await crearEscenario();
    const pendiente = cliente.modulo.actualizar('resultado', 0);
    cliente.grafico.isConnected = cliente.region.isConnected = false;
    await pendiente;
    await cliente.modulo.actualizar('resultado', 1);
    afirmar.equal(cliente.llamadas.length, 0);
});

prueba('una escena de dominio sin resultado no recibe proyecciones', async () => {
    const cliente = await crearEscenario();
    cliente.grafico.data = [{}];
    await cliente.modulo.actualizar('resultado', 1);
    afirmar.equal(cliente.llamadas.length, 0);
});
