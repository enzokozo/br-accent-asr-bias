# Viés de reconhecimento de voz com sotaques brasileiros

Avaliação do desempenho de sistemas de transcrição automática de fala (ASR) entre variedades regionais do português brasileiro.

Trabalho final da disciplina **Informática e Sociedade**.

## Objetivo

Verificar se sistemas de reconhecimento automático de fala apresentam desempenho desigual entre grupos regionais de falantes. Para isso, serão usadas as bases públicas Common Voice e CORAA ASR, transcritas por modelos abertos, e a taxa de erro de palavra (WER) será comparada entre as regiões. Os resultados serão usados para discutir as implicações sociais do viés encontrado.

## Equipe

| Nome | Matrícula |
|---|---|
| Enzo Kozonoe | 2022010384 |
| Felipe Medeiros Loiola | 2024001188 |
| Lucas Maciel Gonçalves Aguiar | 2023001174 |
| Pedro Lucas Crisp | 2022003272 |
| Rafael Cardoso de Azevedo | 2022002918 |

## Configuração do ambiente

Requer **Python 3.11**.

```bash
git clone https://github.com/enzokozo/br-accent-asr-bias
cd br-accent-asr-bias

python -m venv .venv
```

Ative o ambiente virtual:

| Sistema | Comando |
|---|---|
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| Windows (CMD) | `.venv\Scripts\activate.bat` |
| Mac / Linux | `source .venv/bin/activate` |

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Estrutura do repositório

```text
br-accent-asr-bias/
├── data/
│   ├── raw/               # Dados brutos descarregados (CORAA ASR)
│   └── interim/           # Dados filtrados e preparados em formato Parquet
├── notebooks/             # Notebooks de execução e análise
│   └── 01_download_and_transform.ipynb
├── src/                   # Código fonte e módulos Python
│   ├── __init__.py
│   ├── download_coraa.py  # Ingestão e transferência de dados da Hugging Face
│   └── transform_coraa.py # Tratamento, filtragem e limpeza de dados
├── .env.example           # Modelo para variáveis de ambiente
├── .gitignore
├── requirements.txt       # Dependências do projeto
└── README.md
```

Esta seção é atualizada à medida que novas pastas são criadas.

## Pipeline de Dados
O tratamento de dados segue os princípios da Arquitetura Medallion:

1. **Camada Raw (Bronze)**: Transferência dos ficheiros brutos de áudio e metadados (metadata_dev_final.csv e metadata_test_final.csv) a partir do repositório CORAA v1.1.

2. **Camada Interim (Prata)**:

- Seleção das colunas essenciais (file_path, variety, accent, text).

- Escolha de amostras apenas em português do Brasil (pt_br)

- Remoção de amostras com sotaque indefinido (Misc.).

- Filtragem de frases curtas (mantidas apenas transcrições com mais de 3 palavras).

- Armazenamento otimizado em formato .parquet.

3. **Rastreabilidade**: Registo automático do histórico de extração e transformação em ficheiros proveniencia.jsonl.