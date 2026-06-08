# Predicción de Ventas con ML.NET y Dashboard Interactivo

[![.NET](https://img.shields.io/badge/.NET-8.0-blue)](https://dotnet.microsoft.com/)
[![ML.NET](https://img.shields.io/badge/ML.NET-5.0-green)](https://dotnet.microsoft.com/apps/machinelearning-ai/ml-dotnet)
[![Python](https://img.shields.io/badge/Python-3.x-yellow)](https://www.python.org/)

> Proyecto académico integrador de **Machine Learning**, **bases de datos relacionales** e **inteligencia de negocios** para la predicción de demanda comercial.

---

## Resumen Ejecutivo

Este repositorio contiene un pipeline completo de predicción de ventas que incluye:

- **Generación sintética** de datos transaccionales (4 años históricos + 1 año futuro).
- **Ingeniería de características** y partición temporal 90/10.
- **Modelo de regresión** entrenado con **ML.NET** (FastTree).
- **Evaluación** con métricas estándar: MAE, RMSE, R² y MAPE.
- **Persistencia** en SQLite y scripts para SQL Server.
- **Dashboard interactivo** en HTML con Chart.js.

| Métrica | Valor |
|---------|-------|
| **MAE** | 1.273,59 |
| **RMSE** | 1.971,88 |
| **R²** | **0,9681** |
| **MAPE** | **11,96 %** |

---

## Estructura del Proyecto

```
├── data/                          # Datasets generados
│   ├── ventas_historicas.csv      # Datos crudos (2021-2024)
│   ├── ventas_train.csv           # 90% entrenamiento
│   ├── ventas_test.csv            # 10% prueba
│   ├── predicciones_test.csv      # Resultados sobre test
│   ├── predicciones_futuro.csv    # Pronóstico 2025
│   └── ...
├── scripts/                       # Automatización Python (stdlib)
│   ├── generar_datos.py           # Generación sintética
│   ├── preparar_dataset.py        # ETL + features + split
│   ├── crear_sqlite.py            # Persistencia en BD
│   └── generar_dashboard.py       # Generador HTML
├── modelo_mlnet/                  # Proyecto C# + ML.NET
│   ├── Program.cs                 # Pipeline de entrenamiento
│   ├── VentasPredictor.csproj
│   └── modelo_ventas.zip          # Modelo serializado
├── sqlite/
│   └── ventas_prediccion.db       # Base de datos portable
├── sql/
│   └── schema.sql                 # DDL para SQL Server
├── dashboard/
│   └── dashboard.html             # Dashboard ejecutivo
└── docs/
    └── Proyecto_Prediccion_Ventas.md  # Documentación académica completa
```

---

## Cómo ejecutar

### 1. Requisitos
- [.NET 8 SDK](https://dotnet.microsoft.com/download)
- Python 3.x (solo stdlib, no requiere instalación de paquetes)
- Navegador web (para el dashboard)

### 2. Generar datos y entrenar modelo

```bash
# Generar datos sintéticos
cd scripts
python generar_datos.py
python preparar_dataset.py

# Entrenar modelo ML.NET
cd ../modelo_mlnet
dotnet run -c Release

# Crear base de datos SQLite y dashboard
cd ../scripts
python crear_sqlite.py
python generar_dashboard.py
```

### 3. Ver el dashboard
Abre `dashboard/dashboard.html` en tu navegador.

---

## Tecnologías Utilizadas

| Capa | Tecnología |
|------|------------|
| Lenguaje ML | C# / ML.NET 5.0 |
| Algoritmo | FastTree Regression |
| ETL & Datos | Python (stdlib) |
| Base de Datos | SQLite / SQL Server |
| Visualización | HTML + Chart.js |

---

## Autor

Proyecto académico desarrollado para la asignatura **Modelos de Datos / Inteligencia de Negocios**.

---

## Licencia

Uso exclusivo para fines educativos.
