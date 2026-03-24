# Auditoria de Qualidade de Dados — Pipeline de Vendas

## Resumo

Projeto de auditoria em dados de vendas usando Python, PostgreSQL e Power BI. O foco não foi gerar métricas — foi garantir que os dados faziam sentido antes de qualquer análise.

No processo, encontrei uma falha de carga que teria distorcido completamente qualquer indicador de performance gerado em cima desses dados.

> Dataset sintético criado para simular um ambiente corporativo real.

---

## Estrutura do Projeto

```
.
├── pedidos.csv
├── itens_pedido.csv
├── analise.py
├── diagnostico_dados.py
├── investigar_anomalias.py
├── postgres.sql
├── DASHBOARD.pbix
└── tema-dark-dashboard.json
```

---

## Fluxo de Trabalho

### Exploração Inicial — Python

Comecei com `analise.py` pra ter uma visão geral: carreguei as bases, removi duplicatas, tratei nulos, converti datas e calculei receita e volume por mês.

Foi aí que apareceu a primeira estranheza: julho com volume muito abaixo do normal e agosto com um pico logo em seguida. Poderia ser sazonalidade, mas a queda foi abrupta demais pra ignorar.

---

### Validação Estruturada — PostgreSQL

Importei as bases pro PostgreSQL e fui fundo via `postgres.sql`:

- Receita mensal recalculada pelos itens (`SUM(quantidade * preco_unitario)`)
- Taxa de cancelamento por mês
- Ticket médio e top 10 clientes por receita
- Receita por categoria ao longo do tempo
- Pedidos com `valor_total` nulo
- Divergências entre `valor_total` e soma dos itens
- View `pedidos_receita_corrigida` com `COALESCE` pra corrigir os nulos
- Verificação de duplicidade

**O que encontrei:**

- 106 pedidos com `valor_total` nulo (2,1%)
- 100 `pedido_id` duplicados
- 246 pedidos com valor divergente da soma dos itens — parte atribuída a frete e desconto, parte a erro mesmo

---

### Dashboard — Power BI

Com os dados tratados, montei o `DASHBOARD.pbix` com DAX pra acompanhar receita, volume, ticket médio, taxa por status e evolução mensal.

Visualmente, a anomalia de julho ficou ainda mais evidente. O tema dark foi configurado via `tema-dark-dashboard.json`.

---

### Diagnóstico Automatizado

Pra não depender de análise visual, criei dois scripts que rodam no terminal:

#### `diagnostico_dados.py`
Varredura completa da base:
- Nulos por coluna
- Duplicatas (`pedido_id` e `item_id`)
- Lacunas de dias sem pedidos
- Meses com volume anômalo via z-score
- Consistência entre tabelas: itens órfãos, pedidos sem item, divergência de valores

#### `investigar_anomalias.py`
Drill-down nos meses que o diagnóstico sinalizou:
- Cobertura de dias com pedido no mês
- Classifica se foi queda real ou carga parcial de dados

---

## Resultados

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

**Conclusão:** carga parcial de dados — o mês não estava incompleto por falta de vendas.

---

### Janeiro/2026
- 13 pedidos (z = -2.5)
- Cobertura: 3,2%

**Conclusão:** extração incompleta, mesmo padrão de julho.

---

### Agosto/2025
- 723 pedidos (z = +1.9)

Pico logo depois de julho. Provavelmente pedidos que deveriam ter sido capturados em julho e chegaram com atraso na base.

---

## Conclusão

Sem a auditoria, qualquer análise de performance teria mostrado uma queda brusca em julho seguida de recuperação em agosto — e alguém poderia tomar uma decisão de negócio em cima disso.

A queda não existia. Era dado faltando.

> Qualidade vem antes de insight.

---

## Tecnologias

- Python (Pandas)
- PostgreSQL
- Power BI (DAX)
- Estatística básica (z-score)

---

## Como Executar

```bash
# Diagnóstico completo
python diagnostico_dados.py pedidos.csv itens_pedido.csv

# Investigação detalhada de anomalias
python investigar_anomalias.py
```
