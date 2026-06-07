# Proyecto de Predicción de Ventas con ML.NET y Explotación Visual

## 1. Resumen Ejecutivo

Este proyecto integra **Machine Learning** (ML.NET), **ingeniería de datos** y **inteligencia de negocios** para construir un sistema predictivo de ventas. Se generó una fuente sintética de 657.450 registros transaccionales (4 años históricos), se entrenó un modelo de regresión supervisada con ML.NET, se reservó el 10 % cronológico para prueba y se proyectó la demanda para el año 2025. Los resultados se almacenaron en una base de datos relacional (SQLite) y se visualizaron mediante un dashboard HTML interactivo con KPIs ejecutivos.

**Resultado clave:**

| Métrica | Valor |
|---------|-------|
| MAE | 1.273,59 |
| RMSE | 1.971,88 |
| R² | 0,9681 |
| MAPE | 11,96 % |

El modelo explica ~96,8 % de la variabilidad de las ventas y presenta un error porcentual medio inferior al 12 %, nivel aceptable para planificación comercial y logística.

---

## 2. Contexto del Caso

Una empresa comercial de alcance nacional necesita migrar de reportes descriptivos a análisis predictivos. Las decisiones de inventario, abastecimiento y fuerza de ventas se basan hoy en intuición y promedios históricos. La dirección plantea las siguientes preguntas:

- ¿Cuál será la venta esperada para las próximas semanas o meses?
- ¿Qué productos o categorías tendrán mayor demanda proyectada?
- ¿Qué zonas, bodegas o vendedores presentan mejores proyecciones?
- ¿Qué tan confiable es el modelo frente a datos no observados?

La solución académica consiste en un pipeline completo: datos → modelo → base de datos → dashboard.

---

## 3. Objetivos

### Objetivo General
Desarrollar un proyecto aplicado de predicción de ventas utilizando ML.NET, a partir de una fuente histórica de ventas detalladas, reservando el último 10 % cronológico para prueba y publicando los resultados en una base de datos para su exploración visual.

### Objetivos Específicos
1. Preparar una fuente de datos histórica de ventas con estructura transaccional.
2. Realizar limpieza, transformación y generación de variables relevantes.
3. Entrenar un modelo de regresión supervisada con ML.NET.
4. Separar datos en entrenamiento y prueba respetando el orden temporal.
5. Evaluar el modelo con métricas de error y precisión.
6. Generar predicciones futuras (2025).
7. Persistir resultados en base de datos relacional.
8. Diseñar un dashboard con indicadores y comparativos real vs predicho.
9. Documentar conclusiones técnicas y comerciales.

---

## 4. Fuente de Datos

### 4.1 Generación Sintética
Dado que no se dispone de una base real anonimizada, se procedió a **simular** un universo transaccional representativo mediante un script en Python (`scripts/generar_datos.py`), garantizando reproducibilidad (`seed = 42`).

**Parámetros del escenario:**

| Dimensión | Cardinalidad |
|-----------|--------------|
| Productos | 30 |
| Categorías | 4 |
| Vendedores | 5 |
| Bodegas | 3 |
| Zonas | 3 |
| Período histórico | 2021-01-01 a 2024-12-31 (1.461 días) |
| Período futuro | 2025-01-01 a 2025-12-31 (365 días) |

**Comportamientos modelados en la generación:**

- **Tendencia:** crecimiento anual del ~6 %.
- **Estacionalidad anual:** pico en diciembre, valle en febrero (senoide desplazada).
- **Estacionalidad semanal:** incremento los viernes/sábados (+15 %) y caída los domingos/lunes (-10 %).
- **Promociones:** ~8 % de los días con evento promocional (+30 % de volumen y descuentos mayores).
- **Ruido:** multiplicador log-normal con σ = 0,10 (~10 % de coeficiente de variación).
- **Descuentos:** entre 0 % y 20 % (hasta 30 % en promociones), con efecto positivo en cantidad.

**Volumen resultante:**

- Histórico: **657.450 filas** (450 combinaciones × 1.461 días).
- Futuro: **164.250 filas** (450 combinaciones × 365 días).
- Venta total histórica simulada: **~9.615 millones** (moneda local).

### 4.2 Diccionario de Datos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| FechaVenta | Date | Fecha de la transacción. |
| CodigoProducto | String | Identificador único del producto. |
| NombreProducto | String | Descripción legible. |
| Categoria | String | Segmento comercial (4 valores). |
| Vendedor | String | Responsable de la venta. |
| Bodega | String | Punto de despacho. |
| Zona | String | Región geográfica derivada de bodega. |
| CantidadVendida | Integer | Unidades vendidas. |
| PrecioUnitario | Decimal | Precio efectivo post-descuento. |
| Descuento | Decimal | Porcentaje de descuento aplicado. |
| TotalVenta | Decimal | Variable objetivo (cantidad × precio). |
| EsPromo | Integer | Bandera de día promocional. |

---

## 5. Preparación de Datos (ETL y Feature Engineering)

El script `scripts/preparar_dataset.py` ejecuta las siguientes operaciones sin dependencias externas:

### 5.1 Limpieza
- Eliminación implícita de duplicados mediante estructura determinista de generación.
- Corrección de fechas nulas: no aplica por construcción.
- Tratamiento de ventas negativas: no se generan valores negativos.
- Outliers: controlados por el ruido log-normal acotado.

### 5.2 Variables Temporales
A partir de `FechaVenta` se derivan:

| Variable | Tipo | Descripción |
|----------|------|-------------|
| Anio | Entero | Año de la fecha. |
| Mes | Entero | Mes (1-12). |
| Dia | Entero | Día del mes. |
| DiaSemana | Entero | 0=Lunes, 6=Domingo. |
| SemanaAnio | Entero | Semana ISO. |
| Trimestre | Entero | 1-4. |
| DiaAnio | Entero | Día juliano. |
| EsFinDeSemana | Binario | 1 si sábado o domingo. |
| EsPromo | Binario | 1 si día promocional. |

### 5.3 Partición Entrenamiento / Prueba
Se ordenan los registros cronológicamente y se aplica la **regla metodológica obligatoria** del caso académico:

- **Entrenamiento:** primer 90 % de las fechas (hasta **2024-08-06**) → 591.300 filas.
- **Prueba:** último 10 % de las fechas (desde **2024-08-07**) → 66.150 filas.

Esta partición respeta la naturaleza temporal y evita filtraje de información futura.

---

## 6. Diseño del Modelo Predictivo en ML.NET

### 6.1 Elección de Herramienta
Se seleccionó **ML.NET 5.0** sobre **.NET 8** por ser el framework oficial de machine learning para la plataforma .NET, con capacidad de entrenamiento on-premise, serialización de modelos en ZIP e integración nativa con aplicaciones empresariales.

### 6.2 Algoritmo
**FastTreeRegression** (gradient boosting sobre árboles de regresión). Se eligió por:

- Alta capacidad de capturar interacciones no lineales entre variables categóricas y temporales.
- Buen desempeño con datasets tabulares de tamaño medio-grande.
- Soporte nativo en ML.NET sin dependencias de Python/R.

**Hiperparámetros configurados:**

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| NumberOfLeaves | 20 | Complejidad moderada para evitar sobreajuste. |
| NumberOfTrees | 100 | Suficiente para estabilizar el error de generalización. |
| MinimumExampleCountPerLeaf | 10 | Evita hojas con conteos extremadamente bajos. |

### 6.3 Pipeline de Transformaciones

```text
Copiar TotalVenta → Label
OneHotEncoding(CodigoProducto)   → CodigoProductoEncoded
OneHotEncoding(Categoria)        → CategoriaEncoded
OneHotEncoding(Vendedor)         → VendedorEncoded
OneHotEncoding(Bodega)           → BodegaEncoded
OneHotEncoding(Zona)             → ZonaEncoded
Concatenar(
  Anio, Mes, Dia, DiaSemana, SemanaAnio, Trimestre, DiaAnio,
  EsFinDeSemana, EsPromo, PrecioUnitario, Descuento,
  CodigoProductoEncoded, CategoriaEncoded, VendedorEncoded,
  BodegaEncoded, ZonaEncoded
) → Features
FastTreeRegression(Label, Features)
```

### 6.4 Entrenamiento y Serialización
El entrenamiento se ejecutó en modo Release desde la CLI de .NET:

```bash
cd modelo_mlnet
dotnet run -c Release
```

Duración aproximada: **~60 segundos** sobre el conjunto de 591.300 ejemplos. El modelo se serializó en `modelo_mlnet/modelo_ventas.zip` para su reutilización.

---

## 7. Evaluación del Modelo

### 7.1 Métricas Obtenidas (Conjunto de Prueba)

| Métrica | Fórmula | Resultado | Interpretación |
|---------|---------|-----------|----------------|
| **MAE** | mean(\|y - ŷ\|) | 1.273,59 | En promedio, el modelo se desvía ~1.274 unidades monetarias por transacción. |
| **RMSE** | sqrt(mean((y - ŷ)²)) | 1.971,88 | Penaliza errores grandes; indica dispersión moderada. |
| **R²** | 1 - SS_res/SS_tot | 0,9681 | El modelo explica el ~96,8 % de la varianza de las ventas. |
| **MAPE** | mean(\|y - ŷ\|/y)×100 | 11,96 % | Error porcentual medio; fácil de comunicar a la dirección comercial. |

### 7.2 Análisis de Error por Dimensión
Aunque el MAPE global es ~12 %, se recomienda segmentar el error por:
- **Producto:** artículos de bajo volumen suelen tener MAPE más alto (efecto de escala).
- **Zona/Bodega:** diferencias en estacionalidad regional no capturadas totalmente.
- **Promociones:** días con evento promocional pueden incrementar la varianza residual.

El dashboard incluye gráficos de barras por dimensión para identificar estos puntos de atención.

---

## 8. Predicción Futura (2025)

Se generaron predicciones para el año siguiente (365 días × 450 combinaciones = 164.250 filas). Como las variables de precio y descuento futuros no se conocen, se asumió:

- **PrecioUnitario:** precio base del catálogo (sin descuento).
- **Descuento:** 0 % en línea base; el modelo infiere el impacto del flag `EsPromo`.
- **TotalVenta:** calculada por el modelo en función de las features temporales y categóricas.

Los resultados se almacenaron en:
- `data/predicciones_futuro.csv`
- Tabla `ML_SALES_FORECAST_DETAIL` (filas con `REAL_SALES IS NULL`).

El análisis de la serie futura muestra una **continuidad de la tendencia creciente** y los picos estacionales esperados (diciembre, julio), validando la coherencia del modelo.

---

## 9. Persistencia en Base de Datos

### 9.1 SQLite (Entregable Portátil)
Se creó `sqlite/ventas_prediccion.db` con dos tablas trazables:

- **ML_SALES_FORECAST_RUN:** metadatos de la ejecución, hiperparámetros y métricas globales.
- **ML_SALES_FORECAST_DETAIL:** granularidad transaccional con real, predicho, error absoluto y error porcentual.

Además se generaron vistas resumen exportadas a CSV:
- `data/resumen_test_diario.csv`
- `data/resumen_futuro_diario.csv`

### 9.2 SQL Server (Script de Producción)
El archivo `sql/schema.sql` contiene el DDL equivalente para SQL Server, incluyendo:
- Llaves primarias y foráneas.
- Vistas `VW_FORECAST_DAILY_SUMMARY` y `VW_FORECAST_FUTURE_MONTHLY` listas para consumo desde Power BI.

---

## 10. Dashboard y KPIs

Se diseñó un dashboard HTML interactivo (`dashboard/dashboard.html`) con **6 visualizaciones** y **6 KPIs ejecutivos**. Utiliza Chart.js v4 (CDN) para renderizado ligero y responsivo.

### 10.1 KPIs Principales

| KPI | Valor (Test) | Uso Ejecutivo |
|-----|--------------|---------------|
| Venta Real (Test) | ~6,58 M diario promedio | Benchmark histórico. |
| Venta Predicha (Test) | Similar al real | Validación de calidad. |
| Diferencia Absoluta | Baja en relación al volumen | Alerta de sesgo. |
| MAPE | 11,96 % | Confianza del pronóstico. |
| RMSE | 1.971,88 | Magnitud del error cuadrático. |
| R² | 0,9681 | Capacidad explicativa. |

### 10.2 Gráficos Incluidos
1. **Real vs Predicho (Diario-Test):** línea temporal comparativa.
2. **Pronóstico Futuro 2025 (Diario):** tendencia proyectada.
3. **Pronóstico 2025 (Mensual):** barras mensuales para planificación.
4. **Ventas por Producto:** ranking real vs predicho.
5. **Ventas por Categoría:** comparativo de desempeño segmentado.
6. **Ventas por Zona:** análisis geográfico de proyecciones.

### 10.3 Uso desde Power BI
Si se prefiere Power BI, basta con:
1. Importar `sqlite/ventas_prediccion.db` mediante el conector ODBC de SQLite.
2. Cargar las vistas de resumen diario y mensual.
3. Replicar los mismos KPIs y gráficos descritos arriba.
4. Aplicar filtros de producto, categoría, zona y vendedor.

---

## 11. Estructura de Entregables

```text
ML.NET Predictivo Y PowerBI-Looker/
├── data/
│   ├── ventas_historicas.csv          # Datos crudos sintéticos
│   ├── ventas_futuro.csv              # Período futuro sin venta real
│   ├── ventas_train.csv               # 90 % para entrenamiento
│   ├── ventas_test.csv                # 10 % para prueba
│   ├── predicciones_test.csv          # Resultados del modelo sobre test
│   ├── predicciones_futuro.csv        # Pronóstico 2025
│   ├── resumen_test_diario.csv        # Agregado diario test
│   └── resumen_futuro_diario.csv      # Agregado diario futuro
├── scripts/
│   ├── generar_datos.py               # Generación sintética
│   ├── preparar_dataset.py            # ETL + features + split
│   ├── crear_sqlite.py                # Persistencia en BD
│   └── generar_dashboard.py           # Generador HTML
├── sql/
│   └── schema.sql                     # DDL SQL Server
├── sqlite/
│   └── ventas_prediccion.db           # Base SQLite portable
├── modelo_mlnet/
│   ├── VentasPredictor.csproj         # Proyecto .NET
│   ├── Program.cs                     # Pipeline ML.NET
│   └── modelo_ventas.zip              # Modelo serializado
├── dashboard/
│   └── dashboard.html                 # Dashboard interactivo
└── docs/
    └── Proyecto_Prediccion_Ventas.md  # Documento académico
```

---

## 12. Conclusiones y Recomendaciones

### Hallazgos Técnicos
- El modelo **FastTreeRegression** logró un **R² de 0,968** y un **MAPE de ~12 %**, lo cual valida que las variables temporales y categóricas seleccionadas explican adecuadamente el comportamiento de ventas.
- La partición cronológica 90/10 demostró ser robusta; no se observó filtraje de información futura ni sobreajuste extremo.
- El uso de `OneHotEncoding` para las dimensiones de negocio permitió al modelo diferenciar el efecto de cada producto, bodega y vendedor sin asumir ordinalidad.

### Hallazgos Comerciales
- La **estacionalidad anual** (picos en diciembre) y la **semanal** (viernes/sábado) son los factores más dominantes en la predicción.
- Las **promociones** generan incrementos significativos pero también elevan la varianza residual; se recomienda incluir variables de campaña (código de promoción, canal) en iteraciones futuras.
- El **pronóstico 2025** mantiene la tendencia de crecimiento, sugiriendo que la capacidad logística actual debería soportar la demanda, salvo picos puntuales que requieren planificación preventiva.

### Recomendaciones de Mejora
1. **Ingeniería de características avanzada:** agregar lags (venta día-7, día-14), medias móviles y ratios de crecimiento por producto.
2. **Ensemble:** combinar FastTree con LightGBM o SDCA para reducir el MAPE por debajo del 10 %.
3. **Datos externos:** incorporar calendario de feriados, eventos de marketing y variables macroeconómicas.
4. **Nivel de agregación:** evaluar predicción a nivel semanal para suavizar el ruido diario.
5. **Alertas automáticas:** integrar el modelo en un servicio .NET que genere alertas cuando el error de predicción diario supere un umbral configurable.

---

## 13. Anexos Técnicos

### A. Reproducibilidad
- Seed utilizado: `42`.
- Framework: ML.NET 5.0 sobre .NET 8.
- Entorno: Windows 10/11, CLI de .NET, Python 3.14 (solo stdlib).

### B. Notas sobre Rendimiento
- Entrenamiento: ~60 s para 591k filas y ~56 features.
- Predicción: ~5 s para 66k filas de test + 164k filas futuras.
- Consumo de memoria: < 1 GB en ejecución Release.

### C. Licencia de Uso Académico
Todo el código y los datos sintéticos generados en este proyecto son de uso exclusivo para fines educativos dentro del curso de Modelos de Datos / Inteligencia de Negocios.
