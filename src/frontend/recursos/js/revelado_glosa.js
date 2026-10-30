/** Vincula respuestas escapadas al motor de revelado sin temporizadores de servidor. */
{
    'use strict';
    const selector = '[data-escritura-pendiente]';

    function revelar(contenido) {
        contenido.removeAttribute('data-escritura-pendiente');
        const bitacora = contenido.closest('[role="log"]');
        const respuesta = contenido.closest('.glosa-respuesta');
        const burbuja = contenido.closest('.glosa-burbuja-asistente') || contenido;
        window.scalaris.escritura.cancelarEn(bitacora);
        const recorrido = document.createTreeWalker(contenido, NodeFilter.SHOW_TEXT);
        const fragmentos = [];
        while (recorrido.nextNode()) {
            fragmentos.push({ nodo: recorrido.currentNode, texto: recorrido.currentNode.textContent });
        }
        window.scalaris.escritura.revelar(contenido, fragmentos, {
            bitacora, respuesta, burbuja,
            duracion: window.scalaris.movimiento.duracion('--escritura-revelado-maximo'),
            velocidad: window.scalaris.movimiento.duracion('--escritura-caracter'),
        });
    }

    function buscar(raiz) {
        if (raiz.nodeType !== 1) return;
        procesar(raiz);
        raiz.querySelectorAll('[data-glosa-respuesta], ' + selector).forEach(procesar);
    }

    function procesar(nodo) {
        if (nodo.matches('[data-glosa-respuesta]')) {
            window.scalaris.escritura.cancelarEn(nodo.closest('[role="log"]'));
        }
        if (nodo.matches(selector)) revelar(nodo);
    }

    function registrarReveladoGlosa() {
        const observador = new MutationObserver(function actualizar(mutaciones) {
            window.scalaris.escritura.retirarDesconectados();
            mutaciones.forEach(mutacion => mutacion.addedNodes.forEach(buscar));
        });
        observador.observe(document.documentElement, { childList: true, subtree: true });
        document.querySelectorAll(selector).forEach(revelar);
    }
    registrarReveladoGlosa();
}
