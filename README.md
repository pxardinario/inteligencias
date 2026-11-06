# Inteligências

*A IA explicada a quem tem mais que fazer.*

Sebenta digital e gratuita de inteligência artificial prática, em português de Portugal. Sai à segunda e à quinta, por volta das 14h00 (hora de Lisboa): duas ou três novidades, uma técnica e um conceito do dia. **Feito por IA**: cada edição é escolhida, escrita e ilustrada por agentes de inteligência artificial (Claude, da Anthropic). Um projeto de Pedro Silva.

## Estrutura

```
site/editions/NNN.json   conteúdo de cada edição (fonte de verdade)
site/config.json         nome, slogan, periodicidade, endereço do site
site/sobre.html          texto da página «Como é feita»
site/assets/             CSS, JavaScript e tipos de letra
tools/build.py           gera public/ (edições, arquivo, RSS, sitemap, registo)
tools/serve.py           servidor local que imita a Cloudflare
tools/check.py           teste de navegador (desktop + telemóvel)
public/                  site gerado e publicado (não editar à mão)
AGENTS.md                instruções para os agentes que fazem cada edição
wrangler.jsonc           configuração da Cloudflare (Workers static assets)
```

Cada envio para `main` é publicado pela Cloudflare (Workers Builds, sem passo de build: `public/` já vem gerado).

## Executar localmente

```bash
python3 tools/build.py
python3 tools/serve.py 8791 &
python3 tools/check.py http://127.0.0.1:8791 /tmp/capturas
```

## Licenças

Código: MIT. Textos e diagramas: CC BY 4.0, com atribuição a «Inteligências». Tipos de letra Newsreader e IBM Plex (SIL OFL).
