'use strict';
const prueba = require('node:test');
const afirmar = require('node:assert/strict');
const { cargarAssetCliente } = require('./comun_cliente_javascript.js');
const { crearClienteNumerico, crearCeldaNumerica, insertar } = require('./comun_entrada_numerica.js');

prueba('la captura conserva los literales Unicode de números exactos al teclear y pegar', () => {
    const cliente = crearClienteNumerico();
    const entrada = crearCeldaNumerica(cliente);
    for (const literal of ['−3÷5', '2⁄3', '3∕4', '⅞', '↉', '12.5‰']) {
        afirmar.equal(insertar(cliente, entrada, literal).bloqueado, false);
        afirmar.equal(insertar(cliente, entrada, literal, { inputType: 'insertFromPaste' }).bloqueado, false);
        afirmar.equal(cliente.ventana.scalaris.entradaNumerica.prepararValor(entrada, literal), literal);
    }
    afirmar.equal(insertar(cliente, entrada, 'α').bloqueado, true);
});

prueba('cada perfil ofrece la sintaxis que admite su captura', () => {
    const { ventana, contexto } = crearClienteNumerico();
    cargarAssetCliente('catalogo_simbolos.js', contexto);
    const { catalogoSimbolos, perfilesSimbolos } = ventana.scalaris;
    const esperados = {
        numero: new Map([['÷', '/'], ['‰', '‰']]),
        ecuacion: new Map(Array.from('×·⋅∙₀₁₂₃₄₅₆₇₈₉απΩ‰', simbolo => [simbolo, simbolo])),
        base: new Map([['−', '-']]),
    };
    for (const [tipo, inserciones] of Object.entries(esperados)) {
        const disponibles = perfilesSimbolos.simbolosDisponibles(catalogoSimbolos, [tipo]);
        const porSimbolo = new Map(disponibles.map(entrada => [entrada.simbolo, entrada]));
        for (const [simbolo, texto] of inserciones) {
            afirmar.equal(perfilesSimbolos.textoInsercion(porSimbolo.get(simbolo), { tipo }), texto);
        }
        afirmar.equal(porSimbolo.has('√'), false);
        afirmar.equal(porSimbolo.has('²'), false);
    }
});
