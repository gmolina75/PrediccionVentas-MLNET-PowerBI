#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generar_datos.py  (Pure Python)
==================
Genera datos sintéticos de ventas históricas y un período futuro.
No requiere librerías externas (solo stdlib).

Histórico: 2021-01-01 .. 2024-12-31  (4 años)
Futuro    : 2025-01-01 .. 2025-12-31  (1 año)
Dimensiones: 30 productos, 4 categorías, 5 vendedores, 3 bodegas, 3 zonas.
"""

import csv
import random
import math
from datetime import datetime, timedelta
import os

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(OUT_DIR, exist_ok=True)

# Catálogos
N_PRODUCTS = 30
N_CATEGORIES = 4
N_SALESMEN = 5
N_WAREHOUSES = 3
N_ZONES = 3

categories = [f'Categoria_{i+1}' for i in range(N_CATEGORIES)]
products = [f'PROD_{i+1:03d}' for i in range(N_PRODUCTS)]
product_category = {p: categories[i % N_CATEGORIES] for i, p in enumerate(products)}
product_base_price = {p: round(random.uniform(10.0, 200.0), 2) for p in products}
product_base_qty = {p: random.randint(20, 300) for p in products}

salesmen = [f'Vendedor_{i+1}' for i in range(N_SALESMEN)]
warehouses = [f'Bodega_{i+1}' for i in range(N_WAREHOUSES)]
zones = [f'Zona_{i+1}' for i in range(N_ZONES)]
warehouse_zone = {w: zones[i % N_ZONES] for i, w in enumerate(warehouses)}


def date_range(start: str, end: str):
    s = datetime.strptime(start, '%Y-%m-%d').date()
    e = datetime.strptime(end, '%Y-%m-%d').date()
    days = (e - s).days + 1
    return [s + timedelta(days=i) for i in range(days)]


def generate(rows_out: str, start: str, end: str, is_future: bool = False):
    dates = date_range(start, end)
    # Precalcular componentes por fecha
    date_info = []
    for d in dates:
        doy = d.timetuple().tm_yday
        year = d.year
        dow = d.weekday()  # 0=Lunes
        trend = 1.0 + (year - 2021) * 0.06
        annual = 1.0 + 0.25 * math.sin(2 * math.pi * (doy - 30) / 365.25)
        weekly = 1.0
        if dow == 4 or dow == 5:  # viernes, sábado
            weekly = 1.15
        elif dow == 0 or dow == 6:  # lunes, domingo
            weekly = 0.90
        promo = 1.30 if random.random() < 0.08 else 1.0
        base_temp = trend * annual * weekly * promo
        date_info.append({
            'date': d,
            'base_temp': base_temp,
            'promo': 1 if promo > 1 else 0
        })

    with open(rows_out, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'FechaVenta', 'CodigoProducto', 'NombreProducto', 'Categoria',
            'Vendedor', 'Bodega', 'Zona', 'CantidadVendida',
            'PrecioUnitario', 'Descuento', 'TotalVenta', 'EsPromo'
        ])
        writer.writeheader()
        total_rows = 0
        for info in date_info:
            d = info['date']
            base_temp = info['base_temp']
            es_promo = info['promo']
            for p in products:
                bp = product_base_price[p]
                bq = product_base_qty[p]
                for w in warehouses:
                    for v in salesmen:
                        if not is_future:
                            noise = random.lognormvariate(0.0, 0.10)
                            discount = round(random.uniform(0.0, 0.20), 2) if not es_promo else round(random.uniform(0.10, 0.30), 2)
                            eff_price = round(bp * (1 - discount), 2)
                            qty = max(0, int(round(bq * base_temp * noise * (1 + discount))))
                            total = round(qty * eff_price, 2)
                            row = {
                                'FechaVenta': d.strftime('%Y-%m-%d'),
                                'CodigoProducto': p,
                                'NombreProducto': f'Producto {p}',
                                'Categoria': product_category[p],
                                'Vendedor': v,
                                'Bodega': w,
                                'Zona': warehouse_zone[w],
                                'CantidadVendida': qty,
                                'PrecioUnitario': eff_price,
                                'Descuento': discount,
                                'TotalVenta': total,
                                'EsPromo': es_promo
                            }
                        else:
                            row = {
                                'FechaVenta': d.strftime('%Y-%m-%d'),
                                'CodigoProducto': p,
                                'NombreProducto': f'Producto {p}',
                                'Categoria': product_category[p],
                                'Vendedor': v,
                                'Bodega': w,
                                'Zona': warehouse_zone[w],
                                'CantidadVendida': '',
                                'PrecioUnitario': bp,
                                'Descuento': 0.0,
                                'TotalVenta': '',
                                'EsPromo': es_promo
                            }
                        writer.writerow(row)
                        total_rows += 1
        print(f'  -> {rows_out} ({total_rows:,} filas)')


def main():
    print('Generando datos históricos...')
    hist_path = os.path.join(OUT_DIR, 'ventas_historicas.csv')
    generate(hist_path, '2021-01-01', '2024-12-31', is_future=False)

    print('Generando período futuro...')
    fut_path = os.path.join(OUT_DIR, 'ventas_futuro.csv')
    generate(fut_path, '2025-01-01', '2025-12-31', is_future=True)

    # Guardar catálogo
    cat_path = os.path.join(OUT_DIR, 'catalogo_productos.csv')
    with open(cat_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['CodigoProducto', 'NombreProducto', 'Categoria', 'PrecioBase'])
        writer.writeheader()
        for p in products:
            writer.writerow({
                'CodigoProducto': p,
                'NombreProducto': f'Producto {p}',
                'Categoria': product_category[p],
                'PrecioBase': product_base_price[p]
            })
    print(f'  -> {cat_path}')
    print('Listo.')


if __name__ == '__main__':
    main()
