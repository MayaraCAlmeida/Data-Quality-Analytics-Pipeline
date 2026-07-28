-- Mais um achado de qualidade de dado: NULL em valor_total distorce ranking
--
-- O problema: pedidos.valor_total tem NULL em ~1-2% dos registros
-- (aprovado: 80/3774, cancelado: 21/985, devolvido: 3/241).
-- Por padrão, ORDER BY ... DESC no Postgres trata NULL como maior que qq valor numérico, 
    -- então são clientes com pedido sem valor lançado apareciam que em 1º lugar no ranking
    -- à frente de clientes com dezenas de milhares em faturamento real.

-- Correção: excluir linhas com valor_total NULL do cálculo, já que
    -- representam pedido com dado incompleto, não um "cliente que gastou zero".

SELECT
    status,
    cliente_id,
    SUM(valor_total) AS total_gasto,
    RANK() OVER (
        PARTITION BY status
        ORDER BY SUM(valor_total) DESC
    ) AS ranking
FROM pedidos
WHERE valor_total IS NOT NULL
GROUP BY status, cliente_id
ORDER BY status, ranking;
