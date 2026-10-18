'use strict';
const { afirmar, base, crearNavegador, crearContexto, observarErrores, estable, captura, guardar } = require('./comun_navegador.cjs');
(async () => {
    const navegador = await crearNavegador(), contexto = await crearContexto(navegador,{tema:'papel'});
    const pagina = await contexto.newPage(), errores = observarErrores(pagina), resultados = [];
    try {
        await pagina.goto(base+'/visualizador');
        const entradas = pagina.locator('.matriz-entrada input'); await entradas.first().waitFor();
        for (const [indice,valor] of ['1','1','1','1','-1','0'].entries()) await entradas.nth(indice).fill(valor);
        await pagina.waitForFunction(() => [...document.querySelectorAll('.js-plotly-plot')].some(e=>e._fullLayout));
        for (const tema of ['papel','marea','medianoche']) {
            await pagina.evaluate(t => scalaris.tema.establecer(t,{x:1300,y:40}),tema); await estable(pagina);
            const figuras = await pagina.evaluate(() => [...document.querySelectorAll('.js-plotly-plot')].filter(e=>e._fullLayout).map(e=>({
                color:e._fullLayout.font.color, esperado:scalaris.graficos.texto[document.documentElement.getAttribute('data-tema')],
            })));
            afirmar.ok(figuras.length > 0); figuras.forEach(figura=>afirmar.equal(figura.color,figura.esperado));
            resultados.push({tema,figuras});
        }
        await captura(pagina,'grafico-sincronizado-medianoche'); afirmar.deepEqual(errores,[]);
        guardar('graficos.json',{resultados,errores}); console.log('GRAFICOS reales correctos');
    } finally { await contexto.close(); await navegador.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
