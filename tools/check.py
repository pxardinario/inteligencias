#!/usr/bin/env python3
"""Teste de navegador do site gerado. Requer o servidor local (tools/serve.py) a correr.
Uso: python3 tools/check.py [http://127.0.0.1:8791] [pasta_capturas]
Falha (código 1) se houver erros de JavaScript, ligações internas partidas,
página mais larga do que o ecrã no telemóvel ou arquivo vazio."""
import json, sys
from pathlib import Path
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8791"
SHOTS = Path(sys.argv[2]) if len(sys.argv) > 2 else None
ROOT = Path(__file__).resolve().parent.parent
reg = json.loads((ROOT / "public/data/registo.json").read_text())
pages = ["/", "/arquivo/", "/sobre/"] + [ed["url"] for ed in reg["edicoes"]]
erros = []
with sync_playwright() as p:
    try:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
    except Exception:
        b = p.chromium.launch()
    vistos = set()
    for vp, nome in (({"width": 1200, "height": 900}, "desktop"), ({"width": 390, "height": 844}, "telemovel")):
        ctx = b.new_context(viewport=vp)
        for path in pages:
            pg = ctx.new_page()
            js = []
            pg.on("pageerror", lambda ex: js.append(str(ex)))
            r = pg.goto(BASE + path)
            pg.wait_for_timeout(700)
            if not r or r.status != 200:
                erros.append(f"{path}: HTTP {r.status if r else '?'}")
            if js:
                erros.append(f"{path} [{nome}]: erro JS {js}")
            sw = pg.evaluate("document.documentElement.scrollWidth")
            if sw > vp["width"] + 1:
                erros.append(f"{path} [{nome}]: largura {sw}px > {vp['width']}px")
            if path == "/arquivo/":
                n = pg.locator("#lista .item").count()
                if n == 0:
                    erros.append("/arquivo/: nenhum resultado")
            if SHOTS:
                SHOTS.mkdir(parents=True, exist_ok=True)
                pg.screenshot(path=str(SHOTS / f"{nome}{path.replace('/', '_') or '_'}.png"), full_page=True)
            if nome == "desktop":
                for href in pg.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))"):
                    u = urlparse(urljoin(BASE + path, href))
                    if u.netloc == urlparse(BASE).netloc and u.path not in vistos:
                        vistos.add(u.path)
                        rr = ctx.request.get(BASE + u.path)
                        if rr.status != 200:
                            erros.append(f"{path}: ligação interna partida {href} ({rr.status})")
            pg.close()
        ctx.close()
    b.close()
if erros:
    print("FALHOU:\n- " + "\n- ".join(erros)); sys.exit(1)
print(f"OK: {len(pages)} páginas × 2 ecrãs, ligações internas verificadas ({len(vistos)}).")
