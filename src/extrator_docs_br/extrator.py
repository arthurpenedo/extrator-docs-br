"""Extração de campos por regex + validação determinística.

Dois modos, para medir quanto os validadores valem:
- `validar=False` (ingênuo): pega o primeiro padrão que parece o campo.
- `validar=True` (completo): usa o rótulo, exige dígito verificador válido e cruza valor/vencimento
  com a linha digitável do boleto (que é a fonte mais confiável).
"""
from __future__ import annotations

import re
from datetime import datetime

from .validadores import (
    chave_nfe_valida,
    cnpj_valido,
    cpf_valido,
    dados_linha_digitavel,
    linha_digitavel_valida,
    so_digitos,
)

RE_CNPJ = re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}")
RE_CPF = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
RE_LINHA = re.compile(r"\d{5}\.?\d{5} \d{5}\.?\d{6} \d{5}\.?\d{6} \d \d{14}|(?<!\d)\d{47}(?!\d)")
RE_CHAVE = re.compile(r"(?<!\d)(?:\d{4} ){10}\d{4}(?!\d)|(?<!\d)\d{44}(?!\d)")
RE_DATA = r"(\d{2}[/-]\d{2}[/-]\d{4})"
RE_VALOR = r"(?:R\$\s*)?(\d{1,3}(?:\.\d{3})*,\d{2})"


def detectar_tipo(texto: str) -> str:
    baixo = texto.lower()
    if "danfe" in baixo or "nota fiscal" in baixo:
        return "nfe"
    if "pix" in baixo:
        return "pix"
    return "boleto"


def _segmento_apos(texto: str, rotulos: str) -> str | None:
    """Trecho da linha (até quebra ou '|') que começa no rótulo."""
    m = re.search(rf"(?:{rotulos})[^\n|]*", texto, re.IGNORECASE)
    return m.group(0) if m else None


def _valor(texto: str, rotulo: str) -> str | None:
    m = re.search(rf"(?:{rotulo})[^:\n|]*:\s*{RE_VALOR}", texto, re.IGNORECASE)
    if not m:
        return None
    inteiro, centavos = m.group(1).replace(".", "").split(",")
    return f"{int(inteiro)}.{centavos}"


def _data(texto: str, rotulo: str) -> str | None:
    m = re.search(rf"(?:{rotulo})[^:\n|]*:\s*{RE_DATA}", texto, re.IGNORECASE)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1).replace("-", "/"), "%d/%m/%Y").date().isoformat()
    except ValueError:
        return None


def _doc_no_segmento(texto: str, rotulos: str, regex: re.Pattern, validador, validar: bool) -> str | None:
    seg = _segmento_apos(texto, rotulos)
    if seg is None:
        return None
    for m in regex.finditer(seg):
        if not validar or validador(m.group(0)):
            return so_digitos(m.group(0))
    return None


def _primeiro(texto: str, regex: re.Pattern) -> str | None:
    m = regex.search(texto)
    return so_digitos(m.group(0)) if m else None


def _boleto(texto: str, validar: bool) -> dict[str, str]:
    out: dict[str, str] = {}
    if validar:
        cnpj = _doc_no_segmento(texto, "benefici[aá]rio|cedente", RE_CNPJ, cnpj_valido, True)
    else:
        cnpj = _primeiro(texto, RE_CNPJ)
    if cnpj:
        out["cnpj_beneficiario"] = cnpj

    linha = None
    for m in RE_LINHA.finditer(texto):
        if not validar or linha_digitavel_valida(m.group(0)):
            linha = so_digitos(m.group(0))
            break
    if linha:
        out["linha_digitavel"] = linha

    valor = _valor(texto, "valor")
    venc = _data(texto, "vencimento")
    if validar and linha and linha_digitavel_valida(linha):
        valor_l, venc_l = dados_linha_digitavel(linha)
        valor, venc = valor_l, venc_l.isoformat()
    if valor:
        out["valor"] = valor
    if venc:
        out["vencimento"] = venc
    return out


def _nfe(texto: str, validar: bool) -> dict[str, str]:
    out: dict[str, str] = {}
    chave = None
    for m in RE_CHAVE.finditer(texto):
        if not validar or chave_nfe_valida(m.group(0)):
            chave = so_digitos(m.group(0))
            break
    if chave:
        out["chave_acesso"] = chave
    if validar:
        cnpj = _doc_no_segmento(texto, "emitente", RE_CNPJ, cnpj_valido, True)
        if cnpj is None and chave:  # a chave carrega o CNPJ do emitente nas posições 6 a 20
            cand = chave[6:20]
            cnpj = cand if cnpj_valido(cand) else None
    else:
        cnpj = _primeiro(texto, RE_CNPJ)
    if cnpj:
        out["cnpj_emitente"] = cnpj
    valor = _valor(texto, "valor total")
    emissao = _data(texto, "emiss[aã]o")
    if valor:
        out["valor"] = valor
    if emissao:
        out["data_emissao"] = emissao
    return out


def _pix(texto: str, validar: bool) -> dict[str, str]:
    out: dict[str, str] = {}
    valor = _valor(texto, "valor")
    data = _data(texto, "data")
    if valor:
        out["valor"] = valor
    if data:
        out["data"] = data
    if validar:
        cpf = _doc_no_segmento(texto, "quem pagou", RE_CPF, cpf_valido, True)
        cnpj = _doc_no_segmento(texto, "quem recebeu", RE_CNPJ, cnpj_valido, True)
    else:
        cpf, cnpj = _primeiro(texto, RE_CPF), _primeiro(texto, RE_CNPJ)
    if cpf:
        out["cpf_pagador"] = cpf
    if cnpj:
        out["cnpj_recebedor"] = cnpj
    return out


def extrair(texto: str, tipo: str | None = None, validar: bool = True) -> dict[str, str]:
    tipo = tipo or detectar_tipo(texto)
    return {"boleto": _boleto, "nfe": _nfe, "pix": _pix}[tipo](texto, validar)
