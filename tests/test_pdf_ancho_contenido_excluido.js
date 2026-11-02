'use strict';
const afirmar = require('node:assert/strict');
const prueba = require('node:test');
const maquinaVirtual = require('node:vm');
const {cargarCapturadorPdf} = require('./comun_capturador_pdf.js');

prueba('un descendiente excluido no reduce el contenido documental al ampliar el ancho', async () => {
    const visible = {scrollWidth: 400, closest: () => null};
    const excluido = {scrollWidth: 9000, closest: () => ({})};
    const region = {dataset: {pdfCaptura: 'transformaciones-resumen'}, scrollWidth: 400, scrollHeight: 200,
        querySelectorAll: () => [visible, excluido], getClientRects: () => [{}],
        getBoundingClientRect: () => ({width: 400, height: 200})};
    const documento = {getElementById: () => ({inert: false, querySelectorAll: () => [region]}),
        querySelectorAll: () => [], fonts: {ready: Promise.resolve()}};
    const medidas = [];
    const ventana = {MathJax: {typesetPromise: async () => {}},
        html2canvas: async (nodo, opciones) => {
            medidas.push(opciones.width);
            return {width: 400, height: 200, toDataURL: () => 'data:image/png;base64,AAAA'};
        }};
    cargarCapturadorPdf(maquinaVirtual.createContext({window: ventana, document: documento, setTimeout, clearTimeout}));
    const respuesta = await ventana.scalaris.capturaPdf.capturar('raiz', {maximoFiguras: 12,
        maximoBytesImagen: 1024, maximoBytesTotal: 2048, maximoLado: 4096,
        maximoPixeles: 12000000, plazoMathjax: 1, plazoCaptura: 1, escala: 2});
    afirmar.equal(respuesta.capturas.length, 1);
    afirmar.deepEqual(medidas, [400]);
});
