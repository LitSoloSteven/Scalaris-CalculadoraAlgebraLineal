'use strict';
const {afirmar,base,crearNavegador,observarErrores,estable,guardar}=require('./comun_navegador.cjs');
(async()=>{
 const navegador=await crearNavegador(), contexto=await navegador.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
 const pagina=await contexto.newPage(),errores=observarErrores(pagina),resultados={};
 try{
  await contexto.addInitScript(()=>{if(location.protocol==='http:')sessionStorage.setItem('presentacion-mostrada','1');});
  await pagina.goto(base+'/');await estable(pagina);
  afirmar.match(await pagina.locator('#inicio-fila-algebra').innerText(),/Empieza aquí/);
  await pagina.locator('#inicio-fila-algebra').tap();await pagina.locator('dialog[open]').waitFor();
  await pagina.locator('dialog[open] a[href="/algebra-lineal/matrices"]').tap();await pagina.waitForURL('**/algebra-lineal/matrices');await estable(pagina);
  const lista=pagina.locator('.navegacion-elementos'),sesion=await contexto.newCDPSession(pagina);
  await lista.evaluate(e=>e.scrollLeft=0);const caja=await lista.boundingBox();
  const y=caja.y+caja.height/2,inicio=caja.x+caja.width*.85,fin=caja.x+caja.width*.15;
  await sesion.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:inicio,y}]});
  for(let indice=1;indice<=8;indice++){await sesion.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:inicio+(fin-inicio)*indice/8,y}]});await pagina.waitForTimeout(20);}
  await sesion.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await pagina.waitForTimeout(250);
  resultados.tactil=await lista.evaluate(e=>e.scrollLeft);afirmar.ok(resultados.tactil>10);
  await lista.evaluate(e=>e.scrollLeft=0);await lista.hover();await pagina.mouse.wheel(500,0);await pagina.waitForTimeout(250);
  resultados.trackpad=await lista.evaluate(e=>e.scrollLeft);afirmar.ok(resultados.trackpad>10);
  afirmar.equal(await pagina.evaluate(()=>scrollX),0);
  await pagina.locator('.navegacion-inicio').tap();await pagina.waitForURL(base+'/');await estable(pagina);
  afirmar.match(await pagina.locator('#inicio-fila-algebra').innerText(),/Sigue aquí/);
  afirmar.deepEqual(errores,[]);resultados.recientes=true;resultados.errores=errores;
  guardar('desplazamiento-tactil-trackpad.json',resultados);console.log('TACTIL Y TRACKPAD correctos',JSON.stringify(resultados));
 }finally{await contexto.close();await navegador.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
