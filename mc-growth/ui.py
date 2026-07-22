"""
ui.py — peças visuais compartilhadas pelas telas (Streamlit).

Existe para que a cascata (DRE) seja DESENHADA num lugar só. Antes, cada aba tinha a
sua cópia dos estilos e da tabela — e elas divergiam a cada mudança. A forma do DRE é
definida em `cascata.montar_cascata` (os números) e aqui (as cores e a indentação).

Formato único (spec 2026-07-14):
    Vendas
    (−) Deduções            ← subtotal do grupo, CINZA
          PIS/COFINS + CBS … (5 linhas, recuadas)
    (−) Cost of Delivery    ← subtotal do grupo, CINZA
          CMV                ← CINZA CLARO (⚠️ quando parte dele é estimada em 30%)
          Frete … (5 linhas, recuadas)
    (=) Lucro Bruto
    (−) Mídia Paga
    (=) Margem de Contribuição
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

COR_POSITIVA = "#1f7a3d"  # verde — resultado ≥ 0
COR_NEGATIVA = "#b91c1c"  # vermelho — resultado < 0

# Marcador de operação no nome da linha: (+) soma, (−) subtrai, (=) subtotal.
_MARCADOR = {
    "topo": "(+)", "grupo": "(−)", "deducao": "(−)", "cmv": "(−)", "custo": "(−)",
    "midia": "(−)", "subtotal": "(=)", "resultado": "(=)",
}

# Linhas filhas entram recuadas — a hierarquia se lê de bater o olho.
_RECUO = "  "  # dois espaços "em"
_FILHAS = {"deducao", "cmv", "custo"}

_ESTILO = {
    "grupo": "background-color:#e5e7eb; color:#111827; font-weight:700",     # cinza (subtotal)
    "cmv": "background-color:#f3f4f6; color:#111827",                        # cinza claro
    "subtotal": "background-color:#dbeafe; color:#1e3a8a; font-weight:700",  # Lucro Bruto (azul)
    "resultado": "background-color:#1f7a3d; color:#ffffff; font-weight:700", # MC (verde)
}


def _rotulo(linha) -> str:
    marca = _MARCADOR.get(linha.tipo, "")
    recuo = _RECUO if linha.tipo in _FILHAS else ""
    return f"{recuo}{marca} {linha.rotulo}".rstrip()


def tabela_dre(linhas, base_receita: float, reais, numero, cor_resultado: str | None = None,
               titulo_pct: str = "% da Receita") -> None:
    """
    Desenha a cascata. `linhas` são os `LinhaDRE` de `cascata.montar_cascata`.

    `base_receita` é o denominador da análise vertical (a linha Vendas da própria tela).
    `cor_resultado` pinta a última linha (MC): use verde/vermelho onde há linha do zero
    (aquisição, coortes); no painel geral fica o verde padrão.
    """
    def pct(valor: float) -> str:
        if not base_receita:
            return "—"
        return numero(valor / base_receita * 100, 1) + "%"

    tabela = pd.DataFrame({
        "Linha": [_rotulo(l) for l in linhas],
        "Valor": [reais(l.valor) for l in linhas],
        titulo_pct: [pct(l.valor) for l in linhas],
    })
    tipos = [l.tipo for l in linhas]

    estilos = dict(_ESTILO)
    if cor_resultado:
        estilos["resultado"] = f"background-color:{cor_resultado}; color:#ffffff; font-weight:700"

    def _estilo_linha(linha_estilo):
        return [estilos.get(tipos[linha_estilo.name], "")] * len(linha_estilo)

    estilizada = (
        tabela.style.apply(_estilo_linha, axis=1)
        .set_properties(subset=["Valor", titulo_pct], **{"text-align": "right"})
        .hide(axis="index")
    )
    st.table(estilizada)
