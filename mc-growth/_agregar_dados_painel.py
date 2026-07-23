"""Agrega saida_local/afinidade_produtos.csv + tempo_entre_compras.csv num JSON
compacto para o painel local (jornada_produto_painel.html). `afinidade_produtos.csv`
ja vem por PRESENCA de produto (nao classificacao exclusiva do pedido inteiro) -
decisao do Daniel, 2026-07-23, pra parar de esconder informacao em "Multiprodutos"/
"Produto desconhecido". A linha sentinela "__RETENCAO__" carrega o numero do grafico
de retencao (ver `jornada_produto.afinidade_por_compra`)."""

import json

import pandas as pd

from jornada_produto import linhas_da_entrada

a = pd.read_csv("saida_local/afinidade_produtos.csv")
t = pd.read_csv("saida_local/tempo_entre_compras.csv")
seq = pd.read_csv("saida_local/sequencia_compras_detalhe.csv")
ltv = pd.read_csv("saida_local/ltv_por_entrada.csv").set_index("entrada")
taxas = pd.read_csv("saida_local/taxas_por_entrada.csv").set_index("entrada")

n_entrada = seq[seq.posicao == 1].groupby("entrada")["e_mail"].nunique().sort_values(ascending=False)

entradas = []
for entrada, n in n_entrada.items():
    sub_a = a[a.entrada == entrada]
    sub_t = t[t.entrada == entrada].set_index("compra")

    compras_out = []
    for compra in ["2a", "3a", "4a", "5a"]:
        g = sub_a[sub_a.compra == compra]
        if g.empty:
            continue
        ret = g[g.produto == "__RETENCAO__"]
        pct_mesmo_produto = float(ret["pct_da_entrada"].iloc[0]) if len(ret) else 0.0
        n_base = int(g["n_base_da_compra"].iloc[0])
        pct_nao_voltou = round((n - n_base) / n * 100, 1)

        # SEM cap de top-N: mostra todo produto que passou do minimo de celula (ja
        # filtrado em afinidade_por_compra) — Polo/Comfort etc. ficam escondidos se
        # a gente corta em top 6; a lista completa raramente passa de ~28 linhas.
        prod = g[g.produto != "__RETENCAO__"].sort_values("clientes", ascending=False)
        produtos = [{"produto": r.produto, "pct": round(r.pct_da_entrada, 1)} for r in prod.itertuples()]
        compras_out.append({
            "compra": compra, "produtos": produtos, "pct_mesmo_produto": round(pct_mesmo_produto, 1),
            "pct_nao_voltou": pct_nao_voltou,
        })

    tempos_out = []
    for compra in ["2a", "3a", "4a", "5a"]:
        if compra in sub_t.index:
            r = sub_t.loc[compra]
            tempos_out.append({
                "compra": compra,
                "clientes": int(r["clientes"]),
                "acumulado": round(float(r["dias_acumulado_mediana"]), 0),
                "gap": round(float(r["dias_entre_recompras_mediana"]), 0),
            })

    lr = ltv.loc[entrada]
    tx = taxas.loc[entrada]
    entradas.append({
        "nome": entrada,
        "linhas_requeridas": sorted(linhas_da_entrada(entrada)),  # p/ destacar "faz parte da entrada" na tabela
        "n": int(n),
        "compras": compras_out,
        "tempos": tempos_out,
        "ltv_180d_mediana": round(float(lr["ltv_180d_mediana"]), 2),
        "taxa_repeticao": round(float(tx["taxa_repeticao"]), 1),
        "taxa_reativacao": round(float(tx["taxa_reativacao"]), 1),
        "pct_recente_hoje": round(float(tx["pct_recente_hoje"]), 1),
        "pct_ativo_hoje": round(float(tx["pct_ativo_hoje"]), 1),
        "pct_inativo_hoje": round(float(tx["pct_inativo_hoje"]), 1),
    })

with open("saida_local/jornada_dados.json", "w", encoding="utf-8") as f:
    json.dump(entradas, f, ensure_ascii=False)

print(f"{len(entradas)} entradas exportadas")
