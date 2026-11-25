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

    d = sub.add_parser("demo", help="gera a página HTML de demo (documentos sintéticos e o que foi extraído)")
    d.add_argument("--saida", default="site/index.html")
    d.add_argument("--por-tipo", type=int, default=2)

    a = p.parse_args(argv)
    if a.cmd in ("benchmark", "gerar", "demo") and a.por_tipo < 1:
        print("Erro: --por-tipo precisa ser 1 ou mais.", file=sys.stderr)
        return 2
    if a.cmd in ("demo", "benchmark") and a.saida and Path(a.saida).is_dir():
        print(f"Erro: --saida é uma pasta, passe um arquivo: {a.saida}", file=sys.stderr)
        return 2
    if a.cmd in ("demo", "benchmark") and a.saida and any(p.is_file() for p in Path(a.saida).parents):
        print(f"Erro: --saida passa por um arquivo, passe um caminho dentro de uma pasta: {a.saida}", file=sys.stderr)
        return 2
    if a.cmd == "demo":
        from .demo import gerar_html

        destino = Path(a.saida)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(gerar_html(a.por_tipo), encoding="utf-8")
        print(destino)
    elif a.cmd == "extrair":
        if a.arquivo == "-":
            texto = sys.stdin.read()
        else:
            try:
                bruto = Path(a.arquivo).read_bytes()
            except OSError as e:
                print(f"Não consegui abrir {a.arquivo}: {e}", file=sys.stderr)
                return 2
            try:
                texto = bruto.decode("utf-8-sig")
            except UnicodeDecodeError:
                texto = bruto.decode("cp1252", errors="replace")  # arquivo salvo no Windows em ANSI
        print(json.dumps(extrair(texto, a.tipo, validar=not a.sem_validar), ensure_ascii=False, indent=2))
    elif a.cmd == "benchmark":
        corpus = gerar_corpus(a.por_tipo, a.semente)
        tabela = tabela_markdown(avaliar(corpus, validar=False), avaliar(corpus, validar=True))
        cab = f"Corpus sintético: {len(corpus)} documentos ({a.por_tipo} por tipo), semente {a.semente}.\n\n"
        print(cab + tabela)
        if a.saida:
            Path(a.saida).parent.mkdir(parents=True, exist_ok=True)  # `--saida docs/tabela.md` sem a pasta
            Path(a.saida).write_text(cab + tabela + "\n", encoding="utf-8")
    elif a.cmd == "gerar":
        pasta = Path(a.pasta)
        try:
            pasta.mkdir(parents=True, exist_ok=True)
        except OSError as e:  # o caminho já existe como arquivo, por exemplo
            print(f"Não consegui criar a pasta {a.pasta}: {e}", file=sys.stderr)
            return 2
        for i, doc in enumerate(gerar_corpus(a.por_tipo, 7)):
            (pasta / f"{doc.tipo}-{i:02d}.txt").write_text(doc.texto, encoding="utf-8")
            (pasta / f"{doc.tipo}-{i:02d}.gabarito.json").write_text(
                json.dumps(doc.gabarito, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
