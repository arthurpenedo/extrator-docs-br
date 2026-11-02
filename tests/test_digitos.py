from datetime import date

from extrator_docs_br.validadores import (
    cnpj_valido,
    completar_cnpj,
    completar_cpf,
    cpf_valido,
    fator_vencimento,
    so_digitos,
)


def test_so_digitos_tira_pontuacao_e_letras():
    assert so_digitos("123.456.789-09") == "12345678909"
    assert so_digitos("sem número") == ""


def test_completar_cpf_gera_cpf_valido():
    assert cpf_valido(completar_cpf("123456789"))
    assert completar_cpf("123456789") == "12345678909"


def test_completar_cnpj_gera_cnpj_valido():
    assert cnpj_valido(completar_cnpj("112223330001"))


def test_fator_vencimento_data_base_e_virada_de_2025():
    assert fator_vencimento(date(1997, 10, 7)) == 0
    assert fator_vencimento(date(2025, 2, 21)) == 9999
    assert fator_vencimento(date(2025, 2, 22)) == 1000
