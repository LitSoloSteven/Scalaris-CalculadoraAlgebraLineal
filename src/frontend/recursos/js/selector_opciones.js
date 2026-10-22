"use strict";
{
    function activar(evento) {
        const boton = evento.currentTarget;
        const grupo = boton.closest('.selector-opciones');
        const opciones = Array.from(grupo.querySelectorAll('[role="radio"]'));
        const indice = opciones.indexOf(boton);
        const anterior = Math.max(0, opciones.findIndex(opcion => opcion.getAttribute?.('aria-checked') === 'true'));
        const columnas = Number(grupo.dataset?.selectorColumnas) || opciones.length;
        const indicador = grupo.querySelector?.('.selector-opciones-indicador');
        const origen = indicador && window.getComputedStyle?.(indicador).transform;
        if (origen) grupo.style.setProperty('--selector-origen-transformacion', origen);
        grupo.classList?.remove('selector-opciones-cambiando');
        grupo.style.setProperty('--selector-indice-anterior', anterior);
        grupo.style.setProperty('--selector-columna-anterior', anterior % columnas);
        grupo.style.setProperty('--selector-fila-anterior', Math.floor(anterior / columnas));
        grupo.style.setProperty('--selector-indice', indice);
        grupo.style.setProperty('--selector-columna-compacta', indice % columnas);
        grupo.style.setProperty('--selector-fila-compacta', Math.floor(indice / columnas));
        opciones.forEach(opcion => {
            const activo = opcion === boton;
            opcion.setAttribute('aria-checked', String(activo));
            opcion.setAttribute('tabindex', activo ? '0' : '-1');
        });
        if (indice !== anterior) {
            void grupo.offsetWidth;
            grupo.classList?.add('selector-opciones-cambiando');
        }
    }

    function teclado(evento) {
        const desplazamientos = { ArrowLeft: -1, ArrowRight: 1 };
        const desplazamiento = desplazamientos[evento.key];
        if (desplazamiento === undefined || evento.altKey || evento.ctrlKey || evento.metaKey) return;
        const boton = evento.currentTarget;
        const opciones = Array.from(boton.closest('.selector-opciones').querySelectorAll('[role="radio"]'));
        const indice = (opciones.indexOf(boton) + desplazamiento + opciones.length) % opciones.length;
        evento.preventDefault();
        opciones[indice].focus();
        opciones[indice].click();
    }

    window.scalaris = window.scalaris || {};
    window.scalaris.selectorOpciones = { activar, teclado };
}
