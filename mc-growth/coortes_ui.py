"""
coortes_ui.py — peças comuns às DUAS telas de coorte (3. Cohorts e A2 - Auditoria MC Cohort).

Só formatação e leitura cacheada. A regra de negócio mora em `coortes.py`; o desenho da
cascata, em `ui.py`. Existe para que as duas telas leiam a MESMA base (um cache só) e
mostrem os números com a mesma cara.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import coortes
import dados

COR_POSITIVA = "#1f7a3d"  # verde — a turma se pagou (≥ 0)
COR_NEGATIVA = "#b91c1c"  # vermelho — ainda no vermelho

_VERDE_CLARO = (233, 245, 237)  # ratio baixo (mas ≥ 0)
_VERDE_ESCURO = (31, 122, 61)   # ratio alto — o mesmo COR_POSITIVA


def reais(valor: float) -> str:
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def ratio(valor: float) -> str:
    """Múltiplo do CAC: 3,26×. NaN (sem CAC / mês não fechado) vira '—'."""
    if pd.isna(valor):
        return "—"
    return numero(valor, 2) + "×"


def verde_gradiente(valor: float, minimo: float, maximo: float, limiar: float = 0.0) -> str:
    """
    CSS da célula de ratio: **tons de verde, mais escuro quanto maior o ratio** (pedido do João).

    `limiar` = a linha do empate. Abaixo dela o fundo fica branco e o número vermelho — um verde
    clarinho não avisaria que a turma ainda não se pagou. No ratio **Lucro Bruto ÷ CAC** o empate
    é **1,00×** (a turma devolveu exatamente o que custou trazê-la); no LTV de receita não há
    empate a marcar (limiar 0, nunca fica vermelho).
    """
    if pd.isna(valor):
        return ""
    if valor < limiar:
        return f"background-color:#ffffff; color:{COR_NEGATIVA}; font-weight:600; text-align:right"

    piso = max(minimo, limiar)
    intervalo = maximo - piso
    t = 0.0 if intervalo <= 0 else (valor - piso) / intervalo
    canais = [round(c + (e - c) * t) for c, e in zip(_VERDE_CLARO, _VERDE_ESCURO)]
    fundo = "#%02x%02x%02x" % tuple(canais)
    texto = "#ffffff" if t > 0.55 else "#14532d"  # branco só onde o verde já é escuro
    return f"background-color:{fundo}; color:{texto}; text-align:right"


def numero(valor: float, casas: int = 2) -> str:
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(fracao: float) -> str:
    return numero(fracao * 100, 1) + "%"


@st.cache_data(show_spinner="Lendo coortes…")
def carregar_e_calcular(hoje_iso: str):
    """Lê as abas + o CSV do HubSpot e monta as coortes. Cacheado por dia (hoje_iso)."""
    base = dados.carregar_tudo()
    deals = dados.carregar_hubspot()
    hist = dados.carregar_itens_historico()  # CMV real na história inteira; vazia = 30% estimado
    resultado = coortes.calcular_coortes(base, deals, hoje=pd.Timestamp(hoje_iso), hist=hist)
    mes_arquivo = str(deals["data_de_fechamento"].dropna().dt.to_period("M").max())
    return resultado, mes_arquivo


@st.cache_data(show_spinner="Preparando a auditoria…")
def _preparar_auditoria(hoje_iso: str):
    """Enriquecimento pesado (ponte + safra + idade), 1× por dia — reusado por safra/horizonte."""
    base = dados.carregar_tudo()
    deals = dados.carregar_hubspot()
    hist = dados.carregar_itens_historico()
    return base, coortes.preparar_deals_cache(base, deals, hist=hist)


def auditar(safra: str, hoje_iso: str, ate_idade: int | None = None):
    """Abre a cascata de uma safra até o horizonte `ate_idade`. Rápido (reusa o cache pesado)."""
    base, enr = _preparar_auditoria(hoje_iso)
    return coortes.detalhar_safra(base, None, safra, hoje=pd.Timestamp(hoje_iso),
                                  ate_idade=ate_idade, enr=enr)
