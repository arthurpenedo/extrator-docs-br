"""Validadores determinísticos: dígitos verificadores de CNPJ, CPF, chave de NF-e e boleto."""
from __future__ import annotations

import re
from datetime import date, timedelta

BASE_FATOR = date(1997, 10, 7)


def so_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto)


def _dv_cnpj(base: str) -> str:
    pesos = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    digitos = ""
    for _ in range(2):
        soma = sum(int(d) * p for d, p in zip(base, pesos))
        resto = soma % 11
        dv = 0 if resto < 2 else 11 - resto
        digitos += str(dv)
        base += str(dv)
        pesos = [6] + pesos
    return digitos


def cnpj_valido(texto: str) -> bool:
    n = so_digitos(texto)
    if len(n) != 14 or len(set(n)) == 1:
        return False
    return n[12:] == _dv_cnpj(n[:12])


def completar_cnpj(base12: str) -> str:
    return base12 + _dv_cnpj(base12)


def _dv_cpf(base: str) -> str:
    digitos = ""
    for tamanho in (9, 10):
        soma = sum(int(d) * p for d, p in zip(base, range(tamanho + 1, 1, -1)))
        dv = (soma * 10 % 11) % 10
        digitos += str(dv)
        base += str(dv)
    return digitos


def cpf_valido(texto: str) -> bool:
    n = so_digitos(texto)
    if len(n) != 11 or len(set(n)) == 1:
        return False
    return n[9:] == _dv_cpf(n[:9])


def completar_cpf(base9: str) -> str:
    return base9 + _dv_cpf(base9)


def _mod11_chave(base43: str) -> str:
    soma = sum(int(d) * (2 + i % 8) for i, d in enumerate(reversed(base43)))
    resto = soma % 11
    return "0" if resto < 2 else str(11 - resto)


def chave_nfe_valida(texto: str) -> bool:
    n = so_digitos(texto)
    return len(n) == 44 and n[43] == _mod11_chave(n[:43])


def completar_chave_nfe(base43: str) -> str:
    return base43 + _mod11_chave(base43)


def _mod10(campo: str) -> str:
    soma = 0
    for i, d in enumerate(reversed(campo)):
        p = int(d) * (2 if i % 2 == 0 else 1)
        soma += p // 10 + p % 10
    return str((10 - soma % 10) % 10)


def _mod11_boleto(base43: str) -> str:
    soma = sum(int(d) * (2 + i % 8) for i, d in enumerate(reversed(base43)))
    dv = 11 - soma % 11
    return "1" if dv in (0, 10, 11) else str(dv)


def montar_linha_digitavel(banco: str, moeda: str, fator: int, valor_centavos: int, livre: str) -> str:
    """Monta a linha digitável (47 dígitos, sem pontuação) a partir dos campos do código de barras."""
    fv = f"{fator:04d}{valor_centavos:010d}"
    barras_sem_dv = f"{banco}{moeda}{fv}{livre}"
    dv_geral = _mod11_boleto(barras_sem_dv)
    c1 = f"{banco}{moeda}{livre[:5]}"
    c2 = livre[5:15]
    c3 = livre[15:25]
    return f"{c1}{_mod10(c1)}{c2}{_mod10(c2)}{c3}{_mod10(c3)}{dv_geral}{fv}"


def linha_digitavel_valida(texto: str) -> bool:
    n = so_digitos(texto)
    if len(n) != 47:
        return False
    c1, c2, c3 = n[0:9], n[10:20], n[21:31]
    if not (n[9] == _mod10(c1) and n[20] == _mod10(c2) and n[31] == _mod10(c3)):
        return False
    barras_sem_dv = n[0:4] + n[33:47] + n[4:9] + n[10:20] + n[21:31]
    return n[32] == _mod11_boleto(barras_sem_dv)


def dados_linha_digitavel(texto: str, referencia: date = date(2026, 1, 1)) -> tuple[str, date]:
    """Devolve (valor em string '1234.56', vencimento). Só chamar com linha válida.

    O fator de vencimento tem 4 dígitos e reinicia em 1000 a cada 9000 dias (a última rolagem foi em
    22/02/2025), então o mesmo fator serve a vários ciclos: escolhe-se a data mais próxima de `referencia`.
    """
    n = so_digitos(texto)
    fator = int(n[33:37])
    centavos = int(n[37:47])
    valor = f"{centavos // 100}.{centavos % 100:02d}"
    candidatas = [BASE_FATOR + timedelta(days=fator + 9000 * k) for k in range(0, 4)]
    return valor, min(candidatas, key=lambda d: abs((d - referencia).days))


def fator_vencimento(venc: date) -> int:
    dias = (venc - BASE_FATOR).days
    return dias if dias <= 9999 else 1000 + (dias - 9000 - 1000) % 9000
