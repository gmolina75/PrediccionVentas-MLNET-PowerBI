using System.Globalization;
using System.Text;
using Microsoft.ML;
using Microsoft.ML.Data;

namespace VentasPredictor;

public class SalesRecord
{
    [LoadColumn(0)] public string FechaVenta { get; set; } = "";
    [LoadColumn(1)] public float Anio { get; set; }
    [LoadColumn(2)] public float Mes { get; set; }
    [LoadColumn(3)] public float Dia { get; set; }
    [LoadColumn(4)] public float DiaSemana { get; set; }
    [LoadColumn(5)] public float SemanaAnio { get; set; }
    [LoadColumn(6)] public float Trimestre { get; set; }
    [LoadColumn(7)] public float DiaAnio { get; set; }
    [LoadColumn(8)] public float EsFinDeSemana { get; set; }
    [LoadColumn(9)] public float EsPromo { get; set; }
    [LoadColumn(10)] public string CodigoProducto { get; set; } = "";
    [LoadColumn(11)] public string Categoria { get; set; } = "";
    [LoadColumn(12)] public string Vendedor { get; set; } = "";
    [LoadColumn(13)] public string Bodega { get; set; } = "";
    [LoadColumn(14)] public string Zona { get; set; } = "";
    [LoadColumn(15)] public float PrecioUnitario { get; set; }
    [LoadColumn(16)] public float Descuento { get; set; }
    [LoadColumn(17)] public float TotalVenta { get; set; }
}

public class FutureRecord
{
    [LoadColumn(0)] public string FechaVenta { get; set; } = "";
    [LoadColumn(1)] public float Anio { get; set; }
    [LoadColumn(2)] public float Mes { get; set; }
    [LoadColumn(3)] public float Dia { get; set; }
    [LoadColumn(4)] public float DiaSemana { get; set; }
    [LoadColumn(5)] public float SemanaAnio { get; set; }
    [LoadColumn(6)] public float Trimestre { get; set; }
    [LoadColumn(7)] public float DiaAnio { get; set; }
    [LoadColumn(8)] public float EsFinDeSemana { get; set; }
    [LoadColumn(9)] public float EsPromo { get; set; }
    [LoadColumn(10)] public string CodigoProducto { get; set; } = "";
    [LoadColumn(11)] public string Categoria { get; set; } = "";
    [LoadColumn(12)] public string Vendedor { get; set; } = "";
    [LoadColumn(13)] public string Bodega { get; set; } = "";
    [LoadColumn(14)] public string Zona { get; set; } = "";
    [LoadColumn(15)] public float PrecioUnitario { get; set; }
    [LoadColumn(16)] public float Descuento { get; set; }
    [LoadColumn(17)] public float TotalVenta { get; set; } // placeholder, will be ignored
}

public class Prediction
{
    [ColumnName("Score")]
    public float PredictedSales { get; set; }
}

class Program
{
    static void Main(string[] args)
    {
        var mlContext = new MLContext(seed: 42);
        string basePath = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", ".."));
        string trainPath = Path.Combine(basePath, "data", "ventas_train.csv");
        string testPath = Path.Combine(basePath, "data", "ventas_test.csv");
        string futurePath = Path.Combine(basePath, "data", "ventas_futuro_features.csv");
        string modelPath = Path.Combine(basePath, "modelo_mlnet", "modelo_ventas.zip");
        string metricsPath = Path.Combine(basePath, "modelo_mlnet", "metricas.json");
        string testPredPath = Path.Combine(basePath, "data", "predicciones_test.csv");
        string futurePredPath = Path.Combine(basePath, "data", "predicciones_futuro.csv");

        Console.WriteLine("Cargando datos de entrenamiento...");
        var trainData = mlContext.Data.LoadFromTextFile<SalesRecord>(trainPath, separatorChar: ',', hasHeader: true);
        var testData = mlContext.Data.LoadFromTextFile<SalesRecord>(testPath, separatorChar: ',', hasHeader: true);
        var futureData = mlContext.Data.LoadFromTextFile<FutureRecord>(futurePath, separatorChar: ',', hasHeader: true);

        Console.WriteLine("Construyendo pipeline...");
        var pipeline = mlContext.Transforms.CopyColumns("Label", "TotalVenta")
            .Append(mlContext.Transforms.Categorical.OneHotEncoding("CodigoProductoEncoded", "CodigoProducto"))
            .Append(mlContext.Transforms.Categorical.OneHotEncoding("CategoriaEncoded", "Categoria"))
            .Append(mlContext.Transforms.Categorical.OneHotEncoding("VendedorEncoded", "Vendedor"))
            .Append(mlContext.Transforms.Categorical.OneHotEncoding("BodegaEncoded", "Bodega"))
            .Append(mlContext.Transforms.Categorical.OneHotEncoding("ZonaEncoded", "Zona"))
            .Append(mlContext.Transforms.Concatenate("Features",
                "Anio", "Mes", "Dia", "DiaSemana", "SemanaAnio", "Trimestre", "DiaAnio",
                "EsFinDeSemana", "EsPromo", "PrecioUnitario", "Descuento",
                "CodigoProductoEncoded", "CategoriaEncoded", "VendedorEncoded", "BodegaEncoded", "ZonaEncoded"))
            .Append(mlContext.Regression.Trainers.FastTree(
                labelColumnName: "Label",
                featureColumnName: "Features",
                numberOfLeaves: 20,
                numberOfTrees: 100,
                minimumExampleCountPerLeaf: 10));

        Console.WriteLine("Entrenando modelo (puede tardar varios minutos)...");
        var model = pipeline.Fit(trainData);
        Console.WriteLine("Modelo entrenado. Guardando...");
        mlContext.Model.Save(model, trainData.Schema, modelPath);
        Console.WriteLine($"Modelo guardado en: {modelPath}");

        // Evaluar en test
        Console.WriteLine("Evaluando en conjunto de prueba...");
        var predictions = model.Transform(testData);
        var metrics = mlContext.Regression.Evaluate(predictions, labelColumnName: "Label", scoreColumnName: "Score");

        // Calcular MAPE manualmente
        var testEnumerable = mlContext.Data.CreateEnumerable<SalesRecord>(testData, reuseRowObject: false);
        var predEnumerable = mlContext.Data.CreateEnumerable<Prediction>(predictions, reuseRowObject: false);
        double mape = 0;
        int count = 0;
        foreach (var pair in testEnumerable.Zip(predEnumerable, (actual, pred) => new { Actual = actual.TotalVenta, Pred = pred.PredictedSales }))
        {
            if (pair.Actual != 0)
            {
                mape += Math.Abs((pair.Actual - pair.Pred) / pair.Actual);
                count++;
            }
        }
        mape = count > 0 ? (mape / count) * 100.0 : 0;

        Console.WriteLine($"MAE  : {metrics.MeanAbsoluteError:F4}");
        Console.WriteLine($"RMSE : {metrics.RootMeanSquaredError:F4}");
        Console.WriteLine($"R2   : {metrics.RSquared:F4}");
        Console.WriteLine($"MAPE : {mape:F4}%");

        // Guardar métricas
        var sb = new StringBuilder();
        sb.AppendLine("{");
        sb.AppendLine($"  \"MAE\": {metrics.MeanAbsoluteError.ToString(CultureInfo.InvariantCulture)},");
        sb.AppendLine($"  \"RMSE\": {metrics.RootMeanSquaredError.ToString(CultureInfo.InvariantCulture)},");
        sb.AppendLine($"  \"R2\": {metrics.RSquared.ToString(CultureInfo.InvariantCulture)},");
        sb.AppendLine($"  \"MAPE\": {mape.ToString(CultureInfo.InvariantCulture)}");
        sb.AppendLine("}");
        File.WriteAllText(metricsPath, sb.ToString());

        // Escribir predicciones de test
        Console.WriteLine("Generando predicciones de test...");
        WritePredictions(testEnumerable, predEnumerable, testPredPath, true);

        // Predicciones futuras
        Console.WriteLine("Generando predicciones futuras...");
        var futurePred = model.Transform(futureData);
        var futureEnumerable = mlContext.Data.CreateEnumerable<FutureRecord>(futureData, reuseRowObject: false);
        var futurePredEnumerable = mlContext.Data.CreateEnumerable<Prediction>(futurePred, reuseRowObject: false);
        WritePredictionsFuture(futureEnumerable, futurePredEnumerable, futurePredPath);

        Console.WriteLine("Proceso completado.");
    }

    static void WritePredictions(IEnumerable<SalesRecord> actuals, IEnumerable<Prediction> preds, string path, bool includeActual)
    {
        using var writer = new StreamWriter(path, false, Encoding.UTF8);
        writer.WriteLine("FechaVenta,CodigoProducto,Categoria,Vendedor,Bodega,Zona,RealSales,PredictedSales,AbsoluteError,PercentageError");
        foreach (var pair in actuals.Zip(preds, (a, p) => new { A = a, P = p }))
        {
            var a = pair.A;
            var pred = pair.P.PredictedSales;
            var absErr = Math.Abs(a.TotalVenta - pred);
            var pctErr = a.TotalVenta != 0 ? (absErr / a.TotalVenta) * 100.0 : 0;
            writer.WriteLine($"{a.FechaVenta},{a.CodigoProducto},{a.Categoria},{a.Vendedor},{a.Bodega},{a.Zona},{a.TotalVenta.ToString(CultureInfo.InvariantCulture)},{pred.ToString(CultureInfo.InvariantCulture)},{absErr.ToString(CultureInfo.InvariantCulture)},{pctErr.ToString(CultureInfo.InvariantCulture)}");
        }
    }

    static void WritePredictionsFuture(IEnumerable<FutureRecord> records, IEnumerable<Prediction> preds, string path)
    {
        using var writer = new StreamWriter(path, false, Encoding.UTF8);
        writer.WriteLine("FechaVenta,CodigoProducto,Categoria,Vendedor,Bodega,Zona,PredictedSales");
        foreach (var pair in records.Zip(preds, (a, p) => new { A = a, P = p }))
        {
            var a = pair.A;
            var pred = pair.P.PredictedSales;
            writer.WriteLine($"{a.FechaVenta},{a.CodigoProducto},{a.Categoria},{a.Vendedor},{a.Bodega},{a.Zona},{pred.ToString(CultureInfo.InvariantCulture)}");
        }
    }
}
