# Sessão 2026-07-09 — Spec + construção da V2 (aba de aquisição)

> Modo B (construção — toca dinheiro: MC-novos, CAC, aROAS). Continuação do discovery da V2
> feito de manhã (`docs/sessions/2026-07-09-discovery-v2-aquisicao.md`).

## Objetivo
Escrever a spec da V2 (aba de aquisição) a partir do `PRODUCT.md` e — a pedido do João no
meio da sessão ("já tá tudo pronto, agora é executar") — **construir e verificar** a aba.

## O que foi feito

### 1. Perguntas críticas (PASSO 1) → 3 decisões de construção
- **Onde vive:** página nova no menu lateral (`pages/2_Aquisicao.py`), com seletor de período
  próprio — segue o padrão da Auditoria. (Descartado: abas `st.tabs` dentro do painel.)
- **Profundidade da tela:** 5 cartões **+ mini-cascata de novos** (Vendas-novos → deduções →
  CMV-novos → custos → Lucro Bruto-novos → mídia inteira → MC-novos), pra mostrar COMO a
  MC-novos se forma.
- **Amarração "sem classificação":** **guarda silenciosa** — a tela mostra só os novos; por
  baixo confere que novos + recompra + sem-classificação = total e só avisa se não fechar
  (fiel a "recompra não aparece na tela").

### 2. Spec escrita
`docs/specs/2026-07-09-v2-aba-aquisicao.md` — estrutura padrão do trilho (8 seções + checklist),
regras R1..R13, critérios de aceite testáveis, bordas. Glossário respeitado ("MC", nunca "lucro").

### 3. Verificação da fonte (antes de codar a regra)
Li a aba `Vendas` ao vivo: `customer_type` existe (5ª coluna), grafia exata **`Primeira Compra`**
/ **`Recompra`** / vazio. Contagens: base inteira 38.095 pedidos (19.569 novos, 18.026 recompra,
500 sem-classif); junho 14.049 (7.507 / 6.542 / 0).

### 4. Construção (3 peças)
- **`dados.py`** — `carregar_vendas` passou a exigir e mapear `customer_type` (`Dados.vendas`
  ganhou a coluna). Ausência → `ErroDeDados` claro (decisão: barulhento > silencioso).
- **`cascata.py`** — função nova `calcular_aquisicao` + dataclass `ResultadoAquisicao`. **Não
  toca `calcular`.** Reusa `_recorte_pedidos`; mídia inteira (convenção 100% mídia → novos).
- **`pages/2_Aquisicao.py`** — herói MC-novos (verde/vermelho = linha do zero), 5 cartões,
  mini-cascata, alertas/notas de borda.

### 5. Verificação (tudo verde)
- **Amarração:** as 3 faixas somam o total do painel (14.026 pedidos em junho, após exclusões);
  Vendas por faixa somam a Vendas do painel; Ad Spend idêntico ao do painel.
- **Aritmética:** MC-novos = LB-novos − Ad Spend; CAC = Ad Spend ÷ Pedidos-novos; aROAS =
  Vendas-novos ÷ Ad Spend — todos conferem.
- **Junho/2026 (ao vivo):** MC-novos **+R$237.855** (verde), CAC **R$189,72**, aROAS **2,74**.
- **Telas:** `AppTest` sobe a página nova (5 cartões + DRE) e o painel V1 e a Auditoria **sem
  regressão**.
- **Bordas (sintético):** sem mídia → aROAS "—", CAC R$0; sem novos → CAC "—", MC-novos =
  −mídia; rótulo inesperado ("VIP") → sem-classificação + aviso, amarração fecha.

## Decisões duráveis (também no ARCHITECTURE.md, tabela de decisões)
- V2 = página nova; partição por `customer_type`; mídia inteira nos novos; guarda silenciosa;
  ausência do carimbo = falha barulhenta.

## Achado a resolver (não bloqueia)
- **`PRODUCT.md` seção 3** cita "em junho/2026, 84 de 37.593 (0,22%)" para sem-classificação;
  a fonte ao vivo mostra junho com 14.049 pedidos e **0** sem-classificação (base inteira: 500).
  Parece retrato ilustrativo do discovery. **Sugestão:** corrigir a frase numa próxima passada.
  A regra é robusta a isso.

## Decisão fechada nesta sessão
- **Ausência do `customer_type` → trava a leitura inteira** (Opção A, falha barulhenta). Já
  implementado; trocar para "só desativar a aba" é 1 linha, se um dia fizer sentido.

## Pendências / próximo passo
- **Commitado** ao fim desta sessão (V2 inteira: código + docs) no `main`.
- Herdadas: encaminhar `docs/skus-custo-zerado-aba-3-1.csv` (137 SKUs) e
  `docs/orientacao-base-itens-confiavel.md` ao time de Dados.
- Rodar: `python3 -m streamlit run painel.py` (a aba "Aquisicao" aparece no menu lateral).
</content>
