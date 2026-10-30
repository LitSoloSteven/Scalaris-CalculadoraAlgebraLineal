'use strict';
const prueba = require('node:test');
const afirmar = require('node:assert/strict');
const { crearRevelado, insertarRespuesta } = require('./comun_revelado_glosa.js');

prueba('el revelado conserva nodos y texto hostil, ocupa hasta cuatro segundos y limpia estado', () => {
    const cliente = crearRevelado();
    const textos = ['A'.repeat(500), '<img src=x onerror=alert(1)>', 'Código\n'.repeat(100)];
    const { contenido, bitacora, respuesta, burbuja } = insertarRespuesta(cliente, textos);
    const nodos = [...contenido.nodos];
    afirmar.equal(contenido.nodos[0].textContent, 'A');
    afirmar.equal(contenido.nodos[1].textContent, '');
    afirmar.equal(bitacora.getAttribute('aria-busy'), 'true');
    afirmar.equal(respuesta.getAttribute('data-escritura-estado'), 'activo');
    for (let indice = 0; indice < cliente.tareas.length; indice++) cliente.avanzar(cliente.tareas[indice]);
    afirmar.equal(cliente.tiempo(), 4000);
    afirmar.ok(cliente.tareas.length <= 54);
    afirmar.deepEqual(contenido.nodos.map(nodo => nodo.textContent), textos);
    afirmar.deepEqual(contenido.nodos, nodos);
    afirmar.equal(bitacora.getAttribute('aria-busy'), undefined);
    afirmar.equal(respuesta.getAttribute('data-escritura-estado'), undefined);
    afirmar.equal(bitacora.scrollTop, 1000);
    afirmar.equal(burbuja.eventos.size, 0);
});

prueba('clic y callbacks ya en cola no reanudan el texto ni conservan listeners', () => {
    const cliente = crearRevelado();
    const respuesta = insertarRespuesta(cliente, ['Texto completo']);
    respuesta.burbuja.eventos.get('click')();
    afirmar.equal(cliente.tareas[0].cancelada, true);
    cliente.avanzar(cliente.tareas[0]);
    afirmar.equal(respuesta.contenido.nodos[0].textContent, 'Texto completo');
    afirmar.equal(respuesta.burbuja.eventos.size, 0);
});

prueba('una respuesta nueva completa la anterior sin interferir con su aria-busy', () => {
    const cliente = crearRevelado();
    const anterior = insertarRespuesta(cliente, ['Respuesta anterior']);
    const nueva = insertarRespuesta(cliente, ['Respuesta nueva'], anterior.bitacora);
    afirmar.equal(anterior.contenido.nodos[0].textContent, 'Respuesta anterior');
    afirmar.equal(anterior.burbuja.eventos.size, 0);
    cliente.avanzar(cliente.tareas[0]);
    afirmar.equal(nueva.bitacora.getAttribute('aria-busy'), 'true');
    nueva.burbuja.eventos.get('click')();
    afirmar.equal(nueva.bitacora.getAttribute('aria-busy'), undefined);
});

prueba('el borrado restaura los nodos desconectados y retira el temporizador', () => {
    const cliente = crearRevelado();
    const respuesta = insertarRespuesta(cliente, ['Borrada']);
    respuesta.contenido.isConnected = false;
    cliente.observar([{ addedNodes: [] }]);
    afirmar.equal(cliente.tareas[0].cancelada, true);
    afirmar.equal(respuesta.bitacora.getAttribute('aria-busy'), undefined);
    afirmar.equal(respuesta.burbuja.eventos.size, 0);
});

for (const modo of ['reducido', 'teclado', 'vacio']) {
    prueba(`el modo ${modo} completa sin programar tareas`, () => {
        const cliente = crearRevelado();
        if (modo === 'reducido') cliente.ventana.matchMedia = () => ({ matches: true });
        if (modo === 'teclado') cliente.raiz.setAttribute('data-entrada', 'teclado');
        const texto = modo === 'vacio' ? '' : 'Contenido inmediato';
        const respuesta = insertarRespuesta(cliente, [texto]);
        afirmar.equal(respuesta.contenido.nodos[0].textContent, texto);
        afirmar.equal(cliente.tareas.length, 0);
        afirmar.equal(respuesta.bitacora.getAttribute('aria-busy'), undefined);
    });
}

prueba('el ritmo proporcional conserva caracteres fuera del BMP', () => {
    const cliente = crearRevelado();
    const respuesta = insertarRespuesta(cliente, ['\uD83D\uDE00Texto']);
    afirmar.equal(respuesta.contenido.nodos[0].textContent, '');
    for (let indice = 0; indice < cliente.tareas.length; indice++) cliente.avanzar(cliente.tareas[indice]);
    afirmar.ok(cliente.tiempo() <= 84 && cliente.tiempo() >= 72);
    afirmar.equal(respuesta.contenido.nodos[0].textContent, '\uD83D\uDE00Texto');
});
