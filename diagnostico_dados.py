"""
Diagnóstico de Qualidade de Dados
============================================
Uso:
    python diagnostico_dados.py pedidos.csv itens_pedido.csv

Detecta automaticamente:
- Lacunas de dias/meses sem dados
- Meses com volume anormalmente baixo
- Valores nulos e duplicatas
- Inconsistências entre os dois arquivos
"""

import pandas as pd
import sys
from datetime import timedelta


# ── Cores para o terminal ──────────────────────────────────────────────────
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
BOLD = "\033[1m"
RESET = "\033[0m"


def ok(msg):
    print(f"  {GREEN}✓{RESET} {msg}")


def warn(msg):
    print(f"  {YELLOW}⚠{RESET}  {msg}")


def erro(msg):
    print(f"  {RED}✗{RESET} {msg}")


def titulo(msg):
    print(f"\n{BOLD}{'─'*55}\n  {msg}\n{'─'*55}{RESET}")


# ── Carregamento ───────────────────────────────────────────────────────────
def carregar(pedidos_path, itens_path):
    pedidos = pd.read_csv(pedidos_path, parse_dates=["data_pedido"])
    itens = pd.read_csv(itens_path)
    return pedidos, itens


# ── 1. Nulos e tipos ───────────────────────────────────────────────────────
def checar_nulos(pedidos, itens):
    titulo("1. VALORES NULOS")
    for nome, df in [("pedidos", pedidos), ("itens_pedido", itens)]:
        nulos = df.isnull().sum()
        nulos = nulos[nulos > 0]
        if nulos.empty:
            ok(f"{nome}: sem nulos")
        else:
            for col, n in nulos.items():
                erro(f"{nome}.{col}: {n} nulos ({n/len(df)*100:.1f}%)")


# ── 2. Duplicatas ──────────────────────────────────────────────────────────
def checar_duplicatas(pedidos, itens):
    titulo("2. DUPLICATAS")
    dup_p = pedidos.duplicated(subset="pedido_id").sum()
    dup_i = itens.duplicated(subset="item_id").sum()
    if dup_p == 0:
        ok("pedidos: sem pedido_id duplicado")
    else:
        erro(f"pedidos: {dup_p} pedido_id duplicados!")
    if dup_i == 0:
        ok("itens: sem item_id duplicado")
    else:
        erro(f"itens: {dup_i} item_id duplicados!")


# ── 3. Lacunas de dias ─────────────────────────────────────────────────────
def checar_lacunas_dias(pedidos):
    titulo("3. LACUNAS DE DIAS (dias sem nenhum pedido)")
    datas = sorted(pedidos["data_pedido"].dt.normalize().unique())
    inicio, fim = datas[0], datas[-1]
    todos_os_dias = pd.date_range(inicio, fim, freq="D")
    faltando = [d for d in todos_os_dias if d not in set(datas)]

    if len(faltando) == 0:
        ok("Nenhum dia sem pedido no período")
    else:
        # Agrupa dias consecutivos em intervalos
        intervalos = []
        ini = faltando[0]
        ant = faltando[0]
        for d in faltando[1:]:
            if d - ant > timedelta(days=1):
                intervalos.append((ini, ant))
                ini = d
            ant = d
        intervalos.append((ini, ant))

        warn(f"{len(faltando)} dias sem pedidos → {len(intervalos)} intervalo(s):")
        for a, b in intervalos:
            if a == b:
                print(f"     • {a.date()}")
            else:
                dias = (b - a).days + 1
                print(f"     • {a.date()} → {b.date()} ({dias} dias)")


# ── 4. Anomalia de volume mensal ───────────────────────────────────────────
def checar_volume_mensal(pedidos, limiar_zscore=2.0):
    titulo("4. MESES COM VOLUME ANÔMALO")
    pedidos = pedidos.copy()
    pedidos["mes"] = pedidos["data_pedido"].dt.to_period("M")

    mensal = (
        pedidos.groupby("mes")
        .agg(qtd_pedidos=("pedido_id", "count"), receita=("valor_total", "sum"))
        .reset_index()
    )

    # Ignora primeiro e último mês (podem estar incompletos)
    mensal_mid = mensal.iloc[1:-1]

    media = mensal_mid["qtd_pedidos"].mean()
    std = mensal_mid["qtd_pedidos"].std()

    print(f"  Média mensal de pedidos (meses completos): {media:.0f} ± {std:.0f}")
    print()

    anomalias = False
    for _, row in mensal.iterrows():
        z = (row["qtd_pedidos"] - media) / std if std > 0 else 0
        flag = ""
        if abs(z) >= limiar_zscore:
            anomalias = True
            flag = f"{RED}← ANOMALIA (z={z:+.1f}){RESET}"
        elif abs(z) >= 1.5:
            flag = f"{YELLOW}← atenção (z={z:+.1f}){RESET}"
        print(
            f"  {row['mes']}  |  {row['qtd_pedidos']:>4} pedidos  |  R$ {row['receita']:>12,.2f}  {flag}"
        )

    if not anomalias:
        print()
        ok("Nenhum mês com anomalia estatística significativa")


# ── 5. Consistência entre tabelas ─────────────────────────────────────────
def checar_consistencia(pedidos, itens):
    titulo("5. CONSISTÊNCIA ENTRE TABELAS")

    ids_pedidos = set(pedidos["pedido_id"])
    ids_em_itens = set(itens["pedido_id"])

    orphan_itens = ids_em_itens - ids_pedidos
    pedidos_sem_item = ids_pedidos - ids_em_itens

    if not orphan_itens:
        ok("Todos os itens têm pedido correspondente")
    else:
        erro(f"{len(orphan_itens)} itens com pedido_id inexistente em pedidos.csv")

    if not pedidos_sem_item:
        ok("Todos os pedidos têm ao menos um item")
    else:
        warn(f"{len(pedidos_sem_item)} pedidos sem nenhum item em itens_pedido.csv")

    # Checa se valor_total bate com soma dos itens
    itens2 = itens.copy()
    itens2["subtotal"] = itens2["quantidade"] * itens2["preco_unitario"]
    soma_itens = itens2.groupby("pedido_id")["subtotal"].sum()
    merged = pedidos.set_index("pedido_id")[["valor_total"]].join(
        soma_itens, how="inner"
    )
    merged["diff"] = (merged["valor_total"] - merged["subtotal"]).abs()
    divergentes = merged[merged["diff"] > 0.05]  # tolerância de R$ 0,05

    if divergentes.empty:
        ok("Valores totais batem com a soma dos itens")
    else:
        warn(
            f"{len(divergentes)} pedidos com valor_total divergente da soma dos itens (possível frete/desconto ou erro):"
        )
        print(divergentes.head(10).to_string())


# ── 6. Resumo final ────────────────────────────────────────────────────────
def resumo(pedidos):
    titulo("RESUMO GERAL")
    d_min = pedidos["data_pedido"].min().date()
    d_max = pedidos["data_pedido"].max().date()
    print(f"  Período        : {d_min} → {d_max}")
    print(f"  Total pedidos  : {len(pedidos):,}")
    print(f"  Receita total  : R$ {pedidos['valor_total'].sum():,.2f}")
    print(f"  Ticket médio   : R$ {pedidos['valor_total'].mean():,.2f}")
    print()


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 3:
        # Tenta caminhos padrão
        pedidos_path = "pedidos.csv"
        itens_path = "itens_pedido.csv"
    else:
        pedidos_path = sys.argv[1]
        itens_path = sys.argv[2]

    print(f"\n{BOLD}DIAGNÓSTICO DE QUALIDADE DE DADOS{RESET}")
    print(f"Arquivos: {pedidos_path}  |  {itens_path}")

    pedidos, itens = carregar(pedidos_path, itens_path)

    resumo(pedidos)
    checar_nulos(pedidos, itens)
    checar_duplicatas(pedidos, itens)
    checar_lacunas_dias(pedidos)
    checar_volume_mensal(pedidos)
    checar_consistencia(pedidos, itens)

    print(f"\n{BOLD}Diagnóstico concluído.{RESET}\n")


if __name__ == "__main__":
    main()
