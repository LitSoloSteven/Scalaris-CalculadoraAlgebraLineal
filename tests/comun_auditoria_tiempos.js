'use strict';
const acorn = require('internal/deps/acorn/acorn/dist/acorn');
const fs = require('node:fs');

function recorrer(nodo, visitar) {
  if (!nodo || typeof nodo !== 'object') return;
  if (typeof nodo.type === 'string') visitar(nodo);
  for (const valor of Object.values(nodo)) {
    if (Array.isArray(valor)) valor.forEach(hijo => recorrer(hijo, visitar));
    else if (valor && typeof valor === 'object') recorrer(valor, visitar);
  }
}

function analizarTiempos(texto) {
  const arbol = acorn.parse(texto, { ecmaVersion: 'latest', sourceType: 'module' });
  const declaraciones = new Map(), errores = [];
  recorrer(arbol, nodo => {
    if (nodo.type === 'VariableDeclarator' && nodo.id.type === 'Identifier') {
      declaraciones.set(nodo.id.name, nodo.init);
    }
  });
  function esDuracion(nodo) {
    return esNumero(nodo, declaraciones, new Set());
  }
  recorrer(arbol, nodo => comprobarNodo(nodo, esDuracion, errores));
  return errores;
}

function comprobarNodo(nodo, esDuracion, errores) {
  if (nodo.type === 'Property' && ['duration', 'delay'].includes(nodo.key.name || nodo.key.value) && esDuracion(nodo.value)) errores.push('duración literal');
  if (esLlamadaAnimate(nodo) && esDuracion(nodo.arguments[1])) errores.push('animate con duración literal');
  if (esCurvaLiteral(nodo)) errores.push('curva literal');
  if (esTemporizadorAnimado(nodo, esDuracion)) errores.push('retardo literal de animación');
}

function esTemporizadorAnimado(nodo, esDuracion) {
  if (nodo.type !== 'CallExpression' || nodo.callee.name !== 'setTimeout' || !esDuracion(nodo.arguments[1])) return false;
  let anima = false;
  recorrer(nodo.arguments[0], hijo => { if (esLlamadaAnimate(hijo)) anima = true; });
  return anima;
}

function esLlamadaAnimate(nodo) {
  return nodo.type === 'CallExpression' && nodo.callee.type === 'MemberExpression' &&
    (nodo.callee.property.name || nodo.callee.property.value) === 'animate';
}

function esCurvaLiteral(nodo) {
  if (nodo.type === 'Literal' && typeof nodo.value === 'string') return /cubic-bezier\s*\(/i.test(nodo.value);
  return nodo.type === 'TemplateLiteral' && nodo.quasis.some(parte => /cubic-bezier\s*\(/i.test(parte.value.raw));
}

function esNumero(nodo, declaraciones, vistos) {
  if (!nodo) return false;
  if (nodo.type === 'Literal') return typeof nodo.value === 'number';
  if (nodo.type === 'UnaryExpression') return esNumero(nodo.argument, declaraciones, vistos);
  if (nodo.type === 'BinaryExpression') return esNumero(nodo.left, declaraciones, new Set(vistos)) && esNumero(nodo.right, declaraciones, new Set(vistos));
  if (nodo.type !== 'Identifier' || vistos.has(nodo.name)) return false;
  vistos.add(nodo.name);
  return esNumero(declaraciones.get(nodo.name), declaraciones, vistos);
}

if (require.main === module) {
  const rutas = JSON.parse(fs.readFileSync(0, 'utf8'));
  const errores = rutas.flatMap(ruta => analizarTiempos(fs.readFileSync(ruta, 'utf8')).map(error => `${ruta}: ${error}`));
  process.stdout.write(JSON.stringify(errores));
}
module.exports = { analizarTiempos };
