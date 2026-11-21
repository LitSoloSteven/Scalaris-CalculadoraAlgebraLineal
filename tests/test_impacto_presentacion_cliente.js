'use strict';
const prueba = require('node:test');
const afirmar = require('node:assert/strict');
const { crearPresentacion } = require('./comun_presentacion_cliente.js');

const LOGOTIPO = '#presentacion-logotipo';
const ABERTURA = '#presentacion-abertura';

prueba('el montaje se confirma durante el anillo y la onda empieza al contacto', async () => {
    const cliente = crearPresentacion();
    const { entradaInicio, presentacion } = cliente.ventana.scalaris;
    await cliente.reloj.avanzar(32);
    afirmar.equal(await entradaInicio.directorioListo, true);
    afirmar.equal(presentacion.activa, true);
    afirmar.equal(cliente.atributos.has('data-inicio-pendiente'), false);
    await cliente.reloj.avanzar(899);
    afirmar.equal(cliente.animaciones.length, 4);
    await cliente.reloj.avanzar(1689);
    afirmar.equal(cliente.fondo.propiedades.has('data-revelando'), false);
    await cliente.reloj.avanzar(1690);
    const [entrada, elevacion, impacto] = cliente.animaciones.filter(animacion => animacion.selector === LOGOTIPO);
    const anillo = cliente.animaciones.find(animacion => animacion.selector === '#presentacion-anillo circle');
    const onda = cliente.animaciones.find(animacion => animacion.selector === ABERTURA);
    afirmar.equal(entrada.inicio, anillo.inicio);
    afirmar.equal(anillo.inicio + anillo.tiempos.duration, elevacion.inicio);
    afirmar.equal(elevacion.fotogramas.at(-1).transform, 'translateY(-18px) scale(1.2)');
    afirmar.equal(elevacion.inicio + elevacion.tiempos.duration, impacto.inicio);
    afirmar.equal(elevacion.fotogramas.at(-1).transform, impacto.fotogramas[0].transform);
    afirmar.equal(impacto.fotogramas.at(-1).transform, 'translateY(0) scale(0.95)');
    afirmar.equal(impacto.inicio + impacto.tiempos.duration, onda.inicio);
    afirmar.equal(onda.fotogramas.map(fotograma => fotograma.transform).join(), 'scale(0),scale(1)');
    afirmar.equal(cliente.fondo.propiedades.has('data-revelando'), true);
    await cliente.reloj.avanzar(2290);
    await presentacion.terminada;
    afirmar.equal(presentacion.activa, false);
    afirmar.equal(cliente.montado(), false);
});

prueba('la geometría a 320 px se mide antes de elevar el logotipo en cada tema', async () => {
    for (const tema of ['papel', 'marea', 'medianoche']) {
        const cliente = crearPresentacion({ ancho: 320, tema });
        const mediciones = [];
        cliente.imagen.getBoundingClientRect = () => {
            mediciones.push(cliente.animaciones.length);
            return { left: 120, top: 180, width: 80, height: 80 };
        };
        await cliente.reloj.avanzar(900);
        const { propiedades } = cliente.nodos.get(ABERTURA);
        const superficie = cliente.nodos.get('#presentacion-superficie-mascara').propiedades;
        afirmar.equal(superficie.get('width'), 320);
        afirmar.equal(superficie.get('height'), 600);
        afirmar.deepEqual(mediciones, [4]);
        afirmar.equal(propiedades.get('cx'), 160);
        afirmar.equal(propiedades.get('cy'), 220);
        afirmar.equal(propiedades.get('r'), Math.hypot(160, 380));
        afirmar.equal(cliente.imagen.src, tema === 'medianoche' ? '/assets/LogoClaro.png' : '/assets/LogoOscuro.png');
    }
});

prueba('un directorio ausente libera el montaje y todas las tareas en el plazo único', async () => {
    const cliente = crearPresentacion({ contenido: false });
    await cliente.reloj.avanzar(2889);
    afirmar.equal(cliente.reloj.tareas.size, 1);
    afirmar.equal(cliente.montado(), true);
    await cliente.reloj.avanzar(2890);
    afirmar.equal(await cliente.ventana.scalaris.entradaInicio.directorioListo, false);
    afirmar.equal(cliente.montado(), false);
    afirmar.equal(cliente.reloj.tareas.size, 0);
    afirmar(cliente.observadores.every(observador => !observador.activo));
    cliente.montarContenido();
    await cliente.reloj.avanzar(3000);
    afirmar.equal(cliente.animaciones.length, 4);
});

prueba('un directorio demasiado tardío se muestra sin iniciar una onda incompleta', async () => {
    const cliente = crearPresentacion({ contenido: false });
    await cliente.reloj.avanzar(1480);
    cliente.montarContenido();
    await cliente.reloj.avanzar(1512);
    afirmar.equal(await cliente.ventana.scalaris.entradaInicio.directorioListo, true);
    afirmar.equal(cliente.montado(), false);
    afirmar.equal(cliente.animaciones.length, 4);
    afirmar.equal(cliente.reloj.tareas.size, 0);
});

prueba('sin máscara o WAAPI la aplicación queda disponible desde el montaje', async () => {
    for (const opciones of [{ sinMascara: true }, { sinAnimacion: true }]) {
        const cliente = crearPresentacion(opciones);
        afirmar.equal(cliente.montado(), false);
        await cliente.reloj.avanzar(32);
        afirmar.equal(await cliente.ventana.scalaris.entradaInicio.directorioListo, true);
        afirmar.equal(cliente.animaciones.length, 0);
        afirmar.equal(cliente.reloj.tareas.size, 0);
    }
});

prueba('un rechazo durante la onda retira la máscara, las animaciones y los oyentes', async () => {
    const cliente = crearPresentacion();
    await cliente.reloj.avanzar(1700);
    cliente.animaciones.at(-1).rechazar(new Error('Onda interrumpida'));
    await cliente.reloj.avanzar(1700);
    afirmar.equal(cliente.montado(), false);
    afirmar.equal(cliente.atributos.has('data-presentacion-activa'), false);
    afirmar(cliente.animaciones.every(animacion => animacion.cancelada));
    afirmar.equal(cliente.ventana.oyentes.size, 0);
    afirmar.equal(cliente.preferencia.oyentes.size, 0);
    afirmar.equal(cliente.reloj.tareas.size, 0);
});
