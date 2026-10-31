/** Mantiene el silencio compartido por controles, recargas y pestañas. */
{
    'use strict';
    window.scalaris = window.scalaris || {};
    window.scalaris.preferenciaSonido?.destruir();
    const clave = window.scalaris.catalogoSonidos.claveSilencio;
    const selector = '[data-sonido-control]';
    let silenciado = false;

    function sincronizarControles() {
        document.querySelectorAll(selector).forEach(boton => {
            boton.setAttribute('aria-pressed', String(silenciado));
            boton.setAttribute('title', silenciado ? 'Activar sonidos' : 'Silenciar sonidos');
            boton.querySelectorAll('[data-sonido-icono]').forEach(icono => {
                icono.hidden = (icono.getAttribute('data-sonido-icono') === 'activo') === silenciado;
            });
        });
    }

    function aplicarSilencio(valor) {
        silenciado = valor;
        window.scalaris.sonido.silenciar(silenciado);
        sincronizarControles();
    }

    function leerPreferencia() {
        try { aplicarSilencio(localStorage.getItem(clave) === 'true'); }
        catch (_) { sincronizarControles(); }
    }

    function alternarPorGesto(evento) {
        if (!evento.isTrusted || evento.defaultPrevented || evento.button !== 0) return;
        const boton = evento.target.closest?.(selector);
        if (!boton || boton.disabled || boton.getAttribute('aria-disabled') === 'true') return;
        aplicarSilencio(!silenciado);
        try { localStorage.setItem(clave, String(silenciado)); }
        catch (_) { /* El control sigue funcionando durante esta visita sin almacenamiento. */ }
    }

    function recibirPreferencia(evento) {
        if (evento.key === clave || evento.key === null) aplicarSilencio(evento.newValue === 'true');
    }

    const observador = new MutationObserver(mutaciones => {
        if (window.scalaris.observacion?.contiene(mutaciones, selector) === false) return;
        sincronizarControles();
    });

    function destruir() {
        observador.disconnect();
        document.removeEventListener('click', alternarPorGesto);
        window.removeEventListener?.('storage', recibirPreferencia);
        window.removeEventListener?.('pageshow', leerPreferencia);
    }

    leerPreferencia();
    observador.observe(document.documentElement, { childList: true, subtree: true });
    document.addEventListener('click', alternarPorGesto);
    window.addEventListener?.('storage', recibirPreferencia);
    window.addEventListener?.('pageshow', leerPreferencia);
    window.scalaris.preferenciaSonido = { destruir };
}
