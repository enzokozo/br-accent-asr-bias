"""Script de ingestão da base de dados CORAA.

Download dos dados brutos do CORAA ASR v1.1 para data/raw/coraa/ e registro de proveniência.
"""

from datetime import datetime
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import hf_hub_download

# Carrega as variáveis de ambiente do arquivo .env na raiz do projeto
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

REPO_ID = "gabrielrstan/CORAA-v1.1"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "coraa"
SPLITS = ("dev", "test")
HF_TOKEN = os.getenv("HF_TOKEN")


def _download(filename: str) -> Path:
    """Baixa um arquivo do repositório do CORAA para data/raw/coraa/."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    file_path = hf_hub_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        filename=filename,
        local_dir=OUTPUT_DIR,
        token=HF_TOKEN,  # Passa o token do Hugging Face
    )
    return Path(file_path)


def _check_split(split: str) -> None:
    if split not in SPLITS:
        raise ValueError(f"split deve ser um de {SPLITS}, recebido: {split!r}")


def download_metadata(split: str) -> Path:
    """Baixa o CSV de metadados e transcrições de um conjunto (dev ou test)."""
    _check_split(split)
    return _download(f"metadata_{split}_final.csv")


def download_audio(split: str) -> Path:
    """Baixa o .zip de áudios de um conjunto (dev ou test)."""
    _check_split(split)
    return _download(f"{split}.zip")


def register_provenance(downloaded_files: list[str]) -> Path:
    """Registra o histórico de extração no arquivo proveniencia.jsonl."""
    provenance_data = {
        "source": "CORAA ASR v1.1 (Hugging Face)",
        "repo_id": REPO_ID,
        "files": downloaded_files,
        "extracted_at": datetime.now().isoformat(),
        "description": "Dados brutos de áudio e metadados para avaliação de sotaques regionais em ASR",
    }

    provenance_file = OUTPUT_DIR / "proveniencia.jsonl"
    with provenance_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(provenance_data, ensure_ascii=False) + "\n")

    return provenance_file


def download_all() -> list[Path]:
    """Baixa todos os arquivos de dev e test e registra a proveniência."""
    downloaded_paths = []
    downloaded_filenames = []

    for split in SPLITS:
        metadata_path = download_metadata(split)
        audio_path = download_audio(split)

        downloaded_paths.extend([metadata_path, audio_path])
        downloaded_filenames.extend([metadata_path.name, audio_path.name])

    register_provenance(downloaded_filenames)
    return downloaded_paths