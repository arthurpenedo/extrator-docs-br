import json
import random

from extrator_docs_br import extrair
from extrator_docs_br.avaliacao import avaliar, resumo
from extrator_docs_br.cli import main
from extrator_docs_br.gerador import gerar_boleto, gerar_corpus, gerar_nfe, gerar_pix
from extrator_docs_br.validadores import (
    chave_nfe_valida,
    cnpj_valido,
    completar_chave_nfe,
    cpf_valido,
    dados_linha_digitavel,
    linha_digitavel_valida,
)


def test_cnpj_conhecido():
    assert cnpj_valido("11.222.333/0001-81")
    assert not cnpj_valido("11.222.333/0001-82")
    assert not cnpj_valido("00.000.000/0000-00")
    assert not cnpj_valido("123")


def test_cpf_conhecido():
    assert cpf_valido("529.982.247-25")
    assert not cpf_valido("529.982.247-26")
    assert not cpf_valido("111.111.111-11")


def test_chave_nfe_dv():
    chave = completar_chave_nfe("3526" + "0" * 39)
    assert chave_nfe_valida(chave)
    errada = chave[:-1] + str((int(chave[-1]) + 1) % 10)
    assert not chave_nfe_valida(errada)


def test_linha_digitavel_exemplo_gerado():
    doc = gerar_boleto(random.Random(1))
    linha = doc.gabarito["linha_digitavel"]
    assert linha_digitavel_valida(linha)
    assert not linha_digitavel_valida(linha[:-1] + str((int(linha[-1]) + 1) % 10))  # valor adulterado... DV geral
    valor, venc = dados_linha_digitavel(linha)
    assert valor == doc.gabarito["valor"] and venc.isoformat() == doc.gabarito["vencimento"]


def test_linha_com_dv_de_campo_errado():
    linha = gerar_boleto(random.Random(2)).gabarito["linha_digitavel"]
    ruim = linha[:9] + str((int(linha[9]) + 1) % 10) + linha[10:]
    assert not linha_digitavel_valida(ruim)


def test_extrai_boleto_completo():
    doc = gerar_boleto(random.Random(3))
    assert extrair(doc.texto) == doc.gabarito


def test_extrai_nfe_e_pix():
    rng = random.Random(4)
    nfe, pix = gerar_nfe(rng), gerar_pix(rng)
    assert extrair(nfe.texto) == nfe.gabarito
    assert extrair(pix.texto) == pix.gabarito


def test_isca_de_cnpj_invalido_derruba_modo_ingenuo():
    # em algum boleto o CNPJ falso (Protocolo) vem antes do beneficiário e engana o modo ingênuo
    corpus = [d for d in gerar_corpus(60, 5) if d.tipo == "boleto"]
    ing, com = avaliar(corpus, validar=False), avaliar(corpus, validar=True)
    assert com["boleto.cnpj_beneficiario"]["corretos"] > ing["boleto.cnpj_beneficiario"]["corretos"]


def test_validadores_nao_pioram_nenhum_campo():
    corpus = gerar_corpus(50, 6)
    ing, com = avaliar(corpus, validar=False), avaliar(corpus, validar=True)
    for campo in com:
        assert com[campo]["corretos"] >= ing[campo]["corretos"], campo


def test_acerto_total_alto_no_corpus():
    ok, total = resumo(avaliar(gerar_corpus(100, 42), validar=True))
    assert ok / total >= 0.99


def test_chave_invalida_nao_e_extraida():
    texto = "DANFE\nChave de acesso: " + "1" * 44
    assert "chave_acesso" not in extrair(texto, "nfe")
    assert extrair(texto, "nfe", validar=False)["chave_acesso"] == "1" * 44


def test_corpus_reprodutivel():
    assert [d.texto for d in gerar_corpus(5, 9)] == [d.texto for d in gerar_corpus(5, 9)]


def test_cli_extrair_e_benchmark(tmp_path, capsys):
    doc = gerar_pix(random.Random(8))
    arq = tmp_path / "pix.txt"
    arq.write_text(doc.texto, encoding="utf-8")
    assert main(["extrair", str(arq)]) == 0
    assert json.loads(capsys.readouterr().out) == doc.gabarito
    saida = tmp_path / "b.md"
    assert main(["benchmark", "--por-tipo", "10", "--saida", str(saida)]) == 0
    assert "Total" in saida.read_text(encoding="utf-8")


def test_demo_html_mostra_documentos_e_acerto():
    from extrator_docs_br.demo import gerar_html

    html = gerar_html(por_tipo=1)
    assert html.startswith("<!doctype html>")
    assert html.count("class='doc'") == 3  # um boleto, uma NF-e, um Pix
    assert "2400/2400" in html and "certo" in html


def test_cli_demo_grava_arquivo(tmp_path):
    saida = tmp_path / "site" / "index.html"
    assert main(["demo", "--saida", str(saida), "--por-tipo", "1"]) == 0
    assert "extrator-docs-br: demo" in saida.read_text(encoding="utf-8")


def test_cli_gerar_grava_texto_e_gabarito(tmp_path):
    pasta = tmp_path / "docs"
    assert main(["gerar", str(pasta), "--por-tipo", "2"]) == 0
    textos = sorted(pasta.glob("*.txt"))
    assert len(textos) == 6  # 2 por tipo
    for t in textos:
        gabarito = json.loads(t.with_suffix(".gabarito.json").read_text(encoding="utf-8"))
        assert extrair(t.read_text(encoding="utf-8")) == gabarito


def test_cli_extrair_le_da_entrada_padrao(monkeypatch, capsys):
    import io

    doc = gerar_boleto(random.Random(3))
    monkeypatch.setattr("sys.stdin", io.StringIO(doc.texto))
    assert main(["extrair", "-"]) == 0
    assert json.loads(capsys.readouterr().out) == doc.gabarito
