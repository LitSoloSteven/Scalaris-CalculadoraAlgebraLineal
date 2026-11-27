/** Búsqueda e inserción de símbolos en el campo que abrió el selector. */
'use strict';

{
    const catalogo = window.scalaris.catalogoSimbolos;
    const perfiles = window.scalaris.perfilesSimbolos;
    const selectorCampo = 'textarea, input:is([type="text"], [type="search"], :not([type]))';
    const pagina = 24;
    let controles;
    let destino;
    let ultimoCampo = null;
    let posicionPendiente = null;
    let cantidad;
    let perfilesVigentes = ['texto'];
    let catalogoVigente = catalogo;

    function tipoDesdeAtributos(campo) {
        const datos = campo.dataset;
        if (datos?.simbolos) return datos.simbolos;
        if (datos?.soloNumerico === 'true') return 'numero';
        if (campo.hasAttribute?.('data-ecuaciones-indice') || campo.hasAttribute?.('data-ecuaciones-fila')) {
            return 'ecuacion';
        }
        return 'texto';
    }

    function perfil(campo) {
        if (!campo?.matches?.(selectorCampo) || campo.disabled || campo.readOnly) return '';
        if (campo.closest?.('.simbolos-dialogo')) return '';
        return tipoDesdeAtributos(campo);
    }

    function esCampoVisible(campo) {
        if (!perfil(campo) || !campo.isConnected) return false;
        if (campo.closest?.('[inert], [hidden], [aria-hidden="true"]')) return false;
        return typeof campo.getClientRects !== 'function' || campo.getClientRects().length > 0;
    }

    function resolverCampoDestino(candidato) {
        return [candidato, document.activeElement, ultimoCampo].find(esCampoVisible) || null;
    }

    function guardarSeleccion(campo) {
        const tipo = perfil(campo);
        return tipo ? {campo, tipo, inicio: campo.selectionStart, fin: campo.selectionEnd} : null;
    }

    function obtenerModuloActivo() {
        return document.querySelector?.('meta[name="scalaris-modulo"]')?.getAttribute?.('content')?.trim() || '';
    }

    function limitesSeleccion(seleccion, longitudCampo) {
        const inicio = Math.min(seleccion.inicio ?? longitudCampo, longitudCampo);
        const fin = Math.min(seleccion.fin ?? inicio, longitudCampo);
        return [inicio, fin];
    }

    function puedeInsertar(campo, reemplazo, borrados) {
        if (!campo.isConnected || !perfil(campo)) return false;
        const longitud = campo.value.length - borrados + reemplazo.length;
        return campo.maxLength < 0 || longitud <= campo.maxLength;
    }

    function insertar(entrada, seleccion, texto) {
        if (!seleccion) return false;
        const {campo} = seleccion;
        const [inicio, fin] = limitesSeleccion(seleccion, campo.value.length);
        const esCampoReal = seleccion.tipo === 'funcion' || seleccion.tipo === 'real';
        const esRaiz = esCampoReal && Boolean(entrada.tecla);
        const contenido = campo.value.slice(inicio, fin);
        const reemplazo = textoConSeleccion(texto, contenido, esRaiz, esCampoReal);
        if (!puedeInsertar(campo, reemplazo, fin - inicio)) return false;
        campo.setRangeText(reemplazo, inicio, fin, 'end');
        if (esRaiz && inicio === fin) {
            const cursorRaiz = inicio + texto.length - 1;
            campo.setSelectionRange(cursorRaiz, cursorRaiz);
        }
        campo.dispatchEvent(new Event('input', {bubbles: true}));
        return true;
    }

    function textoConSeleccion(texto, contenido, esRaiz, esCampoReal) {
        if (esRaiz) return texto.slice(0, -1) + contenido + ')';
        if (contenido && esCampoReal && /^[°‰′″]$/u.test(texto)) return '(' + contenido + ')' + texto;
        return texto;
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
        const encontrada = catalogoVigente.find(entrada => entrada.simbolo === simbolo);
        if (encontrada) return encontrada;
        return perfiles.admiteTodos(perfilesVigentes) ? {simbolo, nombre: codigoDe(simbolo), campos: {}} : null;
    }

    function obtenerResultados() {
        const consulta = controles.busqueda.value.trim();
        const grupo = controles.grupo.value;
        const porCodigo = consulta && !grupo ? porUnicode(consulta) : null;
        if (porCodigo && /^(?:U\+)?[0-9A-F]{4,6}$/i.test(consulta)) return [porCodigo];
        const criterio = simplificar(consulta);
        const filtradas = catalogoVigente.filter(({simbolo, nombre, grupo: seccion}) =>
            (!grupo || grupo === seccion) &&
            (!consulta || simbolo.includes(consulta) || simplificar(nombre + ' ' + seccion).includes(criterio)));
        if (!filtradas.length && porCodigo) return [porCodigo];
        return filtradas;
    }

    function etiquetaModo(entrada, texto) {
        if (!destino) return 'Copiar';
        if (entrada.tecla && destino.tipo === 'funcion') {
            return 'Insertar · Ctrl+Mayús+' + entrada.tecla.slice(-1);
        }
        if (texto !== entrada.simbolo) return 'Insertar ' + texto;
        return 'Insertar';
    }

    function crearOpcion(entrada) {
        const texto = perfiles.textoInsercion(entrada, destino);
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
        modo.textContent = etiquetaModo(entrada, texto);
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
            : perfiles.mensajeVacio(perfilesVigentes, controles.busqueda.value.trim());
    }

    async function elegir(entrada, texto) {
        if (texto !== undefined) {
            if (insertar(entrada, destino, texto)) {
                posicionPendiente = [destino.campo.selectionStart, destino.campo.selectionEnd];
                controles.dialogo.close();
            } else {
                controles.estado.textContent = 'El símbolo no cabe en el campo o el campo ya no está disponible.';
            }
            return;
        }
        try {
            await navigator.clipboard.writeText(entrada.simbolo);
            controles.dialogo.close();
        } catch (_) {
            controles.copia.hidden = false;
            const campo = controles.copia.querySelector('input');
            campo.value = entrada.simbolo;
            campo.focus();
            campo.select();
            controles.estado.textContent = 'Pulsa Ctrl+C para copiar el símbolo seleccionado.';
        }
    }

    function manejarTecladoDialogo(evento) {
        if (evento.key === 'Tab') evento.stopPropagation();
        if (evento.key === 'Escape') {
            evento.preventDefault();
            evento.stopPropagation();
            controles.dialogo.close();
            return;
        }
        if (evento.key !== 'Enter' || evento.target !== controles.busqueda || evento.isComposing) return;
        evento.preventDefault();
        controles.lista.firstElementChild?.click();
    }

    function fueraDeDialogo(evento, dialogo) {
        const marco = dialogo.getBoundingClientRect();
        return evento.clientX < marco.left || evento.clientX > marco.right ||
            evento.clientY < marco.top || evento.clientY > marco.bottom;
    }

    function registrarCierreExterior(dialogo) {
        if (typeof HTMLDialogElement !== 'undefined' && 'closedBy' in HTMLDialogElement.prototype) return;
        let pulsadoFuera = false;
        dialogo.addEventListener('pointerdown', evento => {
            pulsadoFuera = fueraDeDialogo(evento, dialogo);
        });
        dialogo.addEventListener('pointerup', evento => {
            if (pulsadoFuera && fueraDeDialogo(evento, dialogo)) dialogo.close();
            pulsadoFuera = false;
        });
    }

    function alCerrarDialogo() {
        if (controles.dialogo.open) return;
        if (destino?.campo.isConnected) {
            destino.campo.focus();
            if (posicionPendiente && posicionPendiente[0] !== null && typeof destino.campo.setSelectionRange === 'function') {
                destino.campo.setSelectionRange(posicionPendiente[0], posicionPendiente[1]);
            }
        }
        posicionPendiente = null;
        destino = null;
    }

    function actualizarGrupos(disponibles) {
        const opciones = [new Option('Todas', ''), ...perfiles.gruposDisponibles(disponibles).map(grupo => new Option(grupo, grupo))];
        controles.grupo.replaceChildren(...opciones);
        controles.grupo.disabled = opciones.length <= 1;
    }

    function construir() {
        const plantilla = document.getElementById('plantilla-simbolos');
        const dialogo = plantilla.content.firstElementChild.cloneNode(true);
        document.body.append(dialogo);
        controles = {
            dialogo, cuerpo: dialogo.querySelector('.simbolos-cuerpo'),
            busqueda: dialogo.querySelector('input[type="search"]'),
            grupo: dialogo.querySelector('select'), lista: dialogo.querySelector('.simbolos-lista'),
            estado: dialogo.querySelector('[role="status"]'), mas: dialogo.querySelector('[data-mas-simbolos]'),
            copia: dialogo.querySelector('[data-copia-simbolo]'),
        };
        controles.busqueda.addEventListener('input', reiniciarResultados);
        controles.grupo.addEventListener('change', reiniciarResultados);
        controles.mas.addEventListener('click', () => {
            const indice = cantidad;
            cantidad += pagina;
            mostrarResultados();
            controles.lista.children[indice]?.focus();
        });
        dialogo.addEventListener('keydown', manejarTecladoDialogo);
        registrarCierreExterior(dialogo);
        dialogo.addEventListener('close', alCerrarDialogo);
    }

    function reiniciarResultados() {
        cantidad = pagina;
        controles.copia.hidden = true;
        mostrarResultados();
    }

    function abrir(candidato) {
        if (!controles) construir();
        if (controles.dialogo.open) return;
        destino = guardarSeleccion(resolverCampoDestino(candidato));
        perfilesVigentes = perfiles.perfilesActivos(destino, obtenerModuloActivo());
        catalogoVigente = perfiles.simbolosDisponibles(catalogo, perfilesVigentes);
        posicionPendiente = null;
        controles.busqueda.value = '';
        actualizarGrupos(catalogoVigente);
        controles.grupo.value = '';
        reiniciarResultados();
        if (controles.cuerpo) controles.cuerpo.scrollTop = 0;
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

    document.addEventListener('focusin', evento => { if (perfil(evento.target)) ultimoCampo = evento.target; });
    document.addEventListener('keydown', atajo);
    window.scalaris.selectorSimbolos = { abrir };
}
