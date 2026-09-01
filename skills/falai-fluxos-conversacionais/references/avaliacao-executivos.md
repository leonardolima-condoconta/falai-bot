# Autoavaliacao de Executivos (C-Level / Diretoria)

Executivos NAO estao no `autoavaliacao_perguntas.json`. Eles tem planilhas Excel individuais
com perguntas customizadas por cargo. Ciclo 2026.2: 5 executivos, 8 perguntas cada (3 escala 1-5,
5 texto aberto).

## Estrutura das planilhas

Cada arquivo `.xlsx` tem 2 abas:
- `Leia-me` — instrucoes gerais (template identico em todos)
- `<Nome do Executivo>` — perguntas especificas

## Perguntas (8 por executivo)

| # | Tipo | Pergunta |
|---|---|---|
| 1 | Escala 1-5 | Como voce avalia seus Resultados neste ciclo? |
| 2 | Texto aberto | Pergunta especifica da area (CFO=orcamento, CTO=uptime, CRO=receita, etc.) |
| 3 | Texto aberto | Situacao de autonomia/responsabilidade extra |
| 4 | Escala 1-5 | Como voce avalia suas Competencias neste ciclo? |
| 5 | Texto aberto | Valor CondoConta que viveu bem |
| 6 | Texto aberto | Valor CondoConta a evoluir |
| 7 | Texto aberto | Plano de carreira / PDI proximos 6 meses |
| 8 | Escala 1-5 | Nivel de motivacao/energia hoje |

## Extracao das perguntas

Ler `.xlsx` como zip + XML (nao depende de openpyxl):

```python
import zipfile, xml.etree.ElementTree as ET

ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

with zipfile.ZipFile(fpath) as z:
    # Shared strings
    with z.open('xl/sharedStrings.xml') as f:
        strings = [si.text or ''.join(si.itertext())
                   for si in ET.parse(f).findall('.//s:si', ns)]

    # Sheet 2 = tab do executivo (sheet 1 = Leia-me)
    with z.open('xl/worksheets/sheet2.xml') as f:
        tree = ET.parse(f)
        rows = tree.findall('.//s:row', ns)

    name = ""
    questions = []

    for row in rows:
        row_num = int(row.get('r', '0'))
        cells = {}
        for c in row.findall('s:c', ns):
            col = c.get('r')[0]  # B, C, D
            v = c.find('s:v', ns)
            val = v.text if v is not None else ''
            if c.get('t') == 's' and val:
                try: val = strings[int(val)]
                except: pass
            cells[col] = val

        b = cells.get('B', '')
        d = cells.get('D', '')

        if row_num == 2 and 'AUTOAVALIACAO' in str(b):
            name = str(b).replace('AUTOAVALIACAO - ', '').strip()

        # Perguntas comecam na linha 7
        if row_num >= 7 and b and len(str(b)) > 20:
            is_scale = 'Escala' in str(d)
            questions.append({
                "n": len(questions) + 1,
                "pergunta": str(b),
                "tipo": "Escala 1-5" if is_scale else "Texto aberto"
            })
```

## Geracao do HTML

Usar o template padrao de autoavaliacao (mesmo CSS, layout, JS da Falai) disponivel em
`/opt/data/exec_form_template.html`. Substituir placeholders:

```
NOME → nome do executivo
EMAIL → email corporativo
CARGO → cargo (COO, CFO, CTO, CRO, Head of People)
AREA → "Lideranca Executiva"
NIVEL → "C-Level"
PERGUNTAS → HTML das perguntas gerado dinamicamente
```

Para perguntas tipo "Escala 1-5", gerar botoes 1 a 5 com `selStar()` no onclick.
Para "Texto aberto", gerar `<textarea>`.

## Publicacao

Mesmo fluxo dos outros formularios: `curl` POST para o webhook do static-server:

```bash
curl -s -X POST https://webhook-proxy.condoconta.com.br/webhooks/static-server \
  -H "X-Service-Account-Token: $STATIC_SERVER_SA_TOKEN" \
  -F "slug=avaliacao-marcelo-cruz" \
  -F "file=@avaliacao-marcelo-cruz.html;type=text/html"
```

Slug = prefixo do email sem dominio (ex: `marcelo@` → `marcelo-cruz`).

## Executivos do ciclo 2026.2

| Nome | Email | Cargo | Slug |
|---|---|---|---|
| Marcelo Cruz | marcelo@condoconta.com.br | COO | marcelo-cruz |
| Luciano Helio Bernardi | luciano.bernardi@condoconta.com.br | CFO | luciano-helio-bernardi |
| Rodrigo Costa | rodrigo.costa@condoconta.com.br | CTO | rodrigo-costa |
| Rodrigo Borer Magela de Oliveira | rodrigo.borer@condoconta.com.br | CRO | rodrigo-borer-magela-de-oliveira |
| Rodrigo Alexandre Catarcione | rodrigo.catarcione@condoconta.com.br | Head of People | rodrigo-alexandre-catarcione |

## Template de DM (autoavaliacao executiva)

Mesmo template da autoavaliacao padrao (Fase 3 do `lancamento-ciclo-dm-lideres.md`),
apenas com a URL correta.

## Pitfalls

- **Juliano Santana e Rodrigo Della Rocca**: estao na lista de lideres mas NAO tinham
  planilha de autoavaliacao no ciclo 2026.2. Confirmar com People se devem receber.
- **Planilhas sao todas identicas no template base**: as 5 planilhas de autoavaliacao
  executiva tem exatamente o mesmo conteudo (todas listam os 6 executivos). Apenas a
  aba individual difere. Nao precisa processar todas — uma basta para extrair o template,
  depois processar cada aba individualmente.
- **Nomes truncados no titulo**: `Rodrigo Borer Magela de Oliv` (truncado a 31 chars
  no titulo da aba). O match por nome deve usar prefixo.