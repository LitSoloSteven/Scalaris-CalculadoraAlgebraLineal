/** Prepara una fórmula fuera de la vista y transfiere solo la revisión vigente. */
{
    "use strict";
    const preparaciones = new WeakMap();

    async function esperarMathJax() {
        const limite = Date.now() + 4000;
        while (!window.MathJax?.tex2chtmlPromise && Date.now() < limite) {
            await new Promise(resolver => setTimeout(resolver, 100));
        }
        return window.MathJax?.tex2chtmlPromise;
    }

    async function componer(nodo, latex, estado, revision) {
        if (!nodo.isConnected || estado.revision !== revision || !latex) return false;
        try {
            if (!await esperarMathJax() || estado.revision !== revision || !nodo.isConnected) return false;
            const formula = await window.MathJax.tex2chtmlPromise(latex, { display: true });
            if (!nodo.isConnected || estado.revision !== revision) return false;
            window.MathJax.startup.document.updateDocument();
            estado.formula = formula;
            return true;
        } catch {
            return false;
        }
    }

    async function preparar({ cuerpo, revision, latex, puntero, token, extremos }) {
        const nodo = document.getElementById(cuerpo);
        if (!nodo) return false;
        const estado = preparaciones.get(nodo) ?? {};
        preparaciones.set(nodo, estado);
        estado.observador?.disconnect();
        estado.revision = revision;
        estado.formula = null;
        estado.pendiente?.resolver(false);
        return new Promise(resolver => {
            estado.pendiente = { latex, revision, puntero, token, extremos, resolver };
            if (!estado.activo) void procesar(nodo, estado);
        });
    }

    async function procesar(nodo, estado) {
        estado.activo = true;
        while (estado.pendiente) {
            const { latex, revision, puntero, token, extremos, resolver } = estado.pendiente;
            estado.pendiente = null;
            const preparado = await componer(nodo, latex, estado, revision);
            if (estado.revision === revision) prepararPublicacion(nodo, estado, {
                revision, puntero, token, extremos: preparado ? extremos : null, preparado,
            });
            resolver(preparado);
        }
        estado.activo = false;
    }

    function prepararPublicacion(nodo, estado, datos) {
        window.scalaris.movimientoBiseccion.cancelar(nodo);
        window.scalaris.bandaBiseccion?.preparar(nodo, datos.extremos, datos.token);
        if (datos.preparado) vigilarPublicacion(nodo, estado, datos);
    }

    function vigilarPublicacion(nodo, estado, { revision, puntero, token }) {
        estado.observador = new MutationObserver(() => {
            const destino = nodo.querySelector(`[data-biseccion-formula="${revision}"] .matematicas-desplazamiento`);
            if (destino) transferir(destino, nodo, estado, { revision, puntero, token });
        });
        estado.observador.observe(nodo, { childList: true, subtree: true });
    }

    function descartar([cuerpo, revision]) {
        const estado = preparaciones.get(document.getElementById(cuerpo));
        if (estado && estado.revision < revision) {
            estado.revision = revision;
            estado.formula = null;
            estado.observador?.disconnect();
            estado.pendiente?.resolver(false);
            estado.pendiente = null;
        }
    }

    function publicar({ identificador, cuerpo, revision, puntero, token }) {
        const nodo = document.getElementById(cuerpo);
        const destino = document.getElementById(identificador);
        if (!destino || !nodo?.contains(destino)) return;
        const estado = preparaciones.get(nodo);
        if (!destino.querySelector?.("mjx-container")
            && !transferir(destino, nodo, estado, { revision, puntero, token })) {
            window.scalaris.renderizarMathJaxVigente(identificador);
        }
    }

    function transferir(destino, nodo, estado, { revision, puntero, token }) {
        if (estado?.revision !== revision || !estado.formula) return false;
        estado.observador?.disconnect();
        destino.replaceChildren(estado.formula);
        estado.formula = null;
        window.scalaris.movimientoBiseccion.entrada(nodo, puntero, 12, token);
        return true;
    }

    window.scalaris.pasoBiseccion = { preparar, publicar, descartar };
}
