/** Detecta recursos montados mediante consultas al subárbol insertado. */
{
    'use strict';
    window.scalaris = window.scalaris || {};

    function contieneNodo(nodo, selector) {
        return nodo.nodeType === 1 && (nodo.matches(selector) || Boolean(nodo.querySelector(selector)));
    }

    /** Indica si los registros afectan al selector o al atributo de tema de la raíz. */
    function contiene(mutaciones, selector) {
        if (!mutaciones) return true;
        return mutaciones.some(mutacion => {
            if (mutacion.type === 'attributes') return mutacion.target === document.documentElement;
            return Boolean(mutacion.target.matches?.(selector)) ||
                Array.from(mutacion.addedNodes).some(nodo => contieneNodo(nodo, selector));
        });
    }

    window.scalaris.observacion = { contiene };
}
