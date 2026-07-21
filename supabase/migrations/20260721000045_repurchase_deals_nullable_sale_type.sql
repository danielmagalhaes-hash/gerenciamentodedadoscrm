-- Migration: fact_repurchase_deals — permite is_first_purchase nulo
-- Reversível: sim
--   ALTER TABLE fact_repurchase_deals ALTER COLUMN is_first_purchase SET NOT NULL;
--
-- Contexto: ~2% das linhas do export histórico (10.480 de 510.915) têm tipo_de_venda
-- em branco na fonte. São transações reais (contam para a matriz M+n de recompra) só
-- que sem classificação — descartar essas linhas subcontaria recompras. NOT NULL
-- forçaria a perder esses registros; nulo aqui significa "não classificado na fonte".

ALTER TABLE fact_repurchase_deals ALTER COLUMN is_first_purchase DROP NOT NULL;
