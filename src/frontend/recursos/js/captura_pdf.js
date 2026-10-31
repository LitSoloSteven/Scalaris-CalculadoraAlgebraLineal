'use strict';
{
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

  function normalizarColores(documento) {
    const lienzo = documento.createElement('canvas');
    lienzo.width = 1;
    lienzo.height = 1;
    const contexto = lienzo.getContext('2d', {willReadFrequently: true});
    const cache = new Map();
    const propiedades = ['color', 'backgroundColor', 'borderTopColor', 'borderRightColor',
      'borderBottomColor', 'borderLeftColor', 'outlineColor', 'textDecorationColor', 'boxShadow', 'backgroundImage'];
    function convertir(color) {
      if (cache.has(color)) return cache.get(color);
      contexto.clearRect(0, 0, 1, 1);
      contexto.fillStyle = color;
      contexto.fillRect(0, 0, 1, 1);
      const [rojo, verde, azul, alfa] = contexto.getImageData(0, 0, 1, 1).data;
      const normalizado = `rgba(${rojo}, ${verde}, ${azul}, ${alfa / 255})`;
      cache.set(color, normalizado);
      return normalizado;
    }
    documento.querySelectorAll('[data-pdf-captura], [data-pdf-captura] *').forEach(nodo => {
      const estilos = documento.defaultView.getComputedStyle(nodo);
      for (const propiedad of propiedades) {
        nodo.style[propiedad] = estilos[propiedad].replace(/(?:color|oklab|oklch|lab|lch)\([^)]*\)/g, convertir);
      }
    });
    lienzo.width = 0;
    lienzo.height = 0;
  }

  function prepararClon(documento, region, ancho) {
    documento.documentElement.setAttribute('data-tema', 'papel');
    documento.body.classList.remove('body--dark');
    documento.body.style.backgroundColor = 'white';
    region.style.setProperty('width', `${ancho}px`, 'important');
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
    normalizarColores(documento);
  }

  async function capturarRegion(nodo, configuracion, biblioteca, estado) {
    const anchos = [...nodo.querySelectorAll('*')].map(hijo => hijo.scrollWidth);
    const ancho = Math.max(nodo.scrollWidth, nodo.getBoundingClientRect().width, ...anchos);
    const alto = Math.max(nodo.scrollHeight, nodo.getBoundingClientRect().height);
    const escala = Math.min(configuracion.escala, configuracion.maximoLado / ancho,
      configuracion.maximoLado / alto, Math.sqrt(configuracion.maximoPixeles / (ancho * alto)));
    if (!(escala > 0)) throw new Error('dimensiones');
    let lienzo;
    try {
      lienzo = await biblioteca(nodo, {backgroundColor: 'white', scale: escala,
        width: ancho, height: alto, logging: false, onclone: (documento, region) => {
          if (estado.cancelada) throw new Error('cancelada');
          prepararClon(documento, region, ancho);
        },
        imageTimeout: configuracion.plazoMathjax * 1000});
      if (estado.cancelada) throw new Error('cancelada');
      const png = lienzo.toDataURL('image/png').split(',')[1];
      if (png.length > Math.ceil(configuracion.maximoBytesImagen / 3) * 4) throw new Error('peso');
      return {clave: nodo.dataset.pdfCaptura, png};
    } finally {
      if (lienzo) { lienzo.width = 0; lienzo.height = 0; }
    }
  }

  async function obtenerCapturas(raiz, configuracion, estado) {
    const biblioteca = await cargarBiblioteca(configuracion);
    await esperarFormulas(configuracion);
    if (estado.cancelada) throw new Error('cancelada');
    const regiones = [...raiz.querySelectorAll('[data-pdf-captura]')].filter(nodo => nodo.getClientRects().length);
    if (!regiones.length || regiones.length > configuracion.maximoFiguras) throw new Error('cantidad');
    const capturas = [];
    let total = 0;
    for (const region of regiones) {
      const captura = await capturarRegion(region, configuracion, biblioteca, estado);
      total += Math.ceil(captura.png.length / 4) * 3;
      if (total > configuracion.maximoBytesTotal) throw new Error('total');
      capturas.push(captura);
    }
    return {capturas};
  }

  /** Captura regiones con plazo global y libera bloqueos incluso si la biblioteca queda pendiente. */
  async function capturar(identificador, configuracion) {
    if (ocupada) return {error: 'captura'};
    const raiz = document.getElementById(identificador);
    if (!raiz) return {error: 'captura'};
    ocupada = true;
    const inerte = raiz.inert;
    const anteriores = new Set(document.querySelectorAll('iframe.html2canvas-container'));
    const estado = {cancelada: false};
    raiz.inert = true;
    try {
      return await conPlazo(obtenerCapturas(raiz, configuracion, estado), configuracion.plazoCaptura);
    } catch (_) {
      return {error: 'captura'};
    } finally {
      estado.cancelada = true;
      document.querySelectorAll('iframe.html2canvas-container').forEach(marco => {
        if (!anteriores.has(marco)) marco.remove();
      });
      raiz.inert = inerte;
      ocupada = false;
    }
  }

  function enfocar(identificador) {
    document.getElementById(identificador)?.focus();
  }

  window.scalaris.capturaPdf = {capturar, enfocar};
}
