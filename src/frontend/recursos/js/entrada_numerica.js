/** Filtro de caracteres de captura compartidos con Python mediante JSON. */
'use strict';
{
    window.scalaris = window.scalaris || {};
    const configuracion = leerConfiguracion();
    const caracteres = new Set(configuracion?.caracteres || '');
    const composiciones = new WeakSet();
    const tiposInsercion = new Set(['insertText', 'insertFromPaste', 'insertFromDrop']);

    function leerConfiguracion() {
        const bloque = document.getElementById?.('scalaris-configuracion-numerica');
        if (!bloque) return null;
        try {
            const datos = JSON.parse(bloque.textContent);
            return typeof datos.caracteres === 'string' && typeof datos.mensaje === 'string' ? datos : null;
        } catch (_) {
            return null;
        }
    }

    function filtrar(texto) {
        if (!configuracion) return texto;
        return Array.from(texto).filter(caracter => caracteres.has(caracter)).join('');
    }

    function esCampo(entrada) {
        return Boolean(configuracion && entrada?.matches?.('input[data-solo-numerico="true"]'));
    }

    function puedeAnimar(evento) {
        return evento.isTrusted && evento.inputType === 'insertText' && !evento.isComposing;
    }

    function prepararValor(entrada, texto) {
        if (!esCampo(entrada)) return texto;
        const filtrado = filtrar(texto);
        if (filtrado !== texto) window.scalaris.rechazoNumerico.rechazar(entrada, configuracion.mensaje, false);
        return filtrado;
    }

    function antesDeInsertar(evento) {
        const entrada = evento.target;
        if (!esCampo(entrada) || evento.isComposing || composiciones.has(entrada)) return;
        if (!tiposInsercion.has(evento.inputType)) return;
        const texto = evento.data ?? evento.dataTransfer?.getData('text/plain');
        if (typeof texto !== 'string') return;
        if (filtrar(texto) === texto) {
            window.scalaris.rechazoNumerico.limpiar();
            return;
        }
        if (!evento.cancelable) return;
        evento.preventDefault();
        window.scalaris.rechazoNumerico.rechazar(entrada, configuracion.mensaje, puedeAnimar(evento));
    }

    function sanearEntrada(entrada) {
        const original = entrada.value;
        const filtrado = filtrar(original);
        if (original === filtrado) return false;
        const inicio = entrada.selectionStart, fin = entrada.selectionEnd;
        const direccion = entrada.selectionDirection;
        entrada.value = filtrado;
        if (inicio !== null && fin !== null) {
            entrada.setSelectionRange(filtrar(original.slice(0, inicio)).length,
                filtrar(original.slice(0, fin)).length, direccion);
        }
        return true;
    }

    function alIntroducir(evento) {
        const entrada = evento.target;
        if (!esCampo(entrada) || evento.isComposing || composiciones.has(entrada)) return;
        if (sanearEntrada(entrada)) {
            window.scalaris.rechazoNumerico.rechazar(entrada, configuracion.mensaje, puedeAnimar(evento));
        }
    }

    function iniciarComposicion(evento) {
        if (esCampo(evento.target)) composiciones.add(evento.target);
    }

    function terminarComposicion(evento) {
        const entrada = evento.target;
        composiciones.delete(entrada);
        if (!esCampo(entrada) || !sanearEntrada(entrada)) return;
        window.scalaris.rechazoNumerico.rechazar(entrada, configuracion.mensaje, false);
        entrada.dispatchEvent(new Event('input', { bubbles: true }));
    }

    function registrarEntradaNumerica() {
        window.scalaris.entradaNumerica?.desmontar();
        const manejadores = { beforeinput: antesDeInsertar, input: alIntroducir,
            compositionstart: iniciarComposicion, compositionend: terminarComposicion };
        Object.entries(manejadores).forEach(([nombre, funcion]) =>
            document.addEventListener(nombre, funcion, { capture: true }));
        window.scalaris.entradaNumerica = { filtrar, esCampo, prepararValor,
            desmontar: () => Object.entries(manejadores).forEach(([nombre, funcion]) =>
                document.removeEventListener(nombre, funcion, { capture: true })) };
    }
    registrarEntradaNumerica();
}
