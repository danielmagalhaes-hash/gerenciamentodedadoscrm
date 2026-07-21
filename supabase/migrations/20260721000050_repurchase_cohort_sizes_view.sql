-- Migration: view leve com o tamanho de cada safra (sem a matriz inteira)
-- Reversível: sim
--   DROP VIEW IF EXISTS vw_repurchase_cohort_sizes;
--
-- Contexto: o painel buscava vw_repurchase_cohort_matrix inteira (2135 linhas, todas
-- as safras) só para popular o seletor de safra e mostrar uma por vez — além de
-- desperdiçar carga, esbarrava no limite padrão de 1000 linhas do PostgREST (a matriz
-- vinha cortada). Essa view só tem 1 linha por mês (~65 linhas), usada pelo seletor;
-- a matriz completa passa a ser buscada filtrada por safra (poucas dezenas de linhas).

CREATE OR REPLACE VIEW vw_repurchase_cohort_sizes AS
SELECT
    date_trunc('month', first_purchase_date)::date AS cohort_month,
    COUNT(*) AS clientes_adquiridos
FROM mv_repurchase_customer_first_purchase
GROUP BY 1
ORDER BY 1;

GRANT SELECT ON vw_repurchase_cohort_sizes TO anon;
