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

    function reproducirSecuencia() {
      const curva = getComputedStyle(raiz).getPropertyValue('--ease-std').trim();
      animar(fondo.querySelector('#presentacion-logotipo'),
        [{ opacity: 0, transform: 'scale(0.88)' }, { opacity: 1, transform: 'scale(1)' }],
        { duration: 600, easing: curva });
      animar(fondo.querySelector('#presentacion-anillo circle'),
        [{ strokeDashoffset: 365 }, { strokeDashoffset: 0 }], { duration: 1200, delay: 600, easing: curva });
      animar(fondo.querySelector('#presentacion-nombre'),
        [{ clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0% 0 0)' }],
        { duration: 500, delay: 800, easing: curva });
      animar(fondo.querySelector('#presentacion-organizacion'),
        [{ opacity: 0, transform: 'translateY(3px)' }, { opacity: 1, transform: 'translateY(0)' }],
        { duration: 400, delay: 1200, easing: curva });
      animar(fondo.querySelector('#presentacion-anillo'),
        [{ transform: 'rotate(-90deg) scale(1)' }, { transform: 'rotate(-90deg) scale(1.03)', offset: 0.5 },
          { transform: 'rotate(-90deg) scale(1)' }], { duration: 800, delay: 1800, easing: curva });
      animar(fondo.querySelector('#presentacion-barra'),
        [{ transform: 'scaleX(0)' }, { transform: 'scaleX(1)' }], { duration: 600, delay: 1800, easing: curva });
      animar(fondo, [{ opacity: 1, transform: 'scale(1)' }, { opacity: 0, transform: 'scale(1.04)' }],
        { duration: 400, delay: 2600, easing: curva }).finished.then(finalizar, finalizar);
    }

    function reproducir() {
      if (completada) return;
      try {
        if (preferencia.matches) {
          animar(fondo, [{ opacity: 1 }, { opacity: 0 }], { duration: 120, delay: 280 })
            .finished.then(finalizar, finalizar);
        } else reproducirSecuencia();
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
      programar(finalizar, preferencia.matches ? 800 : 3800);
      imagen.decode().then(reproducir, finalizar);
    }

    try {
      if (debeReproducirse()) montarPresentacion();
      else finalizar();
    } catch (_) { finalizar(); }
  }
}
