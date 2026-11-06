// Botões «Copiar» dos prompts
document.querySelectorAll('.copy').forEach(function (btn) {
  btn.addEventListener('click', function () {
    var el = document.getElementById(btn.getAttribute('data-copy'));
    var text = el ? el.textContent : '';
    function done(ok) { btn.textContent = ok ? 'Copiado' : 'Seleciona e copia'; setTimeout(function () { btn.textContent = 'Copiar'; }, 1800); }
    function selectText() { try { var r = document.createRange(); r.selectNodeContents(el); var s = window.getSelection(); s.removeAllRanges(); s.addRange(r); } catch (e) {} }
    try { navigator.clipboard.writeText(text).then(function () { done(true); }, function () { selectText(); done(false); }); }
    catch (e) { selectText(); done(false); }
  });
});

// Tema claro (por omissão) / escuro, lembrado neste navegador
(function () {
  var b = document.getElementById('tema');
  if (!b) return;
  var ICON = '<svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true" style="vertical-align:-2px;margin-right:6px"><circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M8 1.5a6.5 6.5 0 0 1 0 13z" fill="currentColor"/></svg>';
  function rotulo() { b.innerHTML = ICON + (document.documentElement.getAttribute('data-theme') === 'dark' ? 'Claro' : 'Escuro'); }
  rotulo();
  b.addEventListener('click', function () {
    var escuro = document.documentElement.getAttribute('data-theme') !== 'dark';
    if (escuro) document.documentElement.setAttribute('data-theme', 'dark'); else document.documentElement.removeAttribute('data-theme');
    try { localStorage.setItem('tema', escuro ? 'escuro' : 'claro'); } catch (e) {}
    rotulo();
  });
})();

// Menu do telemóvel
(function () {
  var b = document.getElementById('menu-btn'), m = document.getElementById('menu');
  if (!b || !m) return;
  function set(open) { m.classList.toggle('open', open); b.setAttribute('aria-expanded', open ? 'true' : 'false'); b.innerHTML = (open ? '<span aria-hidden="true">✕</span> Fechar' : '<span aria-hidden="true">☰</span> Menu'); }
  b.addEventListener('click', function () { set(!m.classList.contains('open')); });
  document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') set(false); });
  m.querySelectorAll('a').forEach(function (a) { a.addEventListener('click', function () { set(false); }); });
})();
