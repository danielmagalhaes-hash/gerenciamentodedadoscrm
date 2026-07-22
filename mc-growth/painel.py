"""
painel.py — a PORTA DE ENTRADA do painel (Streamlit).

Este arquivo não desenha nada: ele só declara o **menu** (quais telas existem, com que
nome e em que ordem) e passa a bola para a tela escolhida. As telas moram em `views/`.

Por que assim: até 2026-07-14 o Streamlit montava o menu sozinho, lendo a pasta `pages/`
— e o nome de cada item vinha do nome do arquivo (a tela principal aparecia como
"painel"). Com `st.navigation` o menu passa a ser nosso: nome e ordem livres.

Rodar:  python3 -m streamlit run painel.py
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="MC Growth — Minimal Club", page_icon="📈", layout="wide")

# Ordem e nomes do menu (pedido do João, 2026-07-14). A auditoria é ferramenta de apoio
# (prefixo "A") e por isso vai depois das três telas de leitura.
menu = st.navigation([
    st.Page("views/geral.py", title="1. Geral", icon="📈", default=True),
    st.Page("views/aquisicao.py", title="2. Aquisição", icon="🎯"),
    st.Page("views/coortes.py", title="3. Cohorts", icon="📊"),
    st.Page("views/portas_entrada.py", title="4. Portas de entrada", icon="🚪"),
    st.Page("views/auditoria.py", title="A1 - Auditoria Custos", icon="🔍"),
    st.Page("views/auditoria_cohort.py", title="A2 - Auditoria MC Cohort", icon="🔍"),
    st.Page("views/auditoria_portas.py", title="A3 - Auditoria Portas", icon="🔍"),
])
menu.run()
