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
    let ultimoIntervalo = 0;
    let exigeGesto = false;
    const ultimos = new Map();

    function detenerVoces() {
        voces.forEach(voz => voz.liberar());
    }

    function silenciar(valor) {
        silenciado = Boolean(valor);
        if (silenciado) detenerVoces();
    }

    function activarPorGesto(evento) {
        if (!evento?.isTrusted || evento.repeat || silenciado || document.hidden) return;
        exigeGesto = false;
        prepararContexto();
    }

    function prepararContexto() {
        const ConstructorAudio = window.AudioContext || window.webkitAudioContext;
        if (!ConstructorAudio) return;
        try {
            if (!contexto || contexto.state === 'closed') contexto = new ConstructorAudio();
            if (contexto.state === 'suspended') contexto.resume().catch(() => {});
        } catch (_) { /* La interfaz conserva las indicaciones visuales sin audio disponible. */ }
    }

    function admiteVoz(nombre, perfil, ahora) {
        if (voces.size >= catalogo.polifonia) return false;
        if (ahora - ultimoSonido < Math.min(ultimoIntervalo, perfil.intervalo)) return false;
        if (ahora - (ultimos.get(nombre) ?? -Infinity) < perfil.intervalo) return false;
        return Array.from(voces).filter(voz => voz.nombre === nombre).length < perfil.limite;
    }

    function reproducir(nombre) {
        if (!Object.hasOwn(catalogo.perfiles, nombre)) return false;
        if (silenciado || document.hidden) return false;
        prepararEntrada(nombre);
        if (contexto?.state !== 'running') return false;
        const ahora = performance.now();
        const perfil = catalogo.perfiles[nombre];
        if (!admiteVoz(nombre, perfil, ahora)) return false;
        const voz = window.scalaris.sintesisSonora.crearVoz(contexto, perfil, terminada => voces.delete(terminada));
        if (!voz) return false;
        voz.nombre = nombre;
        voces.add(voz);
        ultimoSonido = ahora;
        ultimoIntervalo = perfil.intervalo;
        ultimos.set(nombre, ahora);
        return true;
    }

    function prepararEntrada(nombre) {
        if (nombre !== 'entrada' || contexto || exigeGesto) return;
        if (!window.navigator?.userActivation?.hasBeenActive) return;
        prepararContexto();
    }

    function cerrarContexto() {
        detenerVoces();
        const anterior = contexto;
        contexto = null;
        ultimoSonido = -Infinity;
        ultimoIntervalo = 0;
        ultimos.clear();
        exigeGesto = true;
        if (anterior && anterior.state !== 'closed') anterior.close().catch(() => {});
    }

    function ocultarPagina() {
        if (document.hidden) detenerVoces();
    }

    function destruir() {
        document.removeEventListener('pointerdown', activarPorGesto, true);
        document.removeEventListener('keydown', activarPorGesto, true);
        document.removeEventListener('visibilitychange', ocultarPagina);
        window.removeEventListener?.('pagehide', cerrarContexto);
        cerrarContexto();
    }

    document.addEventListener('pointerdown', activarPorGesto, true);
    document.addEventListener('keydown', activarPorGesto, true);
    document.addEventListener('visibilitychange', ocultarPagina);
    window.addEventListener?.('pagehide', cerrarContexto);
    window.scalaris.sonido = { reproducir, silenciar, destruir };
}
