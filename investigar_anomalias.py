import pandas as pd
import calendar


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

    # ignora primeiro e último mês — costumam estar incompletos
    mensal_mid = mensal.iloc[1:-1]
    media = mensal_mid["qtd_pedidos"].mean()
    std = mensal_mid["qtd_pedidos"].std()

    print(f"Média mensal: {media:.0f} ± {std:.0f}\n")

    for _, row in mensal.iterrows():
        z = (row["qtd_pedidos"] - media) / std if std > 0 else 0

        if abs(z) < 2:
            continue

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
            print("⚠️  Mês incompleto — provavelmente carga parcial de dados")
        else:
            print("⚠️  Queda real de volume — investigar com o negócio")

    print("\nInvestigação concluída.\n")


if __name__ == "__main__":
    path = r"C:\Users\Usuário\OneDrive\Documentos\Projetos\Data-Quality-Analytics-Pipeline\pedidos.csv"
    investigar_anomalias(path)
