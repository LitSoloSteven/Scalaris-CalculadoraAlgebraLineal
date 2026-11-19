/** Símbolos de uso frecuente y su sintaxis en cada tipo de captura. */
'use strict';

{
    window.scalaris = window.scalaris || {};
    const operadores = [
        ['−', 'Signo menos', {funcion: '−', matriz: '−', numero: '-', ecuacion: '-'}],
        ['×', 'Multiplicación', {funcion: '×', matriz: '×'}],
        ['·', 'Producto con punto', {funcion: '·', matriz: '·'}],
        ['⋅', 'Punto de multiplicación', {funcion: '⋅', matriz: '⋅'}],
        ['∙', 'Punto operador', {funcion: '∙', matriz: '∙'}],
        ['÷', 'División', {funcion: '÷'}],
        ['⁄', 'Barra de fracción', {funcion: '⁄', numero: '/', ecuacion: '/'}],
        ['∕', 'Barra de división', {funcion: '∕', numero: '/', ecuacion: '/'}],
        ['±', 'Más o menos'], ['∓', 'Menos o más'], ['⊕', 'Suma directa'],
        ['⊗', 'Producto tensorial'], ['∘', 'Composición'], ['∝', 'Proporcional a'],
        ['ᵀ', 'Transpuesta', {matriz: 'ᵀ'}], ['†', 'Adjunta'],
    ];
    const raices = [
        ['√', 'Raíz cuadrada', {funcion: '√()'}, 'Digit2'],
        ['∛', 'Raíz cúbica', {funcion: '∛()'}, 'Digit3'],
        ['∜', 'Raíz cuarta', {funcion: '∜()'}, 'Digit4'],
    ];
    const potencias = Array.from('⁰¹²³⁴⁵⁶⁷⁸⁹', (simbolo, indice) =>
        [simbolo, 'Superíndice ' + indice, {funcion: simbolo}]);
    const negativos = [['⁻¹', 'Exponente menos uno', {funcion: '⁻¹'}]];
    const subindices = Array.from('₀₁₂₃₄₅₆₇₈₉', (simbolo, indice) =>
        [simbolo, 'Subíndice ' + indice]);
    const fracciones = [
        ['¼', '1/4'], ['½', '1/2'], ['¾', '3/4'], ['⅐', '1/7'], ['⅑', '1/9'], ['⅒', '1/10'],
        ['⅓', '1/3'], ['⅔', '2/3'], ['⅕', '1/5'], ['⅖', '2/5'], ['⅗', '3/5'], ['⅘', '4/5'],
        ['⅙', '1/6'], ['⅚', '5/6'], ['⅛', '1/8'], ['⅜', '3/8'], ['⅝', '5/8'], ['⅞', '7/8'], ['↉', '0/3'],
    ].map(([simbolo, fraccion]) => [simbolo, 'Fracción ' + fraccion, {funcion: simbolo, numero: fraccion, ecuacion: fraccion}]);
    const nombresGriegos = 'alfa beta gamma delta épsilon zeta eta theta iota kappa lambda mu nu xi ómicron pi rho sigma tau ípsilon fi ji psi omega'.split(' ');
    const griegas = Array.from('αβγδεζηθικλμνξοπρστυφχψω').flatMap((simbolo, indice) => {
        const nombre = nombresGriegos[indice];
        return [
            [simbolo, nombre + ' minúscula', simbolo === 'π' ? {funcion: simbolo} : undefined],
            [simbolo.toUpperCase(), nombre + ' mayúscula'],
        ];
    });
    const relaciones = [
        ['≤', 'Menor o igual'], ['≥', 'Mayor o igual'], ['≠', 'Distinto de'], ['≈', 'Aproximadamente igual'],
        ['≃', 'Asintóticamente igual'], ['≡', 'Idéntico a'], ['≅', 'Congruente'], ['∼', 'Semejante'],
        ['≪', 'Mucho menor'], ['≫', 'Mucho mayor'], ['⊥', 'Perpendicular'], ['∥', 'Paralelo'],
        ['⇒', 'Implica'], ['⇔', 'Si y solo si'], ['→', 'Flecha derecha'], ['←', 'Flecha izquierda'], ['↔', 'Doble flecha'],
    ];
    const conjuntos = [
        ['ℕ', 'Naturales'], ['ℤ', 'Enteros'], ['ℚ', 'Racionales'], ['ℝ', 'Reales'], ['ℂ', 'Complejos'],
        ['∅', 'Conjunto vacío'], ['∈', 'Pertenece'], ['∉', 'No pertenece'], ['∋', 'Contiene como elemento'],
        ['⊂', 'Subconjunto propio'], ['⊆', 'Subconjunto'], ['⊃', 'Superconjunto propio'], ['⊇', 'Superconjunto'],
        ['∪', 'Unión'], ['∩', 'Intersección'], ['∀', 'Cuantificador universal'], ['∃', 'Existe'], ['∄', 'No existe'],
        ['∧', 'Conjunción'], ['∨', 'Disyunción'], ['¬', 'Negación'],
    ];
    const calculo = [
        ['ℯ', 'Número de Euler', {funcion: 'ℯ'}], ['∞', 'Infinito'], ['∑', 'Sumatoria'], ['∏', 'Productoria'],
        ['∫', 'Integral'], ['∬', 'Integral doble'], ['∭', 'Integral triple'], ['∮', 'Integral de contorno'],
        ['∂', 'Derivada parcial'], ['∇', 'Nabla'], ['′', 'Prima'], ['″', 'Doble prima'],
        ['°', 'Grados'], ['∠', 'Ángulo'], ['△', 'Triángulo'], ['∴', 'Por lo tanto'], ['∵', 'Porque'], ['‰', 'Por mil'],
    ];
    const grupos = {
        'Operadores': operadores,
        'Raíces, potencias y subíndices': [...raices, ...potencias, ...negativos, ...subindices],
        'Fracciones': fracciones,
        'Letras griegas': griegas,
        'Relaciones y flechas': relaciones,
        'Conjuntos y lógica': conjuntos,
        'Cálculo y geometría': calculo,
    };
    window.scalaris.catalogoSimbolos = Object.entries(grupos).flatMap(([grupo, entradas]) =>
        entradas.map(([simbolo, nombre, campos = {}, tecla]) => ({grupo, simbolo, nombre, campos, tecla})));
}
