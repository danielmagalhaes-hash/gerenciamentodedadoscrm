-- Migration: torna customer_email nullable em fact_orders
-- Reversível: sim (ALTER COLUMN SET NOT NULL)
-- Motivo: planilha Shopify removeu a coluna customer_email

ALTER TABLE fact_orders ALTER COLUMN customer_email DROP NOT NULL;
