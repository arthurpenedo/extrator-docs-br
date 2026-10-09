from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .avaliacao import avaliar, tabela_markdown
from .extrator import extrair
from .gerador import gerar_corpus


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="extrator-docs-br")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("extrair", help="extrai campos de um arquivo de texto (ou '-' para stdin)")
    e.add_argument("arquivo")
    e.add_argument("--tipo", choices=["boleto", "nfe", "pix"])
    e.add_argument("--sem-validar", action="store_true")

    b = sub.add_parser("benchmark", help="gera documentos sintéticos e mede o acerto por campo")
    b.add_argument("--por-tipo", type=int, default=200)
    b.add_argument("--semente", type=int, default=42)
    b.add_argument("--saida", help="grava a tabela em Markdown")

    g = sub.add_parser("gerar", help="grava documentos sintéticos de exemplo em uma pasta")
    g.add_argument("pasta")
    g.add_argument("--por-tipo", type=int, default=3)

    a = p.parse_args(argv)
    if a.cmd == "extrair":
        texto = sys.stdin.read() if a.arquivo == "-" else Path(a.arquivo).read_text(encoding="utf-8")
        print(json.dumps(extrair(texto, a.tipo, validar=not a.sem_validar), ensure_ascii=False, indent=2))
    elif a.cmd == "benchmark":
        corpus = gerar_corpus(a.por_tipo, a.semente)
        tabela = tabela_markdown(avaliar(corpus, validar=False), avaliar(corpus, validar=True))
        cab = f"Corpus sintético: {len(corpus)} documentos ({a.por_tipo} por tipo), semente {a.semente}.\n\n"
        print(cab + tabela)
        if a.saida:
            Path(a.saida).write_text(cab + tabela + "\n", encoding="utf-8")
    elif a.cmd == "gerar":
        pasta = Path(a.pasta)
        pasta.mkdir(parents=True, exist_ok=True)
        for i, doc in enumerate(gerar_corpus(a.por_tipo, 7)):
            (pasta / f"{doc.tipo}-{i:02d}.txt").write_text(doc.texto, encoding="utf-8")
            (pasta / f"{doc.tipo}-{i:02d}.gabarito.json").write_text(
                json.dumps(doc.gabarito, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
