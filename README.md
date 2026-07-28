# Auditoria de Qualidade de Dados - Pipeline de Vendas

## Visão Geral

Projeto de auditoria em dados de vendas usando Python, PostgreSQL e Power BI. O foco não foi gerar métricas mas sim foi garantir que os dados faziam sentido antes de qualquer análise.

No processo, foi identificada uma **falha de carga que teria distorcido completamente qualquer indicador de performance** gerado em cima desses dados: uma queda brusca em julho seguida de pico em agosto que, na prática, não existia pois eram dados faltando.

> Dataset sintético criado para simular o ambiente corporativo real.

### Anomalias Encontradas

| Anomalia | Indicador | Conclusão |
|---|---|---|
| **Julho/2025** | 32 pedidos, z = -2.4, cobertura de 6,5% | Carga parcial — não foi queda de vendas |
| **Agosto/2025** | 723 pedidos, z = +1.9 | Pedidos de julho chegando com atraso na base |
| **Janeiro/2026** | 13 pedidos, z = -2.5, cobertura de 3,2% | Extração incompleta, mesmo padrão de julho |

### Problemas Estruturais Identificados

| Indicador | Resultado |
|---|---|
| Nulos em `valor_total` | 106 registros (2,1%) |
| `pedido_id` duplicados | 100 registros |
| Dias sem pedido | 29 (01/07 a 29/07) |
| Pedidos com valor divergente | 246 registros |

---

## Estrutura do Projeto

```plaintext
.
├── pedidos.csv                  # Base de pedidos
├── itens_pedido.csv             # Base de itens por pedido
│
├── analise.py                   # Exploração inicial e cálculo de receita/volume
├── diagnostico_dados.py         # Varredura automatizada de qualidade
├── investigar_anomalias.py      # Drill-down nos meses sinalizados
│
├── postgres.sql                 # Queries de validação e views corrigidas
├── DASHBOARD.pbix               # Dashboard interativo no Power BI
└── tema-dark-dashboard.json     # Tema visual dark do dashboard
```

---

## Fluxo de Trabalho

```
pedidos.csv + itens_pedido.csv
           │
           ▼
       analise.py
  (exploração inicial,
   receita e volume)
           │
     anomalia detectada
     (julho/agosto)
           │
           ▼
      postgres.sql
  (validação estruturada,
   views corrigidas)
           │
    ┌──────┴──────────────┐
    ▼                     ▼
diagnostico_dados.py  investigar_anomalias.py
(varredura completa)  (drill-down por mês)
           │
           ▼
      DASHBOARD.pbix
   (Power BI com DAX)
```

### Etapas

**1. Exploração Inicial (`analise.py`)**
Carregamento das bases, remoção de duplicatas, tratamento de nulos, conversão de datas e cálculo de receita e volume por mês. Foi aqui que apareceu a primeira estranheza: julho com volume muito abaixo do normal e agosto com pico logo em seguida.

**2. Validação Estruturada (`postgres.sql`)**
Importação para PostgreSQL com queries analíticas cobrindo receita mensal, taxa de cancelamento, ticket médio, top 10 clientes, pedidos com `valor_total` nulo, divergências entre `valor_total` e soma dos itens, e verificação de duplicidade. Inclui a view `pedidos_receita_corrigida` com `COALESCE` para corrigir os nulos.

**3. Dashboard (`DASHBOARD.pbix`)**
Visualização com DAX acompanhando receita, volume, ticket médio, taxa por status e evolução mensal. A anomalia de julho ficou ainda mais evidente visualmente. Tema dark configurado via `tema-dark-dashboard.json`.

**4. Diagnóstico Automatizado (`diagnostico_dados.py`)**
Varredura completa da base: nulos por coluna, duplicatas de `pedido_id` e `item_id`, lacunas de dias sem pedidos, meses com volume anômalo via z-score, e consistência entre tabelas (itens órfãos, pedidos sem item, divergência de valores).

**5. Investigação de Anomalias (`investigar_anomalias.py`)**
Drill-down nos meses sinalizados pelo diagnóstico: cobertura de dias com pedido no mês e classificação automática entre queda real de vendas e carga parcial de dados.

---

## Resultados

| Indicador | Resultado |
|---|---|
| Período analisado | 2025-01-01 a 2026-01-01 |
| Total de pedidos | 5.100 |
| Receita total | R$ 12.691.970,31 |
| Ticket médio | R$ 2.541,44 |
| Nulos em `valor_total` | 106 (2,1%) |
| `pedido_id` duplicados | 100 |
| Dias sem pedido | 29 (01/07 a 29/07) |
| Pedidos com valor divergente | 246 |
| Cobertura de jan/2026 | 1 de ~31 dias — mês incompleto |

### Achado - NULL corrompendo RANK() silenciosamente via ORDER BY

Os 106 nulos em `valor_total` (já identificados na auditoria inicial)
tinham um efeito colateral que só apareceu ao construir um ranking de
clientes por faturamento: o Postgres trata NULL como maior que
qualquer valor numérico em `ORDER BY ... DESC`, então clientes com
pedido sem valor lançado apareciam em 1º lugar — à frente de clientes
com dezenas de milhares de reais em vendas reais.

**Detecção:** o topo do ranking não fazia sentido de negócio (cliente
em 1º lugar sem valor exibido).

**Correção:** `WHERE valor_total IS NOT NULL` antes do agrupamento.
Excluir a linha incompleta em vez de tratar como zero (`COALESCE`),
porque um pedido sem valor lançado não é o mesmo que um pedido de
valor zero — tratá-lo como zero inventaria um dado que não existe.

Query completa: [`sql/qualidade_dados/ranking_clientes_null_fix.sql`](ranking_clientes_null_fix.sql)

### Achado - Mês incompleto inflando variação percentual mês a mês

Ao calcular variação de faturamento mês a mês com `LAG()`, janeiro/2026
apareceu com queda de -99,58% em relação a dezembro/2025, número que,
lido sem contexto, pareceria uma queda catastrófica de vendas.

**Detecção:** o volume de pedidos de janeiro/2026 (13 pedidos) destoava
demais de qualquer outro mês do dataset (~400-800 pedidos/mês). Confirmado
via `MIN(data_pedido)` e `MAX(data_pedido)` filtrando esse período: o
dataset contém um único dia de janeiro/2026 (01/01), não o mês inteiro.
O mesmo padrão de corte de extração já identificado em julho/2025.

**Correção:** exclusão explícita de meses incompletos antes do cálculo de
variação (`WHERE data_pedido < '2026-01-01'`), documentando o corte na
própria query. Sem essa exclusão, qualquer dashboard ou relatório
gerencial mostraria o último mês do período como o pior resultado do
ano — quando na verdade é ausência de dado, não queda de faturamento.

**Achado adicional no mesmo exercício:** a query também expôs que o
percentual de perda por cancelamento + devolução sobre a receita
aprovada varia entre ~20% e ~42% ao mês, de forma consistente — métrica
que não estava sendo calculada antes e que tem mais relevância de
negócio do que a variação mês a mês isolada.

Query completa: [`sql/qualidade_dados/variacao_mensal_lag.sql`](variacao_mensal_lag.sql)


---

## Como Executar

```bash
# Diagnóstico completo da base
python diagnostico_dados.py pedidos.csv itens_pedido.csv

# Investigação detalhada de anomalias
python investigar_anomalias.py
```

Para o Power BI, abra `DASHBOARD.pbix` no Power BI Desktop. Para aplicar o tema dark, acesse **Exibição > Temas > Procurar temas** e selecione `tema-dark-dashboard.json`.

---

## Tecnologias

| Tecnologia | Uso |
|---|---|
| `pandas` | Exploração, limpeza e análise dos dados |
| PostgreSQL | Validação estruturada e views corrigidas |
| Power BI (DAX) | Dashboard interativo |
| Z-score (scipy) | Detecção estatística de meses anômalos |

---

## Conclusão

Sem a auditoria, qualquer análise de performance teria mostrado uma queda brusca em julho seguida de recuperação em agosto — e uma decisão de negócio poderia ter sido tomada em cima disso. A queda não existia. Era dado faltando.


> Qualidade vem antes de insight.

---

## Responsável Técnica

Desenvolvido por: **Mayara C. Almeida** 
