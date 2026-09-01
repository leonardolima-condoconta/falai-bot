# Extração de Formulários Executivos a partir de Excel (.xlsx)

Fluxo usado no ciclo 2026.2 para gerar formulários de executivos C-Level que não constavam
no JSON de autoavaliação padrão.

## Estrutura do arquivo Excel

Cada executivo tem DOIS arquivos:
- `CondoConta_Autoavaliacao_[Nome]_2026-2_Ago.xlsx` — autoavaliação
- `CondoConta_Avaliacao_Lider_[Nome]_2026-2_Ago.xlsx` — avaliação do líder

Cada arquivo tem duas abas:
- **Leia-me** — instruções de preenchimento
- **[Nome]** — aba com as perguntas (sheetId=2)

## Extração das perguntas (sem openpyxl)

O container pode não ter `openpyxl` instalado. Usar `zipfile` + `xml.etree.ElementTree`:

```python
import zipfile, xml.etree.ElementTree as ET

ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

with zipfile.ZipFile(fpath) as z:
    # 1. Carregar shared strings
    with z.open('xl/sharedStrings.xml') as f:
        strings = [si.text or ''.join(si.itertext())
                   for si in ET.parse(f).findall('.//s:si', ns)]

    # 2. Ler aba sheet2 (a primeira depois do Leia-me)
    with z.open('xl/worksheets/sheet2.xml') as f:
        rows = ET.parse(f).findall('.//s:row', ns)

    # 3. Para cada linha, extrair colunas B (pergunta) e D (tipo)
    for row in rows:
        cells = {}
        for c in row.findall('s:c', ns):
            col = c.get('r')[0]  # primeira letra da referência (B, C, D...)
            v = c.find('s:v', ns)
            val = v.text if v is not None else ''
            if c.get('t') == 's' and val:
                try: val = strings[int(val)]
                except: pass
            cells[col] = val

        b = str(cells.get('B', ''))
        d = str(cells.get('D', ''))
        # b = pergunta, d = tipo (Escala 1-5, Texto aberto, Lista suspensa)
```

## Colunas relevantes

| Coluna | Conteúdo |
|---|---|
| B | Pergunta (row >= 7 são perguntas reais; rows 2-6 são cabeçalho/metadados) |
| C | Resposta (vazia no template) |
| D | Tipo de campo: "Escala 1-5", "Texto aberto", "Lista suspensa" |

## Gerando o formulário HTML

1. Extrair perguntas conforme código acima
2. Reordenar para a ordem unificada (ver `avaliacao-ordem-unificada.md`)
3. Adicionar pergunta de Potencial (Q5) se não existir na planilha original
4. Substituir placeholders no template `exec_form_template.html`:
   - `NOME` → nome completo
   - `EMAIL` → e-mail
   - `CARGO`, `AREA`, `NIVEL` → metadados
   - `PERGUNTAS` → HTML das perguntas
5. Publicar via `curl` para o webhook do static-server

## Template HTML base

Arquivo: `/opt/data/exec_form_template.html` — template reutilizável com CSS CondoConta + JS de submit.
Mesmo layout dos formulários padrão (`gerar_form_avaliacao.py`).

## Formulário de liderança unificado (CEO/Diretor avaliando múltiplos)

Para líderes que avaliam vários executivos (ex: CEO avaliando 6 C-levels):
- Dropdown com todos os liderados
- Perguntas dinâmicas carregadas via `PERGUNTAS` em JavaScript
- Q2 (métrica da área) é **diferente para cada liderado**
- Salvar estado via `localStorage` para retomar depois
- Ver `gerar_lider_dellarocca.py` como referência de implementação

## Pitfall: nomes truncados no Excel

Os nomes nas abas e no conteúdo podem estar truncados a ~31 caracteres.
Ex: "Rodrigo Borer Magela de Oliv" em vez de "Rodrigo Borer Magela de Oliveira".
Usar prefix matching ao cruzar com dados do Convenia.