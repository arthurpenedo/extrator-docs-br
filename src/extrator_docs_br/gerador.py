"""Gerador de documentos SINTÉTICOS (boleto, NF-e, comprovante Pix) com gabarito.

Nenhum dado real: CNPJ/CPF são números aleatórios com dígito verificador correto, nomes são inventados.
Cada documento tem variação de layout, rótulos e ruído, e "iscas" (números parecidos com CNPJ que
não passam no dígito verificador, CNPJ do pagador ao lado do beneficiário).
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta

from .validadores import (
    completar_chave_nfe,
    completar_cnpj,
    completar_cpf,
    fator_vencimento,
    montar_linha_digitavel,
)

EMPRESAS = ["Padaria Estrela Ltda", "Tech Sul Informática ME", "Doces da Vila EIRELI", "Mecânica Rápida SA",
            "Clínica Bem Viver Ltda", "Papelaria Central ME", "Auto Peças Norte Ltda", "Studio Luz Fotografia ME"]
PESSOAS = ["Maria Souza", "João Pereira", "Ana Lima", "Carlos Nunes", "Beatriz Rocha", "Pedro Alves"]
UFS = {"SP": "35", "RJ": "33", "MG": "31", "PR": "41", "RS": "43", "BA": "29"}


@dataclass
class Documento:
    tipo: str  # boleto | nfe | pix
    texto: str
    gabarito: dict[str, str]


def _cnpj(rng: random.Random, formatado: bool = True) -> str:
    base = "".join(str(rng.randint(0, 9)) for _ in range(8)) + "0001"
    n = completar_cnpj(base)
    return f"{n[:2]}.{n[2:5]}.{n[5:8]}/{n[8:12]}-{n[12:]}" if formatado else n


def _cpf(rng: random.Random) -> str:
    n = completar_cpf("".join(str(rng.randint(0, 9)) for _ in range(9)))
    return f"{n[:3]}.{n[3:6]}.{n[6:9]}-{n[9:]}"


def _cnpj_invalido(rng: random.Random) -> str:
    n = _cnpj(rng, formatado=False)
    errado = n[:13] + str((int(n[13]) + rng.randint(1, 9)) % 10)
    return f"{errado[:2]}.{errado[2:5]}.{errado[5:8]}/{errado[8:12]}-{errado[12:]}"


def _brl(valor_centavos: int, rng: random.Random) -> str:
    s = f"{valor_centavos // 100:,}".replace(",", ".") + f",{valor_centavos % 100:02d}"
    return rng.choice(["R$ " + s, "R$" + s, s])


def _valor_str(centavos: int) -> str:
    return f"{centavos // 100}.{centavos % 100:02d}"


def _data(d: date, rng: random.Random) -> str:
    return d.strftime(rng.choice(["%d/%m/%Y", "%d/%m/%Y", "%d-%m-%Y"]))


def _linha_formatada(linha: str, rng: random.Random) -> str:
    if rng.random() < 0.6:
        return f"{linha[:5]}.{linha[5:10]} {linha[10:15]}.{linha[15:21]} {linha[21:26]}.{linha[26:32]} {linha[32]} {linha[33:]}"
    return linha


def gerar_boleto(rng: random.Random) -> Documento:
    venc = date(2026, 1, 1) + timedelta(days=rng.randint(0, 700))
    centavos = rng.randint(1500, 9_999_999)
    livre = "".join(str(rng.randint(0, 9)) for _ in range(25))
    linha = montar_linha_digitavel(rng.choice(["001", "237", "341", "033", "104"]), "9",
                                   fator_vencimento(venc), centavos, livre)
    benef, pagador = _cnpj(rng), _cnpj(rng)
    isca = _cnpj_invalido(rng)
    rotulo_b = rng.choice(["Beneficiário", "Cedente", "BENEFICIÁRIO"])
    rotulo_v = rng.choice(["Vencimento", "Data de vencimento", "VENCIMENTO"])
    rotulo_val = rng.choice(["Valor do documento", "Valor cobrado", "VALOR"])
    linhas = [
        f"{rotulo_b}: {rng.choice(EMPRESAS)}  CNPJ {benef}",
        f"Pagador: {rng.choice(PESSOAS)}  CNPJ/CPF {pagador}",
        f"Nosso número: {rng.randint(10**7, 10**8 - 1)}  Protocolo {isca}",
        f"{rotulo_v}: {_data(venc, rng)}",
        f"{rotulo_val}: {_brl(centavos, rng)}",
        f"Linha digitável: {_linha_formatada(linha, rng)}",
    ]
    if rng.random() < 0.5:
        linhas.reverse()
    sep = rng.choice(["\n", "\n", "\n\n", "  |  "])
    return Documento("boleto", sep.join(linhas), {
        "cnpj_beneficiario": "".join(c for c in benef if c.isdigit()),
        "valor": _valor_str(centavos),
        "vencimento": venc.isoformat(),
        "linha_digitavel": linha,
    })


def gerar_nfe(rng: random.Random) -> Documento:
    emissao = date(2026, 1, 1) + timedelta(days=rng.randint(0, 700))
    centavos = rng.randint(2000, 99_999_999)
    emit = _cnpj(rng, formatado=False)
    uf = rng.choice(list(UFS.values()))
    base = (f"{uf}{emissao:%y%m}{emit}55{rng.randint(1, 9):03d}"
            f"{rng.randint(1, 999_999_999):09d}1{rng.randint(0, 99_999_999):08d}")
    chave = completar_chave_nfe(base)
    emit_fmt = f"{emit[:2]}.{emit[2:5]}.{emit[5:8]}/{emit[8:12]}-{emit[12:]}"
    chave_fmt = " ".join(chave[i:i + 4] for i in range(0, 44, 4)) if rng.random() < 0.6 else chave
    linhas = [
        "DANFE - Documento Auxiliar da Nota Fiscal Eletrônica",
        f"Emitente: {rng.choice(EMPRESAS)}  CNPJ: {emit_fmt}",
        f"Destinatário: {rng.choice(PESSOAS)}  CPF: {_cpf(rng)}",
        f"Data de emissão: {_data(emissao, rng)}",
        f"Valor total da nota: {_brl(centavos, rng)}",
        f"Chave de acesso: {chave_fmt}",
        f"Série 1  Número {rng.randint(1, 99999)}  Protocolo {_cnpj_invalido(rng)}",
    ]
    return Documento("nfe", rng.choice(["\n", "\n\n"]).join(linhas), {
        "chave_acesso": chave,
        "cnpj_emitente": emit,
        "valor": _valor_str(centavos),
        "data_emissao": emissao.isoformat(),
    })


def gerar_pix(rng: random.Random) -> Documento:
    dia = date(2026, 1, 1) + timedelta(days=rng.randint(0, 700))
    centavos = rng.randint(100, 5_000_000)
    pagador_cpf = _cpf(rng)
    recebedor_cnpj = _cnpj(rng)
    linhas = [
        "Comprovante de transferência Pix",
        f"Valor: {_brl(centavos, rng)}",
        f"Data: {_data(dia, rng)} às {rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}",
        f"Quem pagou: {rng.choice(PESSOAS)}  CPF {pagador_cpf}",
        f"Quem recebeu: {rng.choice(EMPRESAS)}  CNPJ {recebedor_cnpj}",
        f"ID da transação: E{rng.randint(10**30, 10**31 - 1)}",
    ]
    return Documento("pix", "\n".join(linhas), {
        "valor": _valor_str(centavos),
        "data": dia.isoformat(),
        "cpf_pagador": "".join(c for c in pagador_cpf if c.isdigit()),
        "cnpj_recebedor": "".join(c for c in recebedor_cnpj if c.isdigit()),
    })


GERADORES = {"boleto": gerar_boleto, "nfe": gerar_nfe, "pix": gerar_pix}


def gerar_corpus(por_tipo: int = 100, semente: int = 42) -> list[Documento]:
    rng = random.Random(semente)
    return [GERADORES[t](rng) for t in GERADORES for _ in range(por_tipo)]
