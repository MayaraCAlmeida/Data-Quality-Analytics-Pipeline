### analisar as tabelas criadas ###

import pandas as pd

pedidos = pd.read_csv("pedidos.csv")
itens = pd.read_csv("itens_pedido.csv")

print(pedidos.head())
print(itens.head())


### DEPOIS ESSE ###
## quantas linhas, tipos, alguma inconformidade ##
print(pedidos.shape)
print(pedidos.info())
print(pedidos.isnull().sum())


### remover duplicados ###
pedidos = pedidos.drop_duplicates(subset="pedido_id")


### tratar os nulos ###
pedidos = pedidos.dropna(subset=["valor_total"])


### converter a data ###
pedidos["data_pedido"] = pd.to_datetime(pedidos["data_pedido"])


## faturamento total ##
print(pedidos["valor_total"].sum())


### pedido por status ### apv/rep/can/dev
print(pedidos["status"].value_counts())


### produto q mais vende ###
print(itens.groupby("produto")["quantidade"].sum().sort_values(ascending=False))


### valor venda por mês ###
pedidos["mes"] = pedidos["data_pedido"].dt.month

print(pedidos.groupby("mes")["valor_total"].sum())


### Observado: queda brusca no mês 07 e aumento brusco no mês 08 ###
### Observa-se descontinuidade no volume de pedidos em julho ##
### Pode indicar falha operacional, problema de captura ou sazonalidade ##
### Recomenda-se validar com área de negócio ###
