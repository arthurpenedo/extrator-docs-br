# extrator-docs-br

Extrai campos de **boleto, NF-e e comprovante Pix** com regex + validação de dígito verificador, e mede o acerto por campo.

## O problema
Automação com IA em pequenas empresas vive de tirar dados de boleto, nota e comprovante. Um CNPJ ou um valor errado vira pagamento errado. Pegar "o primeiro número que parece um CNPJ" falha quando o documento tem outro número parecido (protocolo, pagador). Dígito verificador e rótulo resolvem isso sem modelo nenhum.

## O que faz
- **Validadores**: CNPJ, CPF, chave de acesso da NF-e (44 dígitos, módulo 11) e linha digitável do boleto (47 dígitos: 3 DVs módulo 10 + DV geral módulo 11). Do boleto válido ele também decodifica **valor e vencimento** (fator de vencimento, com a rolagem de fev/2025).
- **Extrator** com dois modos: `ingênuo` (primeiro padrão que aparece) e `completo` (rótulo + DV + cruzamento com a linha digitável).
- **Gerador** de documentos **sintéticos** com gabarito (layouts, rótulos, formatos de valor/data variados e "iscas": número parecido com CNPJ que não passa no DV, CNPJ do pagador junto do beneficiário).
- **Benchmark** por campo. Zero dependências.

## Resultado medido
Corpus sintético de 600 documentos (200 por tipo, semente 42), `extrator-docs-br benchmark`. Detalhe em [BENCHMARK.md](BENCHMARK.md).

| Modo | Campos corretos |
|---|---|
| Ingênuo | 2297/2400 (95,7%) |
| Com validadores | 2400/2400 (100%) |

Toda a diferença está no CNPJ do beneficiário do boleto (48,5% → 100%).

## Como rodar
```
pip install -e ".[dev]"
pytest -q                                   # 13 testes
extrator-docs-br gerar exemplos             # grava documentos sintéticos + gabarito
extrator-docs-br extrair exemplos/boleto-00.txt
extrator-docs-br benchmark --saida BENCHMARK.md
```

## Limites honestos
- **100% é sobre o corpus que eu mesmo gerei**: o gerador e o extrator foram escritos pelo mesmo autor, então o número mostra que os validadores eliminam as iscas previstas, não que funcione em qualquer boleto real. Não testei com documentos reais (sem dado pessoal por escolha).
- Só texto já extraído: não faz OCR nem lê PDF.
- Um layout real com rótulos diferentes dos previstos não é coberto; o fator de vencimento é ambíguo entre ciclos de 9000 dias (resolvido pela data mais próxima de 01/01/2026, parâmetro `referencia`).
- A comparação com um modelo pequeno local (Ollama) não foi feita.

## Licença
MIT
