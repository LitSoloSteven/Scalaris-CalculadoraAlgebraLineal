/** Aviso accesible y animación reiniciable para caracteres rechazados. */
'use strict';
{
    window.scalaris = window.scalaris || {};
    const animaciones = new WeakMap();
    const identificadorAviso = 'captura-aviso-numerico';

    function prepararAviso() {
        let aviso = document.getElementById(identificadorAviso);
        if (aviso || !document.body) return aviso;
        aviso = document.createElement('div');
        aviso.id = identificadorAviso;
        aviso.className = 'captura-aviso-numerico';
        aviso.setAttribute('role', 'status');
        aviso.setAttribute('aria-live', 'polite');
        aviso.setAttribute('aria-atomic', 'true');
        document.body.appendChild(aviso);
        return aviso;
    }

    function anunciar(mensaje) {
        const aviso = prepararAviso();
        if (aviso) aviso.replaceChildren(document.createTextNode(mensaje));
    }

    function limpiar() {
        const aviso = document.getElementById(identificadorAviso);
        if (aviso) aviso.textContent = '';
    }

    function rechazar(entrada, mensaje, animar) {
        anunciar(mensaje);
        window.scalaris.eventosSonoros?.rechazo();
        if (!animar) return;
        const control = entrada.closest('.q-field__control');
        if (!control) return;
        const reducido = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        const nombre = reducido ? 'rechazoNumericoOpacidad' : 'sacudida';
        let animacion = animaciones.get(control);
        if (animacion?.animationName !== nombre) {
            animacion?.cancel();
            control.classList.toggle('movimiento-sacudida', !reducido);
            control.classList.toggle('captura-rechazo-reducido', reducido);
            animacion = control.getAnimations().find(candidata => candidata.animationName === nombre);
            if (animacion) animaciones.set(control, animacion);
        }
        if (animacion) {
            animacion.cancel();
            animacion.play();
        }
    }

    function registrarRechazoNumerico() {
        if (document.body) prepararAviso();
        else document.addEventListener('DOMContentLoaded', prepararAviso, { once: true });
        window.scalaris.rechazoNumerico = { rechazar, limpiar };
    }
    registrarRechazoNumerico();
}
