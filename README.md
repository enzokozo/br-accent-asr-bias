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

```
.
├── data/
│   └── raw/          # Downloads originais das bases (não versionados)
├── .gitignore
├── README.md
└── requirements.txt
```

Esta seção é atualizada à medida que novas pastas são criadas.

## Dados

Os áudios não são versionados no repositório. Cada integrante baixa as bases localmente em `data/raw/`.