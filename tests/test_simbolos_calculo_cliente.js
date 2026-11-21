'use strict';

const prueba = require('node:test');
const afirmar = require('node:assert/strict');
const { cargarAssetCliente } = require('./comun_cliente_javascript.js');
const { crearClienteNumerico } = require('./comun_entrada_numerica.js');

prueba('ofrece cálculos acotados en funciones y solo constantes en reales', () => {
    const { ventana, contexto } = crearClienteNumerico();
    cargarAssetCliente('catalogo_simbolos.js', contexto);
    const { catalogoSimbolos, perfilesSimbolos } = ventana.scalaris;
    const para = tipo => new Map(perfilesSimbolos.simbolosDisponibles(catalogoSimbolos, [tipo]).map(entrada =>
        [entrada.simbolo, perfilesSimbolos.textoInsercion(entrada, { tipo })]));
    const funciones = para('funcion');
    afirmar.equal(funciones.get('∑'), '∑(i,1,3,i×x)');
    afirmar.equal(funciones.get('∏'), '∏(i,1,3,i×x)');
    for (const simbolo of '°‰′″') afirmar.equal(funciones.get(simbolo), simbolo);
    const reales = para('real');
    for (const simbolo of '×·⋅∙÷⁄∕¼πℯ°‰²') afirmar.equal(reales.get(simbolo), simbolo);
    afirmar.equal(reales.get('√'), '√()');
    for (const simbolo of '∑∏′″∫∞') afirmar.equal(reales.has(simbolo), false);
    afirmar.equal(funciones.get('∫'), '∫(t,t,0,x)');
    afirmar.equal(funciones.get('∞'), '∞');
});
