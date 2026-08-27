#!/usr/bin/env python3
"""
Gera HTML do formulario 1x1 consolidado: autoavaliacao + avaliacao lider + 9box + PDI.
Uso: python3 gerar_form_1x1.py <email_lider> <email_colaborador>
"""
import json, subprocess, sys

LIDER_EMAIL = sys.argv[1] if len(sys.argv) > 1 else None
COLAB_EMAIL = sys.argv[2] if len(sys.argv) > 2 else None
if not LIDER_EMAIL or not COLAB_EMAIL:
    print("Uso: gerar_form_1x1.py <email_lider> <email_colaborador>")
    sys.exit(1)

SA = AUTH = ""
with open("/opt/data/.env") as fenv:
    for line in fenv:
        if line.startswith("CONDOPOWER_SA_TOKEN="):
            SA = line.strip().split("=",1)[1].strip('"').strip("'")
        if line.startswith("CONDOPOWER_AUTH="):
            AUTH = line.strip().split("=",1)[1].strip('"').strip("'")

def call(method, params):
    r = subprocess.run(["curl","-s","-X","POST",
        "https://webhook-proxy.condoconta.com.br/webhooks/condopower-api",
        "-H","Content-Type: application/json",
        "-H","X-Service-Account-Token: "+SA,
        "-H","auth: "+AUTH,
        "-d", json.dumps({"method":method,"params":params})
    ], capture_output=True, text=True, timeout=30)
    try: return json.loads(r.stdout)
    except: return {"ok":False,"error":{"message":"erro de parse"}}

# 1. Identificar lider e colaborador
v_lider = call("access.verify", {"identifier": LIDER_EMAIL})
v_colab = call("access.verify", {"identifier": COLAB_EMAIL})
if not v_lider.get("ok") or not v_colab.get("ok"):
    print("ERRO: lider ou colaborador nao encontrado")
    sys.exit(1)

lider = v_lider["result"]["employee"]
colab = v_colab["result"]["employee"]
lider_id = lider["id"]
colab_id = colab["id"]
colab_nome = colab["full_name"]
colab_cargo = colab.get("job","")
colab_area = colab.get("department","")
lider_nome = lider["full_name"]

# Validar que lider tem esse liderado
reports = v_lider["result"].get("reports", [])
report_ids = [r["id"] for r in reports]
if colab_id not in report_ids:
    print(f"ERRO: {colab_nome} nao e liderado de {lider_nome}")
    sys.exit(1)

# 2. Buscar autoavaliacao
auto = call("form.autoavaliacao.get", {
    "requester_email": LIDER_EMAIL,
    "colaborador_id": colab_id,
    "quantidade": 1
})
auto_raw = {}
if auto.get("ok") and auto["result"]["respostas"]:
    auto_raw = auto["result"]["respostas"][0].get("raw", {})
auto_perguntas = auto_raw.get("perguntas", {}) if auto_raw else {}

# 3. Buscar avaliacao do lider
av_lider = call("form.avaliacao_lider.get", {
    "requester_email": LIDER_EMAIL,
    "lider_id": lider_id,
    "colaborador_id": colab_id,
    "quantidade": 1
})
lider_raw = {}
if av_lider.get("ok") and av_lider["result"]["respostas"]:
    lider_raw = av_lider["result"]["respostas"][0].get("raw", {})
lider_perguntas = lider_raw.get("perguntas", {}) if lider_raw else {}

tem_auto = bool(auto_perguntas)
tem_lider = bool(lider_perguntas)

# 4. Extrair notas para 9box
nota_resultados_auto = None
nota_competencias_auto = None
nota_resultados_lider = None
nota_competencias_lider = None
nota_potencial_lider = None

for k, v in auto_perguntas.items():
    kl = k.lower()
    if "resultados" in kl and v.replace(".","").isdigit(): nota_resultados_auto = float(v)
    if "competências" in kl or "competencias" in kl:
        if v.replace(".","").isdigit(): nota_competencias_auto = float(v)

for k, v in lider_perguntas.items():
    kl = k.lower()
    if "resultados" in kl and v.replace(".","").isdigit(): nota_resultados_lider = float(v)
    if "competências" in kl or "competencias" in kl:
        if v.replace(".","").isdigit(): nota_competencias_lider = float(v)
    if "potencial" in kl and v.replace(".","").isdigit(): nota_potencial_lider = float(v)

# Mapear label → valor para exibicao lado a lado
# Usar as perguntas do JSON de autoavaliacao como referencia
with open("/opt/data/convenia/autoavaliacao_perguntas.json") as f:
    auto_json = json.load(f)
with open("/opt/data/convenia/avaliacao_lider_perguntas.json") as f:
    lider_json = json.load(f)

auto_labels = []
lider_labels = []

for area in auto_json.get("areas",[]):
    for c in area["colaboradores"]:
        if c["nome"].lower().split()[0] in colab_nome.lower():
            for p in c["perguntas"]:
                auto_labels.append(p["pergunta"])
            break

for area in lider_json.get("areas",[]):
    for c in area["colaboradores"]:
        if c["nome"].lower().split()[0] in colab_nome.lower():
            for p in c["perguntas"]:
                lider_labels.append(p["pergunta"])
            break

# 5. Montar linhas comparativas
linhas = []
auto_keys = list(auto_perguntas.keys())
lider_keys = list(lider_perguntas.keys())

for i, label in enumerate(auto_labels[:8]):
    auto_val = auto_perguntas.get(label, auto_perguntas.get(auto_keys[i] if i < len(auto_keys) else "",""))
    lider_val = lider_perguntas.get(label, lider_perguntas.get(lider_keys[i] if i < len(lider_keys) else "",""))
    linhas.append((label, auto_val, lider_val))

# 6. Gerar HTML
css = """
:root{--paper:#F4F6FA;--ink:#0C2440;--navy:#14365C;--navy-deep:#0A2138;--gold:#F4B72C;--gold-deep:#C98F0C;--muted:#5E748C;--line:#DCE3EC;--card:#FFFFFF;--lider-color:#14365C;--auto-color:#F4B72C}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--paper);color:var(--ink);font-family:'Inter',sans-serif;line-height:1.5;padding:30px 16px}
.wrapper{max-width:1200px;margin:0 auto;display:grid;grid-template-columns:1fr 380px;gap:20px;align-items:start}
@media(max-width:900px){.wrapper{grid-template-columns:1fr}}
.sheet{background:var(--card);box-shadow:0 12px 30px -14px rgba(12,36,64,.25),0 0 0 1px var(--line)}
header{background:var(--navy-deep);color:#fff;padding:24px 32px}
.brandrow{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:8px}
.logo b{color:var(--gold)}.logo span{color:#AFC1D6;font-weight:600;font-family:'Sora',sans-serif;font-size:14px}
.tag-conf{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--gold);border:1px solid rgba(244,183,44,.4);padding:4px 10px;border-radius:4px}
header h1{font-family:'Sora',sans-serif;font-size:22px;font-weight:800;letter-spacing:-.02em}
header h1 em{color:var(--gold);font-style:normal}
header .sub{color:#AFC1D6;margin-top:6px;font-size:12px}
.pad{padding:24px 32px}
.section-title{font-family:'Sora',sans-serif;font-size:15px;font-weight:700;color:var(--navy);margin-bottom:14px;padding-bottom:8px;border-bottom:2px solid var(--line)}
.compare-row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;align-items:start;margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid var(--line)}
.compare-label{font-size:12px;font-weight:600;color:var(--muted);line-height:1.4}
.compare-val{font-size:12.5px;line-height:1.5;padding:8px 12px;border-radius:6px}
.compare-val.auto{background:#FFF8E1;color:#8B6914;border:1px solid var(--gold)}
.compare-val.lider{background:#E8F0FE;color:#14365C;border:1px solid var(--navy)}
.compare-val.score{font-size:22px;font-weight:800;text-align:center;padding:12px 0}
.compare-val.empty{color:var(--muted);font-style:italic}
/* 9box */
.ninebox{background:var(--card);box-shadow:0 12px 30px -14px rgba(12,36,64,.25),0 0 0 1px var(--line)}
.ninebox-inner{padding:20px}
.ninebox h2{font-family:'Sora',sans-serif;font-size:15px;font-weight:700;color:var(--navy);margin-bottom:14px}
.ninebox-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:3px;aspect-ratio:1;max-width:300px;margin:0 auto 16px}
.ninebox-grid div{border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:600;text-align:center;padding:4px;color:var(--muted);border:1px solid var(--line);background:#FBFCFE}
.ninebox-grid div.active{box-shadow:0 0 0 3px var(--gold);font-weight:800;font-size:11px}
.ninebox-legend{display:flex;gap:16px;justify-content:center;font-size:11px;color:var(--muted);margin-bottom:12px}
.ninebox-legend span{display:flex;align-items:center;gap:4px}
.dot{width:10px;height:10px;border-radius:50%;display:inline-block}
.dot.auto{background:var(--gold)}
.dot.lider{background:var(--navy)}
/* PDI */
.pdi-section{background:var(--card);box-shadow:0 12px 30px -14px rgba(12,36,64,.25),0 0 0 1px var(--line);margin-top:16px}
.pdi-section .pad textarea{width:100%;padding:10px 12px;border:1.5px solid var(--line);border-radius:8px;font-family:'Inter',sans-serif;font-size:13px;color:var(--ink);background:#FBFCFE;resize:vertical;margin-bottom:10px}
.pdi-section .pad textarea:focus{outline:none;border-color:var(--gold)}
.pdi-section .pad label{display:block;font-size:12px;font-weight:600;color:var(--navy);margin-bottom:5px}
.field-pdi{margin-bottom:14px}
.submit-row{text-align:right;margin-top:20px}
.submit-row button{background:var(--navy);color:#fff;border:none;padding:12px 30px;border-radius:8px;font-family:'Sora',sans-serif;font-size:14px;font-weight:600;cursor:pointer}
.submit-row button:hover{opacity:.9}
#status{text-align:right;margin-top:8px;font-size:12px;color:var(--gold-deep)}
.thank-you{display:none;text-align:center;padding:40px}
.thank-you .emoji{font-size:48px;margin-bottom:16px}
.thank-you h3{font-family:'Sora',sans-serif;font-size:20px;font-weight:700;color:var(--navy);margin-bottom:8px}
.thank-you p{font-size:13px;color:var(--muted)}
.no-data{color:var(--muted);font-style:italic;font-size:12px;padding:20px;text-align:center}
footer{background:var(--navy-deep);color:#AFC1D6;padding:14px 32px;display:flex;justify-content:space-between;font-family:'IBM Plex Mono',monospace;font-size:10px;flex-wrap:wrap;gap:8px}
footer b{color:#fff}footer .gold{color:var(--gold)}
.meta-info{display:flex;gap:24px;flex-wrap:wrap;font-size:11px;color:var(--muted);margin-bottom:16px}
.meta-info strong{color:var(--navy)}
"""

# Montar linhas de comparacao
def fmt_val(v):
    if not v: return '<span class="empty">-</span>'
    vs = str(v).strip()
    if vs.replace(".","").replace(",","").isdigit() and len(vs) <= 3:
        return f'<div class="compare-val score">{vs}</div>'
    return f'<div class="compare-val">{{color}}">{vs}</div>'

linhas_html = ""
for label, auto_v, lider_v in linhas:
    is_numeric = False
    for v in [auto_v, lider_v]:
        vs = str(v).strip()
        if vs and vs.replace(".","").replace(",","").isdigit() and len(vs) <= 3:
            is_numeric = True
            break
    auto_cell = '<span class="empty">-</span>' if not auto_v else f'<div class="compare-val score auto">{auto_v}</div>' if is_numeric else f'<div class="compare-val auto">{auto_v}</div>'
    lider_cell = '<span class="empty">-</span>' if not lider_v else f'<div class="compare-val score lider">{lider_v}</div>' if is_numeric else f'<div class="compare-val lider">{lider_v}</div>'
    linhas_html += f"""
  <div class="compare-row">
    <div class="compare-label">{label}</div>
    <div>{auto_cell}</div>
    <div>{lider_cell}</div>
  </div>"""

if not linhas:
    linhas_html = '<div class="no-data">📋 Nenhuma avaliacao registrada ainda. Preencha a autoavaliacao e a avaliacao do lider primeiro.</div>'

# 9box grid
def nb_pos(r, c, label, active_auto, active_lider):
    # results = coluna (1-3), potencial = linha (3-1)
    cls = ""
    if active_auto and active_lider: cls = " active"
    elif active_auto: cls = " active"
    elif active_lider: cls = " active"
    return f'<div class="{cls}">{label}</div>'

r_auto = round(nota_resultados_auto or nota_competencias_auto or 0)
c_auto = 2  # default: coluna meio se não tem potencial
p_auto = None
r_lider = round(nota_resultados_lider or nota_competencias_lider or 0)
c_lider = round(nota_potencial_lider or 2)

# Mapear notas 1-5 => posicao 9box (1-3)
def to_9box(v):
    if v is None: return None
    if v <= 2: return 1
    if v <= 3.5: return 2
    return 3

r9_auto = to_9box(nota_resultados_auto) if nota_resultados_auto else None
c9_auto = None  # auto nao tem potencial
r9_lider = to_9box(nota_resultados_lider) if nota_resultados_lider else None
c9_lider = to_9box(nota_potencial_lider) if nota_potencial_lider else None

ninebox_grid = ""
for row in range(3,0,-1):  # 3=Alto, 2=Medio, 1=Baixo (potencial)
    for col in range(1,4):  # 1=Baixo, 2=Medio, 3=Alto (resultados)
        labels_9b = [
            "Dilema", "Enigma", "Estrela",
            "Duvida", "Mantenedor", "Forte",
            "Risco", "Efetivo", "Talento"
        ]
        idx = (3-row)*3 + (col-1)
        label = labels_9b[idx]
        active_auto = (r9_auto == col)
        active_lider = (r9_lider == col and c9_lider == row)
        cls = ""
        if active_lider: cls = " active"
        elif active_auto: cls = " active"
        ninebox_grid += f'<div class="{cls}">{label}</div>'

# PDI - dados existentes
pdi_data = call("form.pdi.get", {
    "requester_email": LIDER_EMAIL,
    "lider_id": lider_id,
    "colaborador_id": colab_id,
    "quantidade": 1
})
pdi_raw = {}
if pdi_data.get("ok") and pdi_data["result"]["respostas"]:
    pdi_raw = pdi_data["result"]["respostas"][0].get("raw", {})

pdi_competencia = pdi_raw.get("competencia_foco", "")
pdi_gap = pdi_raw.get("gap_evidencia", "")
pdi_tipo = pdi_raw.get("tipo_acao", "")
pdi_descricao = pdi_raw.get("descricao_acao", "")
pdi_prazo = pdi_raw.get("prazo", "")
pdi_evidencia = pdi_raw.get("evidencia_conclusao", "")

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>1x1 — {lider_nome} & {colab_nome}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
<div class="wrapper">
  <div>
    <div class="sheet">
      <header>
        <div class="brandrow">
          <div class="logo"><b>CondoConta</b><span>· People</span></div>
          <div class="tag-conf">1x1</div>
        </div>
        <h1><em>{lider_nome}</em> ↔ <em>{colab_nome}</em></h1>
        <div class="sub">{colab_cargo} · {colab_area} · Ciclo 2026.2</div>
      </header>
      <section class="pad">
        <div class="section-title">📊 Comparativo — Autoavaliacao vs Avaliacao do Lider</div>
        <div class="meta-info">
          <div>🟡 <strong>Amarelo:</strong> Autoavaliacao</div>
          <div>🔵 <strong>Azul:</strong> Avaliacao do Lider</div>
          <div><strong>Liderado:</strong> {colab_nome}</div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px;font-size:11px;font-weight:600;color:var(--muted)">
          <div>Pergunta</div>
          <div>🟡 Autoavaliacao</div>
          <div>🔵 Lider</div>
        </div>
        {linhas_html}
      </section>
    </div>

    <!-- PDI -->
    <div class="pdi-section" style="margin-top:20px" id="pdi-section">
      <div class="pad">
        <div class="section-title">🎯 PDI — Plano de Desenvolvimento Individual</div>
        <div class="field-pdi">
          <label>Competencia foco</label>
          <textarea rows="2" name="pdi_competencia_foco" placeholder="Qual competencia sera o foco do desenvolvimento?">{pdi_competencia}</textarea>
        </div>
        <div class="field-pdi">
          <label>Gap / Evidencia atual</label>
          <textarea rows="2" name="pdi_gap_evidencia" placeholder="Qual a evidencia do gap atual?">{pdi_gap}</textarea>
        </div>
        <div class="field-pdi">
          <label>Tipo de acao (70% pratica / 20% social / 10% formal)</label>
          <textarea rows="1" name="pdi_tipo_acao" placeholder="Ex: 70%% pratica — liderar squad de cobranca">{pdi_tipo}</textarea>
        </div>
        <div class="field-pdi">
          <label>Descricao da acao</label>
          <textarea rows="3" name="pdi_descricao_acao" placeholder="Descreva a acao de desenvolvimento">{pdi_descricao}</textarea>
        </div>
        <div class="field-pdi">
          <label>Prazo</label>
          <input type="text" name="pdi_prazo" value="{pdi_prazo}" placeholder="Ex: 2026-12-31" style="width:100%;padding:10px 12px;border:1.5px solid var(--line);border-radius:8px;font-family:'Inter',sans-serif;font-size:13px;background:#FBFCFE">
        </div>
        <div class="field-pdi">
          <label>Evidencia de conclusao</label>
          <textarea rows="2" name="pdi_evidencia_conclusao" placeholder="Como sera evidenciada a conclusao?">{pdi_evidencia}</textarea>
        </div>
        <input type="hidden" id="lider_id" value="{lider_id}">
        <input type="hidden" id="lider_email" value="{LIDER_EMAIL}">
        <input type="hidden" id="colaborador_id" value="{colab_id}">
        <input type="hidden" id="colaborador_nome" value="{colab_nome}">
        <input type="hidden" id="area" value="{colab_area}">
        <div class="submit-row">
          <button onclick="enviarPDI()">Salvar PDI</button>
          <div id="status"></div>
        </div>
      </div>
    </div>

    <footer>
      <div><b>FALAI</b> · People</div>
      <div class="gold">condoconta.com.br</div>
      <div>by Falai — CC People</div>
    </footer>
  </div>

  <!-- 9box -->
  <div>
    <div class="ninebox">
      <div class="ninebox-inner">
        <h2>🎯 Nine Box</h2>
        <div class="ninebox-legend">
          <span><span class="dot auto"></span> Autoavaliacao</span>
          <span><span class="dot lider"></span> Lider</span>
        </div>
        <div class="ninebox-grid">
          {ninebox_grid}
        </div>
        <div style="font-size:10px;color:var(--muted);text-align:center;margin-top:8px">
          Horizontal: Resultados | Vertical: Potencial
        </div>
      </div>
    </div>
  </div>
</div>
<div class="thank-you" id="thank-you">
  <div class="emoji">✅</div>
  <h3>PDI Salvo!</h3>
  <p>O plano de desenvolvimento foi registrado com sucesso.</p>
</div>
<script>
function enviarPDI(){{
  var data={{}};
  var fields=document.querySelectorAll('#pdi-section [name]');
  fields.forEach(function(f){{if(f.value)data[f.name]=f.value;}});
  data.lider_id=document.getElementById('lider_id').value;
  data.colaborador_id=document.getElementById('colaborador_id').value;
  data.area=document.getElementById('area').value;
  var s=document.getElementById('status');
  s.textContent='Salvando...';
  fetch('https://condopower-api.aiexpert-condoconta.info/rpc',{{
    method:'POST',
    headers:{{'Content-Type':'application/json','X-Service-Account-Token':'{SA}','auth':'{AUTH}'}},
    body:JSON.stringify({{method:'form.pdi',params:data}})
  }}).then(function(r){{return r.json()}}).then(function(r){{
    if(r.ok){{s.textContent='✅ PDI salvo!';s.style.color='#2E7D32';document.getElementById('thank-you').style.display='block';}}
    else{{s.textContent='❌ Erro: '+(r.error&&r.error.message||'?');s.style.color='#C62828';}}
  }}).catch(function(e){{s.textContent='❌ Erro de conexao';s.style.color='#C62828';}});
}}
</script>
</body>
</html>"""

slug = f"1x1-{lider_nome.lower().replace(' ','-')}-{colab_nome.lower().replace(' ','-')}"[:60]
html_path = f"/tmp/{slug}.html"
with open(html_path, "w") as f:
    f.write(html)

token = ""
with open("/opt/data/.env") as f:
    for line in f:
        if line.startswith("STATIC_SERVER_SA_TOKEN="):
            token = line.strip().split("=",1)[1].strip('"').strip("'")

r = subprocess.run([
    "curl", "-s", "-w", "%{http_code}", "-X", "POST",
    "https://webhook-proxy.condoconta.com.br/webhooks/static-server",
    "-H", "accept: application/json",
    "-H", "X-Service-Account-Token: " + token,
    "-F", f"slug={slug}",
    "-F", f"file=@{html_path};type=text/html"
], capture_output=True, text=True, timeout=30)

code = r.stdout[-3:]; body = r.stdout[:-3]
if "200" in code:
    data = json.loads(body)
    print(data.get("url", "ERRO"))
else:
    print(f"ERRO: {code} - {body[:200]}")