/** Revela nodos de texto con una sola tarea cancelable por contenido. */
{
    'use strict';
    const activas = new Map();

    function completar(estado) {
        if (estado.finalizada) return;
        estado.finalizada = true;
        clearTimeout(estado.temporizador);
        estado.fragmentos.forEach(fragmento => { fragmento.nodo.textContent = fragmento.texto; });
        estado.burbuja.removeEventListener('click', estado.saltar);
        if (estado.cursor) estado.cursor.style.display = 'none';
        if (estado.bitacora) estado.bitacora.removeAttribute('aria-busy');
        if (estado.respuesta) estado.respuesta.removeAttribute('data-escritura-estado');
        activas.delete(estado.elemento);
        desplazar(estado);
    }

    function desplazar(estado) {
        if (estado.bitacora && estado.elemento.isConnected !== false) {
            estado.bitacora.scrollTop = estado.bitacora.scrollHeight;
        }
    }

    function avanzar(estado) {
        if (estado.finalizada) return;
        if (estado.elemento.isConnected === false || !window.scalaris.movimiento.permitido()) {
            completar(estado);
            return;
        }
        const transcurrido = Date.now() - estado.inicio;
        const cantidad = Math.max(1, Math.ceil(estado.total * transcurrido / estado.duracion));
        if (cantidad >= estado.total) {
            completar(estado);
            return;
        }
        pintar(estado, cantidad);
        desplazar(estado);
        estado.temporizador = setTimeout(() => avanzar(estado),
            Math.min(estado.intervalo, estado.duracion - transcurrido));
    }

    function pintar(estado, cantidad) {
        let restante = cantidad;
        estado.fragmentos.forEach(fragmento => {
            let limite = Math.min(restante, fragmento.texto.length);
            // Evita mostrar medio par sustituto de un carácter fuera del BMP.
            if (limite > 0 && /[\uD800-\uDBFF]/.test(fragmento.texto[limite - 1])) limite--;
            const visible = fragmento.texto.slice(0, limite);
            if (fragmento.nodo.textContent !== visible) fragmento.nodo.textContent = visible;
            restante = Math.max(0, restante - fragmento.texto.length);
        });
    }

    function revelar(elemento, fragmentos, opciones = {}) {
        if (activas.has(elemento)) completar(activas.get(elemento));
        const total = fragmentos.reduce((suma, fragmento) => suma + fragmento.texto.length, 0);
        const duracion = Math.min(opciones.duracion, opciones.velocidad * total);
        const estado = {
            elemento, fragmentos, total, duracion, inicio: Date.now(),
            intervalo: window.scalaris.movimiento.duracion('--stagger-step'),
            burbuja: opciones.burbuja || elemento, bitacora: opciones.bitacora,
            respuesta: opciones.respuesta, cursor: opciones.cursor,
            temporizador: null, finalizada: false,
        };
        estado.saltar = () => completar(estado);
        if (!total || !(duracion > 0) || !window.scalaris.movimiento.permitido()) {
            completar(estado);
            return;
        }
        activas.set(elemento, estado);
        if (estado.bitacora) estado.bitacora.setAttribute('aria-busy', 'true');
        if (estado.respuesta) estado.respuesta.setAttribute('data-escritura-estado', 'activo');
        estado.burbuja.addEventListener('click', estado.saltar);
        avanzar(estado);
    }

    function cancelarEn(bitacora) {
        Array.from(activas.values()).forEach(estado => {
            if (estado.bitacora === bitacora) completar(estado);
        });
    }

    function retirarDesconectados() {
        Array.from(activas.values()).forEach(estado => {
            if (estado.elemento.isConnected === false) completar(estado);
        });
    }

    function escribirProgresivamente(identificador, texto, velocidad) {
        const elemento = document.getElementById(identificador);
        if (!elemento) return;
        if (activas.has(elemento)) completar(activas.get(elemento));
        if (!window.scalaris.movimiento.permitido()) {
            elemento.textContent = texto;
            return;
        }
        let fragmento = elemento.querySelector('.escritura-texto');
        if (!fragmento) {
            elemento.textContent = '';
            fragmento = document.createElement('span');
            fragmento.className = 'escritura-texto';
            elemento.appendChild(fragmento);
        }
        revelar(elemento, [{ nodo: fragmento, texto }], {
            duracion: window.scalaris.movimiento.duracion('--dur-didactic'),
            velocidad: velocidad > 0 ? velocidad : Infinity,
            cursor: elemento.querySelector('.escritura-cursor'),
        });
    }

    function registrarEscrituraProgresiva() {
        window.scalaris.escritura = { revelar, cancelarEn, retirarDesconectados };
        window.scalaris.efectoMaquinaEscribir = escribirProgresivamente;
    }
    registrarEscrituraProgresiva();
}
