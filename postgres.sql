-- criando a tabela antes de importar os CSVs
CREATE TABLE pedidos (
    pedido_id INT,
    cliente_id INT,
    data_pedido DATE,
    valor_total NUMERIC,
    status TEXT
);

CREATE TABLE itens_pedido (
    item_id INT,
    pedido_id INT,
    produto TEXT,
    categoria TEXT,
    quantidade INT,
    preco_unitario NUMERIC
);


--- verificando se a importação deu certo 

SELECT COUNT(*) FROM itens_pedido;
SELECT COUNT(*) FROM pedidos;

SELECT * FROM pedidos LIMIT 5;
SELECT * FROM itens_pedido LIMIT 5;

-------- verificar primeiro p ver se tem q corrigir --
--- receita mensal --- 
SELECT
    DATE_TRUNC('month', p.data_pedido) AS mes,
    SUM(i.quantidade * i.preco_unitario) AS receita
FROM pedidos p
JOIN itens_pedido i ON i.pedido_id = p.pedido_id
WHERE p.status = 'aprovado'
GROUP BY mes
ORDER BY mes;

--- taxa de cancelamento por mês ---
SELECT
    DATE_TRUNC('month', data_pedido) AS mes,
    COUNT(*) FILTER (WHERE status = 'cancelado') * 1.0
        / COUNT(*) AS taxa_cancelamento
FROM pedidos
GROUP BY mes
ORDER BY mes;

----- ticket medio por cliente --- 
SELECT
    p.cliente_id,
    SUM(i.quantidade * i.preco_unitario)
        / COUNT(DISTINCT p.pedido_id) AS ticket_medio
FROM pedidos p
JOIN itens_pedido i ON i.pedido_id = p.pedido_id
WHERE p.status = 'aprovado'
GROUP BY p.cliente_id
ORDER BY ticket_medio DESC;

--- top 10 clientes de acordo com a receita real --
SELECT
    p.cliente_id,
    SUM(i.quantidade * i.preco_unitario) AS receita
FROM pedidos p
JOIN itens_pedido i ON i.pedido_id = p.pedido_id
WHERE p.status = 'aprovado'
GROUP BY p.cliente_id
ORDER BY receita DESC
LIMIT 10;

----- receita por categoria ao longo do tempo ---

SELECT
    DATE_TRUNC('month', p.data_pedido) AS mes,
    i.categoria,
    SUM(i.quantidade * i.preco_unitario) AS receita
FROM pedidos p
JOIN itens_pedido i ON i.pedido_id = p.pedido_id
WHERE p.status = 'aprovado'
GROUP BY mes, i.categoria
ORDER BY mes, receita DESC;

---- da p melhorar ---

SELECT
    p.pedido_id,
    p.valor_total,
    SUM(i.quantidade * i.preco_unitario) AS receita_itens,
    p.valor_total - SUM(i.quantidade * i.preco_unitario) AS diferenca
FROM pedidos p
JOIN itens_pedido i ON i.pedido_id = p.pedido_id
GROUP BY p.pedido_id, p.valor_total
HAVING p.valor_total IS NULL
   OR ABS(p.valor_total - SUM(i.quantidade * i.preco_unitario)) > 1;

   ---- que bagunça ----
   --- alguns pedidos n tem valor informado --
   --- na base, identifiquei registros que o valor_total n estava preenchido
   --- a receita foi recalculada a partir dos itens --- 
   ---- SUM(qtde * pç unitario)

SELECT
    p.pedido_id,
    COALESCE(p.valor_total,
             SUM(i.quantidade * i.preco_unitario)) AS valor_corrigido
FROM pedidos p
JOIN itens_pedido i ON i.pedido_id = p.pedido_id
GROUP BY p.pedido_id, p.valor_total;


---- criar uma view p ver os novos valores ---
CREATE OR REPLACE VIEW pedidos_receita_corrigida AS
SELECT
    p.pedido_id,
    p.cliente_id,
    p.data_pedido,
    p.status,
    SUM(i.quantidade * i.preco_unitario) AS receita_real
FROM pedidos p
JOIN itens_pedido i ON i.pedido_id = p.pedido_id
GROUP BY
    p.pedido_id,
    p.cliente_id,
    p.data_pedido,
    p.status;

--- ver ----
SELECT * FROM pedidos_receita_corrigida LIMIT 10;

---- ou uma tabela fisica ---
CREATE TABLE pedidos_receita_corrigida AS
SELECT
    p.pedido_id,
    p.cliente_id,
    p.data_pedido,
    p.status,
    SUM(i.quantidade * i.preco_unitario) AS receita_real
FROM pedidos p
JOIN itens_pedido i ON i.pedido_id = p.pedido_id
GROUP BY
    p.pedido_id,
    p.cliente_id,
    p.data_pedido,
    p.status;
	
--------------------- deu erro
DROP VIEW pedidos_receita_corrigida;

CREATE VIEW pedidos_receita_corrigida AS


-------------------------------
SELECT * 
FROM pedidos_receita_corrigida 
LIMIT 10;

------------------- verificar duplicidade de pedidos ---
SELECT
    pedido_id,
    COUNT(*) AS vezes
FROM pedidos
GROUP BY pedido_id
HAVING COUNT(*) > 1
ORDER BY vezes DESC;
---- tem duplicidade ..... ----

---- qtde de duplicados ---
SELECT COUNT(*) - COUNT(DISTINCT pedido_id) AS total_duplicados
FROM pedidos;

---- valores nulos ---
SELECT COUNT(*) AS nulos_valor
FROM pedidos
WHERE valor_total IS NULL;

---- outras colunas q sao importantes ---
SELECT
    COUNT(*) FILTER (WHERE cliente_id IS NULL) AS cliente_nulo,
    COUNT(*) FILTER (WHERE data_pedido IS NULL) AS data_nula,
    COUNT(*) FILTER (WHERE status IS NULL) AS status_nulo
FROM pedidos;


---- pedido sem item -- 
SELECT p.pedido_id
FROM pedidos p
LEFT JOIN itens_pedido i ON i.pedido_id = p.pedido_id
WHERE i.pedido_id IS NULL;

---- itens sem pedido ----
SELECT i.pedido_id
FROM itens_pedido i
LEFT JOIN pedidos p ON p.pedido_id = i.pedido_id
WHERE p.pedido_id IS NULL;

---- divergencia de valor total vs itens ---
SELECT
    p.pedido_id,
    p.valor_total,
    SUM(i.quantidade * i.preco_unitario) AS soma_itens,
    p.valor_total - SUM(i.quantidade * i.preco_unitario) AS diferenca
FROM pedidos p
JOIN itens_pedido i ON i.pedido_id = p.pedido_id
GROUP BY p.pedido_id, p.valor_total
HAVING p.valor_total IS NULL
   OR ABS(p.valor_total - SUM(i.quantidade * i.preco_unitario)) > 1;

---- volume de vendas por mes --- 
SELECT
    DATE_TRUNC('month', data_pedido) AS mes,
    COUNT(*) AS pedidos
FROM pedidos
GROUP BY mes
ORDER BY mes;
--- mes 7 foi assustador ----

--- evolucao de preço medio ---
SELECT
    DATE_TRUNC('month', p.data_pedido) AS mes,
    AVG(i.preco_unitario) AS preco_medio
FROM pedidos p
JOIN itens_pedido i ON i.pedido_id = p.pedido_id
GROUP BY mes
ORDER BY mes;
--- caiu muito em janeiro/2026 ----
-- mas a receita realmente caiu ??? ---
SELECT
    DATE_TRUNC('month', data_pedido) AS mes,
    SUM(receita_real) AS receita
FROM pedidos_receita_corrigida
WHERE status = 'aprovado'
GROUP BY mes
ORDER BY mes;
--- teve oscilaçao ---
--- foi preço ou volume ??? ---
SELECT
    DATE_TRUNC('month', p.data_pedido) AS mes,
    SUM(i.quantidade) AS volume
FROM pedidos_receita_corrigida p
JOIN itens_pedido i ON i.pedido_id = p.pedido_id
WHERE p.status = 'aprovado'
GROUP BY mes
ORDER BY mes;

SELECT
    DATE_TRUNC('month', p.data_pedido) AS mes,
    AVG(i.preco_unitario) AS preco_medio
FROM pedidos_receita_corrigida p
JOIN itens_pedido i ON i.pedido_id = p.pedido_id
WHERE p.status = 'aprovado'
GROUP BY mes
ORDER BY mes;

--- volume estável + preço cai .... problema comercial

---- preço estável + volume cai .... problema de demanda

--- ambos caem ... alerta vermelho

--- alguma categoria ta puxando a queda ?? --
SELECT
    DATE_TRUNC('month', p.data_pedido) AS mes,
    i.categoria,
    SUM(i.quantidade * i.preco_unitario) AS receita
FROM pedidos_receita_corrigida p
JOIN itens_pedido i ON i.pedido_id = p.pedido_id
WHERE p.status = 'aprovado'
GROUP BY mes, i.categoria
ORDER BY mes;
--- books, papelaria, moda ----
---- papelaria ja caiu no 2º mes ---

--- mas sera q existe problema nos dados?? --
SELECT
    DATE_TRUNC('month', data_pedido) AS mes,
    COUNT(*) AS pedidos
FROM pedidos
GROUP BY mes
ORDER BY mes;
--- mes 07 teve quedra mt brusca --- abissal
-- tem erro ai ---

--- A queda de receita acompanha redução do preço médio ao longo do período ---
--- Descontinuidade no volume no mes 07 ---
---- Sugerindo possível falha operacional além do efeito comercial ----




SELECT *
FROM pedidos
WHERE status = 'Aprovado';

SELECT DISTINCT status
FROM pedidos;

SELECT *
FROM pedidos
WHERE status = 'aprovado';

SELECT *
FROM pedidos
WHERE status = 'cancelado';

SELECT *
FROM pedidos
WHERE status = 'devolvido';