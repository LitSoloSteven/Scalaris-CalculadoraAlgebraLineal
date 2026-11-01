/** Construye tonos y ruido filtrado con envolventes y liberación de todas sus capas. */
{
    'use strict';
    window.scalaris = window.scalaris || {};
    const catalogo = window.scalaris.catalogoSonidos;
    const ruidos = new WeakMap();

    function obtenerRuido(contexto) {
        if (ruidos.has(contexto)) return ruidos.get(contexto);
        const longitud = Math.ceil(contexto.sampleRate * catalogo.duracionRuido);
        const buffer = contexto.createBuffer(1, longitud, contexto.sampleRate);
        const muestras = buffer.getChannelData(0);
        for (let indice = 0; indice < longitud; indice++) muestras[indice] = Math.random() * 2 - 1;
        ruidos.set(contexto, buffer);
        return buffer;
    }

    function registrarNodo(voz, nodo) {
        voz.nodos.push(nodo);
        return nodo;
    }

    function crearFiltro(voz, frecuencias, tiempos) {
        const filtro = registrarNodo(voz, voz.contexto.createBiquadFilter());
        filtro.type = 'lowpass';
        filtro.frequency.setValueAtTime(frecuencias.inicio, tiempos.inicio);
        filtro.frequency.exponentialRampToValueAtTime(frecuencias.fin, tiempos.fin);
        filtro.Q.setValueAtTime(0.5, tiempos.inicio);
        return filtro;
    }

    function envolver(voz, fuente, datos, tiempos) {
        const ganancia = registrarNodo(voz, voz.contexto.createGain());
        ganancia.gain.setValueAtTime(0, tiempos.inicio);
        ganancia.gain.linearRampToValueAtTime(datos.volumen, tiempos.inicio + catalogo.ataque);
        ganancia.gain.exponentialRampToValueAtTime(0.0001, tiempos.fin);
        fuente.connect(ganancia);
        ganancia.connect(datos.destino);
        voz.fuentes.set(fuente, tiempos);
        fuente.onended = () => {
            voz.fuentes.delete(fuente);
            if (!voz.fuentes.size) voz.liberar();
        };
    }

    function tiemposCapa(voz, duracion, demora = 0) {
        const inicio = voz.contexto.currentTime + demora;
        return { inicio, fin: inicio + duracion };
    }

    function crearTono(voz, nota, perfil) {
        const tiempos = tiemposCapa(voz, nota.duracion, nota.demora);
        const tono = registrarNodo(voz, voz.contexto.createOscillator());
        tono.type = perfil.onda;
        tono.frequency.setValueAtTime(nota.inicio * voz.variacionTono, tiempos.inicio);
        tono.frequency.exponentialRampToValueAtTime(nota.fin * voz.variacionTono, tiempos.fin);
        const volumen = voz.volumen * nota.volumen * (1 - perfil.ruido);
        envolver(voz, tono, { volumen, destino: voz.maestro }, tiempos);
    }

    function crearRuido(voz, perfil) {
        const tiempos = tiemposCapa(voz, perfil.duracionClic ?? perfil.duracion);
        const ruido = registrarNodo(voz, voz.contexto.createBufferSource());
        ruido.buffer = obtenerRuido(voz.contexto);
        const frecuencias = { inicio: perfil.filtro, fin: perfil.filtroFin ?? perfil.filtro };
        const filtro = crearFiltro(voz, frecuencias, tiempos);
        filtro.connect(voz.maestro);
        envolver(voz, ruido, { volumen: voz.volumen * perfil.ruido, destino: filtro }, tiempos);
    }

    function prepararCapas(voz, perfil) {
        voz.variacionTono = perfil.variacion ? 1 + (Math.random() * 2 - 1) * catalogo.variacionTono : 1;
        const decibelios = perfil.variacion ? (Math.random() * 2 - 1) * catalogo.variacionDecibelios : 0;
        voz.volumen = catalogo.ganancia * perfil.volumen * Math.pow(10, decibelios / 20);
        crearTono(voz, { inicio: perfil.inicio, fin: perfil.fin, demora: perfil.demoraTono ?? 0,
            duracion: perfil.duracionTono ?? perfil.duracion, volumen: 1 }, perfil);
        (perfil.notas || []).forEach(nota => crearTono(voz, nota, perfil));
        crearRuido(voz, perfil);
    }

    function liberar(voz) {
        if (voz.liberada) return;
        voz.liberada = true;
        voz.nodos.forEach(nodo => {
            if ('onended' in nodo) nodo.onended = null;
            try { nodo.stop?.(); } catch (_) { /* Puede haber terminado o no haberse iniciado. */ }
            nodo.disconnect();
        });
        voz.fuentes.clear();
        voz.terminar(voz);
    }

    function crearVoz(contexto, perfil, terminar) {
        const voz = { contexto, terminar, nodos: [], fuentes: new Map(), liberada: false };
        voz.liberar = () => liberar(voz);
        try {
            const frecuencias = { inicio: catalogo.filtroMaestro, fin: catalogo.filtroMaestro };
            voz.maestro = crearFiltro(voz, frecuencias, tiemposCapa(voz, perfil.duracion));
            voz.maestro.connect(contexto.destination);
            prepararCapas(voz, perfil);
            voz.fuentes.forEach((tiempos, fuente) => {
                fuente.start(tiempos.inicio);
                fuente.stop(tiempos.fin);
            });
            return voz;
        } catch (_) {
            voz.liberar();
            return null;
        }
    }

    window.scalaris.sintesisSonora = { crearVoz };
}
