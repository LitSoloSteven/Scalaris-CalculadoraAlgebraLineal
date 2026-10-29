"use strict";

const afirmar = require("node:assert/strict");
const prueba = require("node:test");
const { cargarAssetCliente } = require("./comun_cliente_javascript.js");
const { crearTemaSimulado, cargarTemaCompleto, simularTransicion } = require("./comun_tema_cliente.js");

prueba("los valores canónicos se leen antes de cargar los estilos", () => {
    for (const [almacenado, esperado] of [["papel", "papel"], ["marea", "marea"], ["medianoche", "medianoche"]]) {
        const cliente = crearTemaSimulado(almacenado);
        cargarAssetCliente("inicializacion_tema.js", cliente.contexto);
        afirmar.equal(cliente.atributos.get("data-tema"), esperado);
        afirmar.equal(cliente.almacen.get("tema"), esperado);
        afirmar.equal(cliente.documento.documentElement.style.colorScheme, esperado === "medianoche" ? "dark" : "light");
        afirmar.equal(JSON.stringify(cliente.ventana.scalaris.graficos), JSON.stringify(cliente.graficos));
    }
});

prueba("el tema inicial conserva valores canónicos desconocidos y ausencia", () => {
    for (const [almacenado, esperado] of [[null, "papel"], ["marea", "marea"], ["desconocido", "desconocido"]]) {
        const cliente = crearTemaSimulado(almacenado);
        cargarTemaCompleto(cliente);
        afirmar.equal(cliente.atributos.get("data-tema"), esperado);
        afirmar.equal(cliente.almacen.get("tema") ?? null, almacenado);
        afirmar.equal(cliente.logotipo.src, "original");
        afirmar.deepEqual(Object.keys(cliente.ventana.scalaris.tema), ["aplicar", "establecer"]);
    }
});

prueba("aplicar tema cambia atributos logotipo almacenamiento y figuras", () => {
    const cliente = crearTemaSimulado();
    cargarTemaCompleto(cliente);
    const llamadas = [];
    cliente.ventana.scalaris.actualizarTemaPlotly = tema => llamadas.push(tema);
    cliente.ventana.scalaris.tema.aplicar("medianoche");
    afirmar.equal(cliente.atributos.get("data-tema"), "medianoche");
    afirmar.equal(cliente.documento.documentElement.style.colorScheme, "dark");
    afirmar.equal(cliente.logotipo.src, "/assets/LogoClaro.png");
    afirmar.equal(cliente.almacen.get("tema"), "medianoche");
    afirmar.deepEqual(llamadas, ["medianoche"]);
    cliente.ventana.scalaris.tema.aplicar("papel");
    afirmar.equal(cliente.logotipo.src, "/assets/LogoOscuro.png");
    afirmar.equal(cliente.documento.documentElement.style.colorScheme, "light");
});

prueba("sin transición nativa el cambio de tema es inmediato", () => {
    const cliente = crearTemaSimulado();
    cargarTemaCompleto(cliente);
    cliente.ventana.scalaris.tema.establecer("marea");
    afirmar.equal(cliente.atributos.get("data-tema"), "marea");
    afirmar.equal(cliente.animaciones.length, 0);
});

prueba("la transición nativa conserva fotogramas duración y curva", async () => {
    const cliente = crearTemaSimulado();
    cargarTemaCompleto(cliente);
    cliente.documento.startViewTransition = cambiar => simularTransicion(cambiar);
    cliente.ventana.scalaris.tema.establecer("medianoche", { x: 1100, y: 50 });
    await Promise.resolve();
    afirmar.equal(cliente.atributos.get("data-tema"), "medianoche");
    afirmar.equal(cliente.animaciones.length, 1);
    afirmar.equal(cliente.animaciones[0].fotogramas.clipPath[0], 'circle(0px at 1100px 50px)');
    afirmar.equal(cliente.animaciones[0].fotogramas.clipPath[1], `circle(${Math.hypot(1100, 750)}px at 1100px 50px)`);
    afirmar.equal(cliente.animaciones[0].opciones.duration, 600);
    afirmar.equal(cliente.animaciones[0].opciones.easing, "cubic-bezier(0.32, 0.72, 0, 1)");
    afirmar.equal(cliente.animaciones[0].opciones.pseudoElement, "::view-transition-new(root)");
});

prueba("el rechazo de la transición vuelve a aplicar el tema", async () => {
    const cliente = crearTemaSimulado();
    cargarTemaCompleto(cliente);
    const rechazo = new Error("transición simulada");
    cliente.documento.startViewTransition = () => simularTransicion(null, Promise.reject(rechazo));
    cliente.ventana.scalaris.tema.establecer("marea");
    await Promise.resolve();
    await Promise.resolve();
    afirmar.equal(cliente.atributos.get("data-tema"), "marea");
    afirmar.equal(cliente.animaciones.length, 0);
});

prueba("la preparación de Glosa conserva selección y límite de escritorio", () => {
    for (const [ancho, almacenado, esperado] of [[1024, "abierto", "abierto"], [1023, "abierto", "cerrado"], [1200, "cerrado", "cerrado"], [1200, null, "cerrado"]]) {
        const cliente = crearTemaSimulado(null, ancho);
        if (almacenado !== null) cliente.almacen.set("scalaris:glosa", almacenado);
        cargarAssetCliente("inicializacion_glosa.js", cliente.contexto);
        afirmar.equal(cliente.atributos.get("data-glosa"), esperado);
    }
});

prueba("el fallo de almacenamiento de Glosa conserva el atributo anterior", () => {
    const cliente = crearTemaSimulado();
    cliente.atributos.set("data-glosa", "abierto");
    cliente.almacenamiento.getItem = () => { throw new Error("almacenamiento simulado"); };
    afirmar.doesNotThrow(() => cargarAssetCliente("inicializacion_glosa.js", cliente.contexto));
    afirmar.equal(cliente.atributos.get("data-glosa"), "abierto");
});

prueba("la activación por teclado aplica el tema sin transición", async () => {
    const cliente = crearTemaSimulado();
    cargarTemaCompleto(cliente);
    cargarAssetCliente("interacciones_globales.js", cliente.contexto);
    cliente.documento.startViewTransition = cambiar => simularTransicion(cambiar);
    cliente.eventos.get("keydown")();
    afirmar.doesNotThrow(() => cliente.ventana.scalaris.tema.establecer("marea"));
    afirmar.equal(cliente.atributos.get("data-tema"), "marea");
    await Promise.resolve();
    afirmar.equal(cliente.animaciones.length, 0);
});

prueba("la preferencia de movimiento reducido aplica el tema sin transición", () => {
    const cliente = crearTemaSimulado();
    cargarTemaCompleto(cliente);
    cargarAssetCliente("interacciones_globales.js", cliente.contexto);
    cliente.ventana.matchMedia = consulta => ({ matches: consulta === '(prefers-reduced-motion: reduce)' });
    cliente.documento.startViewTransition = () => { throw new Error("no debe iniciar transición"); };
    afirmar.doesNotThrow(() => cliente.ventana.scalaris.tema.establecer("medianoche"));
    afirmar.equal(cliente.atributos.get("data-tema"), "medianoche");
    afirmar.equal(cliente.animaciones.length, 0);
});

prueba("el rechazo de una transición antigua no sobrescribe la última selección", async () => {
    const cliente = crearTemaSimulado();
    cargarTemaCompleto(cliente);
    const rechazos = [];
    cliente.documento.startViewTransition = cambiar => {
        return simularTransicion(cambiar, new Promise((resolver, rechazar) => rechazos.push(rechazar)));
    };
    cliente.ventana.scalaris.tema.establecer("marea");
    cliente.ventana.scalaris.tema.establecer("medianoche");
    afirmar.equal(cliente.atributos.get("data-tema"), "medianoche");
    rechazos[0](new Error("primera transición simulada"));
    await Promise.resolve();
    await Promise.resolve();
    afirmar.equal(cliente.atributos.get("data-tema"), "medianoche");
    afirmar.equal(cliente.almacen.get("tema"), "medianoche");
    afirmar.equal(cliente.logotipo.src, "/assets/LogoClaro.png");
});

prueba("un cambio directo invalida el callback diferido de una transición anterior", async () => {
    const cliente = crearTemaSimulado();
    cargarTemaCompleto(cliente);
    let cambioPendiente;
    let resolverPendiente;
    cliente.documento.startViewTransition = cambiar => {
        cambioPendiente = cambiar;
        return simularTransicion(null, new Promise(resolver => { resolverPendiente = resolver; }));
    };
    cliente.ventana.scalaris.tema.establecer("marea");
    cliente.ventana.scalaris.tema.aplicar("medianoche");
    cambioPendiente();
    resolverPendiente();
    await Promise.resolve();
    afirmar.equal(cliente.atributos.get("data-tema"), "medianoche");
    afirmar.equal(cliente.animaciones.length, 0);
});

prueba("las figuras reciben la selección actual antes de capturar el tema", () => {
    const cliente = crearTemaSimulado();
    cargarTemaCompleto(cliente);
    const llamadas = [];
    cliente.ventana.scalaris.actualizarTemaPlotly = tema => llamadas.push(tema);
    cliente.ventana.scalaris.tema.aplicar("marea");
    cliente.ventana.scalaris.tema.aplicar("medianoche");
    afirmar.deepEqual(llamadas, ["marea", "medianoche"]);
    afirmar.equal(cliente.atributos.get("data-tema"), "medianoche");
});

prueba("las seis combinaciones persisten la paleta y el logotipo correctos", async () => {
    const temas = ['papel', 'marea', 'medianoche'];
    for (const origen of temas) {
        for (const destino of temas.filter(tema => tema !== origen)) {
            const cliente = crearTemaSimulado(origen);
            cargarTemaCompleto(cliente);
            cliente.documento.startViewTransition = cambiar => simularTransicion(cambiar);
            cliente.ventana.scalaris.tema.establecer(destino, { x: 100, y: 60 });
            await Promise.resolve();
            afirmar.equal(cliente.almacen.get('tema'), destino);
            afirmar.equal(cliente.atributos.get('data-tema'), destino);
            afirmar.equal(cliente.logotipo.src, destino === 'medianoche' ? '/assets/LogoClaro.png' : '/assets/LogoOscuro.png');
            afirmar.equal(cliente.animaciones.length, 1);
        }
    }
});

prueba("la finalización y la navegación limpian solamente su propia captura", async () => {
    const cliente = crearTemaSimulado();
    cargarTemaCompleto(cliente);
    let finalizar;
    const transicion = simularTransicion();
    transicion.finished = new Promise(resolver => { finalizar = resolver; });
    cliente.documento.startViewTransition = cambiar => { cambiar(); return transicion; };
    cliente.ventana.scalaris.tema.establecer('marea');
    await Promise.resolve();
    afirmar.equal(cliente.atributos.has('data-tema-circular'), true);
    cliente.eventos.get('pageswap')();
    afirmar.equal(transicion.omitida, true);
    afirmar.equal(cliente.animaciones[0].cancelada, true);
    finalizar(); await Promise.resolve();
    afirmar.equal(cliente.atributos.has('data-tema-circular'), false);
});

prueba("la presentación y la navegación activas aplican directamente sin iniciar otra transición", () => {
    for (const caso of ['presentacion', 'navegacion']) {
        const cliente = crearTemaSimulado();
        cargarTemaCompleto(cliente);
        cliente.documento.startViewTransition = () => { throw new Error('No debe competir'); };
        if (caso === 'presentacion') cliente.ventana.scalaris.presentacion = { activa: true };
        else cliente.atributos.set('data-navegacion-circular', '');
        cliente.ventana.scalaris.tema.establecer('medianoche');
        afirmar.equal(cliente.atributos.get('data-tema'), 'medianoche');
        afirmar.equal(cliente.atributos.has('data-tema-circular'), false);
    }
});

prueba("un cambio de preferencia cancela la expansión antes de animar", async () => {
    const cliente = crearTemaSimulado();
    cargarTemaCompleto(cliente);
    const transicion = simularTransicion();
    cliente.documento.startViewTransition = cambiar => { cambiar(); return transicion; };
    cliente.ventana.scalaris.tema.establecer('marea');
    cliente.eventos.get('preferenciaTema')({ matches: true });
    await Promise.resolve();
    afirmar.equal(transicion.omitida, true);
    afirmar.equal(cliente.animaciones.length, 0);
});

prueba("el almacenamiento bloqueado y los fallos síncronos de la API conservan el cambio", async () => {
    const cliente = crearTemaSimulado();
    cliente.almacenamiento.getItem = () => { throw new Error('Bloqueado'); };
    cliente.almacenamiento.setItem = () => { throw new Error('Bloqueado'); };
    cargarTemaCompleto(cliente);
    afirmar.equal(cliente.atributos.get('data-tema'), 'papel');
    cliente.documento.startViewTransition = () => { throw new Error('No disponible'); };
    afirmar.doesNotThrow(() => cliente.ventana.scalaris.tema.establecer('medianoche'));
    await Promise.resolve();
    afirmar.equal(cliente.atributos.get('data-tema'), 'medianoche');
    afirmar.equal(cliente.atributos.has('data-tema-circular'), false);
});
