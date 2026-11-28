/** Reproduce los gestos de los símbolos del directorio con entradas de puntero. */
'use strict';
{

    const CONTROLES = "[data-gesto-inicio]";
    const SIMBOLO = ".inicio-simbolo svg";
    const preferenciaReducida = window.matchMedia("(prefers-reduced-motion: reduce)");
    const punteroFino = window.matchMedia("(hover: hover) and (pointer: fine)");
    const animaciones = new Set();
    let sesiones = null;

    function recorrido(...posturas) {
        return ["none", ...posturas, "none"];
    }

    const giroInversa = [0, -180, -360].map(angulo => "perspective(60px) rotateY(" + angulo + "deg)");
    const binaria = recorrido("translate(12px, 10px)");
    const decimal = recorrido("translate(-12px, -10px)");
    const elevarVector = recorrido("translateY(-4px)");
    const opacidadReducida = [{ opacity: 1 }, { opacity: 0.72 }, { opacity: 1 }];
    const gestos = new Map(Object.entries({
        "seccion-sistemas-lineales": [
            [0, recorrido("translateY(-3px)")],
            [1, recorrido("translateY(3px)")],
        ],
        "seccion-matrices": [
            [0, recorrido("translateX(-3px) rotateY(-32deg)")],
            [1, recorrido("translateX(3px) rotateY(32deg)")],
        ],
        "seccion-vectores-geometria": [
            [0, recorrido("rotate(-29deg)", "rotate(12deg)")],
        ],
        "seccion-metodos-numericos": [
            [0, recorrido("scaleY(1.16)")],
            [1, recorrido("translateX(-5px)", "translateX(-2px)")],
        ],
        "seccion-sistemas-numeracion": [
            [0, recorrido("translateY(-4px) rotateX(-36deg)")],
            [1, recorrido("translateY(4px) rotateX(36deg)")],
        ],
        sistemas: [
            [1, recorrido("translate(2px, -1px)")],
            [3, recorrido("translateX(1px)")],
        ],
        metodos_iterativos: [
            [0, recorrido("rotate(-28deg)")],
            [1, recorrido("translate(-2px, 2px)")],
        ],
        leontief: [
            [0, recorrido("rotate(-12deg)")],
            [1, recorrido("scaleX(0.45)")],
            [2, recorrido("translateX(-2px) rotate(14deg)")],
        ],
        matrices: [
            [0, recorrido("translate(3px, -3px)")],
            [2, recorrido("translate(-3px, 3px)")],
        ],
        inversa: [[0, giroInversa], [1, giroInversa]],
        determinantes: [
            [0, recorrido("translateX(3px) scaleY(1.18)")],
            [1, recorrido("translateX(-3px) scaleY(1.18)")],
            [2, recorrido("scaleX(0.78)")],
        ],
        factorizacion_lu: [
            [0, recorrido("translate(-3px, 3px)")],
            [1, recorrido("translate(3px, -3px)")],
        ],
        vectores: [[0, recorrido("translateX(-1px) scaleX(1.42)")]],
        espacios_subespacios: [
            [1, recorrido("scale(1.12)")],
            [2, recorrido("scale(1.45)")],
        ],
        transformaciones: [
            [0, recorrido("skewX(-34deg)")],
            [1, recorrido("translateX(2px) skewY(-14deg)")],
        ],
        "vis:rectas-planos": [
            [0, recorrido("rotate(28deg)")],
            [1, recorrido("rotate(-28deg)")],
        ],
        "vis:vectores": [
            [0, recorrido("rotate(30deg)", "translateY(-2px) rotate(30deg)")],
            [1, recorrido("translateY(-4px) scaleY(1.16)")],
        ],
        "vis:combinacion": [
            [0, elevarVector],
            [1, elevarVector],
            [2, ["rotate(0deg)", "rotate(45deg)", "rotate(90deg)"]],
        ],
        metodos_cerrados: [
            [1, recorrido("translateX(5px)", "translateX(3px)")],
            [2, recorrido("translateX(-5px)", "translateX(-3px)")],
            [3, recorrido("scale(1.65)")],
        ],
        metodos_abiertos: [
            [1, recorrido("rotate(-14deg) translateX(2px)")],
            [3, recorrido("translate(3px, -5px)", "translate(3px, -5px)", "translate(7px, -12px)")],
        ],
        bases: [[0, binaria], [1, binaria], [2, decimal], [3, decimal]],
        romanos: [
            [1, recorrido("translateY(4px) scaleX(0.82)")],
            [2, recorrido("scaleY(0.55)", "scaleY(1.18)")],
        ],
    }));

    function cancelarGestos() {
        for (const animacion of animaciones) animacion.cancel();
        animaciones.clear();
    }

    function animarPieza(pieza, fotogramas, opciones) {
        const animacion = pieza.animate(fotogramas, opciones);
        animaciones.add(animacion);
        const retirar = () => animaciones.delete(animacion);
        animacion.finished.then(retirar, retirar);
    }

    function animarGesto(simbolo, gesto, reducido, opciones) {
        for (const [indice, posturas] of gesto) {
            const pieza = simbolo.children[indice];
            if (!pieza?.animate) continue;
            const fotogramas = reducido ? opacidadReducida : posturas.map(transform => ({ transform }));
            animarPieza(pieza, fotogramas, opciones);
        }
    }

    function reproducir(control) {
        const gesto = gestos.get(control?.dataset.gestoInicio);
        if (!gesto) return;

        const simbolo = control.querySelector(SIMBOLO);
        const movimiento = window.scalaris?.movimiento;
        if (!simbolo || !movimiento) return;

        const reducido = preferenciaReducida.matches;
        const duracion = movimiento.duracion(reducido ? "--dur-reduced" : "--dur-state");
        if (!Number.isFinite(duracion) || duracion <= 0) return;
        const opciones = {
            duration: duracion,
            easing: movimiento.curva(),
        };

        cancelarGestos();
        try {
            animarGesto(simbolo, gesto, reducido, opciones);
        } catch {
            cancelarGestos();
        }
    }

    function encontrarControl(nodo) {
        return nodo?.closest?.(CONTROLES);
    }

    function alEntrarPuntero(evento) {
        if (!punteroFino.matches || evento.pointerType === "touch" || evento.buttons) return;
        const control = encontrarControl(evento.target);
        if (control !== encontrarControl(evento.relatedTarget)) reproducir(control);
    }

    function alTocar(evento) {
        if (evento.pointerType === "touch" && evento.isPrimary) reproducir(encontrarControl(evento.target));
    }

    function alCambiarVisibilidad() {
        if (document.hidden) cancelarGestos();
    }

    function desmontar() {
        sesiones.abort();
        sesiones = null;
        cancelarGestos();
    }

    function montar() {
        if (sesiones) return;
        sesiones = new AbortController();
        const opciones = { passive: true, signal: sesiones.signal };
        document.addEventListener("pointerover", alEntrarPuntero, opciones);
        document.addEventListener("pointerdown", alTocar, opciones);
        document.addEventListener("pointercancel", cancelarGestos, opciones);
        document.addEventListener("keydown", cancelarGestos, opciones);
        document.addEventListener("visibilitychange", alCambiarVisibilidad, opciones);
        preferenciaReducida.addEventListener("change", cancelarGestos, opciones);
        punteroFino.addEventListener("change", cancelarGestos, opciones);
        window.addEventListener("pagehide", desmontar, opciones);
    }

    window.addEventListener("pageshow", montar);
    montar();
}
