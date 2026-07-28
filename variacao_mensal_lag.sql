-- Achado de qualidade de dado: mês incompleto inflando variação percentual
--
-- O problema: janeiro/2026 tem apenas 13 pedidos no dataset, contra uma
     -- média de ~400-800 pedidos/mês no resto do período.
-- Calculando variação mês a mês sem filtrar isso, jan/2026 aparecia com -99,58% de queda em
      -- relação a dez/2025 — número que, sem contexto, pareceria uma queda catastrófica de vendas.

-- Detecção: MIN(data_pedido)/MAX(data_pedido) filtrando jan/2026 mostrou
     -- que o dataset contém um único dia desse mês (01/01), não o mês inteiro.
-- Mesmo padrão de corte de extração já identificado em julho/2025.

-- Correção: excluir meses incompletos do cálculo de variação, deixando explícito no filtro
     -- qual o corte usado, em vez de deixar o mês incompleto silenciosamente distorcer a série.

-- Achado adicional: a query também expõe que o % de perda por
     -- cancelamento + devolução sobre a receita aprovada varia entre
     -- ~20% e ~42% ao mês, de forma consistente 
-- Métrica de negócio mais relevante do que a variação isolada mês a mês.

WITH faturamento_mensal AS (
    SELECT
        DATE_TRUNC('month', data_pedido) AS mes,
        SUM(valor_total) FILTER (WHERE status = 'aprovado') AS receita_aprovada,
        SUM(valor_total) FILTER (WHERE status = 'cancelado') AS receita_cancelada,
        SUM(valor_total) FILTER (WHERE status = 'devolvido') AS receita_devolvida
    FROM pedidos
    WHERE data_pedido < '2026-01-01'  -- exclui jan/2026: mês incompleto, 1 dia coletado
    GROUP BY DATE_TRUNC('month', data_pedido)
),
receita AS (
    SELECT
        mes,
        COALESCE(receita_aprovada, 0) AS receita_aprovada,
        COALESCE(receita_cancelada, 0) AS receita_cancelada,
        COALESCE(receita_devolvida, 0) AS receita_devolvida
    FROM faturamento_mensal
)
SELECT
    mes,
    receita_aprovada,
    receita_cancelada,
    receita_devolvida,
    LAG(receita_aprovada) OVER (ORDER BY mes) AS receita_aprovada_mes_anterior,
    receita_aprovada - LAG(receita_aprovada) OVER (ORDER BY mes) AS variacao_absoluta,
    ROUND(
        100.0 * (receita_aprovada - LAG(receita_aprovada) OVER (ORDER BY mes))
        / NULLIF(LAG(receita_aprovada) OVER (ORDER BY mes), 0),
        2
    ) AS variacao_percentual,
    ROUND(
        100.0 * (receita_cancelada + receita_devolvida)
        / NULLIF(receita_aprovada, 0),
        2
    ) AS pct_perda_sobre_aprovado
FROM receita
ORDER BY mes;