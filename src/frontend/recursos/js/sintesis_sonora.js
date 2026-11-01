/** Construye voces por capas y libera todas sus fuentes, ganancias y filtros. */
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

    function envolver(voz, fuente, volumen, tiempos) {
        const ganancia = registrarNodo(voz, voz.contexto.createGain());
        ganancia.gain.setValueAtTime(0, tiempos.inicio);
        ganancia.gain.linearRampToValueAtTime(volumen, tiempos.inicio + catalogo.ataque);
        ganancia.gain.exponentialRampToValueAtTime(0.0001, tiempos.fin);
        fuente.connect(ganancia);
        ganancia.connect(voz.filtro);
        voz.fuentes.add(fuente);
        fuente.onended = voz.liberar;
    }

    function prepararCapas(voz, perfil, tiempos) {
        const tono = registrarNodo(voz, voz.contexto.createOscillator());
        tono.type = perfil.onda;
        tono.frequency.setValueAtTime(perfil.inicio, tiempos.inicio);
        tono.frequency.exponentialRampToValueAtTime(perfil.fin, tiempos.fin);
        const ruido = registrarNodo(voz, voz.contexto.createBufferSource());
        ruido.buffer = obtenerRuido(voz.contexto);
        const volumen = catalogo.ganancia * perfil.volumen;
        envolver(voz, tono, volumen * (1 - perfil.ruido), tiempos);
        envolver(voz, ruido, volumen * perfil.ruido, tiempos);
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
        const voz = { contexto, terminar, nodos: [], fuentes: new Set(), liberada: false };
        voz.liberar = () => liberar(voz);
        const tiempos = { inicio: contexto.currentTime, fin: contexto.currentTime + perfil.duracion };
        try {
            voz.filtro = registrarNodo(voz, contexto.createBiquadFilter());
            voz.filtro.type = 'lowpass';
            voz.filtro.frequency.setValueAtTime(perfil.filtro, tiempos.inicio);
            voz.filtro.Q.setValueAtTime(0.5, tiempos.inicio);
            voz.filtro.connect(contexto.destination);
            prepararCapas(voz, perfil, tiempos);
            voz.fuentes.forEach(fuente => {
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
