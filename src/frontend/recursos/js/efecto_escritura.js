/** Pulsa la superficie del campo solo ante inserciones físicas de texto. */
(function registrarEfectoEscritura() {
    'use strict';
    const animaciones = new WeakMap();
    const campos = '.matriz-entrada, .glosa-entrada, .glosa-campo-entrada';
    window.scalaris.efectoEscritura?.desmontar();

    function pulsar(evento) {
        if (!evento.isTrusted || evento.inputType !== 'insertText' || !evento.data) return;
        const entrada = evento.target;
        if (!entrada.matches?.('input, textarea') || entrada.disabled || entrada.readOnly) return;
        const campo = entrada.closest(campos);
        const superficie = campo?.querySelector('.q-field__control');
        if (!superficie) return;
        superficie.classList.add('escritura-activa');
        let animacion = animaciones.get(superficie);
        if (!animacion) {
            animacion = superficie.getAnimations({ subtree: true }).find(
                candidata => candidata.animationName === 'escrituraPulso');
            if (animacion) animaciones.set(superficie, animacion);
        }
        if (animacion) {
            animacion.cancel();
            animacion.play();
        }
    }

    document.addEventListener('input', pulsar, { passive: true });
    window.scalaris.efectoEscritura = {
        desmontar: () => document.removeEventListener('input', pulsar),
    };
})();
