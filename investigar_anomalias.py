import sys
import pandas as pd
import calendar
from datetime import timedelta

# ── codificação UTF-8 para Windows ──────────────────────────────────────────
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# ── ANSI color codes ─────────────────────────────────────────────────────────
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
WHITE = "\033[97m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"

# ── Separadores ──────────────────────────────────────────────────────────────
SEP_THIN = "─" * 62
SEP_THICK = "=" * 62


# ── helpers ───────────────────────────────────────────────────────────────────
def sec(title: str) -> str:
    return f"\n  {SEP_THIN}\n" f"  {WHITE}{title}{RESET}\n" f"  {SEP_THIN}"


def ok(msg: str) -> str:
    return f"  {GREEN}✓{RESET} {msg}"


def err(msg: str) -> str:
    return f"  {RED}✗{RESET} {msg}"


def warn(msg: str) -> str:
    return f"  {YELLOW}⚠{RESET} {msg}"


def lbl(key: str, value: str) -> str:
    return f"  {WHITE}{key:<16}{RESET} : {value}"


# ── relatório principal ───────────────────────────────────────────────────────
def relatorio_completo(pedidos_path: str, itens_path: str | None = None):

    print()
    print(f"  {BOLD}{WHITE}DIAGNÓSTICO DE QUALIDADE DE DADOS{RESET}")
    arqs = "pedidos.csv"
    if itens_path:
        arqs += "  |  itens_pedido.csv"
    print(f"  Arquivos: {arqs}")

    pedidos = pd.read_csv(pedidos_path, parse_dates=["data_pedido"])
    itens = pd.read_csv(itens_path) if itens_path else None

    # ── RESUMO GERAL ──────────────────────────────────────────────────────────
    print(sec("RESUMO GERAL"))
    print()

    total_pedidos = len(pedidos)
    periodo_inicio = pedidos["data_pedido"].min()
    periodo_fim = pedidos["data_pedido"].max()
    receita_total = pedidos["valor_total"].sum()
    pedidos_com_valor = pedidos["valor_total"].notna().sum()
    ticket_medio = receita_total / pedidos_com_valor if pedidos_com_valor > 0 else 0

    print(
        lbl(
            "Período",
            f"{periodo_inicio.strftime('%Y-%m-%d')} → {periodo_fim.strftime('%Y-%m-%d')}",
        )
    )
    print(lbl("Total pedidos", f"{total_pedidos:,}"))
    print(lbl("Receita total", f"R$ {receita_total:,.2f}"))
    print(lbl("Ticket médio", f"R$ {ticket_medio:,.2f}"))

    # ── 1. VALORES NULOS ──────────────────────────────────────────────────────
    print(sec("1. VALORES NULOS"))
    print()

    nulos = pedidos.isnull().sum()
    nulos_col = nulos[nulos > 0]

    if nulos_col.empty:
        print(ok("pedidos: sem nulos"))
    else:
        for col, n in nulos_col.items():
            pct = n / total_pedidos * 100
            print(err(f"pedidos.{col}: {n} nulos ({pct:.1f}%)"))

    if itens is not None:
        nulos_itens = itens.isnull().sum().sum()
        if nulos_itens == 0:
            print(ok("itens_pedido: sem nulos"))
        else:
            print(err(f"itens_pedido: {nulos_itens} valores nulos"))

    # ── 2. DUPLICATAS ─────────────────────────────────────────────────────────
    print(sec("2. DUPLICATAS"))
    print()

    dup_ped = pedidos.duplicated(subset=["pedido_id"]).sum()
    if dup_ped > 0:
        print(err(f"pedidos: {dup_ped} pedido_id duplicados!"))
    else:
        print(ok("pedidos: sem pedido_id duplicado"))

    if itens is not None and "item_id" in itens.columns:
        dup_it = itens.duplicated(subset=["item_id"]).sum()
        if dup_it > 0:
            print(err(f"itens: {dup_it} item_id duplicados!"))
        else:
            print(ok("itens: sem item_id duplicado"))

    # ── 3. LACUNAS DE DIAS ────────────────────────────────────────────────────
    print(sec("3. LACUNAS DE DIAS (dias sem nenhum pedido)"))
    print()

    datas_esp = pd.date_range(
        start=pedidos["data_pedido"].min(), end=pedidos["data_pedido"].max()
    )
    datas_real = set(
        pd.to_datetime(pedidos["data_pedido"].dt.normalize().unique()).date
    )
    faltantes = sorted(set(datas_esp.date) - datas_real)

    if not faltantes:
        print(ok("Nenhuma lacuna encontrada"))
    else:
        intervalos, ini, fim = [], faltantes[0], faltantes[0]
        for d in faltantes[1:]:
            if d == fim + timedelta(days=1):
                fim = d
            else:
                intervalos.append((ini, fim))
                ini = fim = d
        intervalos.append((ini, fim))

        print(
            warn(f"{len(faltantes)} dias sem pedidos → {len(intervalos)} intervalo(s):")
        )
        for i, f in intervalos:
            dias = (f - i).days + 1
            print(f"      • {i} → {f} ({dias} dias)")

    # ── 4. MESES COM VOLUME ANÔMALO ───────────────────────────────────────────
    print(sec("4. MESES COM VOLUME ANÔMALO"))

    pedidos["_mes"] = pedidos["data_pedido"].dt.to_period("M")
    pedidos["_ano"] = pedidos["data_pedido"].dt.year
    pedidos["_num_mes"] = pedidos["data_pedido"].dt.month

    mensal = (
        pedidos.groupby(["_ano", "_num_mes", "_mes"])
        .agg(qtd=("pedido_id", "count"), receita=("valor_total", "sum"))
        .reset_index()
        .sort_values(["_ano", "_num_mes"])
    )

    mid = mensal.iloc[1:-1]
    media = mid["qtd"].mean()
    std = mid["qtd"].std()

    print(f"\n  Média mensal de pedidos (meses completos): {media:.0f} ± {std:.0f}\n")

    for _, row in mensal.iterrows():
        z = (row["qtd"] - media) / std if std > 0 else 0
        mes = str(row["_mes"])
        qtd = int(row["qtd"])
        rec = row["receita"]

        sufixo = ""
        if abs(z) >= 2.0:
            sufixo = f"  {RED}← ANOMALIA (z={z:+.1f}){RESET}"
        elif abs(z) >= 1.8:
            sufixo = f"  {YELLOW}← atenção (z={z:+.1f}){RESET}"

        print(f"  {mes}  |  {qtd:>4} pedidos  |  R$ {rec:>14,.2f}{sufixo}")

    # ── 5. CONSISTÊNCIA ENTRE TABELAS ─────────────────────────────────────────
    if itens is not None:
        print(sec("5. CONSISTÊNCIA ENTRE TABELAS"))
        print()

        ped_ids = set(pedidos["pedido_id"])
        it_ids = set(itens["pedido_id"]) if "pedido_id" in itens.columns else set()

        orfaos = it_ids - ped_ids
        sem_item = ped_ids - it_ids

        print(
            err(f"{len(orfaos)} itens sem pedido correspondente")
            if orfaos
            else ok("Todos os itens têm pedido correspondente")
        )
        print(
            err(f"{len(sem_item)} pedidos sem nenhum item")
            if sem_item
            else ok("Todos os pedidos têm ao menos um item")
        )

        # calcula subtotal como quantidade * preco_unitario
        if "quantidade" in itens.columns and "preco_unitario" in itens.columns:
            itens["subtotal"] = itens["quantidade"] * itens["preco_unitario"]

        if "subtotal" in itens.columns:
            sub = itens.groupby("pedido_id", as_index=False)["subtotal"].sum()
            ped_uniq = pedidos.drop_duplicates(subset=["pedido_id"])[
                ["pedido_id", "valor_total"]
            ]
            mg = ped_uniq.merge(sub, on="pedido_id", how="inner")
            mg["diff"] = (mg["valor_total"] - mg["subtotal"]).abs()
            div = mg[mg["diff"] > 1.0].sort_values("pedido_id").reset_index(drop=True)

            if div.empty:
                print(ok("Nenhuma divergência de valor entre pedidos e itens"))
            else:
                print(
                    warn(
                        f"{len(div)} pedidos com valor_total divergente da soma dos "
                        "itens (possível frete/desconto ou erro):"
                    )
                )
                print(
                    f"  {'pedido_id':<12}  {'valor_total':>12}  {'subtotal':>12}  {'diff':>10}"
                )
                for _, r in div.head(10).iterrows():
                    pid = int(r["pedido_id"])
                    print(
                        f"  {str(pid):<12}  {r['valor_total']:>12,.2f}  "
                        f"{r['subtotal']:>12,.2f}  {r['diff']:>10,.2f}"
                    )
                if len(div) > 10:
                    print(f"  {DIM}... e mais {len(div)-10} pedidos{RESET}")

    print(f"\n  {DIM}Diagnóstico concluído.{RESET}\n")

    # ── INVESTIGAÇÃO AUTOMÁTICA DE ANOMALIAS ──────────────────────────────────


def investigar_anomalias(pedidos_path):
    print("\n=== INVESTIGAÇÃO AUTOMÁTICA DE ANOMALIAS ===\n")

    pedidos = pd.read_csv(pedidos_path, parse_dates=["data_pedido"])

    pedidos["mes"] = pedidos["data_pedido"].dt.to_period("M")
    pedidos["ano"] = pedidos["data_pedido"].dt.year
    pedidos["num_mes"] = pedidos["data_pedido"].dt.month

    mensal = (
        pedidos.groupby(["ano", "num_mes", "mes"])
        .agg(qtd_pedidos=("pedido_id", "count"))
        .reset_index()
    )

    # Ignora primeiro e último mês
    mensal_mid = mensal.iloc[1:-1]

    media = mensal_mid["qtd_pedidos"].mean()
    std = mensal_mid["qtd_pedidos"].std()

    print(f"Média mensal: {media:.0f} ± {std:.0f}\n")

    for _, row in mensal.iterrows():
        z = (row["qtd_pedidos"] - media) / std if std > 0 else 0

        if abs(z) >= 2:
            print("=" * 60)
            print(f"🚨 ANOMALIA DETECTADA: {row['mes']}")
            print(f"Pedidos no mês: {row['qtd_pedidos']} (z={z:+.2f})")

            ano = row["ano"]
            mes = row["num_mes"]

            df_mes = pedidos[(pedidos["ano"] == ano) & (pedidos["num_mes"] == mes)]

            dias_existentes = sorted(df_mes["data_pedido"].dt.day.unique())
            total_dias_mes = calendar.monthrange(ano, mes)[1]

            cobertura = len(dias_existentes) / total_dias_mes * 100

            print(f"Dias com pedido: {len(dias_existentes)} de {total_dias_mes}")
            print(f"Cobertura do mês: {cobertura:.1f}%")

            if cobertura < 50:
                print("⚠️ Provavelmente mês incompleto (carga parcial de dados)")
            else:
                print("⚠️ Queda real de volume — investigar negócio")

    print("\nInvestigação concluída.\n")


if __name__ == "__main__":
    investigar_anomalias("pedidos.csv")

# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    pedidos_path = sys.argv[1] if len(sys.argv) > 1 else "pedidos.csv"
    itens_path = sys.argv[2] if len(sys.argv) > 2 else None
    relatorio_completo(pedidos_path, itens_path)
