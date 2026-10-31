'use strict';
const afirmar = require('node:assert/strict');
const prueba = require('node:test');
const maquinaVirtual = require('node:vm');
const {cargarAssetCliente} = require('./comun_cliente_javascript.js');

function prepararEscenario(opciones = {}) {
    const registro = {purgas: 0, retiradas: 0, lienzos: 0};
    const camara = {eye: {x: 3, y: 2, z: 1}};
    const figura = {data: [{type: opciones.tipo || 'scatter3d', x: [0, 7], visible: 'legendonly',
        marker: {color: 'oscuro'}, meta: {scalaris_colores: {'marker.color': 'serie:0'}}}],
    layout: {font: {color: 'oscuro'}, xaxis: {range: [-3, 7], autorange: false},
        scene: {xaxis: {range: [-3, 7]}, camera: {eye: {x: 1, y: 1, z: 1}}}},
    _fullLayout: {scene: {camera: camara}}, getBoundingClientRect: () => ({width: 200, height: 100})};
    const region = {dataset: {pdfCaptura: 'visualizador-figura', pdfMotor: 'plotly'},
        querySelector: () => opciones.sinFigura ? null : figura, getClientRects: () => [{}]};
    const raiz = {inert: false, querySelectorAll: () => [region]};
    const temporal = {style: {}, dataset: {}, setAttribute() {}, remove() { registro.retiradas++; }};
    const biblioteca = {
        async newPlot(nodo, datos, disposicion, configuracion) {
            registro.datos = datos;
            registro.disposicion = disposicion;
            registro.configuracion = configuracion;
            if (opciones.fallarMontaje) throw new Error('montaje');
            if (opciones.esperarMontaje) await opciones.esperarMontaje;
        },
        async toImage(nodo, ajustes) {
            registro.ajustes = ajustes;
            if (opciones.fallarImagen) throw new Error('imagen');
            return opciones.imagen || 'data:image/png;base64,AAAA';
        },
        purge() { registro.purgas++; },
    };
    const ventana = {Plotly: opciones.sinBiblioteca ? null : biblioteca,
        scalaris: {graficos: {paletas: {papel: ['rojo']}, texto: {papel: 'negro'}, cuadricula: {papel: 'gris'}}},
        MathJax: {startup: {promise: Promise.resolve()}, typesetPromise: async () => {}},
        html2canvas: () => { registro.lienzos++; throw new Error('no usar para Plotly'); }};
    const documento = {getElementById: () => raiz, querySelectorAll: () => [],
        createElement: () => temporal, body: {appendChild() {}}, fonts: {ready: Promise.resolve()}};
    const contexto = maquinaVirtual.createContext({window: ventana, document: documento,
        setTimeout, clearTimeout, structuredClone});
    cargarAssetCliente('captura_pdf.js', contexto);
    const configuracion = {maximoFiguras: 12, maximoBytesImagen: 1024, maximoBytesTotal: 2048,
        maximoLado: 4096, maximoPixeles: 12000000, plazoMathjax: 0.1, plazoCaptura: 0.1, escala: 2};
    return {registro, figura, raiz, capturador: ventana.scalaris.capturaPdf, configuracion};
}

for (const tipo of ['scatter', 'scatter3d', 'surface']) {
    prueba(`Plotly ${tipo} conserva trazas, rangos y cámara sin html2canvas ni mutación original`, async () => {
        const escenario = prepararEscenario({tipo});
        const original = JSON.stringify(escenario.figura);
        const respuesta = await escenario.capturador.capturar('raiz', escenario.configuracion);
        const {registro} = escenario;
        afirmar.equal(respuesta.capturas[0].clave, 'visualizador-figura');
        afirmar.equal(registro.lienzos, 0);
        afirmar.equal(registro.datos[0].x[1], 7);
        afirmar.equal(registro.datos[0].visible, 'legendonly');
        afirmar.equal(registro.datos[0].marker.color, 'rojo');
        afirmar.equal(registro.disposicion.font.color, 'negro');
        afirmar.equal(registro.disposicion.paper_bgcolor, 'white');
        afirmar.deepEqual(registro.disposicion.xaxis.range, [-3, 7]);
        afirmar.equal(registro.disposicion.scene.camera.eye.x, 3);
        afirmar.equal(registro.ajustes.width, 400);
        afirmar.equal(registro.ajustes.height, 200);
        afirmar.equal(JSON.stringify(escenario.figura), original);
        afirmar.equal(registro.purgas, 1);
        afirmar.equal(registro.retiradas, 1);
        afirmar.equal(escenario.raiz.inert, false);
    });
}

for (const fallo of ['fallarMontaje', 'fallarImagen', 'sinFigura', 'sinBiblioteca']) {
    prueba(`el fallo ${fallo} rechaza captura y libera la raíz`, async () => {
        const escenario = prepararEscenario({[fallo]: true});
        const respuesta = await escenario.capturador.capturar('raiz', escenario.configuracion);
        afirmar.equal(respuesta.error, 'captura');
        afirmar.equal(escenario.raiz.inert, false);
        afirmar.equal(escenario.registro.lienzos, 0);
        if (fallo.startsWith('fallar')) afirmar.equal(escenario.registro.retiradas, 1);
    });
}

prueba('el plazo purga de inmediato un montaje pendiente y descarta su resultado tardío', async () => {
    let completar;
    const esperarMontaje = new Promise(resolver => { completar = resolver; });
    const escenario = prepararEscenario({esperarMontaje});
    escenario.configuracion.plazoCaptura = 0.01;
    const respuesta = await escenario.capturador.capturar('raiz', escenario.configuracion);
    afirmar.equal(respuesta.error, 'captura');
    afirmar.equal(escenario.registro.purgas, 1);
    afirmar.equal(escenario.registro.retiradas, 1);
    afirmar.equal(escenario.raiz.inert, false);
    completar();
    await new Promise(resolver => setImmediate(resolver));
    afirmar.equal(escenario.registro.ajustes, undefined);
});

prueba('las dimensiones y el peso gráfico respetan los límites del transporte compartido', async () => {
    const escenario = prepararEscenario();
    escenario.configuracion.maximoLado = 100;
    escenario.configuracion.maximoPixeles = 1000;
    const respuesta = await escenario.capturador.capturar('raiz', escenario.configuracion);
    afirmar.equal(respuesta.capturas.length, 1);
    afirmar.ok(escenario.registro.ajustes.width <= 100);
    afirmar.ok(escenario.registro.ajustes.width * escenario.registro.ajustes.height <= 1000);
    escenario.configuracion.maximoBytesImagen = 1;
    const excesiva = prepararEscenario({imagen: 'data:image/png;base64,AAAAAAAA'});
    excesiva.configuracion.maximoBytesImagen = 1;
    afirmar.equal((await excesiva.capturador.capturar('raiz', excesiva.configuracion)).error, 'captura');
    afirmar.equal(excesiva.registro.retiradas, 1);
});
