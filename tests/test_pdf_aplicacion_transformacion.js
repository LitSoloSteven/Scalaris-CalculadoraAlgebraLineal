'use strict';
const afirmar = require('node:assert/strict');
const prueba = require('node:test');
const maquinaVirtual = require('node:vm');
const {cargarCapturadorPdf} = require('./comun_capturador_pdf.js');

function crearEntorno(figura, registro) {
    const temporal = {style: {}, dataset: {}, setAttribute() {}, remove() { registro.retirado = true; }};
    const region = {dataset: {pdfCaptura: 'transformaciones-grafica-1', pdfMotor: 'plotly'},
        querySelector: () => figura, getClientRects: () => [{}]};
    const documento = {getElementById: () => ({inert: false, querySelectorAll: () => [region]}),
        querySelectorAll: () => [], createElement: () => temporal,
        body: {appendChild() {}}, fonts: {ready: Promise.resolve()}};
    const ventana = {MathJax: {typesetPromise: async () => {}}, html2canvas() {},
        Plotly: {async newPlot(nodo, datos) { registro.datos = datos; },
            async toImage() { return 'data:image/png;base64,AAAA'; }, purge() {}},
        scalaris: {graficos: {texto: {papel: 'negro'}, cuadricula: {papel: 'gris'}}}};
    cargarCapturadorPdf(maquinaVirtual.createContext({window: ventana, document: documento, setTimeout, clearTimeout}));
    return ventana.scalaris.capturaPdf;
}

for (const tipo of ['scatter', 'scatter3d']) {
    prueba(`el PDF de ${tipo} conserva el resultado final y omite la proyección activa`, async () => {
        const figura = {data: [{type: tipo, name: 'Transformado', x: [0, 4 / 3]},
            {type: tipo, name: 'Componente activa', visible: true, x: [4 / 3],
                meta: {scalaris_proyeccion: [4 / 3, 3 / 2]}}],
        layout: {}, _fullLayout: {}, getBoundingClientRect: () => ({width: 200, height: 100})};
        const original = JSON.stringify(figura);
        const registro = {};
        const capturador = crearEntorno(figura, registro);
        const respuesta = await capturador.capturar('raiz', {maximoFiguras: 12,
            maximoBytesImagen: 1024, maximoBytesTotal: 2048, maximoLado: 4096,
            maximoPixeles: 12000000, plazoMathjax: 1, plazoCaptura: 1, escala: 2});
        afirmar.equal(respuesta.capturas[0].clave, 'transformaciones-grafica-1');
        afirmar.equal(registro.datos.length, 1);
        afirmar.equal(registro.datos[0].x[1], 4 / 3);
        afirmar.equal(JSON.stringify(figura), original);
        afirmar.equal(registro.retirado, true);
    });
}
