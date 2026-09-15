# VotaMG

O eleitor mineiro tem, nas eleições de 2026, uma lista enorme e pouco
legível de candidatos a Deputado Federal e Deputado Estadual por MG.
O VotaMG existe pra transformar isso numa consulta rápida e neutra:
busca o candidato, vê a ficha oficial dele, decide com informação — sem
recomendação, sem score, sem opinião embutida.

## O que o app resolve

- **Ficha objetiva por candidato**, direto do TSE: bens declarados,
  doações recebidas, processos ligados à candidatura (com o aviso claro
  de que processo não é condenação).
- **Insights de trajetória**, calculados a partir do próprio dado
  oficial: está concorrendo à reeleição, quantas candidaturas anteriores
  teve (desde 2010), ocupação declarada. Sem cruzar fonte não-oficial —
  tudo rastreável até o dado bruto do TSE.
- **Fácil de consultar no celular**: busca por nome/número/partido/cidade,
  cards curtos, detalhe completo só ao tocar. Pensado pra quem vai
  abrir isso na fila do trabalho, não fazer uma pesquisa acadêmica.
- **Sempre atualizado sem esforço manual**: um job diário busca os dados
  mais recentes do TSE (a prestação de contas final só fecha perto da
  eleição) e republica o site sozinho.

## Fora do escopo (por decisão consciente, não esquecimento)

- **Propostas de governo**: não existe fonte oficial estruturada pra
  candidato a deputado (só pro Executivo) — incluir isso puxaria dado
  não-oficial e abriria espaço pra viés.
- **Histórico de mandato** (presença, projetos, votos de quem já foi
  deputado): fica pra uma v2, usando as APIs da Câmara dos Deputados e
  da ALMG.
- **Um "score" ou ranking de candidatos**: propositalmente não existe.
  A ideia é mostrar o fato e deixar a conclusão com o eleitor.

## Estrutura do projeto

- `site/` — o site estático (mobile-first). Roda com dados de exemplo
  fictícios em `site/data/candidatos.exemplo.json` até o pipeline gerar
  o `candidatos.json` real.
- `pipeline/fetch_and_build.py` — baixa os dados oficiais do TSE, filtra
  MG (federal + estadual), cruza com bens e prestação de contas, calcula
  os insights.
- `.github/workflows/` — `update-data.yml` roda o pipeline todo dia e
  commita o resultado; `deploy.yml` publica `site/` no GitHub Pages a
  cada atualização.

## Rodar localmente

Ver o site com os dados de exemplo:
```
cd site
python3 -m http.server 8000
```
Abra `http://localhost:8000`.

Rodar o pipeline com dados reais (precisa de internet livre — não
funciona em sandboxes com rede restrita):
```
python3 -m venv venv && source venv/bin/activate
pip install requests pandas
cd pipeline
python fetch_and_build.py --ano 2026 --uf MG
```
Isso gera `site/data/candidatos.json`. Depois, em `site/app.js`, troque
`DATA_URL` de `"data/candidatos.exemplo.json"` para `"data/candidatos.json"`.

## Pendências técnicas conhecidas

Estão comentadas no topo de `pipeline/fetch_and_build.py`:
1. Confirmar se o padrão de URL do bulk 2026 se manteve igual ao de anos
   anteriores.
2. Confirmar o nome exato do dataset de prestação de contas 2026
   (`RECEITAS_URL`).
3. Confirmar se processos judiciais/certidões vêm no bulk ou exigem
   consulta individual ao DivulgaCandContas.
