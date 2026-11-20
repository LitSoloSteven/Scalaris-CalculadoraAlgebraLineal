/** Búsqueda e inserción de símbolos en el campo que abrió el selector. */
'use strict';

{
    const catalogo = window.scalaris.catalogoSimbolos;
    const selectorCampo = 'textarea, input:is([type="text"], [type="search"], :not([type]))';
    const pagina = 24;
    let controles;
    let destino;
    let cantidad;

    function perfil(campo) {
        if (!campo?.matches?.(selectorCampo) || campo.disabled || campo.readOnly) return '';
        if (campo.dataset.simbolos) return campo.dataset.simbolos;
        if (campo.dataset.soloNumerico === 'true') return 'numero';
        return campo.hasAttribute('data-ecuaciones-fila') ? 'ecuacion' : '';
    }

    function guardarSeleccion(campo) {
        const tipo = perfil(campo);
        return tipo ? {campo, tipo, inicio: campo.selectionStart, fin: campo.selectionEnd} : null;
    }

    function insercion(entrada, seleccion) {
        if (!seleccion) return undefined;
        return seleccion.tipo === 'texto' ? entrada.simbolo : entrada.campos[seleccion.tipo];
    }

    function insertar(entrada, seleccion, texto) {
        const {campo} = seleccion;
        if (!campo.isConnected || !perfil(campo)) return false;
        const inicio = Math.min(seleccion.inicio, campo.value.length);
        const fin = Math.min(seleccion.fin, campo.value.length);
        const radicando = campo.value.slice(inicio, fin);
        const esRaiz = seleccion.tipo === 'funcion' && entrada.tecla;
        const reemplazo = esRaiz ? texto.slice(0, -1) + radicando + ')' : texto;
        const longitud = campo.value.length - (fin - inicio) + reemplazo.length;
        if (campo.maxLength >= 0 && longitud > campo.maxLength) return false;
        campo.setRangeText(reemplazo, inicio, fin, 'end');
        if (esRaiz && inicio === fin) campo.setSelectionRange(inicio + 2, inicio + 2);
        campo.dispatchEvent(new Event('input', {bubbles: true}));
        return true;
    }

    function simplificar(texto) {
        return texto.normalize('NFD').replace(/\p{M}/gu, '').trim().toLowerCase();
    }

    function codigoDe(simbolo) {
        return 'U+' + simbolo.codePointAt(0).toString(16).toUpperCase().padStart(4, '0');
    }

    function porUnicode(consulta) {
        const coincidencia = /^(?:U\+)?([0-9A-F]{4,6})$/i.exec(consulta);
        const codigo = coincidencia ? Number.parseInt(coincidencia[1], 16) : -1;
        const simbolo = codigo >= 0 && codigo <= 0x10ffff ? String.fromCodePoint(codigo) : consulta;
        if (Array.from(simbolo).length !== 1 || /[\p{C}\p{Z}]/u.test(simbolo)) return null;
        return catalogo.find(entrada => entrada.simbolo === simbolo) ||
            {simbolo, nombre: codigoDe(simbolo), campos: {}};
    }

    function obtenerResultados() {
        const consulta = controles.busqueda.value.trim();
        const grupo = controles.grupo.value;
        const porCodigo = consulta && !grupo ? porUnicode(consulta) : null;
        if (porCodigo && /^(?:U\+)?[0-9A-F]{4,6}$/i.test(consulta)) return [porCodigo];
        const criterio = simplificar(consulta);
        const filtradas = catalogo.filter(({simbolo, nombre, grupo: seccion}) =>
            (!grupo || grupo === seccion) &&
            (!consulta || simbolo.includes(consulta) || simplificar(nombre + ' ' + seccion).includes(criterio)));
        if (!filtradas.length && porCodigo) return [porCodigo];
        return filtradas.sort((primera, segunda) =>
            Number(Boolean(insercion(segunda, destino))) - Number(Boolean(insercion(primera, destino))));
    }

    function crearOpcion(entrada) {
        const texto = insercion(entrada, destino);
        const accion = texto === undefined ? 'Copiar' : 'Insertar';
        const boton = document.createElement('button');
        boton.type = 'button';
        boton.className = 'simbolos-opcion';
        boton.setAttribute('aria-label', accion + ' ' + entrada.nombre + ' ' + entrada.simbolo);
        const signo = document.createElement('span');
        signo.className = 'simbolos-signo';
        signo.textContent = entrada.simbolo;
        const nombre = document.createElement('span');
        nombre.textContent = entrada.nombre;
        const modo = document.createElement('small');
        const atajo = entrada.tecla && destino?.tipo === 'funcion' ? ' · Ctrl+Mayús+' + entrada.tecla.slice(-1) : '';
        modo.textContent = texto && texto !== entrada.simbolo && !entrada.tecla ? accion + ' ' + texto : accion + atajo;
        boton.append(signo, nombre, modo);
        boton.addEventListener('click', () => elegir(entrada, texto));
        return boton;
    }

    function mostrarResultados() {
        const resultados = obtenerResultados();
        controles.lista.replaceChildren(...resultados.slice(0, cantidad).map(crearOpcion));
        controles.mas.hidden = resultados.length <= cantidad;
        controles.estado.textContent = resultados.length
            ? 'Se muestran ' + Math.min(cantidad, resultados.length) + ' de ' + resultados.length + ' símbolos.'
            : 'Sin resultados. Busca por nombre, símbolo o código Unicode, como U+221E.';
    }

    async function elegir(entrada, texto) {
        if (texto !== undefined) {
            if (insertar(entrada, destino, texto)) controles.dialogo.close();
            else controles.estado.textContent = 'El símbolo no cabe en el campo o el campo ya no está disponible.';
            return;
        }
        try {
            await navigator.clipboard.writeText(entrada.simbolo);
            controles.estado.textContent = 'Símbolo copiado ' + entrada.simbolo;
        } catch (_) {
            controles.copia.hidden = false;
            const campo = controles.copia.querySelector('input');
            campo.value = entrada.simbolo;
            campo.focus();
            campo.select();
            controles.estado.textContent = 'Pulsa Ctrl+C para copiar el símbolo seleccionado.';
        }
    }

    function construir() {
        const plantilla = document.getElementById('plantilla-simbolos');
        const dialogo = plantilla.content.firstElementChild.cloneNode(true);
        document.body.append(dialogo);
        controles = {
            dialogo, busqueda: dialogo.querySelector('input[type="search"]'), grupo: dialogo.querySelector('select'),
            lista: dialogo.querySelector('.simbolos-lista'), estado: dialogo.querySelector('[role="status"]'),
            mas: dialogo.querySelector('[data-mas-simbolos]'), copia: dialogo.querySelector('[data-copia-simbolo]'),
        };
        const grupos = new Set(catalogo.map(entrada => entrada.grupo));
        grupos.forEach(grupo => controles.grupo.add(new Option(grupo, grupo)));
        controles.busqueda.addEventListener('input', reiniciarResultados);
        controles.grupo.addEventListener('change', reiniciarResultados);
        controles.mas.addEventListener('click', () => {
            const indice = cantidad;
            cantidad += pagina;
            mostrarResultados();
            controles.lista.children[indice]?.focus();
        });
        dialogo.addEventListener('keydown', evento => {
            if (evento.key === 'Tab') evento.stopPropagation();
            if (evento.key === 'Escape') {
                evento.preventDefault();
                evento.stopPropagation();
                dialogo.close();
                return;
            }
            if (evento.key !== 'Enter' || evento.target !== controles.busqueda || evento.isComposing) return;
            evento.preventDefault();
            controles.lista.firstElementChild?.click();
        });
        dialogo.addEventListener('close', () => {
            if (dialogo.open) return;
            if (destino?.campo.isConnected) destino.campo.focus();
            destino = null;
        });
    }

    function reiniciarResultados() {
        cantidad = pagina;
        controles.copia.hidden = true;
        mostrarResultados();
    }

    function abrir(campo) {
        if (!controles) construir();
        if (controles.dialogo.open) return;
        destino = guardarSeleccion(campo);
        controles.busqueda.value = '';
        controles.grupo.value = '';
        reiniciarResultados();
        controles.dialogo.showModal();
        controles.busqueda.focus();
    }

    function esCombinacion(evento) {
        return evento?.ctrlKey && evento.shiftKey && !evento.altKey && !evento.metaKey &&
            !evento.defaultPrevented && !evento.isComposing;
    }

    function atajo(evento) {
        if (!esCombinacion(evento)) return;
        if (evento.code === 'Space') {
            evento.preventDefault();
            if (!evento.repeat) abrir(evento.target);
            return;
        }
        if (perfil(evento.target) !== 'funcion') return;
        const entrada = catalogo.find(opcion => opcion.tecla === evento.code);
        if (!entrada) return;
        evento.preventDefault();
        if (!evento.repeat) insertar(entrada, guardarSeleccion(evento.target), entrada.campos.funcion);
    }

    document.addEventListener('keydown', atajo);
    document.addEventListener('click', evento => {
        const boton = evento?.target?.closest?.('[data-campo-simbolos]');
        if (boton) abrir(document.getElementById(boton.dataset.campoSimbolos));
    });
}
