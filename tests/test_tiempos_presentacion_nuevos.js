'use strict';
const prueba = require('node:test');
const afirmar = require('node:assert/strict');
const { crearPresentacion } = require('./comun_presentacion_cliente.js');

prueba('la presentación encadena duraciones de token sin retardos ni curva literal', async () => {
  const cliente = crearPresentacion();
  await cliente.reloj.avanzar(1982);
  afirmar.deepEqual(cliente.animaciones.map(animacion => animacion.tiempos.duration), [600, 900, 600, 450, 600, 600, 450]);
  afirmar(cliente.animaciones.every(animacion => animacion.tiempos.delay === undefined));
  afirmar(cliente.animaciones.every(animacion => animacion.tiempos.easing === cliente.ventana.scalaris.movimiento.curva()));
  afirmar.equal(cliente.animaciones[0].fotogramas[0].transform, 'scale(0.95)');
});

prueba('movimiento reducido usa únicamente opacidad, sin retardo', async () => {
  const cliente = crearPresentacion({ reducido: true });
  await cliente.reloj.avanzar(152);
  const animacion = cliente.animaciones[0];
  afirmar.equal(animacion.tiempos.duration, 120);
  afirmar.equal(animacion.tiempos.delay, undefined);
  afirmar.equal(animacion.tiempos.easing, cliente.ventana.scalaris.movimiento.curva());
  afirmar(animacion.fotogramas.every(fotograma => Object.keys(fotograma).join() === 'opacity'));
});

prueba('una llegada por teclado no reproduce la presentación', async () => {
  const cliente = crearPresentacion({ teclado: true });
  await cliente.reloj.avanzar(32);
  afirmar.equal(cliente.animaciones.length, 0);
  afirmar.equal(cliente.montado(), false);
});
