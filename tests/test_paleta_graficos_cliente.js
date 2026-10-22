'use strict';
const prueba = require('node:test');
const afirmar = require('node:assert/strict');
const maquinaVirtual = require('node:vm');
const { cargarAssetCliente } = require('./comun_cliente_javascript');

/** Simula Plotly con roles y registra el orden de las actualizaciones. */
function crearFiguraTematica() {
    const figura = { isConnected: true, _fullLayout: {}, data: [
        { meta: { scalaris_colores: { 'line.color': 'serie:0', 'marker.color': 'texto' } } },
        { meta: { scalaris_colores: { colorscale: 'solucion' } } },
    ] };
    const llamadas = [];
    const graficos = { paletas: {}, texto: {}, cuadricula: {}, solucion: {} };
    for (const tema of ['papel', 'marea', 'medianoche']) {
        graficos.paletas[tema] = [tema + '-serie'];
        for (const rol of ['texto', 'cuadricula', 'solucion']) graficos[rol][tema] = tema + '-' + rol;
    }
    const ventana = { scalaris: { graficos }, Plotly: {
        relayout: async (_, cambios) => llamadas.push({ ejes: cambios }),
        restyle: async (_, cambios, indices) => llamadas.push({ cambios, indices }),
    } };
    const documento = { querySelectorAll: () => [figura], documentElement: { getAttribute: () => 'marea' } };
    cargarAssetCliente('tema_graficos.js', maquinaVirtual.createContext({ window: ventana, document: documento }));
    return { figura, llamadas, actualizar: ventana.scalaris.actualizarTemaPlotly,
        sincronizar: ventana.scalaris.sincronizarTemaPlotly };
}

prueba('los tres temas recolorean series, marcadores, superficies y ejes sin perder roles', async () => {
    const cliente = crearFiguraTematica();
    for (const tema of ['papel', 'marea', 'medianoche', 'papel']) {
        cliente.llamadas.length = 0;
        await cliente.actualizar(tema);
        afirmar.equal(cliente.llamadas[0].ejes['xaxis.color'], tema + '-texto');
        afirmar.equal(cliente.llamadas[0].ejes['scene.zaxis.gridcolor'], tema + '-cuadricula');
        afirmar.equal(cliente.llamadas[1].cambios['line.color'], tema + '-serie');
        afirmar.equal(cliente.llamadas[1].cambios['marker.color'], tema + '-texto');
        afirmar.equal(cliente.llamadas[2].cambios.colorscale[0][1][1], tema + '-solucion');
    }
});

prueba('los cambios rápidos quedan serializados y una figura retirada se omite', async () => {
    const cliente = crearFiguraTematica();
    await Promise.all(['marea', 'papel', 'medianoche'].map(cliente.actualizar));
    afirmar.equal(cliente.llamadas.at(-1).cambios.colorscale[0][1][1], 'medianoche-solucion');
    cliente.figura.isConnected = false;
    cliente.llamadas.length = 0;
    await cliente.actualizar('papel');
    afirmar.equal(cliente.llamadas.length, 0);
});

prueba('una figura montada después del cambio recupera el tema vigente sin bucles', async () => {
    const cliente = crearFiguraTematica();
    cliente.figura._fullLayout = null;
    await cliente.actualizar('marea');
    afirmar.equal(cliente.llamadas.length, 0);
    cliente.figura._fullLayout = {};
    cliente.figura.layout = { font: { color: 'papel-texto' } };
    await Promise.all([cliente.sincronizar(), cliente.sincronizar()]);
    afirmar.equal(cliente.llamadas.length, 3);
    afirmar.equal(cliente.llamadas[1].cambios['line.color'], 'marea-serie');
    cliente.figura.layout.font.color = 'marea-texto';
    await cliente.sincronizar();
    afirmar.equal(cliente.llamadas.length, 3);
});
