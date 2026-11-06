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
