/** Sincroniza las opciones de tema cuando el menú se monta o cambia la paleta. */
{
    function seleccionarTema(evento) {
        const opcion = evento.target.closest?.('[data-tema-opcion]');
        if (!opcion || evento.defaultPrevented || evento.button !== 0) return;
        const caja = opcion.getBoundingClientRect();
        const origen = evento.detail === 0 ? { x: caja.left + caja.width / 2, y: caja.top + caja.height / 2 } :
            { x: evento.clientX, y: evento.clientY };
        window.scalaris.tema.establecer(opcion.getAttribute('data-tema-opcion'), origen);
    }

    document.addEventListener('click', seleccionarTema, true);
    function sincronizarSelectorTema() {
        const seleccionado = document.documentElement.getAttribute('data-tema');
        const tema = ['papel', 'marea', 'medianoche'].includes(seleccionado) ? seleccionado : 'papel';
        document.querySelectorAll('[data-tema-opcion]').forEach(opcion => {
            opcion.setAttribute('aria-checked', String(opcion.getAttribute('data-tema-opcion') === tema));
        });
    }

    const observador = new MutationObserver(sincronizarSelectorTema);
    observador.observe(document.documentElement, {
        childList: true, subtree: true, attributes: true, attributeFilter: ['data-tema']
    });
    sincronizarSelectorTema();
}
