"""
checar_base.py — sanidade rápida da planilha (rode depois de reextrair uma aba).

Uso:  python3 checar_base.py

Diz, em segundos: quantas linhas e que período cada aba cobre, se as colunas
esperadas vieram, e qual a taxa de amarração Vendas × Itens (o que estava quebrado
quando a Itens veio truncada). Não altera nada — só lê.
"""

from __future__ import annotations

import pandas as pd

import dados


def _periodo(serie: pd.Series) -> str:
    validas = serie.dropna()
    if validas.empty:
        return "sem datas"
    return f"{validas.min():%d/%m/%Y} → {validas.max():%d/%m/%Y} ({validas.dt.date.nunique()} dias)"


def main() -> None:
    try:
        d = dados.carregar_tudo()
    except dados.ErroDeDados as erro:
        print("ERRO ao ler a planilha:", erro)
        return

    print("=== Tamanho e período de cada aba ===")
    print(f"Vendas: {len(d.vendas):>7} linhas | {_periodo(d.vendas['data'])}")
    print(f"Itens : {len(d.itens):>7} linhas | {_periodo(d.itens['data'])}")
    print(f"Custos: {len(d.custos):>7} SKUs")
    print(f"Midia : {len(d.midia):>7} linhas | {_periodo(d.midia['data'])}")

    # Sinal de truncagem: número redondo (25000, 50000...) é suspeito.
    if len(d.itens) in (10000, 25000, 50000, 100000):
        print(f"\n⚠️  Itens tem exatamente {len(d.itens)} linhas — número redondo, "
              "cara de LIMITE de extração. Reextraia sem teto de linhas.")

    print("\n=== Amarração Vendas × Itens (todo o histórico) ===")
    ped_vendas = set(d.vendas["order_id"])
    ped_itens = set(d.itens["order_id"])
    casam = ped_vendas & ped_itens
    taxa = 100 * len(casam) / max(len(ped_vendas), 1)
    print(f"Pedidos em Vendas .............. {len(ped_vendas):>7}")
    print(f"Com itens correspondentes ...... {len(casam):>7}  ({taxa:.1f}%)")
    print(f"SEM itens (custo ficaria 0) .... {len(ped_vendas - casam):>7}")
    if taxa < 95:
        print("\n⚠️  Menos de 95% dos pedidos têm itens — provável base de Itens incompleta.")
    else:
        print("\n✅ Amarração saudável (≥95%).")


if __name__ == "__main__":
    main()
