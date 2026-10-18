'use strict';
{

  window.scalaris = window.scalaris || {};

  let temporizadorPendiente = null;
  let observadorPresentacion = null;
  let presentacionEstabaPresente = false;
  let limiteEsperaPendiente = 0;

  if (window.location && window.location.pathname === '/') {
    document.documentElement.setAttribute('data-glosa', 'cerrado');
    if (document.body) document.body.classList.add('inicio-pagina');
    document.documentElement.setAttribute('data-inicio-pendiente', '');
    limiteEsperaPendiente = Date.now() + 3400;
    presentacionEstabaPresente = Boolean(document.getElementById('aplicacion-presentacion-fondo'));
    if (window.MutationObserver) {
      observadorPresentacion = new MutationObserver(function () {
        let existePresentacion = Boolean(document.getElementById('aplicacion-presentacion-fondo'));
        if (existePresentacion) presentacionEstabaPresente = true;
        else if (presentacionEstabaPresente) finalizar_pendiente();
      });
      observadorPresentacion.observe(document.documentElement, { childList: true, subtree: true });
    }
    temporizadorPendiente = setTimeout(function () {
      temporizadorPendiente = null;
      if (document.getElementById('aplicacion-presentacion-fondo')) {
        temporizadorPendiente = setTimeout(finalizar_pendiente, Math.max(0, limiteEsperaPendiente - Date.now()));
      } else {
        finalizar_pendiente();
      }
    }, 1200);
  }

  function finalizar_pendiente() {
    if (temporizadorPendiente) {
      clearTimeout(temporizadorPendiente);
      temporizadorPendiente = null;
    }
    if (observadorPresentacion) {
      observadorPresentacion.disconnect();
      observadorPresentacion = null;
    }
    document.documentElement.removeAttribute('data-inicio-pendiente');
  }

  function limpiar_pendiente() {
    if (!document.getElementById('aplicacion-presentacion-fondo')) finalizar_pendiente();
  }

  let dialogoActivo = null;
  let origenActivo = null;
  let temporizadorCierre = null;
  let manejar_transicion_cierre = null;
  let dialogoCerrandose = null;
  let posicionesDestacada = new WeakMap();
  let fotogramasDestacada = new WeakMap();

  function establecer_modo_entrada(inmediato) {
    if (inmediato) document.documentElement.setAttribute('data-entrada', 'teclado');
    else document.documentElement.removeAttribute('data-entrada');
  }

  function cancelar_espera_cierre() {
    if (temporizadorCierre) {
      clearTimeout(temporizadorCierre);
      temporizadorCierre = null;
    }
    if (manejar_transicion_cierre && dialogoCerrandose) {
      let tarjeta = dialogoCerrandose.querySelector('.inicio-dialogo-tarjeta');
      if (tarjeta) tarjeta.removeEventListener('transitionend', manejar_transicion_cierre);
    }
    manejar_transicion_cierre = null;
    dialogoCerrandose = null;
  }

  function finalizar_cierre(dialogo, devolverFoco) {
    let identificadorPilar = dialogo.id.replace(/^inicio-dialogo-/, '');
    let origen = origenActivo || document.getElementById('inicio-fila-' + identificadorPilar);
    cancelar_espera_cierre();
    if (dialogo.open) dialogo.close();
    dialogo.removeAttribute('data-abierto');
    document.documentElement.removeAttribute('data-inicio-dialogo-abierto');
    let tarjeta = dialogo.querySelector('.inicio-dialogo-tarjeta');
    if (tarjeta) tarjeta.style.removeProperty('transform-origin');
    if (dialogoActivo === dialogo) {
      dialogoActivo = null;
      origenActivo = null;
    }
    if (devolverFoco !== false && origen && origen.isConnected) {
      origen.focus({ preventScroll: true });
    }
  }

  function calcular_desplazamiento(desplazamiento) {
    return desplazamiento < 0 ? '- ' + Math.abs(desplazamiento) + 'px' : '+ ' + desplazamiento + 'px';
  }

  function establecer_origen_ventana_emergente(tarjeta, fila) {
    let rectangulo = fila.getBoundingClientRect();
    let centroHorizontal = rectangulo.left + rectangulo.width / 2;
    let centroVertical = rectangulo.top + rectangulo.height / 2;
    let desplazamientoHorizontal = centroHorizontal - window.innerWidth / 2;
    let origenVertical;
    if (window.matchMedia('(max-width: 639px)').matches) {
      origenVertical = 'calc(100% ' + calcular_desplazamiento(centroVertical - window.innerHeight) + ')';
    } else {
      origenVertical = 'calc(50% ' + calcular_desplazamiento(centroVertical - window.innerHeight / 2) + ')';
    }
    tarjeta.style.transformOrigin = 'calc(50% ' + calcular_desplazamiento(desplazamientoHorizontal) + ') ' + origenVertical;
  }

  function prepararOrigenDialogo(dialogo, fila, inmediato) {
    let tarjeta = dialogo.querySelector('.inicio-dialogo-tarjeta');
    if (tarjeta) {
      if (inmediato) tarjeta.style.removeProperty('transform-origin');
      else establecer_origen_ventana_emergente(tarjeta, fila);
    }
  }

  function enfocarDialogo(dialogo) {
    let focoInicial = dialogo.querySelector('.inicio-tarjeta.esta-destacada')
      || dialogo.querySelector('.inicio-tarjeta')
      || dialogo.querySelector('.inicio-dialogo-cerrar');
    if (focoInicial) focoInicial.focus({ preventScroll: true });
  }

  function abrir(identificadorPilar, opciones) {
    let inmediato = opciones && opciones.inmediato;
    let elementoOrigen = opciones && opciones.elementoOrigen;
    limpiar_pendiente();
    let fila = elementoOrigen || document.getElementById('inicio-fila-' + identificadorPilar);
    let dialogo = document.getElementById('inicio-dialogo-' + identificadorPilar);
    if (!fila || !dialogo || typeof dialogo.showModal !== 'function') return;

    establecer_modo_entrada(Boolean(inmediato));
    if (dialogoActivo && dialogoActivo !== dialogo) {
      finalizar_cierre(dialogoActivo, false);
    }
    cancelar_espera_cierre();

    prepararOrigenDialogo(dialogo, fila, inmediato);
    if (!dialogo.open) dialogo.showModal();

    dialogo.setAttribute('data-abierto', '');
    fila.setAttribute('aria-expanded', 'true');
    dialogoActivo = dialogo;
    origenActivo = fila;
    document.documentElement.setAttribute('data-inicio-dialogo-abierto', '');

    enfocarDialogo(dialogo);
  }

  function colapsarFilasInicio() {
    let filasExpandidas = document.querySelectorAll('.inicio-fila[aria-expanded="true"]');
    for (let i = 0; i < filasExpandidas.length; i++) {
      filasExpandidas[i].setAttribute('aria-expanded', 'false');
    }

  }

  function cerrar(opciones) {
    let inmediato = opciones && opciones.inmediato;
    let dialogo = dialogoActivo || document.querySelector('dialog.inicio-dialogo[open]');
    if (!dialogo) return;

    if (inmediato) establecer_modo_entrada(true);
    colapsarFilasInicio();

    dialogo.removeAttribute('data-abierto');
    if (inmediato || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      finalizar_cierre(dialogo);
      return;
    }

    if (temporizadorCierre && dialogoCerrandose === dialogo) return;
    cancelar_espera_cierre();
    dialogoCerrandose = dialogo;
    let tarjeta = dialogo.querySelector('.inicio-dialogo-tarjeta');
    if (!tarjeta) {
      finalizar_cierre(dialogo);
      return;
    }
    manejar_transicion_cierre = function (evento) {
      if (evento.target === tarjeta && evento.propertyName === 'opacity') finalizar_cierre(dialogo);
    };
    tarjeta.addEventListener('transitionend', manejar_transicion_cierre);
    temporizadorCierre = setTimeout(function () { finalizar_cierre(dialogo); }, 220);
  }

  function esta_halo_deshabilitado(evento) {
    return evento.pointerType === 'touch'
      || document.documentElement.getAttribute('data-entrada') === 'teclado'
      || !window.matchMedia('(hover: hover) and (pointer: fine)').matches
      || window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function mover_destacada(fila, evento) {
    let destacada = fila.querySelector('.inicio-destacada');
    if (!destacada) return;
    let rectangulo = fila.getBoundingClientRect();
    posicionesDestacada.set(fila, {
      x: evento.clientX - rectangulo.left,
      y: evento.clientY - rectangulo.top,
    });
    if (fotogramasDestacada.has(fila)) return;

    let fotograma = window.requestAnimationFrame(function () {
      fotogramasDestacada.delete(fila);
      let posicion = posicionesDestacada.get(fila);
      if (!posicion || !fila.isConnected) return;
      destacada.style.transform = 'translate3d(' + posicion.x + 'px, ' + posicion.y + 'px, 0)';
    });
    fotogramasDestacada.set(fila, fotograma);
  }

  function limpiar_destacada_al_salir_puntero(evento) {
    let objetivo = evento.target;
    if (!objetivo || typeof objetivo.closest !== 'function') return;
    let fila = objetivo.closest('.inicio-fila');
    let relacionado = evento.relatedTarget;
    let siguienteFila = relacionado && typeof relacionado.closest === 'function'
      ? relacionado.closest('.inicio-fila')
      : null;
    if (fila && fila !== siguienteFila) fila.removeAttribute('data-destacada-activa');
  }

  function manejar_clic_delegado(evento) {
    let objetivo = evento.target;
    if (!objetivo || typeof objetivo.closest !== 'function') return;
    let botonCerrar = objetivo.closest('.inicio-dialogo-cerrar');
    if (botonCerrar) {
      establecer_modo_entrada(evento.detail === 0);
      cerrar({ inmediato: evento.detail === 0 });
      return;
    }
    let dialogo = objetivo.closest('dialog.inicio-dialogo');
    if (dialogo && objetivo === dialogo) {
      establecer_modo_entrada(evento.detail === 0);
      cerrar({ inmediato: evento.detail === 0 });
      return;
    }
    let fila = objetivo.closest('.inicio-fila');
    if (fila && !objetivo.closest('.inicio-tarjeta')) {
      establecer_modo_entrada(evento.detail === 0);
      abrir(fila.id.replace(/^inicio-fila-/, ''), { inmediato: evento.detail === 0, elementoOrigen: fila });
    }
  }

  function registrar_manejadores_delegados() {
    if (window.__scalarisInicioDelegado) return;
    window.__scalarisInicioDelegado = true;
    document.addEventListener('click', manejar_clic_delegado);
    document.addEventListener('cancel', function (evento) {
      let dialogo = evento.target;
      if (dialogo && dialogo.classList && dialogo.classList.contains('inicio-dialogo')) {
        evento.preventDefault();
        cerrar({ inmediato: true });
      }
    });
    document.addEventListener('keydown', function (evento) {
      if (evento.key === 'Escape' && dialogoActivo) {
        establecer_modo_entrada(true);
        cerrar({ inmediato: true });
      }
    });
    document.addEventListener('pointerenter', function (evento) {
      if (esta_halo_deshabilitado(evento) || !evento.target || typeof evento.target.closest !== 'function') return;
      let fila = evento.target.closest('.inicio-fila');
      if (fila) { fila.setAttribute('data-destacada-activa', ''); mover_destacada(fila, evento); }
    }, true);
    document.addEventListener('pointermove', function (evento) {
      if (esta_halo_deshabilitado(evento) || !evento.target || typeof evento.target.closest !== 'function') return;
      let fila = evento.target.closest('.inicio-fila');
      if (fila) { if (!fila.hasAttribute('data-destacada-activa')) fila.setAttribute('data-destacada-activa', ''); mover_destacada(fila, evento); }
    }, { capture: true, passive: true });
    document.addEventListener('pointerout', limpiar_destacada_al_salir_puntero, true);
  }

  registrar_manejadores_delegados();

  window.scalaris.inicio = {
    abrir: abrir,
    cerrar: cerrar
  };
}
