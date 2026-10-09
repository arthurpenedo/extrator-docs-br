"""Mede precisão e cobertura por campo contra o gabarito do gerador."""
from __future__ import annotations

from collections import defaultdict

from .extrator import extrair
from .gerador import Documento


def avaliar(corpus: list[Documento], validar: bool = True) -> dict[str, dict[str, int]]:
    """Por 'tipo.campo': total, extraidos (campo devolvido), corretos."""
    conta: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "extraidos": 0, "corretos": 0})
    for doc in corpus:
        obtido = extrair(doc.texto, doc.tipo, validar=validar)
        for campo, esperado in doc.gabarito.items():
            c = conta[f"{doc.tipo}.{campo}"]
            c["total"] += 1
            if campo in obtido:
                c["extraidos"] += 1
                if obtido[campo] == esperado:
                    c["corretos"] += 1
    return dict(conta)


def resumo(conta: dict[str, dict[str, int]]) -> tuple[int, int]:
    return sum(c["corretos"] for c in conta.values()), sum(c["total"] for c in conta.values())


def tabela_markdown(ingenuo: dict, completo: dict) -> str:
    linhas = ["| Campo | Ingênuo (acerto) | Com validadores (acerto) | Com validadores (precisão ao extrair) |",
              "|---|---|---|---|"]
    for campo in sorted(completo):
        a, b = ingenuo[campo], completo[campo]
        prec = f"{b['corretos'] / b['extraidos']:.1%}" if b["extraidos"] else "-"
        linhas.append(f"| {campo} | {a['corretos']}/{a['total']} ({a['corretos'] / a['total']:.1%}) "
                      f"| {b['corretos']}/{b['total']} ({b['corretos'] / b['total']:.1%}) | {prec} |")
    ok_a, tot = resumo(ingenuo)
    ok_b, _ = resumo(completo)
    linhas.append(f"| **Total** | **{ok_a}/{tot} ({ok_a / tot:.1%})** | **{ok_b}/{tot} ({ok_b / tot:.1%})** | |")
    return "\n".join(linhas)
