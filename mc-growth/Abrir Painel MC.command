#!/bin/zsh
# Atalho de 1 clique para abrir o Painel de MC.
# Dê dois cliques neste arquivo no Finder. Para fechar o painel, feche esta janela do Terminal.

cd "$(dirname "$0")" || exit 1
echo "Abrindo o Painel de MC… (aguarde o navegador abrir)"
echo "Para fechar o painel depois, é só fechar esta janela."
exec python3 -m streamlit run painel.py
