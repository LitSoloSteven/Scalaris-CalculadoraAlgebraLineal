/** Conmutación circular de temas con selección y cancelación explícitas. */
'use strict';
{
  window.scalaris.tema.preparar();
  const raiz = document.documentElement;
  const revelado = window.scalaris.reveladoCircular;
  let seleccionActual;

  function limpiar(seleccion) {
    seleccion.animacion?.cancel();
    if (seleccion !== seleccionActual) return;
    raiz.removeAttribute('data-tema-circular');
  }

  function cancelarActual() {
    if (!seleccionActual) return;
    seleccionActual.cancelada = true;
    seleccionActual.transicion?.skipTransition();
    limpiar(seleccionActual);
  }

  function nuevaSeleccion() {
    cancelarActual();
    seleccionActual = {};
    return seleccionActual;
  }

  /** Aplica colores, logotipos y persistencia del tema solicitado. */
  function aplicarTema(tema) {
    nuevaSeleccion();
    return actualizarTema(tema);
  }

  function actualizarTema(tema) {
    raiz.setAttribute('data-tema', tema);
    raiz.style.colorScheme = tema === 'medianoche' ? 'dark' : 'light';
    try { localStorage.setItem('tema', tema); } catch (_) { /* La paleta sigue disponible sin persistencia. */ }
    const rutaLogotipo = tema === 'medianoche' ? '/assets/LogoClaro.png' : '/assets/LogoOscuro.png';
    const logotipos = Array.from(document.querySelectorAll('img.marca-logotipo-reactivo')).map(imagen => {
      imagen.src = rutaLogotipo;
      try { return imagen.decode?.(); } catch (_) { return null; }
    });
    try { logotipos.push(window.scalaris.actualizarTemaPlotly?.(tema)); } catch (_) { /* Un gráfico no bloquea la paleta. */ }
    return Promise.allSettled(logotipos);
  }

  function origenDelControl(origen) {
    if (Number.isFinite(origen?.x) && Number.isFinite(origen?.y)) return origen;
    return revelado.centroDe(
      document.querySelector('[data-selector-tema-boton], [aria-label="Seleccionar tema"], [aria-label="Seleccionar Tema"]')
    );
  }

  function movimientoDisponible() {
    if (!revelado || !document.startViewTransition || typeof raiz.animate !== 'function') return false;
    if (!window.scalaris.movimiento.permitido()) return false;
    if (window.scalaris.presentacion?.activa) return false;
    return !raiz.hasAttribute('data-navegacion-circular');
  }

  function animarCirculo(seleccion, origen) {
    if (seleccion !== seleccionActual || seleccion.cancelada) return;
    seleccion.animacion = revelado.animarCaptura(raiz, origen);
    seleccion.animacion.finished.catch(() => {});
  }

  function iniciarTransicion(seleccion, aplicar, origen) {
    raiz.setAttribute('data-tema-circular', '');
    try {
      const transicion = document.startViewTransition(aplicar);
      seleccion.transicion = transicion;
      transicion.updateCallbackDone.catch(() => {});
      transicion.finished.then(() => limpiar(seleccion), () => limpiar(seleccion));
      transicion.ready.then(() => animarCirculo(seleccion, origen)).catch(() => {
        if (seleccion !== seleccionActual) return;
        transicion.skipTransition();
        limpiar(seleccion);
        aplicar();
      });
    } catch (_) {
      limpiar(seleccion);
      aplicar();
    }
  }

  /** Revela la selección desde su control; el teclado también conserva su origen. */
  function establecerTema(tema, origen) {
    const seleccion = nuevaSeleccion();
    const aplicar = () => {
      if (seleccion !== seleccionActual) return;
      return actualizarTema(tema);
    };
    if (!movimientoDisponible() || raiz.getAttribute('data-tema') === tema) {
      aplicar();
      return;
    }
    iniciarTransicion(seleccion, aplicar, origenDelControl(origen));
  }

  window.addEventListener('pageswap', cancelarActual);
  window.addEventListener('pagehide', cancelarActual);
  window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', evento => {
    if (evento.matches) cancelarActual();
  });
  window.scalaris.tema = { aplicar: aplicarTema, establecer: establecerTema };
}
