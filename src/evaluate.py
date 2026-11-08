"""Cálculo da taxa de erro de palavra (WER) por áudio e por sotaque.

WER = (substituições + remoções + inserções) / número de palavras da referência

A WER de cada sotaque é calculada somando os erros de todos os áudios e
dividindo pelo total de palavras (WER de corpus), em vez de tirar a média das
WERs individuais, para que frases muito curtas não distorçam o resultado.
O intervalo de confiança de 95% é obtido por bootstrap.
"""

from pathlib import Path

import jiwer
import numpy as np
import pandas as pd

from src.normalize_text import normalize

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"


def score_utterances(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza os textos e conta os erros de cada áudio.

    Espera as colunas `text` (referência) e `hypothesis` (saída do modelo).
    Adiciona: ref_norm, hyp_norm, n_ref, substitutions, deletions,
    insertions, errors e wer.
    """
    df = df.copy()
    df["ref_norm"] = df["text"].apply(normalize)
    df["hyp_norm"] = df["hypothesis"].apply(normalize)

    counts = []
    for ref, hyp in zip(df["ref_norm"], df["hyp_norm"]):
        n_ref = len(ref.split())
        if not hyp:
            # Modelo não escreveu nada: todas as palavras contam como removidas
            counts.append((n_ref, 0, n_ref, 0))
            continue
        out = jiwer.process_words(ref, hyp)
        counts.append((n_ref, out.substitutions, out.deletions, out.insertions))

    df[["n_ref", "substitutions", "deletions", "insertions"]] = counts
    df["errors"] = df["substitutions"] + df["deletions"] + df["insertions"]
    df["wer"] = df["errors"] / df["n_ref"]
    # Alucinação: o modelo inventou mais palavras do que existem na referência
    # (ex.: laços "é que é que é que..." ou "até o próximo vídeo")
    df["alucinacao"] = df["insertions"] > df["n_ref"]
    return df


def _bootstrap_ci(errors: np.ndarray, n_ref: np.ndarray, n_boot: int, seed: int):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(errors), size=(n_boot, len(errors)))
    wers = errors[idx].sum(axis=1) / n_ref[idx].sum(axis=1)
    return np.percentile(wers, 2.5), np.percentile(wers, 97.5)


def wer_by_group(
    scored: pd.DataFrame,
    group_col: str = "accent",
    n_boot: int = 1000,
    seed: int = 42,
) -> pd.DataFrame:
    """Agrega a WER por grupo (sotaque), com intervalo de confiança de 95%.

    Também informa quantos áudios tiveram alucinação e a WER calculada sem
    eles (`wer_sem_alucinacao`), para mostrar o quanto esses casos pesam.
    """
    rows = []
    for group, g in scored.groupby(group_col):
        errors = g["errors"].to_numpy()
        n_ref = g["n_ref"].to_numpy()
        low, high = _bootstrap_ci(errors, n_ref, n_boot, seed)
        sem = g[~g["alucinacao"]]
        rows.append(
            {
                group_col: group,
                "n_audios": len(g),
                "n_palavras": int(n_ref.sum()),
                "wer": errors.sum() / n_ref.sum(),
                "ic95_inf": low,
                "ic95_sup": high,
                "n_alucinacoes": int(g["alucinacao"].sum()),
                "wer_sem_alucinacao": sem["errors"].sum() / sem["n_ref"].sum(),
                "substituicoes": int(g["substitutions"].sum()),
                "remocoes": int(g["deletions"].sum()),
                "insercoes": int(g["insertions"].sum()),
            }
        )
    return pd.DataFrame(rows).sort_values("wer", ascending=False).reset_index(drop=True)


def evaluate_model(transcriptions_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Lê as transcrições de um modelo, calcula a WER e salva os resultados.

    Saídas em results/:
    - wer_por_audio_{modelo}.csv
    - wer_por_sotaque_{modelo}.csv
    """
    df = pd.read_parquet(transcriptions_path)
    model_name = df["model"].iloc[0]

    scored = score_utterances(df)
    summary = wer_by_group(scored)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    scored.to_csv(RESULTS_DIR / f"wer_por_audio_{model_name}.csv", index=False)
    summary.to_csv(RESULTS_DIR / f"wer_por_sotaque_{model_name}.csv", index=False)
    return scored, summary
