/** Acompaña inserciones físicas sin leer ni conservar el contenido escrito. */
{
    'use strict';
    window.scalaris = window.scalaris || {};
    window.scalaris.escrituraSonora?.destruir();
    const tiposCampo = new Set(['text', 'search', 'email', 'url', 'tel', 'password', 'number']);
    const inserciones = new Set(['insertText', 'insertReplacementText', 'insertFromPaste',
        'insertFromDrop', 'insertLineBreak', 'insertParagraph']);

    function campoEditable(entrada) {
        if (!entrada || entrada.closest?.('[inert], [data-sonido-omitir]')) return false;
        if (entrada.disabled || entrada.readOnly || entrada.getAttribute?.('aria-disabled') === 'true') return false;
        if (entrada.isContentEditable) return true;
        if (entrada.matches?.('textarea')) return true;
        return Boolean(entrada.matches?.('input') && tiposCampo.has(entrada.type || 'text'));
    }

    function alInsertar(evento) {
        if (!evento.isTrusted || evento.isComposing || !inserciones.has(evento.inputType)) return;
        if (campoEditable(evento.target)) window.scalaris.sonido.reproducir('escritura');
    }

    function alComponer(evento) {
        if (!evento.isTrusted || !evento.data || !campoEditable(evento.target)) return;
        window.scalaris.sonido.reproducir('escritura');
    }

    function destruir() {
        document.removeEventListener('input', alInsertar);
        document.removeEventListener('compositionend', alComponer);
    }

    document.addEventListener('input', alInsertar, { passive: true });
    document.addEventListener('compositionend', alComponer, { passive: true });
    window.scalaris.escrituraSonora = { destruir };
}
