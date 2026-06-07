#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generar_dashboard.py
====================
Genera un dashboard HTML estático con KPIs y gráficos de líneas/barras
usando Chart.js vía CDN.  No requiere librerías externas.

Entradas:
  data/predicciones_test.csv
  data/predicciones_futuro.csv
  data/resumen_test_diario.csv
  data/resumen_futuro_diario.csv
  modelo_mlnet/metricas.json

Salida:
  dashboard/dashboard.html
"""

import csv
import json
import os
from collections import defaultdict

BASE = os.path.join(os.path.dirname(__file__), '..')
OUT_HTML = os.path.join(BASE, 'dashboard', 'dashboard.html')


def read_csv(path):
    with open(path, 'r', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def read_metrics():
    with open(os.path.join(BASE, 'modelo_mlnet', 'metricas.json'), 'r', encoding='utf-8') as f:
        return json.load(f)


def fmt(n):
    return f"{n:,.2f}"


def main():
    metrics = read_metrics()
    test_rows = read_csv(os.path.join(BASE, 'data', 'predicciones_test.csv'))
    fut_rows = read_csv(os.path.join(BASE, 'data', 'predicciones_futuro.csv'))
    test_daily = read_csv(os.path.join(BASE, 'data', 'resumen_test_diario.csv'))
    fut_daily = read_csv(os.path.join(BASE, 'data', 'resumen_futuro_diario.csv'))

    # KPIs test
    total_real = sum(float(r['RealSales']) for r in test_rows)
    total_pred = sum(float(r['PredictedSales']) for r in test_rows)
    total_abs_err = sum(float(r['AbsoluteError']) for r in test_rows)
    diff = total_pred - total_real

    # Agregaciones para gráficos
    # 1) Test diario (ya agregado)
    test_dates = [r['FechaVenta'] for r in test_daily]
    test_real = [float(r['RealSales']) for r in test_daily]
    test_pred = [float(r['PredictedSales']) for r in test_daily]

    # 2) Futuro diario
    fut_dates = [r['FechaVenta'] for r in fut_daily]
    fut_pred = [float(r['PredictedSales']) for r in fut_daily]

    # 3) Por producto (test)
    prod_real = defaultdict(float)
    prod_pred = defaultdict(float)
    for r in test_rows:
        prod_real[r['CodigoProducto']] += float(r['RealSales'])
        prod_pred[r['CodigoProducto']] += float(r['PredictedSales'])
    prod_labels = sorted(prod_real.keys())
    prod_real_vals = [prod_real[p] for p in prod_labels]
    prod_pred_vals = [prod_pred[p] for p in prod_labels]

    # 4) Por categoría (test)
    cat_real = defaultdict(float)
    cat_pred = defaultdict(float)
    for r in test_rows:
        cat_real[r['Categoria']] += float(r['RealSales'])
        cat_pred[r['Categoria']] += float(r['PredictedSales'])
    cat_labels = sorted(cat_real.keys())
    cat_real_vals = [cat_real[c] for c in cat_labels]
    cat_pred_vals = [cat_pred[c] for c in cat_labels]

    # 5) Por zona (test)
    zone_real = defaultdict(float)
    zone_pred = defaultdict(float)
    for r in test_rows:
        zone_real[r['Zona']] += float(r['RealSales'])
        zone_pred[r['Zona']] += float(r['PredictedSales'])
    zone_labels = sorted(zone_real.keys())
    zone_real_vals = [zone_real[z] for z in zone_labels]
    zone_pred_vals = [zone_pred[z] for z in zone_labels]

    # 6) Futuro mensual
    fut_month = defaultdict(float)
    for r in fut_rows:
        m = r['FechaVenta'][:7]
        fut_month[m] += float(r['PredictedSales'])
    fut_month_labels = sorted(fut_month.keys())
    fut_month_vals = [fut_month[m] for m in fut_month_labels]

    # Helper para serializar listas JS
    def js_list(lst):
        return json.dumps(lst)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard - Predicción de Ventas ML.NET</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background:#f4f6f8; margin:0; padding:20px; color:#333; }}
  h1 {{ text-align:center; color:#1a237e; margin-bottom:10px; }}
  .subtitle {{ text-align:center; color:#555; margin-bottom:30px; }}
  .kpi-container {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(180px,1fr)); gap:15px; margin-bottom:30px; }}
  .kpi {{ background:#fff; border-radius:8px; padding:15px; box-shadow:0 2px 5px rgba(0,0,0,0.08); text-align:center; }}
  .kpi h3 {{ margin:0 0 8px; font-size:0.9rem; color:#666; text-transform:uppercase; }}
  .kpi .value {{ font-size:1.5rem; font-weight:bold; color:#1a237e; }}
  .grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(420px,1fr)); gap:20px; }}
  .chart-box {{ background:#fff; border-radius:8px; padding:15px; box-shadow:0 2px 5px rgba(0,0,0,0.08); }}
  .chart-box h2 {{ margin:0 0 10px; font-size:1.1rem; color:#333; }}
  canvas {{ max-height:300px; }}
  .footer {{ text-align:center; margin-top:30px; font-size:0.85rem; color:#888; }}
</style>
</head>
<body>
<h1>Dashboard Ejecutivo de Predicción de Ventas</h1>
<p class="subtitle">Modelo ML.NET (FastTree) | Período de prueba: ago-dic 2024 | Pronóstico 2025</p>

<div class="kpi-container">
  <div class="kpi"><h3>Venta Real (Test)</h3><div class="value">{fmt(total_real)}</div></div>
  <div class="kpi"><h3>Venta Predicha (Test)</h3><div class="value">{fmt(total_pred)}</div></div>
  <div class="kpi"><h3>Diferencia Absoluta</h3><div class="value">{fmt(diff)}</div></div>
  <div class="kpi"><h3>MAPE</h3><div class="value">{metrics['MAPE']:.2f}%</div></div>
  <div class="kpi"><h3>RMSE</h3><div class="value">{metrics['RMSE']:,.2f}</div></div>
  <div class="kpi"><h3>R²</h3><div class="value">{metrics['R2']:.4f}</div></div>
</div>

<div class="grid">
  <div class="chart-box">
    <h2>Real vs Predicho (Diario - Test)</h2>
    <canvas id="chartTestDaily"></canvas>
  </div>
  <div class="chart-box">
    <h2>Pronóstico Futuro 2025 (Diario)</h2>
    <canvas id="chartFutDaily"></canvas>
  </div>
  <div class="chart-box">
    <h2>Pronóstico 2025 (Mensual)</h2>
    <canvas id="chartFutMonth"></canvas>
  </div>
  <div class="chart-box">
    <h2>Ventas por Producto (Test)</h2>
    <canvas id="chartProduct"></canvas>
  </div>
  <div class="chart-box">
    <h2>Ventas por Categoría (Test)</h2>
    <canvas id="chartCategory"></canvas>
  </div>
  <div class="chart-box">
    <h2>Ventas por Zona (Test)</h2>
    <canvas id="chartZone"></canvas>
  </div>
</div>

<div class="footer">Generado automáticamente por pipeline ML.NET + Python | {os.path.basename(OUT_HTML)}</div>

<script>
const colors = {{
  real: 'rgba(25,118,210,0.7)',
  pred: 'rgba(255,143,0,0.7)',
  borderReal: 'rgba(25,118,210,1)',
  borderPred: 'rgba(255,143,0,1)'
}};

// 1) Test diario
new Chart(document.getElementById('chartTestDaily'), {{
  type: 'line',
  data: {{
    labels: {js_list(test_dates)},
    datasets: [
      {{ label: 'Real', data: {js_list(test_real)}, borderColor: colors.borderReal, backgroundColor: colors.real, fill:false, tension:0.3, pointRadius:1 }},
      {{ label: 'Predicho', data: {js_list(test_pred)}, borderColor: colors.borderPred, backgroundColor: colors.pred, fill:false, tension:0.3, pointRadius:1 }}
    ]
  }},
  options: {{ responsive:true, plugins:{{ legend:{{position:'top'}} }}, scales:{{ y:{{ beginAtZero:true }} }} }}
}});

// 2) Futuro diario
new Chart(document.getElementById('chartFutDaily'), {{
  type: 'line',
  data: {{
    labels: {js_list(fut_dates)},
    datasets: [
      {{ label: 'Predicho 2025', data: {js_list(fut_pred)}, borderColor: colors.borderPred, backgroundColor: colors.pred, fill:true, tension:0.3, pointRadius:1 }}
    ]
  }},
  options: {{ responsive:true, plugins:{{ legend:{{position:'top'}} }}, scales:{{ y:{{ beginAtZero:true }} }} }}
}});

// 3) Futuro mensual
new Chart(document.getElementById('chartFutMonth'), {{
  type: 'bar',
  data: {{
    labels: {js_list(fut_month_labels)},
    datasets: [
      {{ label: 'Predicho Mensual', data: {js_list(fut_month_vals)}, backgroundColor: colors.pred, borderColor: colors.borderPred, borderWidth:1 }}
    ]
  }},
  options: {{ responsive:true, plugins:{{ legend:{{display:false}} }}, scales:{{ y:{{ beginAtZero:true }} }} }}
}});

// 4) Producto
new Chart(document.getElementById('chartProduct'), {{
  type: 'bar',
  data: {{
    labels: {js_list(prod_labels)},
    datasets: [
      {{ label: 'Real', data: {js_list(prod_real_vals)}, backgroundColor: colors.real, borderColor: colors.borderReal, borderWidth:1 }},
      {{ label: 'Predicho', data: {js_list(prod_pred_vals)}, backgroundColor: colors.pred, borderColor: colors.borderPred, borderWidth:1 }}
    ]
  }},
  options: {{ responsive:true, plugins:{{ legend:{{position:'top'}} }}, scales:{{ y:{{ beginAtZero:true }} }} }}
}});

// 5) Categoría
new Chart(document.getElementById('chartCategory'), {{
  type: 'bar',
  data: {{
    labels: {js_list(cat_labels)},
    datasets: [
      {{ label: 'Real', data: {js_list(cat_real_vals)}, backgroundColor: colors.real, borderColor: colors.borderReal, borderWidth:1 }},
      {{ label: 'Predicho', data: {js_list(cat_pred_vals)}, backgroundColor: colors.pred, borderColor: colors.borderPred, borderWidth:1 }}
    ]
  }},
  options: {{ responsive:true, plugins:{{ legend:{{position:'top'}} }}, scales:{{ y:{{ beginAtZero:true }} }} }}
}});

// 6) Zona
new Chart(document.getElementById('chartZone'), {{
  type: 'bar',
  data: {{
    labels: {js_list(zone_labels)},
    datasets: [
      {{ label: 'Real', data: {js_list(zone_real_vals)}, backgroundColor: colors.real, borderColor: colors.borderReal, borderWidth:1 }},
      {{ label: 'Predicho', data: {js_list(zone_pred_vals)}, backgroundColor: colors.pred, borderColor: colors.borderPred, borderWidth:1 }}
    ]
  }},
  options: {{ responsive:true, plugins:{{ legend:{{position:'top'}} }}, scales:{{ y:{{ beginAtZero:true }} }} }}
}});
</script>
</body>
</html>
"""

    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    with open(OUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Dashboard generado: {OUT_HTML}')


if __name__ == '__main__':
    main()
