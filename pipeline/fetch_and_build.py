#!/usr/bin/env python3
"""
VotaMG — pipeline de dados
===========================

Baixa os arquivos oficiais e ABERTOS do TSE, filtra candidatos de Minas
Gerais a Deputado Federal e Deputado Estadual, cruza com bens declarados
e prestação de contas, calcula os insights (reeleição, candidaturas
anteriores, ocupação declarada) e gera um único candidatos.json que o
site estático consome.

REQUER INTERNET LIVRE (rode isso no seu computador ou num GitHub Action —
não funciona em sandboxes com rede restrita).

Uso:
    pip install requests pandas
    python fetch_and_build.py --ano 2026 --uf MG

O QUE ESTE SCRIPT AINDA PRECISA QUE VOCÊ CONFIRME NA PRIMEIRA RODADA
---------------------------------------------------------------------
1. O padrão de URL abaixo (CANDIDATOS_URL, BENS_URL) é o mesmo usado
   desde 2002 até 2022. Para 2026 ele PROVAVELMENTE se mantém, mas
   confirme acessando https://dadosabertos.tse.jus.br/dataset/candidatos-2026
   antes de rodar em produção — se o nome do arquivo mudou, ajuste as
   constantes abaixo.
2. Prestação de contas (doações/gastos) tem datasets próprios
   (ex: "prestacao-de-contas-eleitorais-2026"). O nome exato do
   recurso varia um pouco a cada eleição — procure por
   "receitas_candidatos_2026.zip" e "despesas_candidatos_2026.zip"
   no mesmo portal e ajuste RECEITAS_URL / DESPESAS_URL.
3. Processos judiciais e certidões criminais NÃO vêm nesses bulks —
   confirme se aparecem em algum campo de "situação" do consulta_cand
   ou se é necessário consultar o DivulgaCandContas por candidato
   (nesse caso, isso vira uma etapa separada e mais lenta).
"""

import argparse
import io
import json
import zipfile
from collections import defaultdict

import pandas as pd
import requests

BASE = "https://cdn.tse.jus.br/estatistica/sead/odsele"
CANDIDATOS_URL = "{base}/consulta_cand/consulta_cand_{ano}.zip"
BENS_URL = "{base}/bem_candidato/bem_candidato_{ano}.zip"
# Ajustar depois de confirmar o nome exato do dataset de contas para 2026:
RECEITAS_URL = "{base}/receitas_candidatos/receitas_candidatos_{ano}.zip"

CARGOS_ALVO = {"DEPUTADO FEDERAL", "DEPUTADO ESTADUAL"}

# Anos de pleitos gerais anteriores, usados só para contar candidaturas
# prévias (histórico). Ajustável.
ANOS_HISTORICO = [2010, 2014, 2018, 2022]


def baixar_csv_de_zip(url: str, encoding="latin-1", sep=";") -> pd.DataFrame:
    """Baixa um .zip do TSE e concatena todos os CSVs de dentro."""
    print(f"Baixando {url} ...")
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(resp.content))
    frames = []
    for name in z.namelist():
        if name.lower().endswith(".csv"):
            with z.open(name) as f:
                frames.append(pd.read_csv(f, sep=sep, encoding=encoding, dtype=str))
    if not frames:
        raise RuntimeError(f"Nenhum CSV encontrado dentro de {url}")
    return pd.concat(frames, ignore_index=True)


def contar_candidaturas_anteriores(titulo_eleitoral: str, uf: str) -> int:
    """
    Conta em quantos dos ANOS_HISTORICO essa pessoa (por título eleitoral)
    também aparece como candidata. É uma chamada de rede por ano de
    histórico na primeira vez rodando; dá pra cachear em disco depois.
    """
    total = 0
    for ano in ANOS_HISTORICO:
        try:
            df = baixar_csv_de_zip(CANDIDATOS_URL.format(base=BASE, ano=ano))
        except Exception as e:
            print(f"  aviso: não consegui checar {ano} ({e})")
            continue
        col_titulo = "NR_TITULO_ELEITORAL_CANDIDATO"
        if col_titulo in df.columns and titulo_eleitoral in df[col_titulo].values:
            total += 1
    return total


def montar_candidatos(ano: int, uf: str) -> list[dict]:
    cand = baixar_csv_de_zip(CANDIDATOS_URL.format(base=BASE, ano=ano))
    cand = cand[cand["SG_UF"] == uf]
    cand = cand[cand["DS_CARGO"].str.upper().isin(CARGOS_ALVO)]

    bens = baixar_csv_de_zip(BENS_URL.format(base=BASE, ano=ano))
    bens = bens[bens["SQ_CANDIDATO"].isin(cand["SQ_CANDIDATO"])]
    bens_por_candidato = defaultdict(list)
    for _, row in bens.iterrows():
        bens_por_candidato[row["SQ_CANDIDATO"]].append(
            {
                "tipo": row.get("DS_TIPO_BEM_CANDIDATO", ""),
                "descricao": row.get("DS_BEM_CANDIDATO", ""),
                "valor": row.get("VR_BEM_CANDIDATO", "0"),
            }
        )

    try:
        receitas = baixar_csv_de_zip(RECEITAS_URL.format(base=BASE, ano=ano))
        receitas = receitas[receitas["SQ_CANDIDATO"].isin(cand["SQ_CANDIDATO"])]
    except Exception as e:
        print(f"aviso: prestação de contas não carregada ainda ({e}) — "
              f"confirme a URL de RECEITAS_URL")
        receitas = pd.DataFrame(columns=["SQ_CANDIDATO"])

    saida = []
    for _, row in cand.iterrows():
        sq = row["SQ_CANDIDATO"]
        bens_cand = bens_por_candidato.get(sq, [])
        total_bens = sum(
            float(b["valor"].replace(",", ".")) for b in bens_cand if b["valor"]
        )
        doacoes_cand = receitas[receitas["SQ_CANDIDATO"] == sq]

        candidato = {
            "sq_candidato": sq,
            "numero_urna": row.get("NR_CANDIDATO"),
            "nome_urna": row.get("NM_URNA_CANDIDATO"),
            "nome_civil": row.get("NM_CANDIDATO"),
            "cargo": row.get("DS_CARGO"),
            "partido_sigla": row.get("SG_PARTIDO"),
            "partido_nome": row.get("NM_PARTIDO"),
            "municipio_ue": row.get("NM_UE"),
            "genero": row.get("DS_GENERO"),
            "cor_raca": row.get("DS_COR_RACA"),
            "grau_instrucao": row.get("DS_GRAU_INSTRUCAO"),
            "ocupacao_declarada": row.get("DS_OCUPACAO"),
            "situacao_candidatura": row.get("DS_SITUACAO_CANDIDATURA"),
            # campo oficial do TSE: S/N se é candidato buscando reeleição
            "concorrendo_reeleicao": row.get("ST_REELEICAO") == "S",
            "bens": bens_cand,
            "bens_total_declarado": total_bens,
            "doacoes_total": float(
                doacoes_cand["VR_RECEITA"].astype(float).sum()
            ) if "VR_RECEITA" in doacoes_cand.columns and not doacoes_cand.empty else None,
            "fonte": "TSE - Portal de Dados Abertos (DivulgaCandContas)",
            "processos": [],  # etapa separada — ver aviso no topo do arquivo
        }

        titulo = row.get("NR_TITULO_ELEITORAL_CANDIDATO")
        if titulo:
            candidato["candidaturas_anteriores"] = contar_candidaturas_anteriores(
                titulo, uf
            )

        saida.append(candidato)

    return saida


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ano", type=int, default=2026)
    parser.add_argument("--uf", type=str, default="MG")
    parser.add_argument("--saida", type=str, default="../site/data/candidatos.json")
    parser.add_argument(
        "--pular-historico",
        action="store_true",
        help="pula o cálculo de candidaturas anteriores (mais rápido pra testar)",
    )
    args = parser.parse_args()

    global ANOS_HISTORICO
    if args.pular_historico:
        ANOS_HISTORICO = []

    candidatos = montar_candidatos(args.ano, args.uf)

    with open(args.saida, "w", encoding="utf-8") as f:
        json.dump(
            {
                "ano_eleicao": args.ano,
                "uf": args.uf,
                "gerado_em": pd.Timestamp.now(tz="America/Sao_Paulo").isoformat(),
                "total_candidatos": len(candidatos),
                "candidatos": candidatos,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"OK: {len(candidatos)} candidatos gravados em {args.saida}")


if __name__ == "__main__":
    main()
