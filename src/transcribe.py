"""Transcrição automática dos áudios da amostra.

Lê os áudios diretamente de dentro do .zip baixado do CORAA (sem descompactar
tudo), passa cada um pelo modelo de ASR e salva o texto gerado na coluna
`hypothesis`.

O progresso é salvo a cada `save_every` áudios: se a execução for interrompida,
basta rodar de novo que os áudios já transcritos são pulados.
"""

import io
from pathlib import Path
import time
import zipfile

import librosa
import numpy as np
import pandas as pd
import soundfile as sf
import torch
from transformers import pipeline

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data" / "raw" / "coraa"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
TARGET_SR = 16_000  # taxa de amostragem esperada pelos modelos (16 kHz)

# Modelos usados no trabalho: nome curto -> identificador no Hugging Face
MODELS = {
    "whisper-small": "openai/whisper-small",
}


# Proteções contra alucinação do Whisper (laços como "é que é que é que..."):
# - NO_REPEAT_NGRAM: proíbe repetir qualquer sequência de 6 tokens. Laços curtos
#   são bloqueados, mas repetições naturais ("pode atender pode atender") passam.
# - Limite de tokens proporcional à duração do áudio: impede que o modelo gere
#   centenas de palavras para um áudio de 2 segundos.
NO_REPEAT_NGRAM = 6
TOKENS_PER_SECOND = 10
BASE_NEW_TOKENS = 20
MAX_NEW_TOKENS_CAP = 440  # limite do próprio Whisper é 448 tokens


def load_asr(model_name: str = "whisper-small"):
    """Carrega o modelo de ASR. Usa GPU se houver, senão CPU."""
    device = 0 if torch.cuda.is_available() else -1
    model_id = MODELS[model_name]
    asr = pipeline("automatic-speech-recognition", model=model_id, device=device)
    return asr, "whisper" in model_id


def _whisper_kwargs(audio: np.ndarray) -> dict:
    """Parâmetros de geração do Whisper para um áudio específico."""
    seconds = len(audio) / TARGET_SR
    max_tokens = int(BASE_NEW_TOKENS + TOKENS_PER_SECOND * seconds)
    return {
        "generate_kwargs": {
            "language": "portuguese",  # força português
            "task": "transcribe",      # transcrever, não traduzir
            "no_repeat_ngram_size": NO_REPEAT_NGRAM,
            "max_new_tokens": min(max_tokens, MAX_NEW_TOKENS_CAP),
        }
    }


def _zip_index(zip_file: zipfile.ZipFile) -> dict[str, str]:
    """Mapeia 'test/sp/arquivo.wav' -> caminho real dentro do zip."""
    index = {}
    for name in zip_file.namelist():
        if name.lower().endswith(".wav"):
            parts = Path(name).parts
            # Garante a correspondência mesmo se o zip tiver uma pasta extra na raiz
            for i in range(len(parts)):
                index.setdefault("/".join(parts[i:]), name)
    return index


def read_audio(zip_file: zipfile.ZipFile, inner_path: str) -> np.ndarray:
    """Lê um .wav de dentro do zip, converte para mono e 16 kHz."""
    with zip_file.open(inner_path) as file:
        audio, sr = sf.read(io.BytesIO(file.read()), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != TARGET_SR:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=TARGET_SR)
    return audio


def transcribe_sample(
    sample: pd.DataFrame,
    model_name: str = "whisper-small",
    split: str = "test",
    save_every: int = 20,
) -> pd.DataFrame:
    """Transcreve todos os áudios da amostra com o modelo escolhido.

    Saída: data/processed/transcricoes_{model_name}.parquet com as colunas
    originais + hypothesis, model e seconds (tempo de processamento).
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    destination = PROCESSED_DIR / f"transcricoes_{model_name}.parquet"

    # Retoma de onde parou, se já existir um arquivo parcial
    done = pd.read_parquet(destination) if destination.exists() else pd.DataFrame()
    done_paths = set(done["file_path"]) if not done.empty else set()
    pending = sample[~sample["file_path"].isin(done_paths)]
    print(f"{len(done_paths)} já transcritos, {len(pending)} pendentes.")
    if pending.empty:
        return done

    asr, is_whisper = load_asr(model_name)
    zip_path = RAW_DIR / f"{split}.zip"
    results = []

    with zipfile.ZipFile(zip_path) as zip_file:
        index = _zip_index(zip_file)

        for i, row in enumerate(pending.itertuples(index=False), start=1):
            inner_path = index.get(row.file_path)
            if inner_path is None:
                print(f"Áudio não encontrado no zip: {row.file_path}")
                continue

            audio = read_audio(zip_file, inner_path)
            start = time.perf_counter()
            kwargs = _whisper_kwargs(audio) if is_whisper else {}
            output = asr({"raw": audio, "sampling_rate": TARGET_SR}, **kwargs)
            elapsed = time.perf_counter() - start

            record = row._asdict()
            record.update(
                hypothesis=output["text"].strip(),
                model=model_name,
                seconds=round(elapsed, 2),
            )
            results.append(record)

            if i % save_every == 0 or i == len(pending):
                done = pd.concat([done, pd.DataFrame(results)], ignore_index=True)
                done.to_parquet(destination, index=False)
                results = []
                print(f"{i}/{len(pending)} transcritos (salvo em {destination.name})")

    return done
