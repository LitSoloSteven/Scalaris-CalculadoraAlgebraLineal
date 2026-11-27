/** Aviso accesible y animación reiniciable para caracteres rechazados. */
'use strict';
{
    window.scalaris = window.scalaris || {};
    const animaciones = new WeakMap();
    const identificadorAviso = 'captura-aviso-numerico';
    let entradaRechazada = null;
    let temporizador = null;

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

    function vincularDescriptor(entrada) {
        if (!entrada?.setAttribute) return;
        if (entradaRechazada && entradaRechazada !== entrada) limpiarDescriptor(entradaRechazada);
        entradaRechazada = entrada;
        entrada.setAttribute('aria-invalid', 'true');
        entrada.setAttribute('data-rechazo-activo', 'true');
        const actual = (entrada.getAttribute?.('aria-describedby') || '').split(/\s+/).filter(Boolean);
        if (!actual.includes(identificadorAviso)) actual.push(identificadorAviso);
        entrada.setAttribute('aria-describedby', actual.join(' '));
    }

    function limpiarDescriptor(entrada) {
        if (!entrada?.getAttribute) return;
        if (entrada.getAttribute('data-rechazo-activo') === 'true') {
            entrada.removeAttribute?.('aria-invalid');
            entrada.removeAttribute?.('data-rechazo-activo');
        }
        const restantes = (entrada.getAttribute('aria-describedby') || '')
            .split(/\s+/).filter(id => id && id !== identificadorAviso);
        if (restantes.length) entrada.setAttribute?.('aria-describedby', restantes.join(' '));
        else entrada.removeAttribute?.('aria-describedby');
    }

    function limpiar() {
        if (temporizador) {
            clearTimeout(temporizador);
            temporizador = null;
        }
        const aviso = document.getElementById(identificadorAviso);
        if (aviso) aviso.textContent = '';
        if (entradaRechazada) {
            limpiarDescriptor(entradaRechazada);
            entradaRechazada = null;
        }
    }

    function rechazar(entrada, mensaje, animar) {
        if (temporizador) clearTimeout(temporizador);
        anunciar(mensaje);
        vincularDescriptor(entrada);
        temporizador = setTimeout(limpiar, 6000);
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
        document.addEventListener('click', evento => {
            if (evento.target?.closest?.('[role="tab"], [role="radio"], [role="option"], .selector-opciones-boton')) limpiar();
        });
        window.scalaris.rechazoNumerico = { rechazar, limpiar };
    }
    registrarRechazoNumerico();
}
