/** Proyecta la banda en una capa recortada al área trazable. */
{
    "use strict";
    const capas = new WeakMap();
    const solicitudes = new WeakMap();
    const reducido = window.matchMedia("(prefers-reduced-motion: reduce)");

    function proyectar(grafico) {
        const { xaxis, yaxis, shapes } = grafico._fullLayout ?? {};
        const intervalo = shapes?.[0];
        if (!intervalo?.visible || !xaxis?.l2p || !yaxis) return null;
        const ancho = xaxis._length;
        const puntos = [intervalo.x0, intervalo.x1].map(valor => xaxis.l2p(valor));
        if (!puntos.every(Number.isFinite) || !Number.isFinite(ancho) || ancho <= 0) return null;
        const limitar = posicion => Math.max(0, Math.min(ancho, posicion));
        const izquierda = limitar(Math.min(...puntos));
        const longitud = limitar(Math.max(...puntos)) - izquierda;
        const recorte = [xaxis._offset, yaxis._offset, ancho, yaxis._length];
        return {
            recorte, escala: [...recorte, ...xaxis.range].join(","),
            extremos: [intervalo.x0, intervalo.x1].join(","),
            color: intervalo.fillcolor, opacidad: intervalo.opacity,
            transform: `translateX(${izquierda}px) scaleX(${longitud})`,
        };
    }

    function obtenerCapa(marco) {
        if (capas.has(marco)) return capas.get(marco);
        const recorte = document.createElement("div");
        recorte.className = "biseccion-recorte-banda";
        recorte.setAttribute("aria-hidden", "true");
        const banda = document.createElement("div");
        banda.className = "biseccion-banda";
        recorte.append(banda);
        marco.append(recorte);
        const capa = { recorte, banda };
        capas.set(marco, capa);
        return capa;
    }

    function mostrarEstatica(marco) {
        delete marco.dataset.biseccionBanda;
        const capa = capas.get(marco);
        if (!capa) return;
        window.scalaris.movimientoBiseccion.cancelar(capa.banda);
        capa.recorte.hidden = true;
        capa.geometria = null;
    }

    function actualizar(grafico) {
        const marco = grafico?.parentElement;
        if (!marco) return;
        const geometria = !reducido.matches && proyectar(grafico);
        const forma = grafico.querySelector('.shape-group[data-index="0"] path');
        if (!geometria || !forma) return mostrarEstatica(marco);
        const capa = obtenerCapa(marco);
        const solicitud = solicitudes.get(marco);
        const anterior = capa.geometria;
        const coincide = solicitud?.extremos === geometria.extremos;
        if (coincide) solicitudes.delete(marco);
        capa.banda.style.backgroundColor = geometria.color;
        capa.banda.style.opacity = geometria.opacidad;
        if (anterior?.escala === geometria.escala && anterior.transform === geometria.transform) return;
        const [izquierda, superior, ancho, alto] = geometria.recorte.map(valor => `${valor}px`);
        Object.assign(capa.recorte.style, { left: izquierda, top: superior, width: ancho, height: alto });
        capa.recorte.hidden = false;
        marco.dataset.biseccionBanda = "";
        capa.geometria = geometria;
        capa.banda.style.transform = geometria.transform;
        if (!coincide || anterior?.escala !== geometria.escala) {
            window.scalaris.movimientoBiseccion.cancelar(capa.banda);
            return;
        }
        window.scalaris.movimientoBiseccion.animar(capa.banda, { transform: geometria.transform }, {
            origen: { transform: anterior.transform }, puntero: true, token: solicitud.token,
        });
    }

    function preparar(reproductor, extremos, token) {
        const marco = reproductor?.closest(".biseccion-vista")?.querySelector(".biseccion-marco-grafico");
        if (!marco) return;
        if (extremos) solicitudes.set(marco, { extremos: extremos.join(","), token });
        else solicitudes.delete(marco);
    }

    reducido.addEventListener("change", () => {
        for (const grafico of document.querySelectorAll(".biseccion-grafica")) actualizar(grafico);
    });
    window.scalaris.bandaBiseccion = { actualizar, preparar };
}
