#!/usr/bin/env python3
"""Gera o site estático do «Inteligências» em public/ a partir de site/editions/*.json.

Uso:  python3 tools/build.py
Sem dependências externas. Não editar public/ à mão: é sempre regenerado.
"""
import hashlib, html, json, re, shutil
from datetime import date, datetime, timezone
from email.utils import format_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
PUB = ROOT / "public"
CFG = json.loads((SITE / "config.json").read_text())
URL = CFG.get("site_url", "").rstrip("/")
e = html.escape


def _v(name):
    """Impressão digital do ficheiro, para obrigar o navegador a carregar a versão nova."""
    return hashlib.sha1((SITE / "assets" / name).read_bytes()).hexdigest()[:8]


V = {n: _v(n) for n in ("site.css", "site.js", "arquivo.js")}

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]


def data_ext(iso, cap=True):
    d = date.fromisoformat(iso)
    s = f"{DIAS[d.weekday()]}, {d.day} de {MESES[d.month - 1]} de {d.year}"
    return s[0].upper() + s[1:] if cap else s


SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ORG = {"@type": "Organization", "name": "Inteligências", "url": (URL or "") + "/"}


def piece_url(ed, p):
    return f'/edicoes/{ed["numero"]:03d}/{p["slug"]}'


def concept_url(c):
    return f'/conceitos/{c["slug"]}'


def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def strip_tags(t):
    return re.sub(r"<[^>]+>", "", t)


def load_editions():
    eds = [json.loads(p.read_text()) for p in sorted((SITE / "editions").glob("*.json"))]
    eds.sort(key=lambda x: x["numero"])
    nums = [x["numero"] for x in eds]
    assert nums == list(range(1, len(eds) + 1)), f"numeração com falhas: {nums}"
    vistos = set()
    for ed in eds:
        for x in ed["pecas"] + [ed["conceito"]]:
            sl = x.get("slug")
            assert sl and SLUG_RE.match(sl), f'N.º {ed["numero"]}: slug em falta ou inválido em «{x.get("titulo") or x.get("nome")}»'
            assert sl not in vistos, f"slug repetido: {sl} (os endereços são permanentes; escolhe outro)"
            vistos.add(sl)
    return eds


# ------------------------------------------------------------------ peças
def pill(v, cls):
    return f'<span class="pill {cls}">{e(v)}</span>' if cls else e(v)


def piece(i, p, url=None, h="h2"):
    passos = "".join(f"<li>{e(s)}</li>" for s in p["passos"])
    ficha = "".join(f"<dt>{e(k)}</dt><dd>{pill(v, c)}</dd>" for k, v, c in p["ficha"])
    fontes = "".join(f'<a href="{e(u)}" rel="noopener">{e(t)}</a>' for t, u in p["fontes"])
    nota = f'<p class="caveat"><b>{e(p["nota"]["tipo"])}:</b> {e(p["nota"]["texto"])}</p>' if p.get("nota") else ""
    pid = f"p{i}"
    return f'''
<article class="story" id="{e(p["id"])}">
  <div class="kicker"><b>{i:02d}</b><span>{e(p["categoria"])} · {e(p["produto"])} · {e(p["kicker_data"])}</span></div>
  <{h}>{f'<a class="perma" href="{e(url)}">{e(p["titulo"])}</a>' if url else e(p["titulo"])}</{h}>
  <p class="dek">{e(p["lead"])}</p>
  <div class="grid">
    <div>
      <figure class="figure">
        {p["svg"]}
        <figcaption>{e(p["legenda"])}</figcaption>
      </figure>
      <div class="block"><h3>O que é</h3><p>{e(p["o_que_e"])}</p></div>
      <div class="block"><h3>Porque importa</h3><p>{e(p["porque"])}</p></div>
      <div class="use">
        <h3>Como usar já</h3>
        <ol>{passos}</ol>
        <div class="prompt">
          <div class="prompt-head"><span>{e(p["prompt_titulo"])}</span><button class="copy" type="button" data-copy="{pid}">Copiar</button></div>
          <pre id="{pid}">{e(p["prompt"])}</pre>
        </div>
      </div>
      {nota}
    </div>
    <aside class="card" aria-label="Ficha técnica">
      <h4>Ficha</h4>
      <dl>{ficha}</dl>
      <div class="src">Fontes{fontes}</div>
    </aside>
  </div>
</article>'''


def fora(f):
    if not f:
        return ""
    return f'''
<section class="out" id="out-h" aria-labelledby="out-t">
  <span class="lbl">Anunciado, mas não para nós</span>
  <h3 id="out-t">{e(f["titulo"])}</h3>
  <p>{e(f["texto"])} <a href="{e(f["fonte"][1])}" rel="noopener">{e(f["fonte"][0])}</a></p>
</section>'''


def conceito(c, url=None, h="h2"):
    hab = "".join(f"<li><b>{e(a)}</b> {e(b)}</li>" for a, b in c["habitos"])
    apro = " · ".join(f'<a href="{e(u)}" rel="noopener">{e(t)}</a>' for t, u in c["aprofundar"])
    return f'''
<section class="concept" id="c-h" aria-labelledby="c-t">
  <div class="kicker"><b>Conceito do dia</b><span>· {e(c["liga"])}</span></div>
  <{h} id="c-t">{f'<a class="perma" href="{e(url)}">{e(c["nome"])}</a>' if url else e(c["nome"])}</{h}>
  <p class="pron">{c["sub"]}</p>
  <p>{e(c["intro"])}</p>
  <figure class="figure">{c["svg"]}</figure>
  <p>{e(c["corpo"])}</p>
  <p>Três hábitos práticos:</p>
  <ul>{hab}</ul>
  <p style="margin-top:16px;font-size:14px;opacity:.8">Para aprofundar: {apro}</p>
</section>'''


# ------------------------------------------------------------------ moldura
def head(title, desc, path, extra="", og_type="website"):
    canon = f'<link rel="canonical" href="{URL}{path}">' if URL else ""
    og_url = f'<meta property="og:url" content="{URL}{path}">' if URL else ""
    rss = '<link rel="alternate" type="application/rss+xml" title="Inteligências" href="/feed.xml">' if URL else ""
    return f'''<!DOCTYPE html>
<html lang="pt-PT">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:type" content="{og_type}">
<meta name="twitter:card" content="summary">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<meta property="og:site_name" content="Inteligências">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:locale" content="pt_PT">
{og_url}
{canon}
{rss}
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/assets/fonts/newsreader-latin-opsz-normal.woff2" as="font" type="font/woff2" crossorigin>
<script>try{{if(localStorage.getItem('tema')==='escuro')document.documentElement.setAttribute('data-theme','dark')}}catch(e){{}}</script>
<link rel="stylesheet" href="/assets/site.css?v={V['site.css']}">
{extra}
</head>
<body>'''


MENU = [("edicao", "/", "Última edição"), ("arquivo", "/arquivo/", "Arquivo"), ("sobre", "/sobre/", "Como é feita"), ("redacao", "/redacao/", "A redação")]


def masthead(stamp, h1="Inteligências", tag=None, active=None):
    tag = tag or CFG["slogan"]
    cur = ' aria-current="page"'
    links = "".join(f'<a href="{u}"{cur if k == active else ""}>{t}</a>' for k, u, t in MENU)
    stamp_html = f'<span class="stamp">{stamp}</span>' if stamp else ""
    return f'''
<header class="topbar">
  <div class="wrap topbar-in">
    <button class="menu-btn" id="menu-btn" type="button" aria-expanded="false" aria-controls="menu"><span aria-hidden="true">☰</span> Menu</button>
    <nav class="menu" id="menu" aria-label="Principal">{links}</nav>
    <button class="theme" id="tema" type="button" aria-label="Mudar o tema"><svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true" style="vertical-align:-2px;margin-right:6px"><circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M8 1.5a6.5 6.5 0 0 1 0 13z" fill="currentColor"/></svg>Escuro</button>
  </div>
</header>
<div class="wrap mast{'' if h1 else ' slim'}">
  {'' if h1 == "Inteligências" else '<a class="eyebrow" href="/">Inteligências</a>'}
  {f'<h1>{e(h1)}<span>.</span></h1>' if h1 else ''}
  {f'<p class="tagline">{e(tag)}</p>' if h1 else ''}
  <div class="stamps">{stamp_html}<a class="badge" href="/sobre/#feito-por-ia">Feito por IA</a></div>
</div>'''


def footer(eds, current=None):
    cur = ' aria-current="page"'
    items = "".join(
        f'<li><a href="/edicoes/{x["numero"]:03d}"{cur if current == x["numero"] else ""}>N.º {x["numero"]} · {e(data_ext(x["data"], False))}</a></li>'
        for x in reversed(eds))
    return f'''
<footer class="wrap">
  <p><b>Como é feita.</b> Seleção e redação por agentes de IA, com um critério: um profissional não técnico consegue tirar partido disto esta semana, em Portugal? As fontes principais são as notas de versão e os anúncios oficiais; newsletters de referência servem de radar. Cada facto é verificado na fonte oficial ou, quando esta não está acessível, em várias fontes independentes. «Testado: não» quer dizer que a redação não experimentou a funcionalidade. <a href="/sobre/">Mais sobre o método</a>.</p>
  <nav class="archive" aria-label="Edições">
    <p><b>Arquivo.</b> <a href="/arquivo/">Pesquisar todas as peças por palavra, mês ou etiqueta →</a></p>
    <ul>{items}</ul>
  </nav>
  <p class="wink">A palavra «revolucionário» não entrou nesta redação. <a href="/redacao/">Conhece a equipa</a>.</p>
  <p class="sister">Da mesma casa: <a href="https://olhamisto.com/"><b>Olhamisto</b></a>, histórias contadas com dados reais e gráficos, todos os dias úteis. Antes de opinar, olha-me isto.</p>
  <p>Um projeto de <a href="https://pedroxaviersilva.eu/">Pedro Silva</a>.</p>
</footer>'''


def toc_style(n):
    if n == 4:
        return ""
    return f'<style>.toc{{grid-template-columns:repeat({n},1fr)}}@media (max-width:760px){{.toc{{grid-template-columns:1fr}}.toc a,.toc a + a{{border-right:0;padding-left:0;border-bottom:1px solid var(--line)}}}}</style>'


def edition_page(ed, eds):
    n = len(ed["pecas"])
    toc = "".join(f'<a href="#{e(p["id"])}"><span class="n">{i:02d} · {e(p["categoria"])}</span><span class="t">{e(p["titulo"])}</span></a>' for i, p in enumerate(ed["pecas"], 1))
    body = "".join(piece(i, p, piece_url(ed, p)) for i, p in enumerate(ed["pecas"], 1))
    title = f'Inteligências N.º {ed["numero"]} · {data_ext(ed["data"], False)}'
    desc = " · ".join(p["titulo"] for p in ed["pecas"])
    left = f'N.º {ed["numero"]} · {e(data_ext(ed["data"]))} · {n} peças · {ed["minutos"]} min de leitura'
    active = "edicao" if ed["numero"] == eds[-1]["numero"] else None
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "url": f'{URL}/edicoes/{ed["numero"]:03d}', "inLanguage": "pt-PT", "datePublished": ed["data"], "publisher": ORG,
          "hasPart": [{"@type": "Article", "headline": p["titulo"], "url": URL + piece_url(ed, p)} for p in ed["pecas"]] + [{"@type": "Article", "headline": ed["conceito"]["nome"], "url": URL + concept_url(ed["conceito"])}]}
    return (head(title, desc, f'/edicoes/{ed["numero"]:03d}', toc_style(n) + jsonld(ld)) + masthead(left, active=active) +
            f'\n<nav class="wrap toc" aria-label="Nesta edição">{toc}</nav>\n<main class="wrap">{body}{fora(ed.get("fica_de_fora"))}{conceito(ed["conceito"], concept_url(ed["conceito"]))}\n</main>' +
            footer(eds, ed["numero"]) + '\n<script src="/assets/site.js?v=' + V['site.js'] + '" defer></script>\n</body>\n</html>\n')


# ------------------------------------------------------------------ páginas por peça e por conceito
def crumbs(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": n, "item": URL + u} for i, (n, u) in enumerate(items, 1)]}


def related(ed, skip=None):
    links = "".join(f'<li><a href="{piece_url(ed, p)}">{e(p["titulo"])}</a> <span>· {e(p["categoria"])}</span></li>' for p in ed["pecas"] if p is not skip)
    c = ed["conceito"]
    if c is not skip:
        links += f'<li><a href="{concept_url(c)}">{e(c["nome"])}</a> <span>· Conceito do dia</span></li>'
    return f'''
<nav class="related" aria-label="Também nesta edição">
  <h2>Também no N.º {ed["numero"]}</h2>
  <ul>{links}</ul>
  <p><a href="/edicoes/{ed["numero"]:03d}">Ler a edição completa →</a> · <a href="/arquivo/">Arquivo</a></p>
</nav>'''


def piece_page(ed, i, p, eds):
    url = piece_url(ed, p)
    title = f'{p["titulo"]} · Inteligências'
    stamp = f'<a href="/edicoes/{ed["numero"]:03d}">N.º {ed["numero"]} · {e(data_ext(ed["data"], False))}</a>'
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": p["titulo"], "description": p["lead"], "url": URL + url,
           "mainEntityOfPage": URL + url, "datePublished": ed["data"], "dateModified": ed["data"], "inLanguage": "pt-PT",
           "author": ORG, "publisher": ORG, "keywords": ", ".join(p["etiquetas"]), "articleSection": p["categoria"],
           "isPartOf": {"@type": "CollectionPage", "name": f'Inteligências N.º {ed["numero"]}', "url": f'{URL}/edicoes/{ed["numero"]:03d}'}},
          crumbs([("Inteligências", "/"), (f'N.º {ed["numero"]}', f'/edicoes/{ed["numero"]:03d}'), (p["titulo"], url)])]
    extra = "".join(jsonld(x) for x in ld) + f'<meta property="article:published_time" content="{ed["data"]}">' + "".join(f'<meta property="article:tag" content="{e(t)}">' for t in p["etiquetas"])
    return (head(title, p["lead"], url, extra, "article") + masthead(stamp, h1=None) +
            f'\n<main class="wrap single">{piece(i, p, h="h1")}{related(ed, p)}\n</main>' + footer(eds) +
            '\n<script src="/assets/site.js?v=' + V['site.js'] + '" defer></script>\n</body>\n</html>\n')


def concept_page(ed, eds):
    c = ed["conceito"]
    url = concept_url(c)
    title = f'Conceito de IA: {c["nome"]} · Inteligências'
    stamp = f'Conceito · <a href="/edicoes/{ed["numero"]:03d}">N.º {ed["numero"]} · {e(data_ext(ed["data"], False))}</a>'
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": f'{c["nome"]}: {c["lead"]}', "description": c["lead"], "url": URL + url,
           "mainEntityOfPage": URL + url, "datePublished": ed["data"], "inLanguage": "pt-PT", "author": ORG, "publisher": ORG,
           "keywords": ", ".join(c["etiquetas"]),
           "about": {"@type": "DefinedTerm", "name": c["nome"], "alternateName": strip_tags(c["sub"]), "description": c["lead"]}},
          crumbs([("Inteligências", "/"), ("Conceitos", "/arquivo/"), (c["nome"], url)])]
    return (head(title, c["lead"], url, "".join(jsonld(x) for x in ld), "article") + masthead(stamp, h1=None) +
            f'\n<main class="wrap single">{conceito(c, h="h1")}{related(ed, c)}\n</main>' + footer(eds) +
            '\n<script src="/assets/site.js?v=' + V['site.js'] + '" defer></script>\n</body>\n</html>\n')


# ------------------------------------------------------------------ outras páginas
def registo(eds):
    out = {"publicacao": "Inteligências", "gerado": datetime.now(timezone.utc).isoformat(timespec="seconds"), "edicoes": []}
    for ed in eds:
        f = ed.get("fica_de_fora")
        out["edicoes"].append({
            "numero": ed["numero"], "data": ed["data"], "url": f'/edicoes/{ed["numero"]:03d}',
            "pecas": [{k: p[k] for k in ("id", "slug", "tipo", "categoria", "produto", "data_anuncio", "titulo", "lead", "etiquetas")} | {"prompt": p["prompt"], "url": piece_url(ed, p)} for p in ed["pecas"]],
            "fica_de_fora": [{"id": "out-h", "titulo": f["titulo"], "lead": f["lead"], "etiquetas": f["etiquetas"]}] if f else [],
            "conceito": {"id": "c-h", "slug": ed["conceito"]["slug"], "url": concept_url(ed["conceito"]), "nome": ed["conceito"]["nome"], "lead": ed["conceito"]["lead"], "etiquetas": ed["conceito"]["etiquetas"]},
        })
    return out


def archive_page(eds):
    left = f'{len(eds)} edições · desde {e(data_ext(eds[0]["data"], False))}'
    return (head("Arquivo · Inteligências", "Todas as peças, técnicas e conceitos do Inteligências, com pesquisa por palavra, mês e etiqueta.", "/arquivo/") +
            masthead(left, "Arquivo", "Todas as peças, técnicas e conceitos. Pesquisa por palavra, mês ou etiqueta.", "arquivo") + '''
<main class="wrap">
  <section class="tools" aria-label="Pesquisa e filtros">
    <div class="row">
      <label for="q" style="position:absolute;left:-9999px">Pesquisar</label>
      <input id="q" class="search" type="search" placeholder="Pesquisar: chatgpt, vídeo, prompt, folhas de cálculo…" autocomplete="off">
      <label for="mes" style="position:absolute;left:-9999px">Mês</label>
      <select id="mes"><option value="">Todos os meses</option></select>
    </div>
    <div class="row" id="tipos" role="group" aria-label="Tipo"></div>
    <div>
      <div class="tags-cloud" id="nuvem" role="group" aria-label="Etiquetas"></div>
      <button class="more" id="mais" type="button">Ver todas as etiquetas</button>
    </div>
    <div class="status"><span id="contagem" aria-live="polite">A carregar…</span><button class="clear" id="limpar" type="button">Limpar filtros</button></div>
  </section>
  <div id="lista"></div>
</main>''' + footer(eds) + '\n<script src="/assets/site.js?v=' + V['site.js'] + '" defer></script>\n<script src="/assets/arquivo.js?v=' + V['arquivo.js'] + '" defer></script>\n</body>\n</html>\n')


def about_page(eds):
    left = "Como é feita"
    body = (SITE / "sobre.html").read_text()
    return (head("Como é feita · Inteligências", "Como o Inteligências é escolhido, escrito e verificado.", "/sobre/") +
            masthead(None, "Como é feita", "O critério, as fontes e o que quer dizer «Feito por IA».", "sobre") + f'\n<main class="wrap prose">{body}</main>' + footer(eds) + '\n<script src="/assets/site.js?v=' + V['site.js'] + '" defer></script>\n</body>\n</html>\n')


def redacao_page(eds):
    body = (SITE / "redacao.html").read_text()
    return (head("A redação · Inteligências", "Quem faz o Inteligências: uma redação de agentes de IA e um humano.", "/redacao/") +
            masthead(None, "A redação", "Oito agentes de IA, um humano e nenhuma reunião de pauta.", "redacao") + f'\n<main class="wrap">{body}</main>' + footer(eds) + '\n<script src="/assets/site.js?v=' + V['site.js'] + '" defer></script>\n</body>\n</html>\n')


def page_404(eds):
    return (head("Página não encontrada · Inteligências", "Página não encontrada.", "/404") + masthead(None, "Não está cá") +
            '\n<main class="wrap prose"><p>Pedimos ao RELEASE-O-MATIC que procurasse esta página nas notas de versão e ao INBOX PONTO ZERO que a procurasse nas newsletters. Nenhum dos dois a encontrou. Pode ter mudado de sítio ou nunca ter existido.</p><p>Tenta a <a href="/">última edição</a> ou procura no <a href="/arquivo/">arquivo</a>.</p></main>' +
            footer(eds) + '\n<script src="/assets/site.js?v=' + V['site.js'] + '" defer></script>\n</body>\n</html>\n')


def rss(eds):
    items = []
    for ed in reversed(eds):
        d = datetime.fromisoformat(ed["data"] + "T14:00:00+00:00")
        desc = " · ".join(p["titulo"] for p in ed["pecas"]) + f' · Conceito do dia: {ed["conceito"]["nome"]}'
        link = f'{URL}/edicoes/{ed["numero"]:03d}'
        items.append(f'<item><title>{e("N.º %d · %s" % (ed["numero"], data_ext(ed["data"], False)))}</title><link>{link}</link><guid>{link}</guid><pubDate>{format_datetime(d)}</pubDate><description>{e(desc)}</description></item>')
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Inteligências</title><link>{URL}/</link><description>{e(CFG["slogan"])}</description><language>pt-PT</language>{"".join(items)}</channel></rss>\n'


def sitemap(eds):
    last = eds[-1]["data"]
    urls = [("/", last), ("/arquivo/", last), ("/sobre/", None), ("/redacao/", None)]
    for x in eds:
        urls.append((f'/edicoes/{x["numero"]:03d}', x["data"]))
        urls += [(piece_url(x, p), x["data"]) for p in x["pecas"]]
        urls.append((concept_url(x["conceito"]), x["data"]))
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(
        f"<url><loc>{URL}{u}</loc>{f'<lastmod>{d}</lastmod>' if d else ''}</url>" for u, d in urls) + "</urlset>\n"


# ------------------------------------------------------------------ main
def main():
    eds = load_editions()
    if PUB.exists():
        shutil.rmtree(PUB)
    (PUB / "edicoes").mkdir(parents=True)
    shutil.copytree(SITE / "assets", PUB / "assets")
    shutil.copy(SITE / "favicon.svg", PUB / "favicon.svg")
    shutil.copy(SITE / "_headers", PUB / "_headers")
    (PUB / "conceitos").mkdir()
    for ed in eds:
        (PUB / "edicoes" / f'{ed["numero"]:03d}.html').write_text(edition_page(ed, eds))
        d = PUB / "edicoes" / f'{ed["numero"]:03d}'
        d.mkdir()
        for i, p in enumerate(ed["pecas"], 1):
            (d / f'{p["slug"]}.html').write_text(piece_page(ed, i, p, eds))
        (PUB / "conceitos" / f'{ed["conceito"]["slug"]}.html').write_text(concept_page(ed, eds))
    site_ld = jsonld({"@context": "https://schema.org", "@type": "WebSite", "name": "Inteligências", "url": URL + "/", "inLanguage": "pt-PT", "description": CFG["slogan"], "publisher": ORG})
    latest = edition_page(eds[-1], eds).replace("</head>", site_ld + "\n</head>", 1)
    latest = latest.replace(f'<link rel="canonical" href="{URL}/edicoes/{eds[-1]["numero"]:03d}">', f'<link rel="canonical" href="{URL}/">') if URL else edition_page(eds[-1], eds)
    (PUB / "index.html").write_text(latest)
    (PUB / "arquivo").mkdir()
    (PUB / "arquivo" / "index.html").write_text(archive_page(eds))
    (PUB / "sobre").mkdir()
    (PUB / "sobre" / "index.html").write_text(about_page(eds))
    (PUB / "redacao").mkdir()
    (PUB / "redacao" / "index.html").write_text(redacao_page(eds))
    (PUB / "404.html").write_text(page_404(eds))
    (PUB / "data").mkdir()
    (PUB / "data" / "registo.json").write_text(json.dumps(registo(eds), ensure_ascii=False, indent=1))
    robots = "User-agent: *\nAllow: /\n"
    if URL:
        robots += f"Sitemap: {URL}/sitemap.xml\n"
        (PUB / "feed.xml").write_text(rss(eds))
        (PUB / "sitemap.xml").write_text(sitemap(eds))
    (PUB / "robots.txt").write_text(robots)
    print(f"OK: {len(eds)} edições → public/ (site_url={'«' + URL + '»' if URL else 'não definido: sem RSS/sitemap'})")


if __name__ == "__main__":
    main()
