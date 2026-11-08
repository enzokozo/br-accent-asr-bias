"""Amostragem estratificada por sotaque.

Sorteia o mesmo número de áudios para cada sotaque, a partir do parquet
preparado na camada interim. A semente é fixa, para que todos do grupo e todos
os modelos usem exatamente os mesmos áudios.
"""

from datetime import datetime
import json
from pathlib import Path

import pandas as pd

INTERIM_DIR = Path(__file__).resolve().parents[1] / "data" / "interim" / "coraa"
RANDOM_STATE = 42


def stratified_sample(
    split: str = "test",
    n_per_accent: int = 50,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """Sorteia n_per_accent áudios de cada sotaque e salva o resultado.

    Saída: data/interim/coraa/coraa_{split}_sample_{n_per_accent}.parquet
    """
    source = INTERIM_DIR / f"coraa_{split}_prepared.parquet"
    df = pd.read_parquet(source)

    menor_grupo = df["accent"].value_counts().min()
    if n_per_accent > menor_grupo:
        raise ValueError(
            f"n_per_accent={n_per_accent} é maior que o menor grupo ({menor_grupo} áudios)"
        )

    sample = (
        df.groupby("accent", group_keys=False)
        .sample(n=n_per_accent, random_state=random_state)
        .reset_index(drop=True)
    )

    destination = INTERIM_DIR / f"coraa_{split}_sample_{n_per_accent}.parquet"
    sample.to_parquet(destination, index=False)
    _register_provenance(source, destination, n_per_accent, random_state, sample)
    return sample


def _register_provenance(source, destination, n_per_accent, random_state, sample):
    provenance_data = {
        "source_file": source.name,
        "target_file": destination.name,
        "n_per_accent": n_per_accent,
        "random_state": random_state,
        "rows": len(sample),
        "accents": sample["accent"].value_counts().to_dict(),
        "decisions": ["Amostragem estratificada: mesmo número de áudios por sotaque"],
        "sampled_at": datetime.now().isoformat(),
    }
    with (INTERIM_DIR / "proveniencia.jsonl").open("a", encoding="utf-8") as file:
        file.write(json.dumps(provenance_data, ensure_ascii=False) + "\n")
