'use strict';
{
  window.scalaris = window.scalaris || {};
  const TAMANO_LOTE = 250;
  const SELECTOR_CAPTURA = '[data-pdf-captura], [data-pdf-captura] *';
  const PROPIEDADES_COLOR = ['color', 'backgroundColor', 'borderTopColor', 'borderRightColor',
    'borderBottomColor', 'borderLeftColor', 'outlineColor', 'textDecorationColor', 'boxShadow', 'backgroundImage'];

  /** Devuelve el hilo al navegador para atender entrada y progreso entre trabajos costosos. */
  function ceder() {
    if (window.scheduler?.yield) return window.scheduler.yield();
    if (!window.MessageChannel) return new Promise(resolver => setTimeout(resolver, 0));
    return new Promise(resolver => {
      const canal = new window.MessageChannel();
      canal.port1.onmessage = () => {
        canal.port1.close();
        canal.port2.close();
        resolver();
      };
      canal.port2.postMessage(null);
    });
  }

  /** Espera dos fotogramas para pintar el estado antes de comenzar la captura. */
  async function pintarIndicador() {
    const fotograma = () => new Promise(resolver => {
      if (window.requestAnimationFrame) window.requestAnimationFrame(resolver);
      else setTimeout(resolver, 0);
    });
    await fotograma();
    await fotograma();
  }

  function comprobarEstado(estado) {
    if (estado.cancelada) throw new Error('cancelada');
  }

  function mostrarContenido(nodo, documento) {
    const display = documento.defaultView.getComputedStyle(nodo).display;
    const propiedades = {display: display === 'none' ? 'block' : display, height: 'auto',
      'max-height': 'none', overflow: 'visible', visibility: 'visible', opacity: '1'};
    for (const [propiedad, valor] of Object.entries(propiedades)) {
      nodo.style.setProperty(propiedad, valor, 'important');
    }
  }

  function expandirResultados(documento, region) {
    const expansiones = [...region.querySelectorAll('.q-expansion-item')];
    if (region.matches('.q-expansion-item')) expansiones.unshift(region);
    for (const expansion of expansiones) {
      expansion.classList.remove('q-expansion-item--collapsed');
      expansion.classList.add('q-expansion-item--expanded');
      expansion.querySelectorAll('[aria-expanded]').forEach(nodo => nodo.setAttribute('aria-expanded', 'true'));
      expansion.querySelectorAll('.q-expansion-item__toggle-icon').forEach(nodo => {
        nodo.classList.add('q-expansion-item__toggle-icon--rotated');
      });
      expansion.querySelectorAll('.q-expansion-item__content').forEach(contenido => {
        for (let nodo = contenido; nodo && region.contains(nodo); nodo = nodo.parentElement) {
          mostrarContenido(nodo, documento);
          if (nodo === region) break;
        }
      });
    }
  }

  function prepararFormulas(documento) {
    const formulas = [...documento.querySelectorAll('.MathJax, .MathJax *, html2canvascustomelement, html2canvascustomelement *')];
    if (!formulas.length) return;
    const color = documento.defaultView.getComputedStyle(documento.documentElement).getPropertyValue('--text-main');
    formulas.forEach(nodo => { nodo.style.color = color; });
  }

  function prepararNodo(nodo) {
    nodo.style.animation = 'none';
    nodo.style.transition = 'none';
    nodo.style.transform = 'none';
    if (nodo.scrollWidth > nodo.clientWidth) {
      nodo.style.overflow = 'visible';
      nodo.style.maxWidth = 'none';
    }
  }

  async function recorrerLotes(nodos, procesar, estado) {
    for (let inicio = 0; inicio < nodos.length; inicio += TAMANO_LOTE) {
      comprobarEstado(estado);
      nodos.slice(inicio, inicio + TAMANO_LOTE).forEach(procesar);
      if (inicio + TAMANO_LOTE < nodos.length) await ceder();
    }
    comprobarEstado(estado);
  }

  function crearConversor(contexto) {
    const cache = new Map();
    return color => {
      if (cache.has(color)) return cache.get(color);
      contexto.clearRect(0, 0, 1, 1);
      contexto.fillStyle = color;
      contexto.fillRect(0, 0, 1, 1);
      const [rojo, verde, azul, alfa] = contexto.getImageData(0, 0, 1, 1).data;
      const normalizado = `rgba(${rojo}, ${verde}, ${azul}, ${alfa / 255})`;
      cache.set(color, normalizado);
      return normalizado;
    };
  }

  async function normalizarColores(documento, estado) {
    const lienzo = documento.createElement('canvas');
    lienzo.width = lienzo.height = 1;
    try {
      const convertir = crearConversor(lienzo.getContext('2d', {willReadFrequently: true}));
      const nodos = [...documento.querySelectorAll(SELECTOR_CAPTURA)];
      await recorrerLotes(nodos, nodo => {
        const estilos = documento.defaultView.getComputedStyle(nodo);
        for (const propiedad of PROPIEDADES_COLOR) {
          nodo.style[propiedad] = estilos[propiedad].replace(/(?:color|oklab|oklch|lab|lch)\([^)]*\)/g, convertir);
        }
      }, estado);
    } finally {
      lienzo.width = lienzo.height = 0;
    }
  }

  /** Prepara únicamente el documento clonado, abre resultados y conserva sus colores en papel. */
  async function preparar(documento, region, ancho, estado) {
    comprobarEstado(estado);
    documento.documentElement.setAttribute('data-tema', 'papel');
    documento.body.classList.remove('body--dark');
    documento.body.style.backgroundColor = 'white';
    documento.querySelectorAll('[data-pdf-excluir]').forEach(nodo => nodo.remove());
    expandirResultados(documento, region);
    prepararFormulas(documento);
    region.style.setProperty('width', `${ancho}px`, 'important');
    await recorrerLotes([...documento.querySelectorAll(SELECTOR_CAPTURA)], prepararNodo, estado);
    documento.querySelectorAll('.numericos-residuo-activo').forEach(nodo => {
      nodo.style.paddingBlock = 'var(--space-1)';
    });
    await ceder();
    await normalizarColores(documento, estado);
    await ceder();
    comprobarEstado(estado);
  }

  window.scalaris.clonPdf = {preparar, ceder, pintarIndicador};
}
