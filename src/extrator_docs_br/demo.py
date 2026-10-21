"""Página de demo estática: cada documento sintético, o que o extrator tirou dele e se bateu com o gabarito."""
from __future__ import annotations

from html import escape

from .avaliacao import avaliar, resumo
from .extrator import extrair
from .gerador import gerar_corpus

CSS = (
    "body{font-family:system-ui,sans-serif;max-width:1000px;margin:2rem auto;padding:0 1rem}"
    ".doc{display:grid;grid-template-columns:1fr 1fr;gap:1rem;border:1px solid #ddd;border-radius:6px;"
    "padding:.8rem;margin-bottom:1rem}pre{background:#f6f6f6;padding:.6rem;white-space:pre-wrap;margin:0;font-size:.8rem}"
    "table{border-collapse:collapse;width:100%;font-size:.85rem}td,th{border-bottom:1px solid #eee;padding:.25rem;text-align:left}"
    ".ok{color:#0a6b2d}.erro{color:#b00020;font-weight:600}h3{margin:.2rem 0 .6rem}"
)


def _linhas_campos(gabarito: dict[str, str], obtido: dict[str, str]) -> str:
    saida = []
    for campo, esperado in gabarito.items():
        valor = obtido.get(campo)
        certo = valor == esperado
        saida.append(
            "<tr><td>{}</td><td>{}</td><td class='{}'>{}</td></tr>".format(
                escape(campo),
                escape(valor if valor is not None else "(não extraído)"),
                "ok" if certo else "erro",
                "certo" if certo else "esperado: " + escape(esperado),
            )
        )
    return "".join(saida)


def gerar_html(por_tipo: int = 2, semente: int = 7) -> str:
    """Mostra `por_tipo` documentos de cada tipo e o acerto do corpus de 600 documentos (semente 42)."""
    exemplos = gerar_corpus(por_tipo, semente)
    blocos = []
    for doc in exemplos:
        obtido = extrair(doc.texto, doc.tipo, validar=True)
        blocos.append(
            f"<div class='doc'><div><h3>{escape(doc.tipo)}</h3><pre>{escape(doc.texto)}</pre></div>"
            f"<div><h3>Extraído</h3><table><tr><th>Campo</th><th>Valor</th><th>Gabarito</th></tr>"
            f"{_linhas_campos(doc.gabarito, obtido)}</table></div></div>"
        )
    corpus = gerar_corpus(200, 42)
    ing_ok, total = resumo(avaliar(corpus, validar=False))
    comp_ok, _ = resumo(avaliar(corpus, validar=True))
    return (
        "<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>"
        f"<title>extrator-docs-br: demo</title><style>{CSS}</style></head><body>"
        "<h1>extrator-docs-br: demo</h1>"
        "<p>Documentos <b>sintéticos</b> (nenhum dado real) de boleto, NF-e e comprovante Pix, e o que o extrator "
        "com validadores (dígito verificador) tirou de cada um. "
        f"No corpus de {len(corpus)} documentos (semente 42): ingênuo {ing_ok}/{total} campos corretos, "
        f"com validadores {comp_ok}/{total}. "
        "<a href='https://github.com/arthurpenedo/extrator-docs-br'>Código no GitHub</a>.</p>"
        f"{''.join(blocos)}"
        "<p><small>O corpus foi gerado pelo mesmo autor do extrator: o número mostra que os validadores eliminam as "
        "iscas previstas, não que funcione em qualquer documento real.</small></p></body></html>"
    )
