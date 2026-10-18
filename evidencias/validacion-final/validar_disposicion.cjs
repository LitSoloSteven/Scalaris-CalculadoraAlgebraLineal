'use strict';
const { afirmar, base, crearNavegador, crearContexto, crearZoom, observarErrores, comprobarPagina, captura, guardar } = require('./comun_navegador.cjs');
const temas = ['papel','marea','medianoche'];
const herramientas = ['sistemas','vectores','matrices','inversa','determinantes'];
const etiquetas = { papel: 'Papel', marea: 'Marea', medianoche: 'Medianoche' };

async function comprobarInicio(pagina, nombre) {
    await pagina.goto(base + '/'); await comprobarPagina(pagina);
    const geometria = await pagina.evaluate(() => {
        const titulo = document.querySelector('.inicio-titulo'), marca = document.querySelector('.inicio-marca');
        const cabecera = document.querySelector('.inicio-cabecera').getBoundingClientRect();
        const tarjeta = document.querySelector('.inicio-fila').getBoundingClientRect();
        const descripciones = [...document.querySelectorAll('.inicio-descripcion-fila')];
        return { texto: titulo.textContent, hermanos: titulo.parentElement === marca && marca.querySelector('.inicio-logotipo').parentElement === marca,
            ancho: titulo.clientWidth, contenido: titulo.scrollWidth, separacion: tarjeta.top - cabecera.bottom,
            descripcionesCompletas:descripciones.every(e => e.scrollHeight <= e.clientHeight + 1) };
    });
    afirmar.equal(geometria.texto, 'Scalaris'); afirmar.equal(geometria.hermanos, true);
    afirmar.ok(geometria.contenido <= geometria.ancho + 1); afirmar.ok(geometria.separacion > 0);
    afirmar.equal(geometria.descripcionesCompletas, true);
    await captura(pagina, 'inicio-' + nombre);
    const fila = pagina.locator('#inicio-fila-algebra');
    afirmar.match(await fila.innerText(), /5 herramientas/);
    await fila.focus(); await fila.press('Enter');
    const dialogo = pagina.locator('dialog[open]'); await dialogo.waitFor();
    afirmar.equal(await dialogo.locator('.inicio-tarjeta').count(), 5);
    afirmar.equal(await dialogo.evaluate(e => e.contains(document.activeElement)), true);
    await pagina.keyboard.press('Escape'); await dialogo.waitFor({ state: 'hidden' });
    afirmar.equal(await fila.evaluate(e => e === document.activeElement), true);
    return geometria;
}

async function comprobarTema(pagina, tema, nombre) {
    await pagina.getByRole('button', { name: 'Seleccionar Tema', exact: true }).click();
    const opcion = pagina.getByRole('menuitemradio', { name: etiquetas[tema], exact: true }); await opcion.waitFor();
    afirmar.equal(await opcion.getAttribute('aria-checked'), 'true');
    afirmar.equal(await pagina.locator('[data-tema-opcion][aria-checked="true"]').count(), 1);
    afirmar.equal(await pagina.locator('.tema-marca-activa').evaluateAll(e => e.filter(i => getComputedStyle(i).visibility === 'visible').length), 1);
    await captura(pagina, 'tema-' + nombre); await pagina.keyboard.press('Escape');
}

async function comprobarVectores(pagina, nombre) {
    const selector = pagina.locator('.pestanas-vectores');
    const etiquetasSelector = await selector.locator('.q-tab__label').allTextContents();
    afirmar.deepEqual(etiquetasSelector, ['Suma / Resta','Escalar × Vector','Combinación Lineal']);
    const rectangulos = await selector.locator('.q-tab__label').evaluateAll(e => e.map(i => {
        const r = i.getBoundingClientRect(); return { izquierda:r.left, derecha:r.right };
    }));
    for (let indice = 1; indice < rectangulos.length; indice++) afirmar.ok(rectangulos[indice].izquierda >= rectangulos[indice-1].derecha);
    for (const etiqueta of etiquetasSelector) {
        const pestana = pagina.getByRole('tab', { name: etiqueta, exact: true });
        await pestana.focus(); await pestana.press('Enter');
        await pagina.waitForFunction(texto => [...document.querySelectorAll('.pestanas-vectores .q-tab')].some(e => e.getAttribute('aria-selected') === 'true' && e.textContent.includes(texto)), etiqueta);
    }
    await pagina.getByRole('tab', { name: 'Suma / Resta', exact: true }).focus();
    await pagina.keyboard.press('Enter'); await captura(pagina, 'vectores-' + nombre);
    return { etiquetas: etiquetasSelector, teclado: true, solapamientos: false };
}

async function recorrerHerramientas(pagina, nombre) {
    await pagina.goto(base + '/algebra-lineal/sistemas');
    const resultados = [];
    for (const herramienta of herramientas) {
        const ruta = '/algebra-lineal/' + herramienta;
        const enlace = pagina.locator(`.navegacion-elementos a[href="${ruta}"]`);
        await pagina.keyboard.press('Tab');
        await enlace.focus();
        afirmar.equal(await enlace.evaluate(e => e.matches(':focus-visible')), true, 'Foco no visible');
        await Promise.all([pagina.waitForURL(base + ruta), enlace.press('Enter')]);
        await comprobarPagina(pagina);
        afirmar.equal(await pagina.locator('.navegacion-elementos a').count(), 5);
        afirmar.equal(await pagina.locator('.navegacion-elementos [aria-current="page"]').count(), 1);
        afirmar.equal(await pagina.locator('.navegacion-elementos [aria-current="page"]').getAttribute('href'), ruta);
        if (herramienta === 'vectores') resultados.push(await comprobarVectores(pagina, nombre));
        if (herramienta === 'matrices') {
            await pagina.getByRole('button', { name: 'Añadir matriz', exact: true }).click();
            await pagina.locator('#matriz-titulo-B').waitFor(); await comprobarPagina(pagina);
            await captura(pagina, 'matrices-' + nombre);
        }
        console.log('PANTALLA', nombre, herramienta);
    }
    return resultados;
}

(async () => {
    const navegador = await crearNavegador(), filtro = process.env.PERFIL_DISPOSICION;
    const resultados = filtro ? require('./disposicion-accesibilidad.json').filter(r => r.perfil !== filtro) : [];
    try {
        for (const perfil of filtro ? [filtro] : ['escritorio','movil','zoom200']) {
            const contexto = perfil === 'zoom200' ? await crearZoom({tema:'papel'}) : await crearContexto(navegador, { ancho: perfil === 'movil' ? 390 : 1440, tema:'papel' });
            const pagina = await contexto.newPage(); const errores = observarErrores(pagina);
            await pagina.goto(base + '/'); await pagina.locator('.inicio-titulo').waitFor();
            const zoom = perfil === 'zoom200' ? await contexto.aplicarZoom() : 1;
            afirmar.equal(zoom, perfil === 'zoom200' ? 2 : 1);
            for (const tema of temas) {
                await pagina.evaluate(t => scalaris.tema.aplicar(t), tema);
                const nombre = perfil + '-' + tema;
                const inicio = await comprobarInicio(pagina, nombre);
                await pagina.goto(base + '/algebra-lineal/sistemas');
                await comprobarPagina(pagina);
                await comprobarTema(pagina, tema, nombre);
                const vectores = await recorrerHerramientas(pagina, nombre);
                resultados.push({ perfil, tema, zoom, ventana: await pagina.evaluate(() => ({ ancho:innerWidth, exterior:outerWidth, escala:devicePixelRatio })), inicio, vectores });
            }
            afirmar.deepEqual(errores, []); await contexto.close();
        }
        guardar('disposicion-accesibilidad.json', resultados); console.log('DISPOSICION correcta', resultados.length);
    } finally { await navegador.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
