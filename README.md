# Análise de Qualidade de Dados e Auditoria de Vendas

## Resumo Executivo

Auditoria analítica de dados de vendas com foco em validação de qualidade, detecção de anomalias e geração de KPIs confiáveis em Python, PostgreSQL e Power BI — identificando uma falha de carga de dados que poderia ter levado a decisões estratégicas equivocadas.
> Dataset sintético gerado para simular um ambiente corporativo real.


## Objetivo

Este projeto simula um cenário real de auditoria analítica em dados de vendas.

Antes de gerar indicadores estratégicos, foi realizada uma validação completa da qualidade dos dados para evitar conclusões incorretas de negócio. O foco principal não foi apenas calcular métricas, mas garantir que os dados fossem confiáveis antes de qualquer interpretação.

---

## Estrutura do Projeto
.
├── pedidos.csv
├── itens_pedido.csv
├── analise.py
├── diagnostico_dados.py
├── investigar_anomalias.py
├── postgres.sql
├── DASHBOARD.pbix
└── tema-dark-dashboard.json


---

## Fluxo de Trabalho

### Exploração Inicial em Python

A análise começou com `analise.py`, onde:

- As bases foram carregadas
- Duplicatas removidas
- Valores nulos tratados
- Campo de data convertido
- Receita total, status e faturamento mensal calculados

Durante a análise exploratória, foi identificada uma anomalia significativa:

- Queda brusca no volume de pedidos em julho  
- Aumento acentuado em agosto  

Inicialmente poderia ser sazonalidade, mas a descontinuidade levantou a hipótese de falha operacional ou problema na captura de dados.

---

### Análise Estruturada no PostgreSQL

As bases foram importadas para PostgreSQL para validação estruturada via `postgres.sql`.

As consultas incluíram:

- Receita mensal calculada a partir dos itens (`SUM(quantidade * preco_unitario)`)
- Taxa de cancelamento por mês
- Ticket médio por cliente
- Top 10 clientes por receita
- Receita por categoria ao longo do tempo
- Identificação de pedidos com `valor_total` nulo
- Detecção de divergências entre `valor_total` e soma dos itens
- Criação da view `pedidos_receita_corrigida` usando `COALESCE`
- Verificação de duplicidade
- Análise de volume mensal

### Principais achados técnicos:

- 106 pedidos com `valor_total` nulo (2,1%)
- 100 `pedido_id` duplicados
- 246 pedidos com divergência entre `valor_total` e soma dos itens  
  (divergências atribuídas a regras de negócio (frete, descontos) ou inconsistências de entrada de dados.)

---

### Dashboard no Power BI

Com os dados tratados, foi desenvolvido um dashboard em `DASHBOARD.pbix` utilizando DAX para acompanhamento de:

- Receita total
- Volume de pedidos
- Ticket médio
- Taxa por status
- Evolução mensal

O tema visual foi configurado via `tema-dark-dashboard.json`.

Visualmente, a anomalia de julho tornou-se ainda mais evidente.

---

### Diagnóstico Automatizado de Qualidade

Para evitar análise subjetiva, foram criados dois scripts automatizados:

#### `diagnostico_dados.py`

Detecta automaticamente:

- Valores nulos por coluna
- Duplicatas (`pedido_id` e `item_id`)
- Lacunas de dias sem pedidos
- Meses com volume anômalo (z-score)
- Inconsistências entre tabelas:
  - Itens órfãos
  - Pedidos sem itens
  - Divergência de valores

---

#### `investigar_anomalias.py`

Aprofunda a investigação dos meses anômalos:

- Calcula cobertura de dias com pedido
- Classifica como:
  - Mês incompleto (carga parcial)
  - Queda real de volume
- Identifica concentração artificial de pedidos em meses subsequentes

Ambos os scripts são executados via terminal, garantindo reprodutibilidade.

---

## Resultados do Diagnóstico

| Indicador | Resultado |
|-----------|-----------|
| Período analisado | 2025-01-01 a 2026-01-01 |
| Total de pedidos | 5.100 |
| Receita total | R$ 12.691.970,31 |
| Ticket médio | R$ 2.541,44 |
| Nulos em valor_total | 106 (2,1%) |
| pedido_id duplicados | 100 |
| Dias sem pedido | 29 (01/07 a 29/07) |
| Pedidos com valor divergente | 246 |

---

## Anomalias Identificadas

### Julho/2025  
- 32 pedidos (z = -2.4)  
- Apenas 2 dias com registros  
- Cobertura: 6,5%  

**Conclusão:** mês incompleto por carga parcial de dados.

---

### Janeiro/2026  
- 13 pedidos (z = -2.5)  
- Cobertura: 3,2%  

**Conclusão:** extração incompleta.

---

### Agosto/2025  
- 723 pedidos (z = +1.9)  

Provável concentração de pedidos que deveriam ter sido capturados em julho.

---

## Insight Principal

A anomalia identificada não representava uma queda real de demanda, mas uma falha na carga de dados.

Sem a validação de qualidade, a empresa poderia:

- Supor queda de vendas  
- Questionar desempenho comercial  
- Tomar decisões estratégicas equivocadas  

Este projeto reforça um princípio fundamental da análise de dados:

> Qualidade vem antes de insight.

---

## Tecnologias Utilizadas

- Python (Pandas)
- PostgreSQL
- Power BI (DAX)
- SQL
- Estatística básica (z-score)

---

## Como Executar

```bash
# Diagnóstico completo
python diagnostico_dados.py pedidos.csv itens_pedido.csv

# Investigação detalhada de anomalias
python investigar_anomalias.py

## Skills Demonstradas

- Data Quality Auditing
- Data Cleaning & Validation
- SQL Analytics (PostgreSQL)
- Python Data Analysis (Pandas)
- Anomaly Detection (z-score)
- Power BI & DAX
- Reproducible Analytics Pipelines
