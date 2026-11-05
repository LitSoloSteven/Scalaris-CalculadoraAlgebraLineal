/** Proyecta una pulsación deliberada sobre el eje x del gráfico de bisección. */
{
    "use strict";
    const inicios = new WeakMap();
    const tolerancia = 6;

    function coordenadas(evento, grafico, layout) {
        const rectangulo = grafico.getBoundingClientRect();
        return [
            evento.clientX - rectangulo.left - layout.xaxis._offset,
            evento.clientY - rectangulo.top - layout.yaxis._offset,
        ];
    }

    function dentroDeEjes(x, y, layout) {
        return x >= 0 && x <= layout.xaxis._length && y >= 0 && y <= layout.yaxis._length;
    }

    window.scalaris.graficoBiseccion = {
        iniciar(evento) {
            const grafico = evento.currentTarget;
            inicios.delete(grafico);
            if (grafico.closest(".biseccion-seleccion-activa")
                && evento.isPrimary && evento.button === 0 && !evento.target.closest(".modebar")) {
                inicios.set(grafico, [evento.clientX, evento.clientY]);
            }
        },
        abscisa(evento) {
            const grafico = evento.currentTarget;
            const inicio = inicios.get(grafico);
            inicios.delete(grafico);
            if (!inicio || evento.target.closest(".modebar")
                || Math.hypot(evento.clientX - inicio[0], evento.clientY - inicio[1]) > tolerancia) {
                return null;
            }
            const layout = grafico._fullLayout;
            if (!layout?.xaxis?.p2l || !layout.yaxis) return null;
            const [x, y] = coordenadas(evento, grafico, layout);
            if (!dentroDeEjes(x, y, layout)) return null;
            const valor = layout.xaxis.p2l(x);
            return Number.isFinite(valor) ? valor : null;
        },
        marcar(evento) {
            const valor = this.abscisa(evento);
            if (valor !== null) {
                evento.currentTarget.dispatchEvent(new CustomEvent("biseccion_abscisa", { detail: valor }));
            }
        },
    };
}
