// Arquivo: pesquisa, mês, tipo e etiquetas sobre /data/registo.json
function iniciar(reg){
    var MESES = ['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'];
  var DIAS = ['domingo','segunda-feira','terça-feira','quarta-feira','quinta-feira','sexta-feira','sábado'];
  function norm(s){ return (s||'').toString().normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase(); }
  function esc(s){ return (s||'').toString().replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
  function dataExt(iso){ var d=new Date(iso+'T12:00:00'); return DIAS[d.getDay()]+', '+d.getDate()+' de '+MESES[d.getMonth()]+' de '+d.getFullYear(); }

  // achatar
  var itens = [];
  reg.edicoes.slice().sort(function(a,b){return b.numero-a.numero;}).forEach(function(e){
    var base = {ed:e.numero, data:e.data, ficheiro:e.url, mes:e.data.slice(0,7)};
    (e.pecas||[]).forEach(function(p){
      itens.push(Object.assign({}, base, {tipo: p.tipo==='Técnica'?'Técnica':'Notícia', titulo:p.titulo, lead:p.lead, cat:p.categoria, produto:p.produto, tags:p.etiquetas||[], id:p.id}));
    });
    (e.fica_de_fora||[]).forEach(function(f){
      if(typeof f==='string') f={titulo:f};
      itens.push(Object.assign({}, base, {tipo:'Fora de Portugal', titulo:f.titulo, lead:f.lead, cat:'Anunciado, mas não para nós', produto:'', tags:f.etiquetas||[], id:f.id||'out-h'}));
    });
    if(e.conceito){
      var c = typeof e.conceito==='string'?{nome:e.conceito}:e.conceito;
      itens.push(Object.assign({}, base, {tipo:'Conceito', titulo:c.nome, lead:c.lead, cat:'Conceito do dia', produto:'', tags:c.etiquetas||[], id:c.id||'c-h'}));
    }
  });
  itens.forEach(function(i){ i.txt = norm([i.titulo,i.lead,i.cat,i.produto,i.tipo,i.tags.join(' ')].join(' ')); });

  var estado = {q:'', mes:'', tipo:'', tags:[]};
  try{ var s=JSON.parse(sessionStorage.getItem('intel-arquivo')||'null'); if(s) estado=Object.assign(estado,s); }catch(e){}

  // meses
  var meses = Array.from(new Set(itens.map(function(i){return i.mes;}))).sort().reverse();
  var selMes = document.getElementById('mes');
  meses.forEach(function(m){ var o=document.createElement('option'); o.value=m; o.textContent=MESES[+m.slice(5,7)-1]+' de '+m.slice(0,4); selMes.appendChild(o); });

  // tipos
  var TIPOS = [['','Tudo'],['Notícia','Notícias'],['Técnica','Técnicas'],['Conceito','Conceitos'],['Fora de Portugal','Fora de Portugal']];
  var boxTipos = document.getElementById('tipos');
  TIPOS.forEach(function(t){ var b=document.createElement('button'); b.type='button'; b.className='chip'; b.dataset.tipo=t[0]; b.textContent=t[1]; b.addEventListener('click',function(){ estado.tipo=t[0]; render(); }); boxTipos.appendChild(b); });

  // nuvem de etiquetas
  var cont = {};
  itens.forEach(function(i){ i.tags.forEach(function(t){ cont[t]=(cont[t]||0)+1; }); });
  var tagsOrd = Object.keys(cont).sort(function(a,b){ return cont[b]-cont[a] || a.localeCompare(b,'pt'); });
  var nuvem = document.getElementById('nuvem');
  tagsOrd.forEach(function(t){ var b=document.createElement('button'); b.type='button'; b.className='chip'; b.dataset.tag=t; b.innerHTML=esc(t)+'<span class="c">'+cont[t]+'</span>'; b.addEventListener('click',function(){ toggleTag(t); }); nuvem.appendChild(b); });
  document.getElementById('mais').addEventListener('click',function(){ nuvem.classList.toggle('open'); this.textContent = nuvem.classList.contains('open')?'Mostrar menos':'Ver todas as etiquetas'; });

  function toggleTag(t){ var k=estado.tags.indexOf(t); if(k>=0) estado.tags.splice(k,1); else estado.tags.push(t); render(); }

  var q = document.getElementById('q');
  q.value = estado.q;
  selMes.value = estado.mes;
  q.addEventListener('input',function(){ estado.q=q.value; render(); });
  selMes.addEventListener('change',function(){ estado.mes=selMes.value; render(); });
  document.getElementById('limpar').addEventListener('click',function(){ estado={q:'',mes:'',tipo:'',tags:[]}; q.value=''; selMes.value=''; render(); });

  function realca(texto, termos){
    var out = esc(texto); if(!termos.length) return out;
    termos.forEach(function(t){
      if(t.length<2) return;
      var n = norm(out), res='', i=0, j;
      while((j=n.indexOf(t,i))>=0){ res+=out.slice(i,j)+'<mark>'+out.slice(j,j+t.length)+'</mark>'; i=j+t.length; }
      out = res+out.slice(i);
    });
    return out;
  }

  var tipoClasse = {'Notícia':'','Técnica':'t-tecnica','Conceito':'t-conceito','Fora de Portugal':'t-fora'};

  function render(){
    try{ sessionStorage.setItem('intel-arquivo', JSON.stringify(estado)); }catch(e){}
    var termos = norm(estado.q).split(/\s+/).filter(Boolean);
    var res = itens.filter(function(i){
      if(estado.mes && i.mes!==estado.mes) return false;
      if(estado.tipo && i.tipo!==estado.tipo) return false;
      for(var k=0;k<estado.tags.length;k++){ if(i.tags.indexOf(estado.tags[k])<0) return false; }
      for(var m=0;m<termos.length;m++){ if(i.txt.indexOf(termos[m])<0) return false; }
      return true;
    });
    boxTipos.querySelectorAll('.chip').forEach(function(b){ b.setAttribute('aria-pressed', b.dataset.tipo===estado.tipo?'true':'false'); });
    nuvem.querySelectorAll('.chip').forEach(function(b){ b.setAttribute('aria-pressed', estado.tags.indexOf(b.dataset.tag)>=0?'true':'false'); });
    document.getElementById('contagem').textContent = res.length+(res.length===1?' resultado':' resultados')+(estado.tags.length?' · etiquetas: '+estado.tags.join(' + '):'');
    var lista = document.getElementById('lista'), html='', edAtual=null;
    if(!res.length){ lista.innerHTML='<p class="empty">Nada. Nem a Inês encontrou isto nas newsletters. Experimenta outra palavra ou limpa os filtros.</p>'; return; }
    res.forEach(function(i){
      if(i.ed!==edAtual){ if(edAtual!==null) html+='</section>'; edAtual=i.ed; html+='<section class="group"><h2><a href="'+i.ficheiro+'">N.º '+i.ed+' · '+dataExt(i.data)+'</a></h2>'; }
      var href = i.ficheiro+'#'+i.id;
      html+='<article class="item"><div class="type '+tipoClasse[i.tipo]+'">'+esc(i.tipo)+'</div><div>'+
        '<h3><a href="'+href+'">'+realca(i.titulo,termos)+'</a></h3>'+
        (i.lead?'<p>'+realca(i.lead,termos)+'</p>':'')+
        '<div class="meta">'+esc(i.cat)+(i.produto?' · '+esc(i.produto):'')+'</div>'+
        '<div class="tags">'+i.tags.map(function(t){return '<button type="button" class="chip" data-t="'+esc(t)+'" aria-pressed="'+(estado.tags.indexOf(t)>=0)+'">'+esc(t)+'</button>';}).join('')+'</div>'+
        '</div></article>';
    });
    html+='</section>';
    lista.innerHTML = html;
    lista.querySelectorAll('.tags .chip').forEach(function(b){ b.addEventListener('click',function(){ toggleTag(b.dataset.t); window.scrollTo({top:0,behavior:'smooth'}); }); });
  }

  var nEd = reg.edicoes.length, nP = itens.length;
  
  render();
}

fetch('/data/registo.json', {cache: 'no-cache'})
  .then(function(r){ if(!r.ok) throw new Error(r.status); return r.json(); })
  .then(iniciar)
  .catch(function(){ document.getElementById('contagem').textContent = 'Não foi possível carregar o arquivo. Tenta recarregar a página.'; });
