'use strict';
const { afirmar, base, crearNavegador, crearContexto, crearZoom, observarErrores, comprobarPagina, captura: capturar, guardar } = require('./comun_navegador.cjs');

const perfil = process.env.PERFIL_VALIDACION || 'escritorio';
const captura = (pagina,nombre) => capturar(pagina, perfil === 'escritorio' ? nombre : nombre + '-' + perfil);

async function llenar(entradas, valores) {
    afirmar.equal(await entradas.count(), valores.length);
    for (const [indice, valor] of valores.entries()) await entradas.nth(indice).fill(String(valor));
    await entradas.last().press('Tab');
}

async function comprobarMatrices(pagina) {
    await pagina.goto(base + '/algebra-lineal/matrices'); await comprobarPagina(pagina);
    const tarjeta = pagina.locator('.captura-matriz').filter({ has: pagina.locator('#matriz-titulo-A') });
    const entradas = tarjeta.locator('input');
    const valores = ['1/3','0','0','0','1','0','0','0','1'];
    await llenar(entradas, valores);
    await pagina.getByRole('button', { name: 'Añadir matriz', exact: true }).click();
    await pagina.locator('#matriz-titulo-B').waitFor();
    afirmar.deepEqual(await entradas.evaluateAll(elementos => elementos.map(e => e.value)), valores);
    await pagina.getByRole('button', { name: 'Añadir fila a matriz A', exact: true }).click();
    await pagina.waitForFunction(() => document.querySelectorAll('.captura-matriz:first-child input').length === 12);
    await pagina.getByRole('button', { name: 'Añadir columna a matriz A', exact: true }).click();
    await pagina.waitForFunction(() => document.querySelectorAll('.captura-matriz:first-child input').length === 16);
    afirmar.equal(await entradas.first().inputValue(), '1/3');
    await pagina.getByRole('button', { name: 'Quitar fila de matriz A', exact: true }).click();
    await pagina.waitForFunction(() => document.querySelectorAll('.captura-matriz:first-child input').length === 12);
    await pagina.getByRole('button', { name: 'Quitar columna de matriz A', exact: true }).click();
    await pagina.waitForFunction(() => document.querySelectorAll('.captura-matriz:first-child input').length === 9);
    afirmar.deepEqual(await entradas.evaluateAll(elementos => elementos.map(e => e.value)), valores);
    await captura(pagina, 'matrices-varias-escritorio');
    await pagina.getByRole('button', { name: 'Eliminar matriz B', exact: true }).click();
    await pagina.locator('#matriz-titulo-B').waitFor({ state: 'detached' });
    await pagina.getByRole('textbox', { name: 'Expresión matemática', exact: true }).fill('A+A');
    await pagina.getByRole('button', { name: 'Evaluar', exact: true }).click();
    await pagina.locator('#resultados-matrices .distintivo-exito').waitFor();
    await captura(pagina, 'matrices-evaluacion-exacta');
    const resultado = await pagina.locator('#resultados-matrices').innerText();
    await pagina.getByRole('textbox', { name: 'Expresión matemática', exact: true }).fill('A+Z');
    await pagina.getByRole('button', { name: 'Evaluar', exact: true }).click();
    await pagina.locator('#resultados-matrices .distintivo-error').waitFor();
    afirmar.deepEqual(await entradas.evaluateAll(elementos => elementos.map(e => e.value)), valores);
    await captura(pagina, 'matrices-error-conserva-captura');
    await pagina.getByRole('button', { name: 'Abrir matriz A en Matriz inversa', exact: true }).click();
    await pagina.waitForURL('**/algebra-lineal/inversa?*');
    await pagina.locator('.cuadricula-area-desplazamiento input').first().waitFor();
    afirmar.deepEqual(await pagina.locator('.cuadricula-area-desplazamiento input').evaluateAll(e => e.map(i => i.value || '0')), valores);
    await comprobarPagina(pagina); await captura(pagina, 'inversa-transferencia-fracciones');
    await pagina.getByRole('button', { name:'Calcular inversa', exact:true }).click();
    await pagina.getByText('Matriz invertible', { exact:true }).waitFor();
    await comprobarPagina(pagina); await captura(pagina, 'inversa-calculada');
    return { operaciones: ['añadir','redimensionar filas y columnas','reducir','eliminar','evaluar','error sin pérdida','transferir copia exacta'], resultado: resultado.slice(0, 400) };
}

async function dimensionar(pagina, dimension) {
    const entradas = pagina.locator('.cuadricula-area-desplazamiento input');
    let actual = Math.sqrt(await entradas.count());
    while (actual !== dimension) {
        const accion = actual < dimension ? 'Añadir fila y columna' : 'Quitar fila y columna';
        actual += actual < dimension ? 1 : -1;
        await pagina.getByRole('button', { name: accion, exact: true }).click();
        await pagina.waitForFunction(n => document.querySelectorAll('.cuadricula-area-desplazamiento input').length === n*n, actual);
    }
    return entradas;
}

async function comprobarDeterminantes(pagina) {
    await pagina.goto(base + '/algebra-lineal/determinantes'); await comprobarPagina(pagina);
    afirmar.equal(await pagina.getByText('Triangulación LU con aritmética exacta.', { exact: true }).count(), 1);
    afirmar.equal(await pagina.getByRole('tab').count(), 0);
    afirmar.equal(await pagina.getByRole('button', { name: /Cofactores|Eliminación/i }).count(), 0);
    const casos = [
        { nombre: 'uno-por-uno', n: 1, valores: ['7/11'], esperado: '7/11' },
        { nombre: 'identidad', n: 3, valores: [1,0,0,0,1,0,0,0,1], esperado: '1' },
        { nombre: 'singular', n: 2, valores: [1,2,2,4], esperado: '0' },
        { nombre: 'intercambio-filas', n: 2, valores: [0,1,1,0], esperado: '-1' },
        { nombre: 'fracciones', n: 2, valores: ['1/2','1/3','2/5','3/7'], esperado: '17/210' },
    ];
    for (const caso of casos) {
        const entradas = await dimensionar(pagina, caso.n); await llenar(entradas, caso.valores);
        await pagina.getByRole('button', { name: 'Calcular determinante', exact: true }).click();
        await pagina.waitForFunction(valor => document.querySelector('.determinante-valor')?.textContent === 'Determinante: ' + valor, caso.esperado);
        afirmar.equal(await pagina.locator('.determinante-valor').innerText(), 'Determinante: ' + caso.esperado);
        await pagina.getByText('Pasos del cálculo', { exact: true }).click();
        await captura(pagina, 'determinante-' + caso.nombre); await comprobarPagina(pagina);
        console.log('DETERMINANTE', caso.nombre, caso.esperado);
    }
    const entradas = await dimensionar(pagina, 1); await llenar(entradas, ['5']);
    await pagina.getByRole('button', { name: 'Calcular determinante', exact: true }).click();
    await pagina.getByText('Calculando determinante…', { exact: true }).waitFor();
    await entradas.first().fill('9'); await entradas.first().press('Tab');
    await pagina.waitForTimeout(1100);
    afirmar.equal(await pagina.locator('.determinante-valor').count(), 0);
    afirmar.equal(await entradas.first().inputValue(), '9');
    await captura(pagina, 'determinante-edicion-descarta-obsoleto');
    await pagina.getByRole('button', { name: 'Calcular determinante', exact: true }).click();
    await pagina.locator('.determinante-valor').waitFor();
    afirmar.equal(await pagina.locator('.determinante-valor').innerText(), 'Determinante: 9');
    await pagina.goto(base + '/algebra-lineal/matrices?operacion=determinante');
    await pagina.getByText('Triangulación LU con aritmética exacta.', { exact: true }).waitFor();
    return { casos, descarteAlEditar: true, recalculo: '9', enlaceAnterior: true };
}

(async () => {
    const navegador = await crearNavegador(); const contexto = perfil === 'zoom200' ? await crearZoom({tema:'marea'}) : await crearContexto(navegador, { tema: perfil === 'movil' ? 'papel' : 'medianoche', ancho:perfil === 'movil' ? 390 : 1440 });
    const pagina = await contexto.newPage(); const errores = observarErrores(pagina); if(perfil === 'zoom200'){await pagina.goto(base+'/algebra-lineal/matrices');afirmar.equal(await contexto.aplicarZoom(),2);}
    try {
        const matrices = await comprobarMatrices(pagina);
        const determinantes = await comprobarDeterminantes(pagina);
        afirmar.deepEqual(errores, []);
        guardar('funcionalidad-' + perfil + '.json', { matrices, determinantes, errores }); console.log('FUNCIONALIDAD correcta');
    } catch (error) { await captura(pagina, 'fallo-funcionalidad'); guardar('fallo-funcionalidad.json', { mensaje: error.stack, errores }); throw error; }
    finally { await contexto.close(); await navegador.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
