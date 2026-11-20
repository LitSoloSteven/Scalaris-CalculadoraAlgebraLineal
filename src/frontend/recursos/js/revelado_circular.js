/** Geometría y tiempos del revelado circular de la aplicación. */
'use strict';
{
    const tokenOnda = '--dur-view';

    function centroDe(elemento) {
        const caja = elemento?.getBoundingClientRect();
        return caja && { x: caja.left + caja.width / 2, y: caja.top + caja.height / 2 };
    }

    function medir(punto) {
        const ancho = window.innerWidth;
        const alto = window.innerHeight;
        const x = limitar(punto?.x, ancho);
        const y = limitar(punto?.y, alto);
        return { x, y, radio: Math.hypot(Math.max(x, ancho - x), Math.max(y, alto - y)) };
    }

    function limitar(coordenada, dimension) {
        return Number.isFinite(coordenada) ? Math.max(0, Math.min(coordenada, dimension)) : dimension / 2;
    }

    function tiempos(token = tokenOnda) {
        const movimiento = window.scalaris.movimiento;
        return { duration: movimiento.duracion(token), easing: movimiento.curva() };
    }

    function animarCaptura(raiz, origen, opciones = {}) {
        const { x, y, radio } = medir(origen);
        const centro = `at ${x}px ${y}px`;
        return raiz.animate(
            { clipPath: [`circle(0px ${centro})`, `circle(${radio}px ${centro})`] },
            { ...tiempos(), ...opciones, pseudoElement: '::view-transition-new(root)' },
        );
    }

    window.scalaris.reveladoCircular = { centroDe, medir, tiempos, animarCaptura };
}
