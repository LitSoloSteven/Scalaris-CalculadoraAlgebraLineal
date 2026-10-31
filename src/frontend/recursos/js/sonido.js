/** Sintetiza señales con un contexto por página y sin reproducir colas tardías. */
{
    'use strict';
    window.scalaris = window.scalaris || {};
    window.scalaris.sonido?.destruir();
    const catalogo = window.scalaris.catalogoSonidos;
    const voces = new Set();
    let contexto = null;
    let silenciado = false;
    let ultimoSonido = -Infinity;

    function liberarVoz(voz) {
        if (voz.oscilador) voz.oscilador.onended = null;
        voz.oscilador?.disconnect();
        voz.ganancia?.disconnect();
        voces.delete(voz);
    }

    function detenerVoces() {
        voces.forEach(voz => {
            try { voz.oscilador.stop(); } catch (_) { /* Puede haber terminado entre eventos. */ }
            liberarVoz(voz);
        });
    }

    function silenciar(valor) {
        silenciado = Boolean(valor);
        if (silenciado) detenerVoces();
    }

    function activarPorGesto(evento) {
        if (!evento.isTrusted || evento.repeat || silenciado) return;
        const ConstructorAudio = window.AudioContext || window.webkitAudioContext;
        if (!ConstructorAudio) return;
        try {
            if (!contexto || contexto.state === 'closed') contexto = new ConstructorAudio();
            if (contexto.state === 'suspended') contexto.resume().catch(() => {});
        } catch (_) { /* La interfaz conserva las indicaciones visuales sin audio disponible. */ }
    }

    function crearVoz(perfil) {
        const voz = { oscilador: null, ganancia: null };
        voces.add(voz);
        try {
            voz.oscilador = contexto.createOscillator();
            voz.ganancia = contexto.createGain();
            const inicio = contexto.currentTime;
            const fin = inicio + perfil.duracion;
            voz.oscilador.type = 'sine';
            voz.oscilador.frequency.setValueAtTime(perfil.inicio, inicio);
            voz.oscilador.frequency.exponentialRampToValueAtTime(perfil.fin, fin);
            voz.ganancia.gain.setValueAtTime(0, inicio);
            voz.ganancia.gain.linearRampToValueAtTime(catalogo.ganancia, inicio + catalogo.ataque);
            voz.ganancia.gain.linearRampToValueAtTime(0, fin);
            voz.oscilador.connect(voz.ganancia);
            voz.ganancia.connect(contexto.destination);
            voz.oscilador.onended = () => liberarVoz(voz);
            voz.oscilador.start(inicio);
            voz.oscilador.stop(fin);
            return true;
        } catch (_) {
            try { voz.oscilador.stop(); } catch (_) { /* Un nodo sin iniciar no necesita detenerse. */ }
            liberarVoz(voz);
            return false;
        }
    }

    function reproducir(nombre) {
        if (!Object.hasOwn(catalogo.perfiles, nombre)) return false;
        if (silenciado || document.hidden || contexto?.state !== 'running') return false;
        const ahora = performance.now();
        if (ahora - ultimoSonido < catalogo.intervalo || voces.size >= catalogo.polifonia) return false;
        try {
            if (!crearVoz(catalogo.perfiles[nombre])) return false;
            ultimoSonido = ahora;
            return true;
        } catch (_) { return false; }
    }

    function cerrarContexto() {
        detenerVoces();
        const anterior = contexto;
        contexto = null;
        ultimoSonido = -Infinity;
        if (anterior && anterior.state !== 'closed') anterior.close().catch(() => {});
    }

    function ocultarPagina() {
        if (document.hidden) detenerVoces();
    }

    function destruir() {
        document.removeEventListener('pointerdown', activarPorGesto, true);
        document.removeEventListener('keydown', activarPorGesto, true);
        document.removeEventListener('visibilitychange', ocultarPagina);
        window.removeEventListener('pagehide', cerrarContexto);
        cerrarContexto();
    }

    document.addEventListener('pointerdown', activarPorGesto, true);
    document.addEventListener('keydown', activarPorGesto, true);
    document.addEventListener('visibilitychange', ocultarPagina);
    window.addEventListener('pagehide', cerrarContexto);
    window.scalaris.sonido = { reproducir, silenciar, destruir };
}
