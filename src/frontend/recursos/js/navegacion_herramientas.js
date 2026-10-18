/** Mantiene visibles el enlace activo y el enfocado dentro de su lista horizontal. */
{
    'use strict';
    const listas = new WeakSet();

    function actualizarBordes(lista) {
        const centro = lista.closest('.navegacion-centro');
        centro.toggleAttribute('data-opciones-antes', lista.scrollLeft > 12);
        centro.toggleAttribute('data-opciones-despues', lista.scrollLeft + lista.clientWidth < lista.scrollWidth - 12);
    }

    function mostrarEnlace(enlace) {
        const lista = enlace?.closest('.navegacion-elementos');
        if (!lista) return;
        const limite = lista.getBoundingClientRect();
        const caja = enlace.getBoundingClientRect();
        const margen = 8;
        if (caja.right - caja.left > lista.clientWidth - 2 * margen || caja.left < limite.left + margen) {
            lista.scrollLeft += caja.left - limite.left - margen;
        }
        else if (caja.right > limite.right - margen) lista.scrollLeft += caja.right - limite.right + margen;
        actualizarBordes(lista);
    }

    function centrarActivo() {
        mostrarEnlace(document.querySelector('.navegacion-elementos [aria-current="page"]'));
    }

    function prepararLista(lista) {
        if (listas.has(lista)) return;
        listas.add(lista);
        lista.addEventListener('scroll', () => actualizarBordes(lista), { passive: true });
        const observador = new ResizeObserver(() => {
            mostrarEnlace(lista.querySelector('[aria-current="page"]'));
            actualizarBordes(lista);
        });
        observador.observe(lista);
        document.fonts.ready.then(centrarActivo);
        centrarActivo();
    }

    function prepararListas() {
        document.querySelectorAll('.navegacion-elementos').forEach(prepararLista);
    }

    document.addEventListener('focusin', evento => mostrarEnlace(evento.target.closest?.('.navegacion-elemento')));
    const observador = new MutationObserver(prepararListas);
    observador.observe(document.documentElement, { childList: true, subtree: true });
    window.scalaris.navegacion = { centrarActivo };
    prepararListas();
}
