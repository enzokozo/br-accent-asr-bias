"""Normalização de texto para o cálculo da WER.

A mesma função é aplicada à transcrição de referência (CORAA) e à transcrição
gerada pelo modelo, para que diferenças de formatação (maiúsculas, pontuação,
números em algarismos) não sejam contadas como erro de reconhecimento.
"""

import re
import unicodedata

from num2words import num2words

# Números no formato brasileiro: 20, 1.500, 2,5, 1.500,75
_NUMBER_RE = re.compile(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?")
_ORDINAL_RE = re.compile(r"(\d+)\s*([ºª°])")
_PERCENT_RE = re.compile(r"(\d)\s*%")
_MONEY_RE = re.compile(r"r\$\s*([\d.,]+)")
# Qualquer caractere que não seja letra, dígito ou espaço
_PUNCT_RE = re.compile(r"[^\w\s]|_")
_SPACES_RE = re.compile(r"\s+")

# Convenções de transcrição específicas de um acervo, convertidas para a forma padrão.
# "nũ": forma reduzida de "não", usada apenas no C-ORAL Brasil (Minas Gerais).
_SPELLING_VARIANTS = {"nũ": "não"}


def _ordinal_to_words(match: re.Match) -> str:
    words = num2words(int(match.group(1)), lang="pt_BR", to="ordinal")
    if match.group(2) == "ª":  # feminino: primeiro -> primeira
        words = " ".join(w[:-1] + "a" if w.endswith("o") else w for w in words.split())
    return words


def _number_to_words(match: re.Match) -> str:
    inteiro, _, decimal = match.group(0).replace(".", "").partition(",")
    words = num2words(int(inteiro), lang="pt_BR")
    if decimal and int(decimal) != 0:
        words += " vírgula " + num2words(int(decimal), lang="pt_BR")
    return words


def numbers_to_words(text: str) -> str:
    """Escreve números por extenso: '20 anos' -> 'vinte anos'."""
    text = _MONEY_RE.sub(r"\1 reais", text)
    text = _PERCENT_RE.sub(r"\1 por cento", text)
    text = _ORDINAL_RE.sub(_ordinal_to_words, text)
    text = _NUMBER_RE.sub(_number_to_words, text)
    return text


def normalize(text: str) -> str:
    """Padroniza um texto para comparação.

    Passos:
    1. Normalização Unicode (NFC), para que letras acentuadas sejam comparáveis.
    2. Letras minúsculas.
    3. Números por extenso.
    4. Remoção de pontuação.
    5. Remoção de espaços repetidos.
    6. Conversão de grafias próprias de um acervo (ex.: "nũ" -> "não").

    Exemplo:
        >>> normalize("Eu moro há 20 anos, né?")
        'eu moro há vinte anos né'
    """
    if text is None:
        return ""
    text = unicodedata.normalize("NFC", str(text))
    text = text.lower()
    text = numbers_to_words(text)
    text = _PUNCT_RE.sub(" ", text)
    text = _SPACES_RE.sub(" ", text).strip()
    return " ".join(_SPELLING_VARIANTS.get(word, word) for word in text.split())
