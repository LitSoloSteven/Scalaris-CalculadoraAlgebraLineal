"use strict";
const afirmar = require('node:assert/strict');
const prueba = require('node:test');
const { crearObservador, mutacionEntrada, medirConsultas } = require('./comun_optimizacion_observadores.js');

for (const nombre of ['selector_tema.js', 'navegacion_herramientas.js', 'sincronizacion_diseno.js']) {
    prueba(`${nombre} omite búsquedas globales al insertar cien entradas`, () => {
        afirmar.equal(medirConsultas(nombre), 0);
    });
    prueba(`${nombre} reconoce recursos insertados en un subárbol`, () => {
        const cliente = crearObservador(nombre);
        cliente.contadores.consultas = 0;
        const mutacion = mutacionEntrada();
        mutacion.addedNodes[0].querySelector = () => ({});
        cliente.observadores[0]([mutacion]);
        cliente.fotogramas.splice(0).forEach(funcion => funcion());
        afirmar.equal(cliente.contadores.consultas, 1);
    });
}

prueba('el selector actualiza inmediatamente los cambios de tema de la raíz', () => {
    const cliente = crearObservador('selector_tema.js');
    cliente.contadores.consultas = 0;
    cliente.observadores[0]([{ type: 'attributes', target: cliente.raiz }]);
    afirmar.equal(cliente.contadores.consultas, 1);
    afirmar.equal(cliente.fotogramas.length, 0);
});

prueba('el filtro ignora nodos de texto y admite elementos añadidos sin descendientes', () => {
    const cliente = crearObservador('selector_tema.js');
    const mutacion = mutacionEntrada();
    mutacion.addedNodes = [{ nodeType: 3 }, { nodeType: 1, matches: () => true }];
    afirmar.equal(cliente.contexto.window.scalaris.observacion.contiene([mutacion], 'opcion'), true);
    mutacion.addedNodes.pop();
    afirmar.equal(cliente.contexto.window.scalaris.observacion.contiene([mutacion], 'opcion'), false);
});

prueba('los gráficos agrupan inserciones relevantes en un único fotograma', () => {
    const cliente = crearObservador('sincronizacion_diseno.js');
    const mutacion = mutacionEntrada();
    mutacion.target.matches = () => true;
    for (let indice = 0; indice < 100; indice++) cliente.observadores[0]([mutacion]);
    afirmar.equal(cliente.fotogramas.length, 1);
});
