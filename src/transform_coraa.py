"""Script de transformação e limpeza dos dados do CORAA ASR.

Lê os CSVs brutos da camada raw, filtra colunas essenciais,
aplica regras de qualidade (sotaque e tamanho da frase) e salva na camada interim.
"""

from datetime import datetime
import json
from pathlib import Path
import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "coraa"
INTERIM_DIR = Path(__file__).resolve().parents[1] / "data" / "interim" / "coraa"
SPLITS = ("dev", "test")
TARGET_COLUMNS = ["file_path", "variety", "accent", "text"]


def load_raw_data(split: str) -> Path:
    """Retorna o caminho do CSV bruto correspondente ao split."""
    file_path = RAW_DIR / f"metadata_{split}_final.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    return file_path


def clean_coraa_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra as colunas essenciais e aplica as regras de limpeza nos dados."""
    # Seleciona apenas as 4 colunas principais
    df_clean = df[TARGET_COLUMNS].copy()

    # Remove espaços em branco antes e depois dos textos
    for col in TARGET_COLUMNS:
        if df_clean[col].dtype == "object":
            df_clean[col] = df_clean[col].astype(str).str.strip()

    # Substitui strings vazias por NaN e remove nulos
    df_clean = df_clean.replace(r"^\s*$", pd.NA, regex=True)
    df_clean = df_clean.dropna(subset=TARGET_COLUMNS)

    # 1. Elimina valores "Misc." na coluna accent
    df_clean = df_clean[df_clean["accent"] != "Misc."]

    # 2. Filtra textos com mais de 3 palavras usando split()
    df_clean = df_clean[df_clean["text"].apply(lambda text: len(text.split()) > 3)]

    return df_clean


def save_interim_data(df: pd.DataFrame, split: str) -> Path:
    """Salva o DataFrame limpo na pasta interim em formato Parquet."""
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    destination = INTERIM_DIR / f"coraa_{split}_prepared.parquet"
    df.to_parquet(destination, index=False)
    return destination


def register_provenance(
    source_file: Path,
    target_file: Path,
    rows_before: int,
    rows_after: int,
) -> None:
    """Registra o histórico de transformação no arquivo proveniencia.jsonl."""
    provenance_data = {
        "source_file": source_file.name,
        "target_file": target_file.name,
        "rows_before": rows_before,
        "rows_after": rows_after,
        "removed_rows": rows_before - rows_after,
        "decisions": [
            "Seleção das colunas: file_path, variety, accent, text",
            "Remoção de espaços em branco (strip) e valores nulos",
            "Remoção dos registros com sotaque 'Misc.'",
            "Filtragem da coluna text para frases com mais de 3 palavras (split)",
            "Exportação para formato Parquet",
        ],
        "transformed_at": datetime.now().isoformat(),
    }

    provenance_file = INTERIM_DIR / "proveniencia.jsonl"
    with provenance_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(provenance_data, ensure_ascii=False) + "\n")


def transform_split(split: str) -> Path:
    """Executa o pipeline completo de transformação para um split (dev ou test)."""
    raw_path = load_raw_data(split)
    df_raw = pd.read_csv(raw_path)

    df_clean = clean_coraa_dataframe(df_raw)
    target_path = save_interim_data(df_clean, split)

    register_provenance(raw_path, target_path, len(df_raw), len(df_clean))
    return target_path


def transform_all() -> list[Path]:
    """Processa todos os splits disponíveis."""
    return [transform_split(split) for split in SPLITS]


if __name__ == "__main__":
    transform_all()