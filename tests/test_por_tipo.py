import pytest

from extrator_docs_br.cli import main


@pytest.mark.parametrize("cmd", [["benchmark"], ["gerar", "pasta-x"], ["demo"]])
@pytest.mark.parametrize("n", ["0", "-1"])
def test_por_tipo_invalido_devolve_2_sem_traceback(cmd, n, capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main([*cmd, "--por-tipo", n]) == 2
    assert "1 ou mais" in capsys.readouterr().err
