/** Sincroniza las opciones de tema cuando el menú se monta o cambia la paleta. */
{
    const selectorOpcion = '[data-tema-opcion]';
    const selectorMenuConfiguracion = '[data-menu-temas-configuracion]';

    function seleccionarTema(evento) {
        const opcion = evento.target.closest?.(selectorOpcion);
        if (!opcion || evento.defaultPrevented || evento.button !== 0) return;
        const caja = opcion.getBoundingClientRect();
        const origen = evento.detail === 0 ? { x: caja.left + caja.width / 2, y: caja.top + caja.height / 2 } :
            { x: evento.clientX, y: evento.clientY };
        window.scalaris.tema.establecer(opcion.getAttribute('data-tema-opcion'), origen);
    }

    function moverFocoTema(evento) {
        if (!['ArrowUp', 'ArrowDown', 'Home', 'End'].includes(evento?.key) || evento.defaultPrevented) return;
        const origen = evento.target?.closest?.(selectorOpcion);
        const menu = origen?.closest(selectorMenuConfiguracion);
        if (!menu) return;
        const opciones = Array.from(menu.querySelectorAll(selectorOpcion));
        const paso = evento.key === 'ArrowUp' ? -1 : 1;
        let indice = (opciones.indexOf(origen) + paso + opciones.length) % opciones.length;
        if (evento.key === 'Home') indice = 0;
        if (evento.key === 'End') indice = opciones.length - 1;
        evento.preventDefault();
        opciones.forEach((opcion, posicion) => { opcion.tabIndex = posicion === indice ? 0 : -1; });
        opciones[indice].focus();
    }

    document.addEventListener('click', seleccionarTema, true);
    document.addEventListener('keydown', moverFocoTema);
    function sincronizarSelectorTema() {
        const seleccionado = document.documentElement.getAttribute('data-tema');
        const tema = ['papel', 'marea', 'medianoche'].includes(seleccionado) ? seleccionado : 'papel';
        document.querySelectorAll(selectorOpcion).forEach(opcion => {
            const seleccionada = opcion.getAttribute('data-tema-opcion') === tema;
            opcion.setAttribute('aria-checked', String(seleccionada));
            const menu = opcion.closest?.(selectorMenuConfiguracion);
            if (menu) {
                const foco = document.activeElement?.closest(selectorOpcion);
                const tabulable = menu.contains(foco) ? opcion === foco : seleccionada;
                opcion.tabIndex = tabulable ? 0 : -1;
            }
        });
    }

    const observador = new MutationObserver(mutaciones => {
        if (window.scalaris.observacion &&
            !window.scalaris.observacion.contiene(mutaciones, selectorOpcion)) return;
        sincronizarSelectorTema();
    });
    observador.observe(document.documentElement, {
        childList: true, subtree: true, attributes: true, attributeFilter: ['data-tema']
    });
    sincronizarSelectorTema();
}
