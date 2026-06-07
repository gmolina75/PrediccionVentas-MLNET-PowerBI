#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crear_sqlite.py
===============
Crea una base de datos SQLite con las tablas de ejecución y detalle de predicciones,
compatibles con el esquema sugerido en la actividad académica.
"""

import csv
import json
import os
import sqlite3

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
DB_PATH = os.path.join(BASE_DIR, 'sqlite', 'ventas_prediccion.db')
TEST_PRED = os.path.join(BASE_DIR, 'data', 'predicciones_test.csv')
FUTURE_PRED = os.path.join(BASE_DIR, 'data', 'predicciones_futuro.csv')
METRICS_FILE = os.path.join(BASE_DIR, 'modelo_mlnet', 'metricas.json')


def ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def read_metrics():
    with open(METRICS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def init_db(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ML_SALES_FORECAST_RUN (
            RUN_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            MODEL_NAME TEXT NOT NULL,
            TRAINING_DATE TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            TRAIN_FROM_DATE TEXT,
            TRAIN_TO_DATE TEXT,
            TEST_FROM_DATE TEXT,
            TEST_TO_DATE TEXT,
            MAE REAL,
            RMSE REAL,
            R2 REAL,
            MAPE REAL,
            OBSERVATIONS_TRAIN INTEGER,
            OBSERVATIONS_TEST INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ML_SALES_FORECAST_DETAIL (
            FORECAST_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            RUN_ID INTEGER NOT NULL,
            FORECAST_DATE TEXT NOT NULL,
            PRODUCT_CODE TEXT,
            PRODUCT_NAME TEXT,
            CATEGORY_NAME TEXT,
            WAREHOUSE_NAME TEXT,
            ZONE_NAME TEXT,
            SALESMAN_NAME TEXT,
            REAL_SALES REAL,
            PREDICTED_SALES REAL NOT NULL,
            ABSOLUTE_ERROR REAL,
            PERCENTAGE_ERROR REAL,
            CREATED_AT TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (RUN_ID) REFERENCES ML_SALES_FORECAST_RUN(RUN_ID)
        )
    """)
    conn.commit()


def insert_run(conn):
    metrics = read_metrics()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ML_SALES_FORECAST_RUN
        (MODEL_NAME, TRAIN_FROM_DATE, TRAIN_TO_DATE, TEST_FROM_DATE, TEST_TO_DATE,
         MAE, RMSE, R2, MAPE, OBSERVATIONS_TRAIN, OBSERVATIONS_TEST)
        VALUES (?, '2021-01-01', '2024-08-06', '2024-08-07', '2024-12-31',
                ?, ?, ?, ?, 591300, 66150)
    """, ("FastTreeRegression", metrics['MAE'], metrics['RMSE'], metrics['R2'], metrics['MAPE']))
    conn.commit()
    return cur.lastrowid


def insert_details(conn, run_id, csv_path, has_real=True):
    cur = conn.cursor()
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        batch = []
        for r in reader:
            real_sales = float(r['RealSales']) if has_real and r.get('RealSales') != '' else None
            abs_err = float(r['AbsoluteError']) if has_real and r.get('AbsoluteError') != '' else None
            pct_err = float(r['PercentageError']) if has_real and r.get('PercentageError') != '' else None
            batch.append((
                run_id,
                r['FechaVenta'],
                r['CodigoProducto'],
                r['CodigoProducto'],
                r['Categoria'],
                r['Bodega'],
                r['Zona'],
                r['Vendedor'],
                real_sales,
                float(r['PredictedSales']),
                abs_err,
                pct_err
            ))
            if len(batch) >= 1000:
                cur.executemany("""
                    INSERT INTO ML_SALES_FORECAST_DETAIL
                    (RUN_ID, FORECAST_DATE, PRODUCT_CODE, PRODUCT_NAME, CATEGORY_NAME,
                     WAREHOUSE_NAME, ZONE_NAME, SALESMAN_NAME, REAL_SALES,
                     PREDICTED_SALES, ABSOLUTE_ERROR, PERCENTAGE_ERROR)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """, batch)
                batch.clear()
        if batch:
            cur.executemany("""
                INSERT INTO ML_SALES_FORECAST_DETAIL
                (RUN_ID, FORECAST_DATE, PRODUCT_CODE, PRODUCT_NAME, CATEGORY_NAME,
                 WAREHOUSE_NAME, ZONE_NAME, SALESMAN_NAME, REAL_SALES,
                 PREDICTED_SALES, ABSOLUTE_ERROR, PERCENTAGE_ERROR)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, batch)
    conn.commit()


def export_csvs(conn):
    cur = conn.cursor()
    # Exportar vista resumen por fecha
    cur.execute("""
        SELECT FORECAST_DATE,
               SUM(REAL_SALES) as REAL_SALES,
               SUM(PREDICTED_SALES) as PREDICTED_SALES,
               SUM(ABSOLUTE_ERROR) as ABSOLUTE_ERROR
        FROM ML_SALES_FORECAST_DETAIL
        WHERE REAL_SALES IS NOT NULL
        GROUP BY FORECAST_DATE
        ORDER BY FORECAST_DATE
    """)
    rows = cur.fetchall()
    out = os.path.join(BASE_DIR, 'data', 'resumen_test_diario.csv')
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['FechaVenta','RealSales','PredictedSales','AbsoluteError'])
        w.writerows(rows)
    # Exportar resumen futuro por fecha
    cur.execute("""
        SELECT FORECAST_DATE,
               SUM(PREDICTED_SALES) as PREDICTED_SALES
        FROM ML_SALES_FORECAST_DETAIL
        WHERE REAL_SALES IS NULL
        GROUP BY FORECAST_DATE
        ORDER BY FORECAST_DATE
    """)
    rows2 = cur.fetchall()
    out2 = os.path.join(BASE_DIR, 'data', 'resumen_futuro_diario.csv')
    with open(out2, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['FechaVenta','PredictedSales'])
        w.writerows(rows2)
    print(f'  Exportados resúmenes: {out}, {out2}')


def main():
    ensure_dir(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    print('Inicializando base de datos SQLite...')
    init_db(conn)
    print('Insertando ejecución del modelo...')
    run_id = insert_run(conn)
    print(f'  RUN_ID = {run_id}')
    print('Insertando predicciones de test...')
    insert_details(conn, run_id, TEST_PRED, has_real=True)
    print('Insertando predicciones futuras...')
    insert_details(conn, run_id, FUTURE_PRED, has_real=False)
    print('Exportando resúmenes CSV...')
    export_csvs(conn)
    conn.close()
    print(f'Base de datos creada: {DB_PATH}')


if __name__ == '__main__':
    main()
