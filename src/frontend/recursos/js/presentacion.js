/** Secuencia de marca al entrar por la raíz una vez por sesión de pestaña. */
'use strict';
{
  window.scalaris = window.scalaris || {};
  if (!window.scalaris.presentacion) {
    const raiz = document.documentElement;
    const animaciones = new Set();
    const temporizadores = new Set();
    const preferencia = window.matchMedia('(prefers-reduced-motion: reduce)');
    let fondo = null;
    let completada = false;
    let resolver;
    const estado = { activa: false, terminada: new Promise(respuesta => { resolver = respuesta; }), finalizar };
    window.scalaris.presentacion = estado;

    function programar(accion, demora) {
      const identificador = setTimeout(() => { temporizadores.delete(identificador); accion(); }, demora);
      temporizadores.add(identificador);
    }

    function finalizar() {
      if (completada) return;
      completada = true;
      temporizadores.forEach(clearTimeout);
      temporizadores.clear();
      animaciones.forEach(animacion => animacion.cancel());
      animaciones.clear();
      fondo?.remove();
      raiz.removeAttribute('data-presentacion-activa');
      window.removeEventListener('pagehide', finalizar);
      document.removeEventListener('keydown', finalizar, true);
      document.removeEventListener('pointerdown', finalizar, true);
      document.removeEventListener('visibilitychange', alOcultar);
      preferencia.removeEventListener('change', alReducir);
      estado.activa = false;
      resolver();
    }

    function alOcultar() { if (document.hidden) finalizar(); }
    function alReducir(evento) { if (evento.matches) finalizar(); }

    function debeReproducirse() {
      try {
        const mostrada = sessionStorage.getItem('presentacion-mostrada');
        sessionStorage.setItem('presentacion-mostrada', '1');
        return location.pathname === '/' && !location.search && !mostrada;
      } catch (_) { return false; }
    }

    function animar(elemento, fotogramas, opciones) {
      const animacion = elemento.animate(fotogramas, { fill: 'both', ...opciones });
      animaciones.add(animacion);
      animacion.finished.catch(finalizar);
      return animacion;
    }

    function opciones(token) {
      return { duration: window.scalaris.movimiento.duracion(token), easing: window.scalaris.movimiento.curva() };
    }

    async function reproducirSecuencia() {
      const entrada = [
        animar(fondo.querySelector('#presentacion-logotipo'),
          [{ opacity: 0, transform: 'scale(0.95)' }, { opacity: 1, transform: 'scale(1)' }], opciones('--dur-view')),
        animar(fondo.querySelector('#presentacion-anillo circle'),
          [{ strokeDashoffset: 365 }, { strokeDashoffset: 0 }], opciones('--dur-didactic')),
        animar(fondo.querySelector('#presentacion-nombre'),
          [{ clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0% 0 0)' }], opciones('--dur-view')),
        animar(fondo.querySelector('#presentacion-organizacion'),
          [{ opacity: 0, transform: 'scale(0.95) translateY(16px)' }, { opacity: 1, transform: 'scale(1) translateY(0)' }], opciones('--dur-panel')),
      ];
      await Promise.all(entrada.map(animacion => animacion.finished));
      if (completada) return;
      const cierre = [
        animar(fondo.querySelector('#presentacion-anillo'),
          [{ transform: 'rotate(-90deg) scale(1)' }, { transform: 'rotate(-90deg) scale(1.03)', offset: 0.5 },
            { transform: 'rotate(-90deg) scale(1)' }], opciones('--dur-view')),
        animar(fondo.querySelector('#presentacion-barra'),
          [{ opacity: 0, transform: 'scaleX(0.95)' }, { opacity: 1, transform: 'scaleX(1)' }], opciones('--dur-view')),
      ];
      await Promise.all(cierre.map(animacion => animacion.finished));
      if (completada) return;
      await animar(fondo, [{ opacity: 1, transform: 'scale(1)' }, { opacity: 0, transform: 'scale(1.04)' }],
        opciones('--dur-view-exit')).finished;
      finalizar();
    }

    function reproducir() {
      if (completada) return;
      try {
        if (preferencia.matches) {
          animar(fondo, [{ opacity: 1 }, { opacity: 0 }], opciones('--dur-reduced'))
            .finished.then(finalizar, finalizar);
        } else reproducirSecuencia().catch(finalizar);
      } catch (_) { finalizar(); }
    }

    function montarPresentacion() {
      const plantilla = document.getElementById('presentacion-plantilla');
      fondo = plantilla.content.firstElementChild.cloneNode(true);
      const imagen = fondo.querySelector('#presentacion-logotipo');
      imagen.src = raiz.getAttribute('data-tema') === 'medianoche' ? '/assets/LogoClaro.png' : '/assets/LogoOscuro.png';
      fondo.toggleAttribute('data-movimiento-reducido', preferencia.matches);
      estado.activa = true;
      raiz.setAttribute('data-presentacion-activa', '');
      raiz.appendChild(fondo);
      window.addEventListener('pagehide', finalizar);
      document.addEventListener('keydown', finalizar, true);
      document.addEventListener('pointerdown', finalizar, true);
      document.addEventListener('visibilitychange', alOcultar);
      preferencia.addEventListener('change', alReducir);
      const duracion = window.scalaris.movimiento.duracion;
      const limite = preferencia.matches ? duracion('--dur-reduced') :
        duracion('--dur-didactic') + duracion('--dur-view') + duracion('--dur-view-exit');
      programar(finalizar, limite + duracion('--dur-view'));
      imagen.decode().then(reproducir, finalizar);
    }

    try {
      if (debeReproducirse()) montarPresentacion();
      else finalizar();
    } catch (_) { finalizar(); }
  }
}
