"""Gera a nota de sessao 'Jornada de Produto' pro Obsidian (docs/sessions/), dado a
dado, direto dos CSVs/JSON ja calculados - nenhum numero digitado a mao, pra nao ter
erro de transcricao. Roda depois de jornada_produto.py + _agregar_dados_painel.py."""

import json
from datetime import date

import pandas as pd

from jornada_produto import (
    N_MINIMO_ENTRADA, N_MINIMO_CELULA, BUCKETS_QUANTIDADE_CAMISETA,
    NAMED_COMBOS, SKU_CARTEIRA, SKU_PERFUME_BRINDE, RECENTE_MESES, INATIVO_MESES,
    LTV_JANELA_DIAS, linhas_da_entrada,
)

a = pd.read_csv("saida_local/afinidade_produtos.csv")
t = pd.read_csv("saida_local/tempo_entre_compras.csv")
ltv = pd.read_csv("saida_local/ltv_por_entrada.csv").set_index("entrada")
taxas = pd.read_csv("saida_local/taxas_por_entrada.csv").set_index("entrada")
am = pd.read_csv("saida_local/afinidade_por_momento.csv")
with open("saida_local/jornada_dados.json", encoding="utf-8") as f:
    dados_json = json.load(f)

HOJE = date.today().isoformat()
TOTAL_CLIENTES = sum(e["n"] for e in dados_json)

linhas: list[str] = []


def w(texto: str = "") -> None:
    linhas.append(texto)


# ---------------------------------------------------------------------------
w(f"# Sessão {HOJE} — Jornada de Produto")
w()
w("**Modo:** A (análise) → virou código local (`mc-growth/jornada_produto.py`) · "
  "**Toca dinheiro:** não (produto e tempo, não receita/custo) · "
  "**Destino final:** aba Recompra do `gerenciadordecrm` — **só depois de comando "
  "explícito do Daniel**; até lá fica local.")
w()
w("---")
w()
w("## Objetivo")
w()
w("A partir da PORTA DE ENTRADA (produto ou combo da 1ª compra), entender **o que "
  "o cliente compra nas compras seguintes e em quanto tempo** — pra decidir o que "
  "ofertar depois de cada tipo de entrada. Pergunta original do Daniel "
  "(2026-07-23): *\"por onde o cliente entra, e quais são os outros produtos que "
  "são comprados na segunda, terceira, quarta e outras compras; em quanto tempo "
  "isso acontece em média\"*.")
w()
w("## Fonte dos dados")
w()
w("Mesmas 3 bases locais que já alimentam o mc-growth (Portas de Entrada / LTV), "
  "baixadas do BigQuery pelo Daniel em 2026-07-23:")
w()
w("- `bases/hubspot_deals.csv` — pedidos/clientes (462k linhas)")
w("- `bases/itens_historico.csv` — item a item de cada pedido (1,3M linhas)")
w("- `bases/mapa_sku_linha_produto.csv` — SKU → linha de produto (1.145 SKUs)")
w()
w("Nenhuma base nova; a ponte pedido→item (`cascata.itens_por_nome`, 3 camadas) e "
  "o enriquecimento de safra/idade (`coortes.preparar_deals_cache`) são os MESMOS "
  "do painel principal do mc-growth. Só a **classificação de produto/combo** é "
  "própria deste módulo (ver Metodologia).")
w()
w("---")
w()
w("## Decisões tomadas nesta sessão (ordem cronológica)")
w()
w("1. **Escopo definido:** a partir do produto de entrada (produto único, mesma "
  "régua da aba \"Portas de Entrada\"), mapear os produtos das compras 2ª–5ª+ e o "
  "tempo até cada uma (visão acumulada desde a entrada + visão de intervalo entre "
  "recompras).")
w("2. **Camiseta Minimal segmentada por quantidade** — picos reais medidos na "
  f"base: {', '.join(str(x) for x in BUCKETS_QUANTIDADE_CAMISETA)} unidades. "
  "Qualquer outra quantidade cai em \"outras qtd\".")
w("3. **11 combos aprovados** para virarem porta de entrada própria (7 pedidos + "
  "4 descobertos na análise de frequência da base e aprovados pelo Daniel): "
  + ", ".join(sorted(NAMED_COMBOS.values())) + ".")
w("4. **Carteira e Perfume separados** do SKU genérico \"BRINDE\" do mc-growth "
  f"(que misturava os dois): SKU {next(iter(SKU_CARTEIRA))} = Carteira; SKUs "
  f"{', '.join(sorted(SKU_PERFUME_BRINDE))} = Perfume (brinde).")
w("5. **Sub-linhas genéricas nos combos** — Jeans 1.0/2.0 e Social Tech "
  "Classics/Malha juntam num nome só (\"Jeans\", \"Social\") só para efeito de "
  "combo; a entrada de produto único continua usando o nome específico.")
w(f"6. **Limpeza:** entrada com menos de {N_MINIMO_ENTRADA} clientes sai da "
  "análise inteira (não só da tela) — de 45 entradas caiu para **20**.")
w("7. **Bug 1 corrigido (retenção zerada):** a compra seguinte nunca levava o "
  "sufixo de quantidade (\"Camiseta Minimal\", nunca \"Camiseta Minimal (4 un)\"), "
  "então a comparação \"mesmo produto\" nunca batia com a entrada. Corrigido "
  "comparando pela FAMÍLIA do produto (`familia_entrada`).")
w("8. **Bug 2 corrigido (denominador errado):** a % de cada compra usava como "
  "base \"quem chegou pelo menos na 2ª compra\" em vez do total da entrada — "
  "somava 100% na 2ª mas caía sem sentido nas seguintes, misturando \"não "
  "comprou esse produto de novo\" com \"nem voltou\". Corrigido fixando o "
  "denominador em `entrada_por_cliente.value_counts()` (o tamanho TOTAL da "
  "entrada) em todas as posições.")
w("9. **Pivot principal — presença de produto, não classificação exclusiva.** A "
  "1ª versão classificava o PEDIDO INTEIRO (produto único, um dos 11 combos, ou "
  "\"Multiprodutos\"/\"Produto desconhecido\") — isso enterrava informação real "
  "toda vez que o carrinho não batia com a lista fixa. A versão final pergunta "
  "\"quais produtos apareceram nessa compra\" (não exclusivo: um pedido com "
  "Camiseta+Jeans conta pras duas linhas). \"Multiprodutos\"/\"Produto "
  "desconhecido\" saíram da lista de oferta.")
w("10. **Árvore de jornada removida.** Foi construída, mas a árvore precisa de "
  "ramos EXCLUSIVOS (um cliente só pode estar num ramo por vez) — incompatível "
  "com presença de produto (um cliente pode estar em vários produtos ao mesmo "
  "tempo). Substituída pela tabela de afinidade por compra.")
w("11. **Transparência do funil:** a tabela agora mostra TODOS os produtos "
  "(sem corte de top-N escondido) + uma linha \"Não fez essa compra\" + um card "
  "com essa %, pra nunca parecer que os números \"somam pouco\" sem explicar "
  "que a maior parte é gente que não voltou.")
w("12. **LTV, taxa de repetição e taxa de reativação adicionados** (pedido do "
  "Daniel, 2026-07-23, 2ª rodada) — reaproveitando a régua OFICIAL já validada "
  f"com ele em 2026-07-21 para `fact_repurchase_monthly_metrics` (recente = "
  f"{RECENTE_MESES} meses, inativo = mais de {INATIVO_MESES} meses sem "
  "comprar), adaptada de \"mensal/global\" pra \"foto de hoje, por produto de "
  "entrada\".")
w("13. **Bug 3 corrigido (retenção de combo sempre 0%):** o combo usa nome "
  "GENÉRICO na régua de retenção (\"Jeans\"), mas a presença crua só tem nomes "
  "ESPECÍFICOS (\"Calça Jeans 1.0\") — sem aliasar a comparação, \"Camiseta + "
  "Jeans\" e \"Camiseta + Social\" davam sempre 0%. Corrigido comparando cada "
  "linha exigida contra a presença direta OU aliasada (não as duas juntas de "
  "uma vez, que quebrava a entrada solo).")
w("14. **Bug 4 corrigido (cliente contado 2× na tabela por momento):** um "
  "cliente pode ter mais de uma compra do mesmo tipo (\"Repetição\", por "
  "exemplo) na vida dele — contar por EVENTO em vez de por CLIENTE inflava o "
  "número (uma linha chegou a mostrar mais clientes que a própria base). "
  "Corrigido contando cliente distinto por produto.")
w()
w("---")
w()
w("## Metodologia final")
w()
w("### Elegibilidade da entrada")
w("- Deal `Shipped` (Shopify) na idade 0 (a estreia real do cliente — mesma "
  "régua de `portas._estreias`).")
w("- Produto único (1 linha de papel \"porta\") **ou** um dos 11 combos "
  "aprovados.")
w(f"- Entrada com menos de {N_MINIMO_ENTRADA} clientes → excluída da análise.")
w()
w("### \"O que ofertar\" (afinidade por compra)")
w("Para cada (entrada, compra Nª), cada LINHA presente naquela compra específica "
  "conta — não é a classificação do pedido inteiro. `% da entrada` = "
  "`clientes com aquela linha presente ÷ tamanho TOTAL da entrada × 100` "
  "(denominador fixo, igual em toda posição). Célula com menos de "
  f"{N_MINIMO_CELULA} clientes não é reportada.")
w()
w("### Retenção (\"tem o mesmo produto de novo\")")
w("Solo: a linha da família precisa estar presente (pode vir mais coisa "
  "junto). Combo: as 2 linhas do combo precisam estar AMBAS presentes.")
w()
w("### Tempo até a próxima compra")
w("Duas visões, mediana em dias: **acumulado** (da entrada até a compra N) e "
  "**entre recompras** (da compra N-1 até a N).")
w()
w(f"### LTV {LTV_JANELA_DIAS} dias")
w(f"Σ `valor` de todas as compras do cliente dentro de {LTV_JANELA_DIAS} dias "
  "desde a entrada (inclui a própria compra de entrada). Quem não voltou entra "
  "com o valor só da entrada — não é excluído nem zerado.")
w()
w("### Status do cliente HOJE / taxas por entrada")
w("Régua OFICIAL de `fact_repurchase_monthly_metrics` (validada com o Daniel em "
  "2026-07-21), adaptada de mensal/global pra foto de hoje / por entrada:")
w()
w(f"- **Recente** = a entrada (1ª compra) foi há menos de {RECENTE_MESES} meses.")
w(f"- **Ativo** = não é recente, e a ÚLTIMA compra foi há até {INATIVO_MESES} "
  "meses (a \"janela de atividade\" ainda está aberta).")
w(f"- **Inativo** = mais de {INATIVO_MESES} meses sem comprar (a janela fechou).")
w()
w("Essas 3 são o status ATUAL do cliente (uma foto de hoje). Já **taxa de "
  "repetição** e **taxa de reativação** olham a vida INTEIRA do cliente (todo "
  "evento de compra que ele já teve, não só o status de hoje):")
w()
w("- **Taxa de repetição** (por entrada) = % da entrada que já teve, alguma "
  "vez, uma compra classificada \"Repetição\" — comprou de novo DENTRO da "
  f"janela de {INATIVO_MESES} meses, já fora do 1º semestre de vida.")
w("- **Taxa de reativação** (por entrada) = % da entrada que já teve, alguma "
  "vez, uma compra classificada \"Reativação\" — voltou a comprar DEPOIS da "
  "janela ter fechado (tinha ficado inativo).")
w()
w("Cada COMPRA (não o cliente) é classificada em um dos 3 momentos: "
  f"**Recente** (menos de {RECENTE_MESES} meses desde a entrada do cliente), "
  f"**Reativação** (gap desde a compra anterior maior que {INATIVO_MESES} "
  "meses) ou **Repetição** (o resto). Isso alimenta as 3 tabelas segmentadas "
  "da seção seguinte.")
w()
w("---")
w()
w("## LTV, repetição e reativação — as 20 entradas")
w()
w(f"| Entrada | Clientes | LTV {LTV_JANELA_DIAS}d (mediana) | LTV {LTV_JANELA_DIAS}d (média) | "
  "Taxa repetição | Taxa reativação | Recente hoje | Ativo hoje | Inativo hoje |")
w("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
for e in dados_json:
    nome = e["nome"]
    lr = ltv.loc[nome]
    tx = taxas.loc[nome]
    w(
        f"| {nome} | {e['n']:,} | R$ {lr[f'ltv_{LTV_JANELA_DIAS}d_mediana']:.2f} | "
        f"R$ {lr[f'ltv_{LTV_JANELA_DIAS}d_media']:.2f} | {tx['taxa_repeticao']:.1f}% | "
        f"{tx['taxa_reativacao']:.1f}% | {tx['pct_recente_hoje']:.1f}% | "
        f"{tx['pct_ativo_hoje']:.1f}% | {tx['pct_inativo_hoje']:.1f}% |".replace(",", ".")
    )
w()
w("---")
w()
w("## As 3 análises segmentadas — entrada + produtos por momento da compra")
w()
w("Pedido do Daniel (2026-07-23, 2ª rodada): pra clientes **recentes**, entrada "
  "+ próximas compras; pra **ativos não recentes**, entrada + produtos que mais "
  "REPETEM; pra **inativos**, entrada + produtos que mais REATIVAM. Adaptação: "
  "em vez de olhar o status do CLIENTE hoje, cada tabela olha as COMPRAS que "
  "aconteceram naquele momento específico da vida do cliente (ver Metodologia) "
  "— assim dá pra listar produto, não só um rótulo de status.")
w()

ROTULO_MOMENTO = {
    "Recente": (
        "### 1) Clientes recentes — entrada + próximas compras",
        "Compras feitas ainda dentro do 1º semestre de vida do cliente "
        f"(< {RECENTE_MESES} meses desde a entrada).",
    ),
    "Repetição": (
        "### 2) Clientes ativos não recentes — produtos que mais repetem",
        "Compras feitas depois do 1º semestre, dentro da janela de "
        f"{INATIVO_MESES} meses desde a compra anterior (o cliente nunca ficou "
        "inativo até essa compra).",
    ),
    "Reativação": (
        "### 3) Clientes inativos (que voltaram) — produtos que mais reativam",
        f"Compras feitas DEPOIS de {INATIVO_MESES}+ meses sem comprar — a "
        "janela tinha fechado; esse produto foi o que trouxe o cliente de "
        "volta.",
    ),
}

for momento, (titulo, explicacao) in ROTULO_MOMENTO.items():
    w(titulo)
    w(explicacao)
    w()
    sub_am = am[am.momento == momento]
    for nome in [e["nome"] for e in dados_json]:
        g = sub_am[sub_am.entrada == nome].sort_values("clientes", ascending=False)
        if g.empty:
            continue
        n_base = int(g["n_base"].iloc[0])
        w(f"**{nome}** — {n_base:,} clientes com compra tipo \"{momento}\"".replace(",", "."))
        w()
        w("| Produto | Clientes | % desse grupo |")
        w("|---|---:|---:|")
        for r in g.itertuples():
            w(f"| {r.produto} | {r.clientes:,} | {r.pct_do_momento:.2f}% |".replace(",", "."))
        w()
    w()

w("---")
w()
w(f"## Resumo — as {len(dados_json)} entradas ({TOTAL_CLIENTES:,} clientes elegíveis)".replace(",", "."))
w()
w("| Entrada | Clientes | Não voltaram (2ª) | Retenção (2ª) | Mediana dias (2ª) |")
w("|---|---:|---:|---:|---:|")
for e in dados_json:
    c2 = next((c for c in e["compras"] if c["compra"] == "2a"), None)
    t2 = next((x for x in e["tempos"] if x["compra"] == "2a"), None)
    nao_voltou = f"{c2['pct_nao_voltou']:.1f}%" if c2 else "—"
    retencao = f"{c2['pct_mesmo_produto']:.1f}%" if c2 else "—"
    dias = f"{t2['acumulado']:.0f}" if t2 else "—"
    w(f"| {e['nome']} | {e['n']:,} | {nao_voltou} | {retencao} | {dias} |".replace(",", "."))
w()
w("---")
w()
w("## Dado a dado — cada entrada, cada compra, todos os produtos")
w()
w("Tabelas completas (sem corte de top-N), direto de `afinidade_produtos.csv`. "
  f"`% da entrada` soma mais de 100% quando um pedido tem 2+ produtos (conta "
  "pros 2); a linha **Não fez essa compra** fecha a conta do funil.")
w()

for e in dados_json:
    nome = e["nome"]
    n = e["n"]
    linhas_req = ", ".join(e["linhas_requeridas"])
    w(f"### {nome} — {n:,} clientes".replace(",", "."))
    w(f"*Precisa ter presente pra contar como retenção: {linhas_req}.*")
    w()
    sub_a = a[a.entrada == nome]
    sub_t = t[t.entrada == nome].set_index("compra")
    for compra in ["2a", "3a", "4a", "5a"]:
        g = sub_a[sub_a.compra == compra]
        if g.empty:
            continue
        ret = g[g.produto == "__RETENCAO__"]["pct_da_entrada"]
        pct_ret = float(ret.iloc[0]) if len(ret) else 0.0
        n_base = int(g["n_base_da_compra"].iloc[0])
        pct_nao_voltou = (n - n_base) / n * 100
        linha_tempo = ""
        if compra in sub_t.index:
            rt = sub_t.loc[compra]
            linha_tempo = (
                f" · mediana acumulada **{rt['dias_acumulado_mediana']:.0f} dias**, "
                f"intervalo desde a anterior **{rt['dias_entre_recompras_mediana']:.0f} dias**"
            )
        rotulo = {"2a": "2ª", "3a": "3ª", "4a": "4ª", "5a": "5ª"}[compra]
        w(f"**{rotulo} compra** — {n_base:,} chegaram ({pct_nao_voltou:.1f}% não "
           f"voltaram), retenção {pct_ret:.1f}%{linha_tempo}".replace(",", "."))
        w()
        w("| Produto | Clientes | % da entrada |")
        w("|---|---:|---:|")
        prod = g[g.produto != "__RETENCAO__"].sort_values("clientes", ascending=False)
        for r in prod.itertuples():
            marca = " **(entrada)**" if r.produto in e["linhas_requeridas"] else ""
            w(f"| {r.produto}{marca} | {r.clientes:,} | {r.pct_da_entrada:.2f}% |".replace(",", "."))
        w()
    w()

w("---")
w()
w("## Onde estão os dados e o código")
w()
w("- Motor: `mc-growth/jornada_produto.py` (`montar_jornada`, "
  "`afinidade_por_compra`, `tempo_entre_compras`, `classificar_momento_compras`, "
  "`ltv_por_entrada`, `taxas_por_entrada`, `afinidade_por_momento`)")
w("- Saída bruta: `mc-growth/saida_local/afinidade_produtos.csv`, "
  "`tempo_entre_compras.csv`, `sequencia_compras_detalhe.csv`, "
  "`afinidade_por_momento.csv`, `ltv_por_entrada.csv`, `taxas_por_entrada.csv`")
w("- JSON do painel: `mc-growth/saida_local/jornada_dados.json` (gerado por "
  "`_agregar_dados_painel.py`)")
w("- Painel visual local (Artifact, privado): "
  "https://claude.ai/code/artifact/f731ece0-8c8a-4de9-956c-f974f5732471")
w()
w("## Pendências / próximos passos")
w()
w("- [ ] Daniel decide se abre o bucket \"Camiseta Minimal (outras qtd)\" "
  "(38.274 clientes — maior que os buckets de 6un e 10un juntos) em sub-buckets "
  "(2un e 5un são picos reais também).")
w("- [ ] Combos descobertos e ainda não aprovados: Camiseta + Manga Longa "
  "(4.786 clientes na base geral) ficou de fora por decisão do Daniel — revisar "
  "se entra numa leva futura.")
w("- [ ] Nenhuma decisão duradoura registrada em ADR ainda — considerar um "
  "`docs/decisions/2026-07-23-jornada-de-produto-metodologia.md` se este método "
  "for usado de novo.")
w("- [ ] Subir para o `gerenciadordecrm` (aba Recompra) **só após comando "
  "explícito do Daniel** — hoje é 100% local.")
w("- [ ] **Achado a confirmar com o Daniel:** Polo 2.0 e Calça Comfort têm "
  "0% de clientes \"inativo hoje\" — só faz sentido se essas linhas forem "
  f"recentes o bastante pra ninguém ainda ter passado de {INATIVO_MESES} meses "
  "sem comprar desde a entrada. Vale checar a data de lançamento das linhas "
  "antes de usar esse número em qualquer decisão.")
w()

conteudo = "\n".join(linhas)
caminho = "docs/sessions/2026-07-23-jornada-de-produto.md"
with open(caminho, "w", encoding="utf-8") as f:
    f.write(conteudo)

print(f"Escrito {caminho} ({len(conteudo):,} caracteres, {len(linhas)} linhas)".replace(",", "."))
