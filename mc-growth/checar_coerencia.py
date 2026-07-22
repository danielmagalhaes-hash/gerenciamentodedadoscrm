"""
checar_coerencia.py — o guarda das DEFINIÇÕES COMPARTILHADAS (CLAUDE.md §11).

Regra do projeto: todas as telas usam as MESMAS definições (data do pedido, cliente novo,
estreia, CMV, deduções, mídia, exclusões). Este script **prova** isso com números, para a
regra não depender de memória. Rodar depois de qualquer mexida em `cascata.py`/`coortes.py`:

    python3 checar_coerencia.py

Sai 0 se tudo bate; 1 (e explica) se alguma tela divergiu.
"""

from __future__ import annotations

import sys

import pandas as pd

import cascata
import coortes
import dados
import portas

TOLERANCIA = 0.01  # R$ 0,01 — diferença de arredondamento, nada mais
HOJE = pd.Timestamp.today()


def _linha(ok: bool, texto: str) -> str:
    return f"{'✅' if ok else '❌'} {texto}"


def main() -> int:
    base = dados.carregar_tudo()
    deals = dados.carregar_hubspot()
    # A base histórica de itens entra aqui também: o guarda tem de conferir a MESMA configuração
    # que o João vê na tela (CMV real na história inteira), não o caminho degradado.
    hist = dados.carregar_itens_historico()
    falhas: list[str] = []

    # O mês fechado mais recente — o terreno onde as telas TÊM de concordar.
    mes = pd.Period(HOJE, freq="M") - 1
    ini, fim = mes.start_time.normalize(), mes.end_time.normalize()
    print(f"Conferindo o mês fechado de {mes} ({ini.date()} a {fim.date()})")
    print(f"Base histórica de itens: {'SIM' if len(hist) else 'AUSENTE (degradado)'}\n")

    geral = cascata.calcular(base, ini, fim, deals=deals, hist=hist)
    aquis = cascata.calcular_aquisicao(base, ini, fim, deals=deals, hist=hist)
    enr = coortes.preparar_deals_cache(base, deals, hist=hist)
    tri = coortes.calcular_coortes(base, deals, hoje=HOJE, hist=hist)
    safra = str(mes)

    # 1) Aquisição × A2 (bloco de novos): mesma régua de "cliente novo" → mesmos números.
    if safra in tri.safras:
        det = coortes.detalhar_safra(base, None, safra, hoje=HOJE, ate_idade=0, enr=enr)
        d_vendas = abs(aquis.vendas_novos - det.vendas_novos)
        d_mc = abs(aquis.mc_novos - det.mc_novos)
        ok = d_vendas <= TOLERANCIA and d_mc <= TOLERANCIA and aquis.pedidos_novos == det.n_novos
        print(_linha(ok, f"Aquisição × A2 (novos): vendas dif R$ {d_vendas:.2f} · MC dif "
                         f"R$ {d_mc:.2f} · pedidos {aquis.pedidos_novos} × {det.n_novos}"))
        if not ok:
            falhas.append("A aba Aquisição e a A2 discordam sobre os clientes novos do mês.")

        # 2) A cascata da A2 re-expõe a MESMA MC do triângulo (não recalcula).
        det_cheio = coortes.detalhar_safra(base, None, safra, hoje=HOJE, enr=enr)
        if det_cheio.ate_idade in tri.mc_acumulada.columns:
            celula = tri.mc_acumulada.loc[safra, det_cheio.ate_idade]
            d = abs(det_cheio.mc_total_cliente - celula)
            ok = d <= 1e-4
            print(_linha(ok, f"A2 × triângulo (MC/cliente): dif R$ {d:.6f}"))
            if not ok:
                falhas.append("A cascata da A2 não bate com a célula do triângulo.")

    # 3) Os subtotais da cascata são soma das filhas (Deduções, Cost of Delivery).
    for nome, res, lucro in (("Geral", geral, geral.lucro_bruto),
                             ("Aquisição", aquis, aquis.lucro_bruto_novos)):
        grupos = [l for l in res.linhas if l.tipo == "grupo"]
        ded = sum(l.valor for l in res.linhas if l.tipo == "deducao")
        cod = sum(l.valor for l in res.linhas if l.tipo in ("cmv", "custo"))
        vendas = res.linhas[0].valor
        ok = (abs(grupos[0].valor - ded) <= TOLERANCIA
              and abs(grupos[1].valor - cod) <= TOLERANCIA
              and abs((vendas + grupos[0].valor + grupos[1].valor) - lucro) <= TOLERANCIA)
        print(_linha(ok, f"Cascata {nome}: subtotais = soma das filhas e Vendas − Deduções − "
                         "Cost of Delivery = Lucro Bruto"))
        if not ok:
            falhas.append(f"A cascata da tela {nome} não fecha.")

    # 4) MC absoluta ÷ clientes = MC por cliente (as duas tabelas da aba Cohorts).
    if tri.safras:
        d = (tri.mc_absoluta.div(pd.Series(tri.n_clientes), axis=0) - tri.mc_acumulada).abs().max().max()
        ok = pd.isna(d) or d <= 1e-6
        print(_linha(ok, f"Triângulo absoluto ÷ clientes = triângulo por cliente: dif {d:.8f}"))
        if not ok:
            falhas.append("Os dois triângulos da aba Cohorts discordam.")

    # 5) Lucro Bruto = MC + CAC (a mídia sai UMA vez, no m+0). É o que garante que o ratio
    #    contra o CAC (tabela "Lucro Bruto ÷ CAC") não conte a mídia duas vezes, e que a linha
    #    do empate 1,00× seja o MESMO payback do triângulo de MC.
    if tri.safras:
        pior = 0.0
        for safra in tri.safras:
            cac_s = tri.cac[safra]
            if cac_s is None:
                continue
            d = (tri.lucro_bruto.loc[safra] - (tri.mc_acumulada.loc[safra] + cac_s)).abs().max()
            if pd.notna(d):
                pior = max(pior, float(d))
        ok = pior <= 1e-6
        print(_linha(ok, f"Lucro Bruto = MC + CAC (mídia contada 1×): dif {pior:.8f}"))
        if not ok:
            falhas.append("O Lucro Bruto da coorte não bate com MC + CAC — o ratio ÷ CAC "
                          "estaria contando a mídia duas vezes.")

    # 6) Portas de entrada: com filtro "todos", a tabela por safra É o Lucro Bruto acumulado da
    #    Cohorts (mesma célula), e as portas PARTICIONAM os clientes (nenhum some). É o que garante
    #    que a aba 4 não inventa dinheiro nem perde gente — só fatia a coorte por produto de estreia.
    if tri.safras:
        try:
            mapa = dados.carregar_mapa_portas()
            res_p = portas.calcular_portas(base, deals, mapa, hoje=HOJE, hist=hist)
            tab = portas.tabela_por_safra(res_p, portas.PORTA_TODOS).set_index("safra")
            # As duas métricas da aba 4 têm de reproduzir a Cohorts ao centavo: Lucro Bruto ↔
            # `coortes.lucro_bruto` e Receita ↔ `coortes.ltv` (mesma turma, mesma idade).
            tab_rec = portas.tabela_por_safra(
                res_p, portas.PORTA_TODOS, metrica="valor").set_index("safra")
            pior, pior_rec = 0.0, 0.0
            for s in res_p.safras:
                for _rot, m in portas.COLUNAS_IDADE:
                    if m in tri.lucro_bruto.columns:
                        a, b = tab.loc[s, m], tri.lucro_bruto.loc[s, m]
                        if pd.notna(a) or pd.notna(b):
                            pior = max(pior, abs((a if pd.notna(a) else 0) - (b if pd.notna(b) else 0)))
                    if m in tri.ltv.columns:
                        a, b = tab_rec.loc[s, m], tri.ltv.loc[s, m]
                        if pd.notna(a) or pd.notna(b):
                            pior_rec = max(pior_rec, abs((a if pd.notna(a) else 0) - (b if pd.notna(b) else 0)))
                a, b = tab.loc[s, "primeira"], tri.lucro_bruto_primeira_compra[s]
                if pd.notna(a) and pd.notna(b):
                    pior = max(pior, abs(a - b))
                a, b = tab_rec.loc[s, "primeira"], tri.ticket_primeira_compra[s]
                if pd.notna(a) and pd.notna(b):
                    pior_rec = max(pior_rec, abs(a - b))
            # Partição: a soma dos clientes por porta = N_S da coorte inteira, em toda safra.
            por_safra = res_p.enr.groupby("safra")["e_mail"].nunique()
            quebrou = sum(int(por_safra.get(s, 0)) != res_p.n_por_safra[s] for s in res_p.safras)
            ok = pior <= 1e-6 and pior_rec <= 1e-6 and quebrou == 0
            print(_linha(ok, f"Portas 'todos' × Cohorts (Lucro Bruto {pior:.8f} · Receita "
                             f"{pior_rec:.8f}/cliente) · partição quebrada em "
                             f"{quebrou}/{len(res_p.safras)} safras"))
            if not ok:
                falhas.append("A aba Portas de entrada ('todos') não bate com a Cohorts (Lucro Bruto "
                              "ou Receita), ou as portas não particionam os clientes.")
        except dados.ErroDeDados as e:
            print(_linha(False, f"Portas de entrada: não deu para conferir ({e})"))
            falhas.append("O mapa de portas não pôde ser lido para o check de coerência.")

    print()
    if falhas:
        print("DIVERGÊNCIA — as telas não estão falando a mesma língua:")
        for f in falhas:
            print(f"  · {f}")
        print("\nVeja CLAUDE.md §11 (definições compartilhadas) antes de mexer.")
        return 1
    print("Todas as telas concordam. ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
