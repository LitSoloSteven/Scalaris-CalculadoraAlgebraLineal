/** Parámetros de señales breves que acompañan las indicaciones visuales. */
{
    'use strict';
    window.scalaris = window.scalaris || {};
    window.scalaris.catalogoSonidos = Object.freeze({
        intervalo: 90,
        polifonia: 2,
        ataque: 0.008,
        ganancia: 0.075,
        claveSilencio: 'scalaris:sonido-silenciado',
        perfiles: Object.freeze({
            escritura: Object.freeze({ inicio: 740, fin: 560, duracion: 0.02, volumen: 0.12 }),
            entrada: Object.freeze({ inicio: 440, fin: 880, duracion: 0.14, volumen: 0.8 }),
            accion: Object.freeze({ inicio: 480, fin: 560, duracion: 0.045 }),
            navegacion: Object.freeze({ inicio: 560, fin: 720, duracion: 0.07 }),
            apertura: Object.freeze({ inicio: 440, fin: 620, duracion: 0.075 }),
            cierre: Object.freeze({ inicio: 620, fin: 440, duracion: 0.065 }),
            exito: Object.freeze({ inicio: 620, fin: 880, duracion: 0.12 }),
            aviso: Object.freeze({ inicio: 440, fin: 400, duracion: 0.1 }),
            error: Object.freeze({ inicio: 330, fin: 260, duracion: 0.14 })
        })
    });
}
