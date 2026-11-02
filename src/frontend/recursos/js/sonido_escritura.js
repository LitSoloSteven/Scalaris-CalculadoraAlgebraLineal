/** Acompaña inserciones físicas sin leer ni conservar el contenido escrito. */
{
    'use strict';
    window.scalaris = window.scalaris || {};
    window.scalaris.escrituraSonora?.destruir();
    const tiposCampo = new Set(['text', 'search', 'email', 'url', 'tel', 'password', 'number']);
    const inserciones = new Set(['insertText', 'insertReplacementText', 'insertFromPaste',
        'insertFromDrop', 'insertLineBreak', 'insertParagraph', 'insertCompositionText', 'insertFromComposition']);

    function campoEditable(entrada) {
        if (!entrada || entrada.closest?.('[inert], [data-sonido-omitir]')) return false;
        if (entrada.disabled || entrada.readOnly || entrada.getAttribute?.('aria-disabled') === 'true') return false;
        if (entrada.isContentEditable) return true;
        if (entrada.matches?.('textarea')) return true;
        return Boolean(entrada.matches?.('input') && tiposCampo.has(entrada.type || 'text'));
    }

    function alInsertar(evento) {
        if (!evento.isTrusted || evento.isComposing || !campoEditable(evento.target)) return;
        if (!inserciones.has(evento.inputType) && !evento.inputType?.startsWith('delete')) return;
        const nombre = window.scalaris.asignacionSonora.escritura(evento.inputType, evento.data === ' ');
        window.scalaris.sonido.reproducir(nombre);
    }

    function destruir() {
        document.removeEventListener('input', alInsertar);
    }

    document.addEventListener('input', alInsertar, { passive: true });
    window.scalaris.escrituraSonora = { destruir };
}
