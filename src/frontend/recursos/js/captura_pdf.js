'use strict';
{
  window.scalaris = window.scalaris || {};
  let carga = null;
  let ocupada = false;
  let pendientes = null;
  let vencimiento = null;
  let solicitud = 0;

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
    prepararFormulas(documento);
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

  function prepararFormulas(documento) {
    const formulas = [...documento.querySelectorAll('.MathJax, .MathJax *, html2canvascustomelement, html2canvascustomelement *')];
    if (!formulas.length) return;
    const color = documento.defaultView.getComputedStyle(documento.documentElement).getPropertyValue('--text-main');
    formulas.forEach(nodo => { nodo.style.color = color; });
  }

  function escalaSegura(ancho, alto, configuracion) {
    return Math.min(configuracion.escala, configuracion.maximoLado / ancho,
      configuracion.maximoLado / alto, Math.sqrt(configuracion.maximoPixeles / (ancho * alto)));
  }

  function ajustarDimensiones(ajustes, region, configuracion) {
    const caja = region.getBoundingClientRect();
    ajustes.width = Math.ceil(Math.max(region.scrollWidth, caja.width));
    ajustes.height = Math.ceil(Math.max(region.scrollHeight, caja.height));
    ajustes.scale = escalaSegura(ajustes.width, ajustes.height, configuracion);
  }

  async function capturarRegion(nodo, configuracion, biblioteca, estado) {
    const anchos = [...nodo.querySelectorAll('*')].map(hijo => hijo.scrollWidth);
    const ancho = Math.max(nodo.scrollWidth, nodo.getBoundingClientRect().width, ...anchos);
    const alto = Math.max(nodo.scrollHeight, nodo.getBoundingClientRect().height);
    const escala = escalaSegura(ancho, alto, configuracion);
    if (!(escala > 0)) throw new Error('dimensiones');
    let lienzo;
    try {
      const ajustes = {backgroundColor: 'white', scale: escala,
        ignoreElements: elemento => elemento.tagName === 'MJX-ASSISTIVE-MML',
        width: ancho, height: alto, logging: false, onclone: (documento, region) => {
          if (estado.cancelada) throw new Error('cancelada');
          prepararClon(documento, region, ancho);
          ajustarDimensiones(ajustes, region, configuracion);
        },
        imageTimeout: configuracion.plazoMathjax * 1000};
      lienzo = await biblioteca(nodo, ajustes);
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
      const captura = region.dataset.pdfMotor === 'plotly'
        ? await capturarPlotly(region, configuracion, estado)
        : await capturarRegion(region, configuracion, biblioteca, estado);
      total += Math.ceil(captura.png.length / 4) * 3;
      if (total > configuracion.maximoBytesTotal) throw new Error('total');
      capturas.push(captura);
    }
    return {capturas};
  }

  function prepararDatosPlotly(figura) {
    const datos = structuredClone(figura.data);
    const colores = window.scalaris.graficos;
    for (const traza of datos) {
      for (const [ruta, rol] of Object.entries(traza.meta?.scalaris_colores || {})) {
        const color = rol.startsWith('serie:') ? colores.paletas.papel[Number(rol.split(':')[1])] : colores[rol].papel;
        const partes = ruta.split('.');
        let destino = traza;
        for (const parte of partes.slice(0, -1)) destino = destino[parte] ||= {};
        destino[partes.at(-1)] = ruta === 'colorscale' ? [[0, color], [1, color]] : color;
      }
    }
    return datos;
  }

  function prepararDisposicionPlotly(figura) {
    const disposicion = structuredClone(figura.layout);
    const colores = window.scalaris.graficos;
    disposicion.font = {...disposicion.font, color: colores.texto.papel};
    disposicion.paper_bgcolor = disposicion.plot_bgcolor = 'white';
    for (const nombre of ['xaxis', 'yaxis', 'zaxis']) {
      for (const contenedor of [disposicion, disposicion.scene].filter(Boolean)) {
        if (!contenedor[nombre]) continue;
        Object.assign(contenedor[nombre], {color: colores.texto.papel, gridcolor: colores.cuadricula.papel,
          zerolinecolor: colores.texto.papel, backgroundcolor: 'white'});
      }
    }
    if (disposicion.scene && figura._fullLayout.scene?.camera) {
      disposicion.scene.camera = structuredClone(figura._fullLayout.scene.camera);
    }
    return disposicion;
  }

  async function capturarPlotly(region, configuracion, estado) {
    const figura = region.querySelector('.js-plotly-plot');
    const biblioteca = window.Plotly || window.getElement?.(figura)?.Plotly;
    if (!figura?._fullLayout || !biblioteca?.newPlot || !biblioteca?.toImage) throw new Error('grafica');
    const caja = figura.getBoundingClientRect();
    const escala = escalaSegura(caja.width, caja.height, configuracion);
    if (!(escala > 0)) throw new Error('dimensiones');
    const temporal = document.createElement('div');
    temporal.setAttribute('aria-hidden', 'true');
    temporal.dataset.pdfTemporal = '';
    Object.assign(temporal.style, {position: 'fixed', left: '100%', top: '0',
      width: `${caja.width}px`, height: `${caja.height}px`, pointerEvents: 'none'});
    document.body.appendChild(temporal);
    const limpiar = () => {
      try { biblioteca.purge(temporal); } finally { temporal.remove(); }
    };
    estado.limpiarPlotly = limpiar;
    try {
      await biblioteca.newPlot(temporal, prepararDatosPlotly(figura), prepararDisposicionPlotly(figura), {staticPlot: true});
      if (estado.cancelada) throw new Error('cancelada');
      const imagen = await biblioteca.toImage(temporal, {format: 'png',
        width: Math.floor(caja.width * escala), height: Math.floor(caja.height * escala)});
      if (estado.cancelada || !imagen.startsWith('data:image/png;base64,')) throw new Error('cancelada');
      const png = imagen.split(',')[1];
      if (png.length > Math.ceil(configuracion.maximoBytesImagen / 3) * 4) throw new Error('peso');
      return {clave: region.dataset.pdfCaptura, png};
    } finally {
      limpiar();
      estado.limpiarPlotly = null;
    }
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
      estado.limpiarPlotly?.();
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

  function liberar(testigo) {
    if (testigo !== solicitud) return false;
    clearTimeout(vencimiento);
    vencimiento = null;
    pendientes = null;
    return true;
  }

  async function preparar(identificador, configuracion) {
    if (ocupada) return {error: 'captura'};
    liberar(solicitud);
    const testigo = ++solicitud;
    const respuesta = await capturar(identificador, configuracion);
    if (!respuesta.capturas) return respuesta;
    pendientes = respuesta.capturas;
    vencimiento = setTimeout(() => liberar(testigo), configuracion.plazoCaptura * 1000);
    return {solicitud: testigo, capturas: pendientes.map(captura =>
      ({clave: captura.clave, longitud: captura.png.length}))};
  }

  function leer(testigo, indice, desplazamiento, cantidad) {
    if (testigo !== solicitud || !pendientes || !Number.isInteger(indice) ||
      !Number.isInteger(desplazamiento) || desplazamiento < 0 || !Number.isInteger(cantidad) || cantidad < 1) return null;
    const captura = pendientes[indice];
    return captura ? captura.png.slice(desplazamiento, desplazamiento + cantidad) : null;
  }

  window.addEventListener?.('pagehide', () => liberar(solicitud));
  window.scalaris.capturaPdf = {capturar, preparar, leer, liberar, enfocar};
}
