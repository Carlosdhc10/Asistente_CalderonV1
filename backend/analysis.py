import pandas as pd

def cargar_datos(ruta_csv: str) -> pd.DataFrame:
    df = pd.read_csv(ruta_csv, parse_dates=["fecha"])
    df.sort_values(by="fecha", inplace=True)
    return df

def calcular_indicadores(df: pd.DataFrame) -> dict:
    dias_sin_agua = df[df["valor"] == 0].shape[0]
    total_dias = df.shape[0]
    fiabilidad = (df["completo_mediciones"] >= df["completo_umbral"]).sum() / total_dias

    return {
        "total_dias": total_dias,
        "dias_sin_agua": dias_sin_agua,
        "porcentaje_sin_agua": dias_sin_agua / total_dias * 100,
        "fiabilidad": round(fiabilidad * 100, 2)
    }
