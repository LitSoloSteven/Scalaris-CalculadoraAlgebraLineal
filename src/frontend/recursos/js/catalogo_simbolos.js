/** Símbolos de uso frecuente y su sintaxis en cada tipo de captura. */
'use strict';

{
    window.scalaris = window.scalaris || {};
    const operadores = [
        ['−', 'Signo menos', {funcion: '−', matriz: '−', numero: '-', ecuacion: '-', base: '-', real: '-'}],
        ['×', 'Multiplicación', {funcion: '×', matriz: '×', ecuacion: '×'}],
        ['·', 'Producto con punto', {funcion: '·', matriz: '·', ecuacion: '·'}],
        ['⋅', 'Punto de multiplicación', {funcion: '⋅', matriz: '⋅', ecuacion: '⋅'}],
        ['∙', 'Punto operador', {funcion: '∙', matriz: '∙', ecuacion: '∙'}],
        ['÷', 'División', {funcion: '÷', matriz: '÷', numero: '/', ecuacion: '/'}],
        ['⁄', 'Barra de fracción', {funcion: '⁄', matriz: '⁄', numero: '/', ecuacion: '/'}],
        ['∕', 'Barra de división', {funcion: '∕', matriz: '∕', numero: '/', ecuacion: '/'}],
        ['±', 'Más o menos'], ['∓', 'Menos o más'], ['⊕', 'Suma directa', {matriz: '⊕'}],
        ['⊗', 'Producto tensorial', {matriz: '⊗'}], ['∘', 'Composición'], ['∝', 'Proporcional a'],
        ['ᵀ', 'Transpuesta', {matriz: 'ᵀ'}], ['†', 'Adjunta'],
    ];
    const raices = [
        ['√', 'Raíz cuadrada', {funcion: '√()'}, 'Digit2'],
        ['∛', 'Raíz cúbica', {funcion: '∛()'}, 'Digit3'],
        ['∜', 'Raíz cuarta', {funcion: '∜()'}, 'Digit4'],
    ];
    const potencias = Array.from('⁰¹²³⁴⁵⁶⁷⁸⁹', (simbolo, indice) =>
        [simbolo, 'Superíndice ' + indice, {funcion: simbolo, matriz: simbolo}]);
    const negativos = [['⁻¹', 'Exponente menos uno', {funcion: '⁻¹', matriz: '⁻¹'}]];
    const subindices = Array.from('₀₁₂₃₄₅₆₇₈₉', (simbolo, indice) =>
        [simbolo, 'Subíndice ' + indice, {ecuacion: simbolo}]);
    const fracciones = [
        ['¼', '1/4'], ['½', '1/2'], ['¾', '3/4'], ['⅐', '1/7'], ['⅑', '1/9'], ['⅒', '1/10'],
        ['⅓', '1/3'], ['⅔', '2/3'], ['⅕', '1/5'], ['⅖', '2/5'], ['⅗', '3/5'], ['⅘', '4/5'],
        ['⅙', '1/6'], ['⅚', '5/6'], ['⅛', '1/8'], ['⅜', '3/8'], ['⅝', '5/8'], ['⅞', '7/8'], ['↉', '0/3'],
    ].map(([simbolo, fraccion]) =>
        [simbolo, 'Fracción ' + fraccion, {funcion: simbolo, matriz: simbolo, numero: fraccion, ecuacion: fraccion}]);
    const nombresGriegos = 'alfa beta gamma delta épsilon zeta eta theta iota kappa lambda mu nu xi ómicron pi rho sigma tau ípsilon fi ji psi omega'.split(' ');
    const griegas = Array.from('αβγδεζηθικλμνξοπρστυφχψω').flatMap((simbolo, indice) => {
        const nombre = nombresGriegos[indice];
        const mayuscula = simbolo.toUpperCase();
        const perfiles = simbolo === 'π' ? {funcion: simbolo, ecuacion: simbolo} : {ecuacion: simbolo};
        return [[simbolo, nombre + ' minúscula', perfiles],
            [mayuscula, nombre + ' mayúscula', {ecuacion: mayuscula}]];
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
        ['°', 'Grados'], ['∠', 'Ángulo'], ['△', 'Triángulo'], ['∴', 'Por lo tanto'], ['∵', 'Porque'],
        ['‰', 'Por mil', {matriz: '‰', numero: '‰', ecuacion: '‰'}],
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
    const catalogo = Object.entries(grupos).flatMap(([grupo, entradas]) =>
        entradas.map(([simbolo, nombre, campos = {}, tecla]) => ({grupo, simbolo, nombre, campos, tecla})));
    const PERFILES_POR_MODULO = {
        inicio: ['texto'],
        sistemas: ['ecuacion', 'numero'],
        matrices: ['matriz', 'numero'],
        vectores: ['numero'],
        inversa: ['numero'],
        determinantes: ['numero'],
        factorizacion_lu: ['numero'],
        leontief: ['numero'],
        transformaciones: ['numero'],
        visualizador: ['numero'],
        bases: ['base'],
        romanos: ['romano'],
        metodos_cerrados: ['funcion', 'real'],
        biseccion: ['funcion', 'real'],
        regla_falsa: ['funcion', 'real'],
        metodos_abiertos: ['funcion', 'real'],
    };
    const MENSAJES_SIN_SIMBOLOS = {
        romano: 'Este campo solo admite números romanos (I, V, X, L, C, D, M).',
        entero: 'Este campo solo admite números enteros positivos.',
    };

    function perfilesActivos(destino, modulo) {
        if (destino?.tipo) return [destino.tipo];
        if (modulo && Object.hasOwn(PERFILES_POR_MODULO, modulo)) return [...PERFILES_POR_MODULO[modulo]];
        return ['texto'];
    }

    function admiteTodos(perfiles) {
        return Array.isArray(perfiles) && perfiles.includes('texto');
    }

    function esCompatibleConPerfiles(entrada, perfiles) {
        if (!entrada || !Array.isArray(perfiles)) return false;
        if (admiteTodos(perfiles)) return true;
        const campos = entrada.campos || {};
        return perfiles.some(perfil => Boolean(campos[perfil]));
    }

    function simbolosDisponibles(listaCatalogo, perfiles) {
        if (admiteTodos(perfiles)) return [...listaCatalogo];
        return listaCatalogo.filter(entrada => esCompatibleConPerfiles(entrada, perfiles));
    }

    function gruposDisponibles(disponibles) {
        return [...new Set(disponibles.map(entrada => entrada.grupo))];
    }

    function textoInsercion(entrada, destino) {
        if (!destino) return undefined;
        if (destino.tipo === 'texto') return entrada.simbolo;
        return entrada.campos?.[destino.tipo];
    }

    function mensajeVacio(perfiles, consulta) {
        if (!simbolosDisponibles(catalogo, perfiles).length) {
            return MENSAJES_SIN_SIMBOLOS[perfiles[0]] || 'Este campo no admite símbolos matemáticos adicionales.';
        }
        if (admiteTodos(perfiles)) {
            return 'Sin resultados. Busca por nombre, símbolo o código Unicode, como U+221E.';
        }
        return consulta
            ? 'Sin resultados compatibles. Prueba otro nombre o símbolo.'
            : 'Este campo no admite símbolos matemáticos adicionales.';
    }

    window.scalaris.catalogoSimbolos = catalogo;
    window.scalaris.perfilesSimbolos = {
        PERFILES_POR_MODULO,
        MENSAJES_SIN_SIMBOLOS,
        perfilesActivos,
        admiteTodos,
        esCompatibleConPerfiles,
        simbolosDisponibles,
        gruposDisponibles,
        textoInsercion,
        mensajeVacio,
    };
}
