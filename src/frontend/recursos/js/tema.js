/** Conmutación circular de temas con selección y cancelación explícitas. */
'use strict';
{
  window.scalaris.tema.preparar();
  const raiz = document.documentElement;
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
    const control = document.querySelector('[aria-label="Seleccionar Tema"]');
    const caja = control?.getBoundingClientRect();
    const centro = caja ? { x: caja.left + caja.width / 2, y: caja.top + caja.height / 2 } :
      { x: window.innerWidth / 2, y: window.innerHeight / 2 };
    const punto = origen && Number.isFinite(origen.x) && Number.isFinite(origen.y) ? origen : centro;
    return { x: Math.max(0, Math.min(punto.x, window.innerWidth)), y: Math.max(0, Math.min(punto.y, window.innerHeight)) };
  }

  function movimientoDisponible() {
    if (!document.startViewTransition || typeof raiz.animate !== 'function') return false;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return false;
    if (window.scalaris.presentacion?.activa) return false;
    return !raiz.hasAttribute('data-navegacion-circular');
  }

  function animarCirculo(seleccion, origen) {
    if (seleccion !== seleccionActual || seleccion.cancelada) return;
    const radio = Math.hypot(Math.max(origen.x, window.innerWidth - origen.x), Math.max(origen.y, window.innerHeight - origen.y));
    const centro = `at ${origen.x}px ${origen.y}px`;
    seleccion.animacion = raiz.animate(
      { clipPath: [`circle(0px ${centro})`, `circle(${radio}px ${centro})`] },
      { duration: 500, easing: 'cubic-bezier(0.32, 0.72, 0, 1)', pseudoElement: '::view-transition-new(root)' },
    );
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
