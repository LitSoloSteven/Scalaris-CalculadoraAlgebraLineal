/** Resuelve una señal semántica con prioridad explícita, reglas e iconos. */
{
    'use strict';
    window.scalaris = window.scalaris || {};
    const catalogo = window.scalaris.catalogoSonidos;
    const asignaciones = catalogo.asignaciones;

    function indiceControl(control, opciones) {
        const declarada = control.getAttribute('data-sonido-indice');
        const hermanos = control.parentElement?.querySelectorAll('[role=tab], button') || [];
        const indice = declarada === null ? Array.from(hermanos).indexOf(control) : Number(declarada);
        return opciones[Math.max(0, indice) % opciones.length];
    }

    function resolverRegla(control, regla) {
        if (regla.estado) return regla.estado[Number(control.getAttribute('aria-checked') === 'true')];
        if (regla.desplegable) return regla.desplegable[Number(control.getAttribute('aria-expanded') === 'true')];
        if (regla.indice) return indiceControl(control, regla.indice);
        if (regla.expansion) {
            const cerrada = control.closest('.q-expansion-item')?.classList.contains('q-expansion-item--collapsed');
            return regla.expansion[Number(!cerrada)];
        }
        return regla.sonido;
    }

    function resolver(control) {
        const explicito = control.getAttribute('data-sonido');
        if (explicito !== null) return Object.hasOwn(catalogo.perfiles, explicito) ? explicito : null;
        const regla = asignaciones.selectores.find(entrada => control.matches(entrada.selector));
        if (regla) return resolverRegla(control, regla);
        const icono = control.querySelector('.q-icon')?.textContent.trim();
        return Object.hasOwn(asignaciones.iconos, icono) ? asignaciones.iconos[icono] : asignaciones.generico;
    }

    function escritura(tipo, esEspacio) {
        const perfiles = asignaciones.escritura;
        if (tipo?.startsWith('delete')) return perfiles.borrado;
        if (tipo === 'insertLineBreak' || tipo === 'insertParagraph') return perfiles.enter;
        return esEspacio ? perfiles.espacio : perfiles.normal;
    }

    window.scalaris.asignacionSonora = { resolver, escritura };
}
