'use strict';
const { afirmar, base, crearNavegador, crearContexto, observarErrores, estable, captura, guardar } = require('./comun_navegador.cjs');
const resultados = [];
async function presentacion(navegador, tema, reducido = false) {
    const contexto = await crearContexto(navegador, { tema, presentacion: true, reducido });
    const pagina = await contexto.newPage(), errores = observarErrores(pagina), muestras = [];
    await pagina.goto(base + '/', { waitUntil:'domcontentloaded' });
    const momentos = reducido ? [0,200,700] : [0,600,1200,1900,2600,3400];
    const inicio = Date.now();
    for (const momento of momentos) {
        await pagina.waitForTimeout(Math.max(1, momento - (Date.now() - inicio)));
        muestras.push(await pagina.evaluate(() => ({ tiempo:performance.now(), tema:document.documentElement.getAttribute('data-tema'),
            activa:scalaris.presentacion.activa, fondo:!!document.getElementById('aplicacion-presentacion-fondo'),
            logotipo:document.querySelector('#presentacion-logotipo')?.getAttribute('src'),
            inicioPendiente:document.documentElement.hasAttribute('data-inicio-pendiente'),
            animaciones:document.getAnimations().map(a => ({ tiempo:a.currentTime, estado:a.playState, objetivo:a.effect?.target?.id })) })));
        if (momento === 1200) await captura(pagina, 'presentacion-' + tema);
    }
    await estable(pagina);
    afirmar.ok(muestras.every(m => m.tema === tema));
    afirmar.ok(muestras.filter(m => m.activa).every(m => m.fondo));
    afirmar.ok(muestras.filter(m => m.logotipo).every(m => m.logotipo.includes(tema === 'medianoche' ? 'LogoClaro' : 'LogoOscuro')));
    const animaciones = await pagina.evaluate(() => window.animacionesVerificadas.filter(a => String(a.elemento).startsWith('presentacion') || a.configuracion.delay));
    afirmar.equal(await pagina.evaluate(() => scalaris.presentacion.activa), false);
    afirmar.ok(animaciones.length >= (reducido ? 1 : 7));
    if (reducido) afirmar.ok(animaciones.every(a => !JSON.stringify(a.fotogramas).includes('transform')));
    else afirmar.ok(animaciones.some(a => a.configuracion.delay === 2600 && a.fin > a.inicio));
    await pagina.reload(); await estable(pagina);
    afirmar.equal(await pagina.evaluate(() => window.animacionesVerificadas.filter(a => String(a.elemento).startsWith('presentacion')).length),0);
    afirmar.deepEqual(errores, []); resultados.push({ tipo:'presentacion', tema, reducido, muestras, animaciones, recargaSinRepeticion:true });
    await contexto.close(); console.log('PRESENTACION',tema,reducido,'correcta');
}
async function alternativas(navegador) {
    for (const sinAPI of [false,true]) {
        const contexto = await crearContexto(navegador,{ ancho:390, reducido:!sinAPI, tema:'papel' });
        if (sinAPI) {
            await contexto.addInitScript(() => { document.startViewTransition = undefined; });
            await contexto.route('**/assets/css/movimiento.css',async ruta => {
                const respuesta=await ruta.fetch();
                await ruta.fulfill({response:respuesta,body:(await respuesta.text()).replace('navigation: auto;','navigation: none;')});
            });
        }
        const pagina = await contexto.newPage(), errores = observarErrores(pagina);
        await pagina.goto(base+'/algebra-lineal/matrices'); await estable(pagina);
        await pagina.evaluate(() => scalaris.tema.establecer('medianoche',{x:100,y:50}));
        afirmar.equal(await pagina.locator('html').getAttribute('data-tema'),'medianoche');
        await Promise.all([pagina.waitForURL('**/algebra-lineal/vectores'),pagina.locator('a[href="/algebra-lineal/vectores"]').press('Enter')]);
        await estable(pagina);
        afirmar.equal(await pagina.evaluate(() => window.animacionesVerificadas.filter(a=>a.configuracion.pseudoElement).length),0);
        afirmar.deepEqual(errores,[]);
        resultados.push({tipo:sinAPI?'sin-api-simulada':'movimiento-reducido',navegacion:true,tema:true,circulos:0});
        await contexto.close();
    }
}
async function expansiones(navegador) {
    const contexto = await crearContexto(navegador, { tema:'papel' }), pagina = await contexto.newPage(), errores = observarErrores(pagina);
    await pagina.goto(base + '/algebra-lineal/matrices'); await estable(pagina);
    for (const desde of ['papel','marea','medianoche']) for (const hacia of ['papel','marea','medianoche'].filter(t => t !== desde)) {
        await pagina.evaluate(t => scalaris.tema.aplicar(t), desde);
        await pagina.getByRole('button',{name:'Seleccionar Tema',exact:true}).click();
        const opcion = pagina.locator(`[data-tema-opcion="${hacia}"]`); await opcion.focus(); await opcion.press('Enter');
        await pagina.waitForFunction(() => !document.documentElement.hasAttribute('data-tema-circular'));
        const animacion = await pagina.evaluate(() => window.animacionesVerificadas.filter(a => a.configuracion.pseudoElement).at(-1));
        afirmar.ok(animacion.fin > animacion.inicio + 400);
        afirmar.ok(animacion.fotogramas.clipPath[0].startsWith('circle(0px'));
        afirmar.equal(await pagina.locator('html').getAttribute('data-tema'), hacia);
        resultados.push({ tipo:'tema', desde, hacia, animacion });
    }
    await pagina.evaluate(() => { scalaris.tema.establecer('marea'); scalaris.tema.establecer('medianoche'); scalaris.tema.establecer('papel'); });
    await pagina.waitForFunction(() => !document.documentElement.hasAttribute('data-tema-circular'));
    afirmar.equal(await pagina.locator('html').getAttribute('data-tema'), 'papel');
    for (const ruta of ['/algebra-lineal/vectores','/algebra-lineal/matrices','/algebra-lineal/determinantes']) {
        await Promise.all([pagina.waitForURL(base + ruta), pagina.locator(`.navegacion-elementos a[href="${ruta}"]`).press('Enter')]);
        await estable(pagina);
        const animacion = await pagina.evaluate(() => window.animacionesVerificadas.filter(a => a.configuracion.pseudoElement).at(-1));
        afirmar.ok(animacion.fin > animacion.inicio + 400);
        resultados.push({ tipo:'navegacion', ruta, animacion });
    }
    await pagina.goBack(); await estable(pagina); await pagina.goForward(); await estable(pagina);
    await pagina.reload(); await estable(pagina);
    afirmar.equal(await pagina.evaluate(() => window.animacionesVerificadas.filter(a => a.configuracion.pseudoElement).length),0);
    afirmar.deepEqual(errores, []); resultados.push({ tipo:'historial-y-cambios-rapidos', correcto:true }); await contexto.close();
    const directo = await crearContexto(navegador,{presentacion:true}), otra = await directo.newPage();
    await otra.goto(base+'/algebra-lineal/determinantes'); await estable(otra); await otra.goto(base+'/'); await estable(otra);
    afirmar.equal(await otra.evaluate(() => scalaris.presentacion.activa),false); await directo.close();
}
(async () => {
    const navegador = await crearNavegador();
    try {
        for (const tema of ['papel','marea','medianoche']) await presentacion(navegador,tema);
        await presentacion(navegador,'papel',true); await expansiones(navegador); await alternativas(navegador);
        guardar('animaciones-temporales.json',resultados); console.log('ANIMACIONES verificadas temporalmente');
    } finally { await navegador.close(); }
})().catch(error => { console.error(error); process.exitCode=1; });
