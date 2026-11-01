'use strict';
const { test } = require('node:test');
const comprobar = require('node:assert/strict');
const { prepararSintesis } = require('./comun_sintesis_sonora.js');

function finalizar(nodos) {
    nodos.forEach(nodo => nodo.onended?.());
    comprobar.ok(nodos.every(nodo => nodo.desconectado));
}

test('todos los perfiles programan notas y filtros dentro de sus limites reales', () => {
    const caso = prepararSintesis();
    caso.activar();
    const contexto = caso.contextos[0];
    for (const [nombre, perfil] of Object.entries(caso.ventana.scalaris.catalogoSonidos.perfiles)) {
        const cantidad = contexto.nodos.length;
        comprobar.equal(caso.motor.reproducir(nombre), true, nombre);
        const nodos = contexto.nodos.slice(cantidad);
        const fuentes = nodos.filter(nodo => nodo.onended);
        comprobar.equal(Math.round((Math.max(...fuentes.map(nodo => nodo.fin)) - contexto.currentTime) * 1000),
            Math.round(perfil.duracion * 1000), nombre);
        for (const nodo of nodos.filter(nodo => nodo.tipo === 'tono' || nodo.tipo === 'filtro')) {
            const maximo = nodo.tipo === 'tono' ? 330 : 2500;
            comprobar.ok(nodo.frequency.valores.every(([valor]) => valor >= 90 && valor <= maximo), nombre);
        }
        comprobar.equal(nodos.filter(nodo => nodo.tipo === 'tono').length, 1 + (perfil.notas?.length || 0));
        finalizar(nodos);
        caso.avanzar(500);
    }
});

test('la variacion mecanica cambia tono y ganancia sin salir de cuatro por ciento y 1.5 dB', () => {
    const caso = prepararSintesis();
    caso.activar();
    const contexto = caso.contextos[0];
    const perfil = caso.ventana.scalaris.catalogoSonidos.perfiles.escritura;
    const tonos = new Set();
    const ganancias = new Set();
    for (let indice = 0; indice < 12; indice++) {
        const cantidad = contexto.nodos.length;
        caso.motor.reproducir('escritura');
        const nodos = contexto.nodos.slice(cantidad);
        const tono = nodos.find(nodo => nodo.tipo === 'tono').frequency.valores[0][0];
        const ganancia = nodos.find(nodo => nodo.tipo === 'ganancia').gain.valores[1][0];
        const base = 0.075 * perfil.volumen * (1 - perfil.ruido);
        comprobar.ok(tono >= perfil.inicio * 0.96 && tono <= perfil.inicio * 1.04);
        comprobar.ok(Math.abs(20 * Math.log10(ganancia / base)) <= 1.5);
        tonos.add(tono);
        ganancias.add(ganancia);
        finalizar(nodos);
        caso.avanzar(100);
    }
    comprobar.ok(tonos.size > 1);
    comprobar.ok(ganancias.size > 1);
});
