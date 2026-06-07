#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preparar_dataset.py  (Pure Python)
====================
Limpieza mínima, generación de variables temporales y partición 90/10 cronológica.

Entradas:
  data/ventas_historicas.csv
  data/ventas_futuro.csv

Salidas:
  data/ventas_train.csv
  data/ventas_test.csv
  data/ventas_futuro_features.csv
"""

import csv
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def week_of_year(d: datetime) -> int:
    # ISO week
    return int(d.strftime('%V'))


def process(input_csv: str, output_csv: str, is_future: bool = False):
    rows = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            d = datetime.strptime(r['FechaVenta'], '%Y-%m-%d')
            dow = d.weekday()  # 0=Lunes
            row = {
                'FechaVenta': r['FechaVenta'],
                'Anio': d.year,
                'Mes': d.month,
                'Dia': d.day,
                'DiaSemana': dow,
                'SemanaAnio': week_of_year(d),
                'Trimestre': (d.month - 1) // 3 + 1,
                'DiaAnio': d.timetuple().tm_yday,
                'EsFinDeSemana': 1 if dow >= 5 else 0,
                'EsPromo': int(r['EsPromo']),
                'CodigoProducto': r['CodigoProducto'],
                'Categoria': r['Categoria'],
                'Vendedor': r['Vendedor'],
                'Bodega': r['Bodega'],
                'Zona': r['Zona'],
                'PrecioUnitario': float(r['PrecioUnitario']),
                'Descuento': float(r['Descuento']),
                'TotalVenta': float(r['TotalVenta']) if r['TotalVenta'] != '' else 0.0
            }
            rows.append(row)
    # Ordenar por fecha, producto, bodega, vendedor
    rows.sort(key=lambda x: (x['FechaVenta'], x['CodigoProducto'], x['Bodega'], x['Vendedor']))
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return rows


def split_train_test(rows, train_path, test_path):
    # Partición 90/10 por fecha cronológica
    dates = sorted({r['FechaVenta'] for r in rows})
    n_train = int(len(dates) * 0.90)
    train_cutoff = dates[n_train - 1]
    train = [r for r in rows if r['FechaVenta'] <= train_cutoff]
    test = [r for r in rows if r['FechaVenta'] > train_cutoff]
    for path, subset in [(train_path, train), (test_path, test)]:
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=subset[0].keys())
            writer.writeheader()
            writer.writerows(subset)
    print(f'  Train: {len(train):,} filas (hasta {train_cutoff})')
    print(f'  Test : {len(test):,} filas (desde {dates[n_train]})')


def main():
    hist_in = os.path.join(DATA_DIR, 'ventas_historicas.csv')
    hist_proc = os.path.join(DATA_DIR, 'ventas_historicas_features.csv')
    print('Procesando histórico...')
    rows = process(hist_in, hist_proc, is_future=False)

    train_path = os.path.join(DATA_DIR, 'ventas_train.csv')
    test_path = os.path.join(DATA_DIR, 'ventas_test.csv')
    print('Particionando 90/10...')
    split_train_test(rows, train_path, test_path)

    fut_in = os.path.join(DATA_DIR, 'ventas_futuro.csv')
    fut_out = os.path.join(DATA_DIR, 'ventas_futuro_features.csv')
    print('Procesando futuro...')
    process(fut_in, fut_out, is_future=True)
    print('Listo.')


if __name__ == '__main__':
    main()
