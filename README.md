# VotaMG — protótipo

## Colocando no ar a partir do celular (repositório público + GitHub Pages)

Como o repositório é público, dá pra usar o GitHub Pages nativo — sem
precisar de Cloudflare nem de nenhuma credencial extra.

**1. Subir os arquivos** — pelo navegador do celular (não pelo app, que não
tem upload de pasta): abra o repositório → "Add file" → "Upload files" →
selecione todos os arquivos desta pasta (mantendo a estrutura `site/`,
`pipeline/`, `.github/workflows/`) → Commit. Se o seletor não deixar subir
pastas de uma vez, suba arquivo por arquivo com "Create new file" digitando
o caminho completo (ex: `site/data/candidatos.exemplo.json`) — o GitHub cria
as pastas sozinho.

**2. Ativar o Pages** — Settings → Pages → em "Build and deployment", em
"Source" escolha **GitHub Actions** (não "Deploy from a branch"). Não precisa
mexer em mais nada; o workflow `deploy.yml` já está configurado pra isso.

**3. Pronto.** Assim que os arquivos subirem, o workflow `Publicar site`
roda sozinho e o site fica em `https://<seu-usuario>.github.io/votamg/`.
O workflow `Atualizar dados do TSE` roda todo dia às 9h (Brasília), busca
os dados novos e commita `candidatos.json` — o que dispara uma nova
publicação automaticamente. Pra forçar uma rodada manual: aba Actions →
escolha o workflow → "Run workflow".

*(Enquanto isso não roda pela primeira vez, o site publicado vai mostrar os
dados de exemplo em `candidatos.exemplo.json` — assim que
`fetch_and_build.py` confirmar as URLs corretas de 2026 e rodar com sucesso,
`candidatos.json` passa a existir e é isso que `app.js` deveria carregar;
lembre de trocar o `DATA_URL` como descrito abaixo.)*

## O que já está pronto
- `site/` — o site estático (mobile-first), funcionando agora com dados
  **fictícios de exemplo** em `site/data/candidatos.exemplo.json`.
- `pipeline/fetch_and_build.py` — script que baixa os dados reais do TSE,
  filtra MG (deputado federal + estadual), cruza com bens e prestação de
  contas, e calcula os insights (reeleição, candidaturas anteriores).

## Como ver o site agora (com dados de exemplo)
Dentro da pasta `site/`, rode um servidor local simples (o navegador
bloqueia `fetch` de arquivo local sem isso):

```
cd site
python3 -m http.server 8000
```

Depois abra `http://localhost:8000` no navegador (ou no celular na mesma
rede, usando o IP do computador).

## Como plugar os dados reais
1. Confirme as 3 pendências no topo de `pipeline/fetch_and_build.py`
   (nome exato dos datasets de 2026 no dadosabertos.tse.jus.br — o
   padrão histórico deve se manter, mas vale conferir antes de rodar
   em produção).
2. Rode, com internet livre (seu computador, não este sandbox):
   ```
   pip install requests pandas
   cd pipeline
   python fetch_and_build.py --ano 2026 --uf MG
   ```
   Isso gera `site/data/candidatos.json`.
3. Em `site/app.js`, troque a constante `DATA_URL` de
   `"data/candidatos.exemplo.json"` para `"data/candidatos.json"`.

## Publicar (grátis, sem servidor)
Como é 100% estático, dá pra hospedar em:
- **GitHub Pages** — sobe a pasta `site/` num repositório e ativa Pages.
- **Cloudflare Pages** — arrasta a pasta `site/` no painel, sem configuração.

Pra manter os dados atualizados perto da eleição (a prestação de contas
final só fecha em novembro), o ideal é agendar `fetch_and_build.py` para
rodar 1x por dia via GitHub Actions (cron), commitando o `candidatos.json`
atualizado automaticamente.

## Pendências conhecidas (fora do MVP atual)
- **Processos judiciais / certidões criminais**: não vêm no bulk de
  dados abertos — é preciso confirmar se dá pra extrair de algum campo
  de situação do `consulta_cand`, ou se vai exigir consulta individual
  ao DivulgaCandContas (mais lento, mas viável para MG).
- **Histórico de mandato** (presença, projetos, votos) ficou fora do
  MVP por decisão sua — quando quiser incluir, a Câmara dos Deputados
  (`dadosabertos.camara.leg.br`) e a ALMG (`dadosabertos.almg.gov.br`)
  têm APIs próprias pra isso.
- **Propostas de governo**: não existe fonte oficial estruturada para
  candidatos a deputado (só para cargos do Executivo) — ficou de fora
  por decisão sua.
