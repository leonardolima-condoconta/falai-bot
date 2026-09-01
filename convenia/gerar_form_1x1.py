#!/usr/bin/env python3
"""
Gera HTML do 1x1 consolidado (autoavaliacao + lider + 9box + PDI).
Uso: python3 gerar_form_1x1.py <email_lider> <email_colaborador>
Layout full-screen: header full-width + grid 60/40 + scroll unico.
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
        "-H","X-Service-Account-Token: "+SA,"-H","auth: "+AUTH,
        "-d", json.dumps({"method":method,"params":params})
    ], capture_output=True, text=True, timeout=30)
    try: return json.loads(r.stdout)
    except: return {"ok":False}

# Identificar lider e colaborador
v_l = call("access.verify", {"identifier": LIDER_EMAIL})
v_c = call("access.verify", {"identifier": COLAB_EMAIL})
if not v_l.get("ok") or not v_c.get("ok"):
    print("ERRO: lider ou colaborador nao encontrado")
    sys.exit(1)

lider = v_l["result"]["employee"]
colab = v_c["result"]["employee"]
lider_id = lider["id"]; colab_id = colab["id"]
lider_nome = lider["full_name"]; colab_nome = colab["full_name"]
colab_cargo = colab.get("job",""); colab_area = colab.get("department","")
reports = [r["id"] for r in v_l["result"].get("reports",[])]

# Buscar dados (autoavaliacao, avaliacao lider, 9box anterior, PDI)
auto = call("form.autoavaliacao.get", {"requester_email":LIDER_EMAIL,"colaborador_id":colab_id,"quantidade":1})
av_l = call("form.avaliacao_lider.get", {"requester_email":LIDER_EMAIL,"lider_id":lider_id,"colaborador_id":colab_id,"quantidade":1})
nbox_prev = call("form.9box.get", {"requester_email":LIDER_EMAIL,"colaborador_id":colab_id,"quantidade":1})
pdi_prev = call("form.pdi.get", {"requester_email":LIDER_EMAIL,"colaborador_id":colab_id,"quantidade":1})

auto_raw = auto["result"]["respostas"][0]["raw"] if auto.get("ok") and auto["result"]["respostas"] else {}
av_raw = av_l["result"]["respostas"][0]["raw"] if av_l.get("ok") and av_l["result"]["respostas"] else {}
nbox_raw = nbox_prev["result"]["respostas"][0]["raw"] if nbox_prev.get("ok") and nbox_prev["result"]["respostas"] else {}
pdi_raw = pdi_prev["result"]["respostas"][0]["raw"] if pdi_prev.get("ok") and pdi_prev["result"]["respostas"] else {}

auto_p = auto_raw.get("perguntas", {})
av_p = av_raw.get("perguntas", {})

# Extrair notas para 9box
def extract_score(data, keywords):
    for k, v in data.items():
        kl = k.lower()
        if any(kw in kl for kw in keywords):
            try: return float(v)
            except: pass
    return None

nota_res_auto = extract_score(auto_p, ["resultados"])
nota_comp_auto = extract_score(auto_p, ["competência"])
nota_res_lider = extract_score(av_p, ["resultados"])
nota_comp_lider = extract_score(av_p, ["competência"])
nota_pot_lider = extract_score(av_p, ["potencial"])

nbox_prev_res = nbox_raw.get("nota_resultados") or extract_score(nbox_raw, ["resultados"])
nbox_prev_pot = nbox_raw.get("nota_potencial") or extract_score(nbox_raw, ["potencial"])

def to_9box(v):
    if v is None: return None
    if v <= 2: return 1
    if v <= 3.5: return 2
    return 3

r9_lider = to_9box(nota_res_lider)
p9_lider = to_9box(nota_pot_lider)
r9_prev = to_9box(nbox_prev_res)
p9_prev = to_9box(nbox_prev_pot)
r9_auto = to_9box(nota_res_auto)

# Construir linhas comparativas — mapeamento por CONCEITO (igual ao gerar_exec_forms.py)
# AUTO:  Q1=Resultados Q2=Área Q3=Step Q4=Competências Q5=V+ Q6=V- Q7=MOTIVAÇÃO(SWAPPED) Q8=PDI(SWAPPED)
# LIDER: Q1=Resultados Q2=Área Q3=Step Q4=Competências Q5=POTENCIAL Q6=SCI Q7=EVOLUIR (Q8=Recomendacao removida)
# No RAW as chaves são o texto completo da pergunta → match por palavra-chave

def match_key(data, *keywords):
    for k, v in data.items():
        kl = k.lower()
        if all(kw.lower() in kl for kw in keywords):
            return v
    return ""

linhas = [
    ("1. Resultados",                  match_key(auto_p, "resultados", "ciclo"),                match_key(av_p, "resultados", "ciclo")),
    ("2. Entrega / Área",              match_key(auto_p, "quantos", "entregou"),               match_key(av_p, "quantos", "entregou")),
    ("3. Competências",                match_key(auto_p, "competências"),                      match_key(av_p, "competências")),
    ("4. Escala de Energia × Potencial", match_key(auto_p, "motivação"),                      match_key(av_p, "potencial")),
    ("5. Step × Step",                 match_key(auto_p, "step", "analisando"),                match_key(av_p, "pronto", "step")),
    ("6. Valor Vivido × SCI",          match_key(auto_p, "valor", "viveu"),                    match_key(av_p, "valor", "exemplo", "situação")),
    ("7. Valor Evoluir × Exemplo Evoluir", match_key(auto_p, "valor", "evoluir"),            match_key(av_p, "valor", "evoluir", "precisa")),
    ("8. PDI (Autoavaliação)",         match_key(auto_p, "carreira", "fazer"),                 ""),
]

def fmt_cell(v, color):
    if not v: return f'<div class="val {color} empty">—</div>'
    vs = str(v).strip()
    is_score = vs.replace(".","").replace(",","").isdigit() and len(vs) <= 4
    if is_score:
        return f'<div class="val {color} num">{vs}</div>'
    return f'<div class="val {color}">{vs}</div>'

# Construir linhas comparativas — DIV.STARS (padrão autoavaliação/líder)
# Para cada conceito: título + stars 1-5 com auto (amarelo) e líder (azul) sobrepostos
# Textos longos (não numéricos) aparecem abaixo dos stars

def is_numeric(v):
    if not v: return False
    vs = str(v).strip()
    return vs.replace(".","").replace(",","").isdigit() and len(vs) <= 4

def star_val(v):
    """Extrai valor numerico 1-5 de uma resposta."""
    try: return int(float(str(v).strip().replace(",",".")))
    except: return None

linhas_html = ""
for label, av, lv in linhas:
    n_auto = star_val(av)
    n_lider = star_val(lv)
    texto_auto = "" if n_auto is not None else str(av).strip() if av else ""
    texto_lider = "" if n_lider is not None else str(lv).strip() if lv else ""
    
    stars = ""
    for s_val in range(1, 6):
        cls = ""
        if n_auto == s_val and n_lider == s_val:
            cls = " mixed"
        elif n_lider == s_val:
            cls = " sel-lider"
        elif n_auto == s_val:
            cls = " sel-auto"
        stars += f'<button class="{cls}" data-value="{s_val}" onclick="toggleStar(this,{s_val})">{s_val}</button>'
    
    texts = ""
    if texto_auto:
        texts += f'<div class="resp auto-resp" title="Autoavaliação">{texto_auto}</div>'
    if texto_lider:
        texts += f'<div class="resp lider-resp" title="Líder">{texto_lider}</div>'
    
    linhas_html += f"""
  <div class="cmp-section">
    <div class="cmp-label">{label}</div>
    <div class="stars">{stars}</div>
    {texts}
  </div>"""

if not linhas:
    linhas_html = '<div class="empty-state">📋 Nenhuma avaliação registrada ainda. Os dados aparecerão aqui após o preenchimento.</div>'

# 9box grid
LABELS_9B = ["Risco","Dilema","Enigma","Efetivo","Mantenedor","Estrela","Dúvida","Talento","Forte"]
ninebox_cells = ""
for row in range(3,0,-1):
    for col in range(1,4):
        idx = (3-row)*3 + (col-1)
        label = LABELS_9B[idx]
        cls = ""
        if r9_lider == col and p9_lider == row: cls += " active-lider"
        if r9_auto == col: cls += " active-auto"
        if r9_prev == col and p9_prev == row: cls += " prev"
        ninebox_cells += f'<div class="nb{cls}">{label}</div>'

# PDI fields
pdi_comp = pdi_raw.get("competencia_foco", "")
pdi_gap = pdi_raw.get("gap_evidencia", "")
pdi_tipo = pdi_raw.get("tipo_acao", "")
pdi_desc = pdi_raw.get("descricao_acao", "")
pdi_prazo = pdi_raw.get("prazo", "")
pdi_evid = pdi_raw.get("evidencia_conclusao", "")

nota_res_v = nota_res_lider or ""
nota_pot_v = nota_pot_lider or ""

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>1x1 — {lider_nome} & {colab_nome}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--paper:#F4F6FA;--ink:#0C2440;--navy:#14365C;--navy-deep:#0A2138;--gold:#F4B72C;--gold-deep:#C98F0C;--muted:#5E748C;--line:#DCE3EC;--card:#FFFFFF;--auto-bg:#FFF8E1;--auto-border:#F4B72C;--lider-bg:#E8F0FE;--lider-border:#14365C}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--paper);color:var(--ink);font-family:'Inter',sans-serif;line-height:1.5;padding:0;height:100vh;overflow-y:auto;display:flex;flex-direction:column}}
body > header{{flex-shrink:0}}
.wrapper{{flex:1;display:grid;grid-template-columns:3fr 2fr;gap:0}}
.wrapper > div{{padding:20px}}
.wrapper > div:last-child{{background:var(--card);border-left:1px solid var(--line)}}
@media(max-width:960px){{.wrapper{{grid-template-columns:1fr}}}}
.sheet{{background:var(--card);box-shadow:0 12px 30px -14px rgba(12,36,64,.25),0 0 0 1px var(--line);margin-bottom:16px}}
header{{background:var(--navy-deep);color:#fff;padding:20px 28px}}
header .brand{{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}}
header .logo b{{color:var(--gold);font-family:'Sora',sans-serif;font-size:13px}}
header .logo span{{color:#AFC1D6;font-weight:600;font-size:13px}}
header .tag{{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);border:1px solid rgba(244,183,44,.4);padding:4px 8px;border-radius:4px}}
header h1{{font-family:'Sora',sans-serif;font-size:20px;font-weight:800;letter-spacing:-.02em;margin-top:10px}}
header h1 em{{color:var(--gold);font-style:normal}}
header .sub{{color:#AFC1D6;font-size:12px;margin-top:4px}}
.pad{{padding:20px 28px}}
.legend{{display:flex;gap:20px;margin-bottom:16px;font-size:11px;color:var(--muted)}}
.legend span{{display:flex;align-items:center;gap:6px}}
.dot{{width:12px;height:12px;border-radius:3px;display:inline-block}}
.dot.auto{{background:var(--auto-border)}}
.dot.lider{{background:var(--lider-border)}}
.header-row{{display:none}}
.row{{display:none}}
.lbl{{display:none}}
.cols{{display:none}}
.val{{display:none}}
.cmp-section{{padding:16px 28px;border-bottom:1px solid var(--line)}}
.cmp-label{{font-size:13px;font-weight:600;color:var(--navy);margin-bottom:10px;line-height:1.4}}
.stars{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px}}
.stars button{{width:44px;height:44px;border-radius:8px;border:1.5px solid var(--line);background:#FBFCFE;font-size:15px;font-weight:600;cursor:pointer;color:var(--muted);transition:all .15s}}
.stars button.sel-auto{{background:var(--auto-bg);border-color:var(--auto-border);color:#8B6914;font-weight:700}}
.stars button.sel-lider{{background:var(--lider-bg);border-color:var(--lider-border);color:#14365C;font-weight:700}}
.stars button.mixed{{background:linear-gradient(135deg,var(--auto-bg) 0% 50%,var(--lider-bg) 50% 100%);border-color:var(--auto-border);border-right-color:var(--lider-border);border-bottom-color:var(--lider-border);color:#14365C;font-weight:800}}
.resp{{font-size:12px;line-height:1.5;padding:8px 12px;border-radius:6px;margin-top:6px}}
.resp.auto-resp{{background:var(--auto-bg);border:1px solid var(--auto-border);color:##8B6914}}
.resp.lider-resp{{background:var(--lider-bg);border:1px solid var(--lider-border);color:##14365C}}
.empty-state{{padding:30px;text-align:center;color:var(--muted);font-size:13px}}
.justify{{margin-top:12px}}
.justify textarea{{width:100%;padding:10px 12px;border:1.5px solid var(--line);border-radius:8px;font-family:'Inter',sans-serif;font-size:13px;color:var(--ink);background:#FBFCFE;resize:vertical}}
.justify textarea:focus{{outline:none;border-color:var(--gold)}}
.justify label{{display:block;font-size:12px;font-weight:600;color:var(--navy);margin-bottom:5px}}
.nb-grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:4px;max-width:100%;margin:0 auto 12px}}
.nb-grid div{{border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:600;text-align:center;padding:14px 4px;color:var(--muted);border:1.5px solid var(--line);background:#FBFCFE;min-height:60px}}
.nb-grid div.active-lider{{box-shadow:0 0 0 3px var(--lider-border);font-weight:800;color:var(--lider-border);font-size:14px}}
.nb-grid div.active-auto{{box-shadow:0 0 0 3px var(--auto-border);font-weight:800;color:#8B6914;font-size:14px}}
.nb-grid div.prev{{background:#E8F0FE30;border-style:dashed}}
.nb-legend{{display:flex;gap:16px;justify-content:center;font-size:12px;color:var(--muted);margin-bottom:6px;flex-wrap:wrap}}
.nb-label{{font-size:12px;color:var(--muted);text-align:center;margin-bottom:16px}}
.pdi-field{{margin-bottom:12px}}
.pdi-field label{{display:block;font-size:13px;font-weight:600;color:var(--navy);margin-bottom:4px}}
.pdi-field input,.pdi-field textarea{{width:100%;padding:10px 12px;border:1.5px solid var(--line);border-radius:8px;font-family:'Inter',sans-serif;font-size:13px;color:var(--ink);background:#FBFCFE}}
.pdi-field textarea{{resize:vertical}}
.pdi-field input:focus,.pdi-field textarea:focus{{outline:none;border-color:var(--gold)}}
.btn-row{{text-align:right;margin-top:16px}}
.btn-row button{{background:var(--navy);color:#fff;border:none;padding:12px 28px;border-radius:8px;font-family:'Sora',sans-serif;font-size:14px;font-weight:600;cursor:pointer}}
.btn-row button:hover{{opacity:.9}}
#status{{text-align:right;margin-top:8px;font-size:12px;color:var(--gold-deep)}}
.thank-you{{display:none;text-align:center;padding:30px}}
.thank-you h3{{font-family:'Sora',sans-serif;font-size:18px;color:var(--navy);margin-bottom:8px}}
footer{{background:var(--navy-deep);color:#AFC1D6;padding:12px 28px;display:flex;justify-content:space-between;font-family:'IBM Plex Mono',monospace;font-size:10px;flex-wrap:wrap;gap:8px}}
footer b{{color:#fff}}
footer .gold{{color:var(--gold)}}
</style>
</head>
<body>

<header>
  <div class="brand"><div class="logo"><b>CondoConta</b><span> · People</span></div><div class="tag">1x1</div></div>
  <h1><em>{lider_nome}</em> ↔ <em>{colab_nome}</em></h1>
  <div class="sub">{colab_cargo} · {colab_area} · Ciclo 2026.2</div>
</header>

<div class="wrapper">
<div>

  <div class="sheet" id="form-section">
    <div class="pad" style="padding-top:12px">
      <div class="legend">
        <span><span class="dot auto"></span> Autoavaliação (Colaborador)</span>
        <span><span class="dot lider"></span> Avaliação do Líder</span>
      </div>
      <div class="header-row"><div>Pergunta</div><div>🟡 Autoavaliação</div><div>🔵 Líder</div></div>
      {linhas_html}
    </div>
    <div class="pad" style="border-top:1px solid var(--line)">
      <div class="justify">
        <label>📝 Justificativa / Feedback consensuado (1x1)</label>
        <textarea rows="4" id="justificativa" placeholder="Registre aqui os pontos discutidos no 1x1, alinhamentos e feedback..."></textarea>
      </div>
    </div>
    <div class="pad" style="border-top:1px solid var(--line)">
      <div class="btn-row">
        <button onclick="submitAll()">Salvar 1x1</button>
        <div id="status"></div>
      </div>
    </div>
    <div class="thank-you" id="thank-you">
      <h3>✅ 1x1 registrado com sucesso!</h3>
      <p>Obrigado por dedicar este tempo ao desenvolvimento do seu time.</p>
    </div>
  </div>

</div>

<div>
  <div class="sheet">
    <div class="pad">
      <h2 style="font-family:'Sora',sans-serif;font-size:15px;font-weight:700;color:var(--navy);margin-bottom:12px">🎯 Nine Box</h2>
      <div class="nb-legend">
        <span><span class="dot lider" style="background:var(--lider-border)"></span> Atual</span>
        <span><span class="dot auto" style="background:var(--auto-border)"></span> Autoavaliação</span>
        <span style="opacity:.6">┅ Anterior</span>
      </div>
      <div class="nb-grid">{ninebox_cells}</div>
      <div style="display:flex;justify-content:space-between;font-size:9px;color:var(--muted);margin:0 auto 0">
        <span style="flex:1;text-align:center">Baixo</span><span style="flex:1;text-align:center">Médio</span><span style="flex:1;text-align:center">Alto</span>
      </div>
      <div class="nb-label">Horizontal: Resultados · Vertical: Potencial</div>
      <div style="font-family:'Sora',sans-serif;font-size:11px;font-weight:700;color:var(--navy);margin-bottom:6px">🎯 Ajustar Posição</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        <div class="pdi-field">
          <label>Resultados (1-5)</label>
          <input type="number" min="1" max="5" step="0.5" id="nb_resultados" value="{nota_res_v}">
        </div>
        <div class="pdi-field">
          <label>Potencial (1-5)</label>
          <input type="number" min="1" max="5" step="0.5" id="nb_potencial" value="{nota_pot_v}">
        </div>
      </div>
    </div>
  </div>

  <div class="sheet" style="margin-top:16px">
    <div class="pad">
      <h2 style="font-family:'Sora',sans-serif;font-size:15px;font-weight:700;color:var(--navy);margin-bottom:12px">📈 PDI — Plano de Desenvolvimento</h2>
      <div class="pdi-field"><label>Competência foco</label><input type="text" id="pdi_competencia" value="{pdi_comp}" placeholder="Qual competência será o foco?"></div>
      <div class="pdi-field"><label>Gap / Evidência atual</label><textarea rows="2" id="pdi_gap" placeholder="Evidência do gap atual">{pdi_gap}</textarea></div>
      <div class="pdi-field"><label>Tipo de ação (70% prática / 20% social / 10% formal)</label><input type="text" id="pdi_tipo" value="{pdi_tipo}" placeholder="Ex: 70% prática — liderar squad"></div>
      <div class="pdi-field"><label>Descrição da ação</label><textarea rows="2" id="pdi_desc" placeholder="Descreva a ação">{pdi_desc}</textarea></div>
      <div class="pdi-field"><label>Prazo</label><input type="text" id="pdi_prazo" value="{pdi_prazo}" placeholder="Ex: 2026-12-31"></div>
      <div class="pdi-field"><label>Evidência de conclusão</label><textarea rows="2" id="pdi_evid" placeholder="Como comprovar a conclusão?">{pdi_evid}</textarea></div>
    </div>
  </div>
</div>
</div>

<footer><div><b>FALAI</b> · People</div><div class="gold">condoconta.com.br</div><div>by Falai — CC People</div></footer>

<input type="hidden" id="lider_id" value="{lider_id}">
<input type="hidden" id="colaborador_id" value="{colab_id}">
<input type="hidden" id="colaborador_nome" value="{colab_nome}">
<input type="hidden" id="area_val" value="{colab_area}">

<script>
var LIDER_ID = '{lider_id}';
var COL_ID = '{colab_id}';
var AREA = '{colab_area}';

function post(method, params){{
  return fetch('https://static-server.aiexpert-condoconta.info/proxy/condopower-rpc',{{
    method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{method:method,params:params}})
  }}).then(function(r){{return r.json()}});
}}

async function submitAll(){{
  var s = document.getElementById('status');
  s.textContent = 'Salvando...'; s.style.color = 'var(--gold-deep)';
  var just = document.getElementById('justificativa').value;
  var nb_r = document.getElementById('nb_resultados').value;
  var nb_p = document.getElementById('nb_potencial').value;
  var errors = [];
  if(just){{
    var r1 = await post('form.1x1',{{lider_id:LIDER_ID,colaborador_id:COL_ID,area:AREA,justificativa:just,data:new Date().toISOString().split('T')[0]}});
    if(!r1.ok) errors.push('1x1: '+(r1.error&&r1.error.message||'?'));
  }}
  if(nb_r && nb_p){{
    var r2 = await post('form.9box',{{lider_id:LIDER_ID,colaborador_id:COL_ID,area:AREA,nota_resultados:parseFloat(nb_r),nota_potencial:parseFloat(nb_p)}});
    if(!r2.ok) errors.push('9box: '+(r2.error&&r2.error.message||'?'));
  }}
  var pdi_c=document.getElementById('pdi_competencia').value,pdi_g=document.getElementById('pdi_gap').value,pdi_t=document.getElementById('pdi_tipo').value,pdi_d=document.getElementById('pdi_desc').value,pdi_p=document.getElementById('pdi_prazo').value,pdi_e=document.getElementById('pdi_evid').value;
  if(pdi_c||pdi_g||pdi_t||pdi_d||pdi_p||pdi_e){{
    var r3=await post('form.pdi',{{lider_id:LIDER_ID,colaborador_id:COL_ID,area:AREA,competencia_foco:pdi_c,gap_evidencia:pdi_g,tipo_acao:pdi_t,descricao_acao:pdi_d,prazo:pdi_p,evidencia_conclusao:pdi_e}});
    if(!r3.ok) errors.push('PDI: '+(r3.error&&r3.error.message||'?'));
  }}
  if(errors.length){{s.textContent='❌ Erros: '+errors.join('; ');s.style.color='#C62828';}}
  else if(!just && !nb_r && !nb_p && !pdi_c){{s.textContent='⚠️ Preencha ao menos a justificativa do 1x1.';s.style.color='#C62828';}}
  else{{s.textContent='✅ Salvo com sucesso!';s.style.color='#2E7D32';document.getElementById('thank-you').style.display='block';}}
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
    "-H", "accept: application/json", "-H", "X-Service-Account-Token: "+token,
    "-F", f"slug={slug}", "-F", f"file=@{html_path};type=text/html"
], capture_output=True, text=True, timeout=30)

code = r.stdout[-3:]; body = r.stdout[:-3]
if "200" in code:
    print(json.loads(body).get("url","ERRO"))
else:
    print(f"ERRO: {code} - {body[:200]}")