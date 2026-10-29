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
  const literales = new Set(), errores = [];
  recorrer(arbol, nodo => {
    if (nodo.type === 'VariableDeclarator' && nodo.id.type === 'Identifier' && esNumero(nodo.init)) {
      literales.add(nodo.id.name);
    }
  });
  function esDuracion(nodo) {
    return esNumero(nodo) || (nodo?.type === 'Identifier' && literales.has(nodo.name));
  }
  recorrer(arbol, nodo => comprobarNodo(nodo, esDuracion, errores));
  return errores;
}

function comprobarNodo(nodo, esDuracion, errores) {
  if (nodo.type === 'Property' && ['duration', 'delay'].includes(nodo.key.name || nodo.key.value) && esDuracion(nodo.value)) errores.push('duración literal');
  if (esLlamadaAnimate(nodo) && esDuracion(nodo.arguments[1])) errores.push('animate con duración literal');
  if (nodo.type === 'Literal' && typeof nodo.value === 'string' && /cubic-bezier\s*\(/i.test(nodo.value)) errores.push('curva literal');
}

function esLlamadaAnimate(nodo) {
  return nodo.type === 'CallExpression' && nodo.callee.type === 'MemberExpression' && nodo.callee.property.name === 'animate';
}

function esNumero(nodo) {
  return nodo?.type === 'Literal' && typeof nodo.value === 'number' ||
    nodo?.type === 'UnaryExpression' && ['+', '-'].includes(nodo.operator) && esNumero(nodo.argument);
}

if (require.main === module) {
  const rutas = JSON.parse(fs.readFileSync(0, 'utf8'));
  const errores = rutas.flatMap(ruta => analizarTiempos(fs.readFileSync(ruta, 'utf8')).map(error => `${ruta}: ${error}`));
  process.stdout.write(JSON.stringify(errores));
}
module.exports = { analizarTiempos };
