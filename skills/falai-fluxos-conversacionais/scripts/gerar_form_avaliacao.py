#!/usr/bin/env python3
"""
Gera formulario HTML de avaliacao (autoavaliacao ou lider) e publica no static server.
Uso: python3 gerar_form_avaliacao.py <email_colaborador> [auto|lider]

IMPORTANTE (21/08/2026):
- auto → busca APENAS em autoavaliacao_perguntas.json
- lider → busca APENAS em avaliacao_lider_perguntas.json
- NAO combinar os dois JSONs — cada tipo tem suas perguntas especificas
"""
import json, subprocess, sys, os

EMAIL = sys.argv[1] if len(sys.argv) > 1 else None
TIPO = sys.argv[2] if len(sys.argv) > 2 else "auto"

if not EMAIL:
    print("Uso: gerar_form_avaliacao.py <email> [auto|lider]")
    sys.exit(1)

with open("/opt/data/convenia/autoavaliacao_perguntas.json") as f:
    auto_data = json.load(f)

# Buscar nos JSONs - AUTO busca auto, LIDER busca apenas lider
all_cols = []
if TIPO == "lider":
    with open("/opt/data/convenia/avaliacao_lider_perguntas.json") as f:
        lider_data = json.load(f)
    for area in lider_data.get("areas", []):
        for col in area["colaboradores"]:
            all_cols.append(("lider", lider_data, col))
else:
    for area in auto_data.get("areas", []):
        for col in area["colaboradores"]:
            all_cols.append(("autoavaliacao", auto_data, col))

best = None
best_score = 0
email_parts = EMAIL.lower().replace("@condoconta.com.br","").replace("@","").split(".")

for t, src, col in all_cols:
    nome = col["nome"].lower()
    nome_parts = nome.split()
    score = 0
    if EMAIL.lower() == col.get("email", "").lower():
        best = (t, src, col)
        break
    for part in email_parts:
        for np in nome_parts:
            if len(np) >= 3 and np in part:
                score += 2
            elif len(np) >= 3 and part in np:
                score += 2
    if score > best_score:
        best_score = score
        best = (t, src, col)

if best and best_score >= 2:
    tipo_form, source_data, colaborador = best
else:
    print(f"Colaborador nao encontrado para: {EMAIL}")
    sys.exit(1)

# Gerar HTML
perguntas_html = ""
for p in colaborador["perguntas"]:
    n = p["n"]
    pergunta = p["pergunta"].replace('"', '&quot;')
    tipo = p["tipo"]
    if "Escala" in tipo:
        opcoes_html = "".join([
            f'<button onclick="selectStar(this,{n})">{opt}</button>'
            for opt in p.get("opcoes", ["1","2","3","4","5"])
        ])
        input_html = f'<div class="stars q{n}" id="stars{n}">{opcoes_html}</div><input type="hidden" name="q{n}" id="q{n}">'
    elif "Lista suspensa" in tipo or "suspensa" in tipo.lower():
        opcoes_html = "".join([
            f'<button onclick="selectReco(this,{n})">{opt}</button>'
            for opt in p.get("opcoes", [])
        ])
        input_html = f'<div class="reco q{n}" id="reco{n}">{opcoes_html}</div><input type="hidden" name="q{n}" id="q{n}">'
    else:
        input_html = f'<textarea rows="3" name="q{n}" placeholder="Sua resposta..."></textarea>'
    perguntas_html += f"""
    <div class="field">
      <label>{n}. {pergunta}</label>
      {input_html}
    </div>"""

titulo = "Autoavaliação" if tipo_form == "autoavaliacao" else "Avaliação do Líder"

# Tokens para o submit via API
with open("/opt/data/.env") as f_env:
    env_data = f_env.read()
sa_token = ""
auth_token = ""
for line in env_data.split("\n"):
    if line.startswith("CONDOPOWER_SA_TOKEN="):
        sa_token = line.strip().split("=",1)[1].strip('"').strip("'")
    if line.startswith("CONDOPOWER_AUTH="):
        auth_token = line.strip().split("=",1)[1].strip('"').strip("'")

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{titulo} — {colaborador["nome"]} — CondoConta</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--paper:#F4F6FA;--ink:#0C2440;--navy:#14365C;--navy-deep:#0A2138;--gold:#F4B72C;--gold-deep:#C98F0C;--muted:#5E748C;--line:#DCE3EC;--card:#FFFFFF}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--paper);color:var(--ink);font-family:'Inter',sans-serif;line-height:1.5;padding:40px 20px;-webkit-font-smoothing:antialiased}}
.sheet{{max-width:860px;margin:0 auto;background:var(--card);box-shadow:0 24px 60px -28px rgba(12,36,64,.35),0 0 0 1px var(--line)}}
header{{background:var(--navy-deep);color:#fff;padding:30px 44px}}
.brandrow{{display:flex;justify-content:space-between;align-items:center;margin-bottom:22px;flex-wrap:wrap;gap:8px}}
.logo{{display:flex;align-items:center;gap:10px;font-family:'Sora',sans-serif;font-weight:700;font-size:15px}}
.logo b{{color:var(--gold)}}.logo span{{color:#AFC1D6;font-weight:600}}
.tag-conf{{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--gold);border:1px solid rgba(244,183,44,.4);padding:5px 10px;border-radius:4px}}
header h1{{font-family:'Sora',sans-serif;font-size:28px;font-weight:800;letter-spacing:-.02em;line-height:1.1}}
header h1 em{{color:var(--gold);font-style:normal}}
.sub{{color:#AFC1D6;margin-top:8px;font-size:13px}}
.pad{{padding:30px 44px}}
.field{{margin-bottom:22px}}
.field label{{display:block;font-size:13px;font-weight:600;color:var(--navy);margin-bottom:7px;line-height:1.4}}
textarea{{width:100%;padding:11px 14px;border:1.5px solid var(--line);border-radius:8px;font-family:'Inter',sans-serif;font-size:14px;color:var(--ink);background:#FBFCFE;resize:vertical}}
textarea:focus{{outline:none;border-color:var(--gold)}}
.stars,.reco{{display:flex;gap:8px;flex-wrap:wrap}}
.stars button{{width:44px;height:44px;border-radius:8px;border:1.5px solid var(--line);background:#FBFCFE;font-size:15px;font-weight:600;cursor:pointer;color:var(--muted);transition:all .15s}}
.stars button.sel{{background:var(--gold);border-color:var(--gold);color:#fff}}
.reco button{{padding:9px 15px;border:1.5px solid var(--line);border-radius:20px;background:#FBFCFE;font-size:12.5px;cursor:pointer;color:var(--muted);transition:all .15s}}
.reco button.sel{{background:var(--navy);border-color:var(--navy);color:#fff}}
footer{{background:var(--navy-deep);color:#AFC1D6;padding:20px 44px;display:flex;justify-content:space-between;font-family:'IBM Plex Mono',monospace;font-size:10.5px;flex-wrap:wrap;gap:8px}}
footer b{{color:#fff}}footer .gold{{color:var(--gold)}}
</style>
</head>
<body>
<div class="sheet">
<header>
  <div class="brandrow">
    <div class="logo"><b>CondoConta</b><span>· People</span></div>
    <div class="tag-conf">Confidencial</div>
  </div>
  <h1>{titulo} <em>{colaborador["nome"]}</em></h1>
  <div class="sub">{colaborador["cargo"]} · {colaborador["area"]} · {colaborador.get("nivel","")} {colaborador.get("step","")} · Ciclo {source_data.get("ciclo","2026.2")}</div>
</header>
<section class="pad">
{perguntas_html}
<div style="text-align:right;margin-top:24px">
  <button onclick="enviarForm()" style="background:var(--navy);color:#fff;border:none;padding:14px 36px;border-radius:10px;font-family:'Sora',sans-serif;font-size:15px;font-weight:600;cursor:pointer">Enviar Avaliação</button>
</div>
<div id="status" style="text-align:right;margin-top:10px;font-size:13px;color:var(--gold-deep)"></div>
</section>
<footer>
  <div><b>FALAI</b> · People</div>
  <div class="gold">condoconta.com.br</div>
  <div>by Falai — CC People</div>
</footer>
</div>
<script>
function selectStar(btn,n){{var g=btn.parentElement;g.querySelectorAll('button').forEach(function(b){{b.classList.remove('sel')}});btn.classList.add('sel');document.getElementById('q'+n).value=btn.textContent;}}
function selectReco(btn,n){{var g=btn.parentElement;g.querySelectorAll('button').forEach(function(b){{b.classList.remove('sel')}});btn.classList.add('sel');document.getElementById('q'+n).value=btn.textContent;}}
function enviarForm(){{var data=new URLSearchParams();var fields=document.querySelectorAll('[name^=\\"q\\"]');fields.forEach(function(f){{if(f.value)data.append(f.name,f.value);}});data.append('method','desempenho.register_avaliacao');data.append('X-Service-Account-Token','{sa_token}');data.append('auth','{auth_token}');var s=document.getElementById('status');s.textContent='Enviando...';fetch('https://webhook-proxy.condoconta.com.br/webhooks/condopower-api/rpc',{{method:'POST',headers:{{'Content-Type':'application/x-www-form-urlencoded'}},body:data.toString()}}).then(function(r){{return r.json()}}).then(function(r){{if(r.ok){{s.textContent='Avaliacao enviada!';s.style.color='#2E7D32';}}else{{s.textContent='Erro: '+(r.error&&r.error.message||'desconhecido');s.style.color='#C62828';}}}}).catch(function(e){{s.textContent='Erro de conexao';s.style.color='#C62828';}});}}
</script>
</body>
</html>"""

# Salvar e publicar
slug = f"avaliacao-{colaborador['nome'].lower().replace(' ','-')[:40]}"
slug = slug.replace('á','a').replace('ã','a').replace('â','a').replace('é','e').replace('ê','e').replace('í','i').replace('ó','o').replace('ô','o').replace('õ','o').replace('ú','u').replace('ç','c')
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
    "-H", f"X-Service-Account-Token: {token}",
    "-F", f"slug={slug}",
    "-F", f"file=@{html_path};type=text/html"
], capture_output=True, text=True, timeout=30)

code = r.stdout[-3:]
body = r.stdout[:-3]
if "200" in code:
    data = json.loads(body)
    print(data.get("url", "ERRO"))
else:
    print(f"ERRO: {code} — {body}")