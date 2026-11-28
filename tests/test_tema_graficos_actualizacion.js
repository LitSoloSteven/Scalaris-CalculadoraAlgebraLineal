"use strict";

const prueba = require("node:test");
const afirmar = require("node:assert/strict");
const {createContext} = require("node:vm");
const {cargarAssetCliente} = require("./comun_cliente_javascript.js");

prueba("Plotly recolorea ejes y trazas juntas y omite posiciones sin rol", async () => {
    const figura = {isConnected: true, _fullLayout: {}, data: [
        {meta: {scalaris_colores: {"line.color": "serie:0"}}},
        {meta: {scalaris_colores: {colorscale: "solucion"}}},
        {line: {color: "propio"}},
    ]};
    const graficos = {paletas: {marea: ["serie"]}, texto: {marea: "texto"},
        cuadricula: {marea: "cuadricula"}, solucion: {marea: "solucion"}};
    const llamadas = [];
    const window = {scalaris: {graficos}, Plotly: {
        update: async (...args) => llamadas.push(args),
        relayout: () => afirmar.fail("Redibujo separado de ejes"),
        restyle: () => afirmar.fail("Redibujo separado de trazas"),
    }};
    const document = {querySelectorAll: () => [figura]};
    cargarAssetCliente("nucleo/tema/tema_graficos.js", createContext({window, document}));

    await window.scalaris.actualizarTemaPlotly("marea");

    afirmar.equal(llamadas.length, 1);
    const [nodo, trazas, ejes] = llamadas[0];
    afirmar.equal(nodo, figura);
    afirmar.deepEqual(Array.from(trazas["line.color"]), ["serie", undefined, undefined]);
    afirmar.equal(trazas.colorscale[0], undefined);
    afirmar.equal(trazas.colorscale[2], undefined);
    afirmar.equal(JSON.stringify(trazas.colorscale[1]), '[[0,"solucion"],[1,"solucion"]]');
    afirmar.equal(ejes["xaxis.color"], "texto");
    afirmar.equal(ejes["scene.zaxis.gridcolor"], "cuadricula");
});
