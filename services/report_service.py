"""Consultas e preparação dos dados usados nos relatórios administrativos."""


def build_daily_chart(daily_sales, daily_topups, datetime_module):
    """Combina vendas e recargas por dia e calcula alturas relativas dos gráficos."""
    daily = {}
    for row in daily_sales:
        day = str(row["dia"])
        daily[day] = {
            "dia": day, "compras": float(row["valor"] or 0), "recargas": 0.0,
            "compras_quantidade": int(row["quantidade"] or 0), "recargas_quantidade": 0,
        }
    for row in daily_topups:
        day = str(row["dia"])
        daily.setdefault(day, {"dia": day, "compras": 0.0, "recargas": 0.0,
                               "compras_quantidade": 0, "recargas_quantidade": 0})
        daily[day]["recargas"] = float(row["valor"] or 0)
        daily[day]["recargas_quantidade"] = int(row["quantidade"] or 0)

    chart_days = []
    for day in sorted(daily):
        item = daily[day]
        try:
            item["rotulo"] = datetime_module.strptime(day[:10], "%Y-%m-%d").strftime("%d/%m")
        except ValueError:
            item["rotulo"] = day[:10]
        chart_days.append(item)
    chart_max = max((max(item["compras"], item["recargas"]) for item in chart_days), default=0) or 1
    for item in chart_days:
        item["compras_altura"] = round(item["compras"] / chart_max * 100, 1)
        item["recargas_altura"] = round(item["recargas"] / chart_max * 100, 1)
    return chart_days, chart_max


def load_report_data(query_fn, movement_where, movement_params, purchase_where, purchase_params,
                     recent_where, recent_params, datetime_module):
    """Executa as consultas do relatório e devolve dados prontos para a rota renderizar."""
    sales = query_fn(
        "SELECT COUNT(*) AS quantidade, COALESCE(SUM(c.total), 0) AS valor "
        f"FROM compras c WHERE 1=1 {purchase_where}", tuple(purchase_params), one=True)
    topups = query_fn(
        "SELECT COALESCE(SUM(m.valor), 0) AS valor FROM movimentacoes m "
        f"WHERE m.operacao='recarga' AND m.status='confirmada' {movement_where}",
        tuple(movement_params), one=True)
    daily_sales = query_fn(
        "SELECT DATE(c.criado_em) AS dia, COUNT(*) AS quantidade, COALESCE(SUM(c.total), 0) AS valor "
        f"FROM compras c WHERE 1=1 {purchase_where} GROUP BY DATE(c.criado_em) "
        "ORDER BY DATE(c.criado_em) DESC LIMIT 31", tuple(purchase_params))
    daily_topups = query_fn(
        "SELECT DATE(m.criado_em) AS dia, COUNT(*) AS quantidade, COALESCE(SUM(m.valor), 0) AS valor "
        "FROM movimentacoes m "
        f"WHERE m.operacao='recarga' AND m.status='confirmada' {movement_where} "
        "GROUP BY DATE(m.criado_em) ORDER BY DATE(m.criado_em) DESC LIMIT 31", tuple(movement_params))
    movements = query_fn(
        "SELECT m.id, m.criado_em, u.nome AS cliente, m.operacao, m.status, m.valor "
        "FROM movimentacoes m JOIN usuarios u ON u.id=m.usuario_id "
        f"WHERE 1=1 {movement_where} {recent_where} "
        "ORDER BY m.criado_em DESC, m.id DESC LIMIT 500",
        tuple(movement_params + recent_params))
    negative_clients = query_fn(
        "SELECT u.nome, u.email, u.matricula, c.saldo FROM carteiras c "
        "JOIN usuarios u ON u.id=c.usuario_id "
        "WHERE u.perfil='cliente' AND c.saldo < 0 ORDER BY c.saldo ASC, u.nome ASC")
    chart_days, chart_max = build_daily_chart(daily_sales, daily_topups, datetime_module)
    return {
        "movimentacoes": movements,
        "resumo": {"compras_quantidade": int(sales["quantidade"] or 0),
                   "vendas_valor": float(sales["valor"] or 0),
                   "recargas_valor": float(topups["valor"] or 0)},
        "chart_days": chart_days,
        "chart_max": chart_max,
        "clientes_saldo_negativo": negative_clients,
        "total_saldo_negativo": sum(abs(float(row["saldo"] or 0)) for row in negative_clients),
    }
