/** Conmutación de temas con fundido de opacidad. */
'use strict';

{
  window.scalaris.tema.preparar();
  let seleccionActual;

  /** Aplica colores, logotipos y persistencia del tema solicitado. */
  function aplicarTema(tema) {
    seleccionActual = {};
    actualizarTema(tema);
  }

  function actualizarTema(tema) {
    document.documentElement.setAttribute('data-tema', tema);
    document.documentElement.style.colorScheme = tema === 'medianoche' ? 'dark' : 'light';
    localStorage.setItem('tema', tema);
    const rutaLogotipo = tema === 'medianoche' ? '/assets/LogoClaro.png' : '/assets/LogoOscuro.png';
    document.querySelectorAll('img.marca-logotipo-reactivo').forEach(function actualizarLogotipo(imagen) {
      imagen.src = rutaLogotipo;
    });
    const seleccion = seleccionActual;
    if (window.scalaris && window.scalaris.actualizarTemaPlotly) {
      setTimeout(function actualizarGraficos() {
        if (seleccion !== seleccionActual) return;
        window.scalaris.actualizarTemaPlotly(tema);
      }, 50);
    }
  }

  /** Establece el tema mediante una transición cuando el navegador la admite. */
  function establecerTema(tema) {
    const seleccion = {};
    seleccionActual = seleccion;
    const aplicarSeleccion = function () {
      if (seleccion === seleccionActual) actualizarTema(tema);
    };
    const movimiento = window.scalaris.movimiento;
    if (!document.startViewTransition || (movimiento && !movimiento.permitido())) {
      aplicarSeleccion();
      return;
    }
    const transicion = document.startViewTransition(aplicarSeleccion);
    transicion.ready.then(function animarFundido() {
      if (seleccion !== seleccionActual) return;
      document.documentElement.animate(
        [{ opacity: 0 }, { opacity: 1 }],
        {
          duration: 240,
          easing: 'cubic-bezier(0.32, 0.72, 0, 1)',
          pseudoElement: '::view-transition-new(root)'
        }
      );
    }).catch(aplicarSeleccion);
  }

  window.scalaris.tema = { aplicar: aplicarTema, establecer: establecerTema };
}
