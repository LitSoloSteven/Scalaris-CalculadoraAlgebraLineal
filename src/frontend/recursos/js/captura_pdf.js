(() => {
  'use strict';
  window.scalaris = window.scalaris || {};
  let carga = null;
  let ocupada = false;

  function conPlazo(promesa, segundos) {
    let reloj;
    const plazo = new Promise((_, rechazar) => {
      reloj = setTimeout(() => rechazar(new Error('plazo')), segundos * 1000);
    });
    return Promise.race([promesa, plazo]).finally(() => clearTimeout(reloj));
  }

  async function cargarBiblioteca(configuracion) {
    if (window.html2canvas) return window.html2canvas;
    if (carga) return carga;
    let etiqueta;
    const pendiente = new Promise((resolver, rechazar) => {
      etiqueta = document.createElement('script');
      etiqueta.src = '/assets/js/html2canvas.min.js';
      etiqueta.onload = () => resolver(window.html2canvas);
      etiqueta.onerror = () => rechazar(new Error('biblioteca'));
      document.head.appendChild(etiqueta);
    });
    carga = conPlazo(pendiente, configuracion.plazoMathjax).catch(error => {
      carga = null;
      throw error;
    }).finally(() => {
      etiqueta.onload = null;
      etiqueta.onerror = null;
      etiqueta.remove();
    });
    return carga;
  }

  async function esperarFormulas(configuracion) {
    const motor = window.MathJax;
    if (!motor) throw new Error('formulas');
    await conPlazo(motor.startup?.promise || Promise.resolve(), configuracion.plazoMathjax);
    if (!motor.typesetPromise) throw new Error('formulas');
    await conPlazo(motor.typesetPromise(), configuracion.plazoMathjax);
    await conPlazo(document.fonts.ready, configuracion.plazoMathjax);
  }

  function prepararClon(documento) {
    documento.documentElement.setAttribute('data-tema', 'papel');
    documento.body.classList.remove('body--dark');
    documento.body.style.backgroundColor = 'white';
    documento.querySelectorAll('[data-pdf-captura], [data-pdf-captura] *').forEach(nodo => {
      nodo.style.animation = 'none';
      nodo.style.transition = 'none';
      nodo.style.transform = 'none';
      if (nodo.scrollWidth > nodo.clientWidth) {
        nodo.style.overflow = 'visible';
        nodo.style.maxWidth = 'none';
      }
    });
    documento.querySelectorAll('[data-pdf-excluir]').forEach(nodo => nodo.remove());
  }

  async function capturarRegion(nodo, configuracion, biblioteca) {
    const ancho = Math.max(nodo.scrollWidth, nodo.getBoundingClientRect().width);
    const alto = Math.max(nodo.scrollHeight, nodo.getBoundingClientRect().height);
    const escala = Math.min(configuracion.escala, configuracion.maximoLado / ancho,
      configuracion.maximoLado / alto, Math.sqrt(configuracion.maximoPixeles / (ancho * alto)));
    if (!(escala > 0)) throw new Error('dimensiones');
    let lienzo;
    try {
      lienzo = await biblioteca(nodo, {backgroundColor: 'white', scale: escala,
        width: ancho, height: alto, logging: false, onclone: prepararClon,
        imageTimeout: configuracion.plazoMathjax * 1000});
      const png = lienzo.toDataURL('image/png').split(',')[1];
      if (png.length > Math.ceil(configuracion.maximoBytesImagen / 3) * 4) throw new Error('peso');
      return {clave: nodo.dataset.pdfCaptura, png};
    } finally {
      if (lienzo) { lienzo.width = 0; lienzo.height = 0; }
    }
  }

  async function capturar(identificador, configuracion) {
    if (ocupada) return {error: 'captura'};
    const raiz = document.getElementById(identificador);
    if (!raiz) return {error: 'captura'};
    ocupada = true;
    const inerte = raiz.inert;
    raiz.inert = true;
    try {
      const biblioteca = await cargarBiblioteca(configuracion);
      await esperarFormulas(configuracion);
      const regiones = [...raiz.querySelectorAll('[data-pdf-captura]')].filter(nodo => nodo.getClientRects().length);
      if (!regiones.length || regiones.length > configuracion.maximoFiguras) throw new Error('cantidad');
      const capturas = [];
      let total = 0;
      for (const region of regiones) {
        const captura = await capturarRegion(region, configuracion, biblioteca);
        total += Math.ceil(captura.png.length / 4) * 3;
        if (total > configuracion.maximoBytesTotal) throw new Error('total');
        capturas.push(captura);
      }
      return {capturas};
    } catch (_) {
      return {error: 'captura'};
    } finally {
      raiz.inert = inerte;
      ocupada = false;
    }
  }

  function enfocar(identificador) {
    document.getElementById(identificador)?.focus();
  }

  window.scalaris.capturaPdf = {capturar, enfocar};
})();
