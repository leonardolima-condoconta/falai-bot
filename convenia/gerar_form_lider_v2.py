#!/usr/bin/env python3
"""
Gera formulario de avaliacao unificado para lideres.
Dropdown com liderados + perguntas dinamicas por liderado.
Uso: python3 gerar_form_lider.py <email_lider>
"""
import json, subprocess, sys

EMAIL = sys.argv[1] if len(sys.argv) > 1 else None
if not EMAIL:
    print("Uso: gerar_form_lider.py <email_lider>")
    sys.exit(1)

# 1. Buscar lider na API condopower-api
SA = ""
AUTH = ""
with open("/opt/data/.env") as f:
    for line in f:
        if line.startswith("CONDOPOWER_SA_TOKEN="):
            SA = line.strip().split("=",1)[1].strip('"').strip("'")
        if line.startswith("CONDOPOWER_AUTH="):
            AUTH = line.strip().split("=",1)[1].strip('"').strip("'")

r = subprocess.run([
    "curl", "-s", "-X", "POST",
    "https://webhook-proxy.condoconta.com.br/webhooks/condopower-api",
    "-H", "Content-Type: application/json",
    "-H", f"X-Service-Account-Token: {SA}",
    "-H", f"auth: {AUTH}",
    "-d", json.dumps({"method":"access.verify","params":{"identifier":EMAIL}})
], capture_output=True, text=True, timeout=30)

verify = json.loads(r.stdout)
if not verify.get("ok"):
    print(f"❌ Lider nao encontrado: {verify.get('error',{}).get('message','?')}")
    sys.exit(1)

result = verify["result"]
leader = result["employee"]
LEADER_ID = leader["id"]
reports = result.get("reports", [])

if not reports:
    print(f"❌ {leader['full_name']} nao tem liderados.")
    sys.exit(1)

print(f"✅ {leader['full_name']} — {len(reports)} liderados")

# 2. Carregar perguntas de avaliacao do lider
with open("/opt/data/convenia/avaliacao_lider_perguntas.json") as f:
    lider_json = json.load(f)

# 3. Para cada liderado, buscar perguntas no JSON
liderados_data = []
for rep in reports:
    nome_rep = rep["full_name"].lower()
    perguntas = None
    
    for area in lider_json.get("areas", []):
        for col in area["colaboradores"]:
            col_nome = col["nome"].lower()
            # Match por partes do nome
            parts = nome_rep.split()
            matches = sum(1 for p in parts if len(p) >= 3 and p in col_nome)
            if matches >= 2:
                perguntas = [{"n": p["n"], "pergunta": p["pergunta"], "tipo": p["tipo"], 
                              "opcoes": p.get("opcoes", [])} for p in col["perguntas"]]
                break
        if perguntas:
            break
    
    liderados_data.append({
        "id": rep["id"],
        "nome": rep["full_name"],
        "email": rep.get("email", ""),
        "cargo": rep.get("job", ""),
        "departamento": rep.get("department", ""),
        "perguntas": perguntas or [],
        "area_json": area["area"] if perguntas else ""
    })

liderados_json = json.dumps(liderados_data, ensure_ascii=False)

# 4. Gerar HTML
html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Avaliação de Liderados — {leader['full_name']} — CondoConta</title>
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
header h1{{font-family:'Sora',sans-serif;font-size:28px;font-weight:800;letter-spacing:-.02em;line-height:1.1;margin-top:8px}}
header h1 em{{color:var(--gold);font-style:normal}}
.pad{{padding:30px 44px}}
.field{{margin-bottom:22px}}
.field label{{display:block;font-size:13px;font-weight:600;color:var(--navy);margin-bottom:7px;line-height:1.4}}
select,textarea{{width:100%;padding:11px 14px;border:1.5px solid var(--line);border-radius:8px;font-family:'Inter',sans-serif;font-size:14px;color:var(--ink);background:#FBFCFE}}
select{{appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M6 8L1 3h10z' fill='%235E748C'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 14px center;padding-right:36px}}
select:focus,textarea:focus{{outline:none;border-color:var(--gold)}}
.stars,.reco{{display:flex;gap:8px;flex-wrap:wrap}}
.stars button{{width:44px;height:44px;border-radius:8px;border:1.5px solid var(--line);background:#FBFCFE;font-size:15px;font-weight:600;cursor:pointer;color:var(--muted);transition:all .15s}}
.stars button.sel{{background:var(--gold);border-color:var(--gold);color:#fff}}
.reco button{{padding:9px 15px;border:1.5px solid var(--line);border-radius:20px;background:#FBFCFE;font-size:12.5px;cursor:pointer;color:var(--muted);transition:all .15s}}
.reco button.sel{{background:var(--navy);border-color:var(--navy);color:#fff}}
.submit-row{{text-align:right;margin-top:24px}}
.submit-row button{{background:var(--navy);color:#fff;border:none;padding:14px 36px;border-radius:10px;font-family:'Sora',sans-serif;font-size:15px;font-weight:600;cursor:pointer}}
#status{{text-align:right;margin-top:10px;font-size:13px;color:var(--gold-deep)}}
#perguntas-container{{min-height:200px}}
.submit-row button:hover{{opacity:.9}}
.thank-you{{display:none;text-align:center;padding:60px 44px}}
.thank-you .emoji{{font-size:64px;margin-bottom:20px}}
.thank-you h3{{font-family:'Sora',sans-serif;font-size:24px;font-weight:700;color:var(--navy);margin-bottom:12px}}
.thank-you p{{font-size:14px;color:var(--muted);max-width:500px;margin:0 auto}}
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
  <h1>Avaliação de <em>Liderados</em></h1>
  <div style="color:#AFC1D6;font-size:13px;margin-top:4px">{leader['full_name']} · {leader.get('job','')} · {len(reports)} liderados</div>
</header>

<section class="pad" id="dropdown-section">
  <div class="field">
    <label>Selecione o liderado para avaliar</label>
    <select id="select-liderado" onchange="carregarPerguntas(this.value)">
      <option value="">Escolha um liderado...</option>
    </select>
  </div>
</section>

<section class="pad" style="border-top:1px solid var(--line)" id="perguntas-section" hidden>
  <div id="perguntas-container"></div>
  <div class="submit-row">
    <button onclick="enviarForm()">Enviar Avaliação</button>
    <div id="status"></div>
  </div>
</section>

<footer>
  <div><b>FALAI</b> · People</div>
  <div class="gold">condoconta.com.br</div>
  <div>by Falai — CC People</div>
</footer>
</div>

<script>
(function(){{
  if(document.cookie.indexOf('avaliacao_lider_respondida=1') >= 0){{
    document.getElementById('dropdown-section').style.display = 'none';
    document.getElementById('perguntas-section').style.display = 'none';
    document.getElementById('thank-you').style.display = 'block';
  }}
}})();
var LIDERADOS = {liderados_json};
var LEADER_EMAIL = "{leader.get('email','')}";
var LEADER_ID = "{LEADER_ID}";
var SA = "{SA}";
var AUTH = "{AUTH}";

// Preencher dropdown
var sel = document.getElementById('select-liderado');
LIDERADOS.forEach(function(l, i){{
  var o = document.createElement('option');
  o.value = i;
  o.textContent = l.nome + ' — ' + l.cargo;
  sel.appendChild(o);
}});

function carregarPerguntas(idx){{
  if(idx === '') {{
    document.getElementById('perguntas-section').hidden = true;
    return;
  }}
  var l = LIDERADOS[idx];
  var html = '<div style="color:var(--muted);font-size:12px;margin-bottom:18px">Avaliando: <b>' + l.nome + '</b> · ' + l.cargo + '</div>';
  l.perguntas.forEach(function(p){{
    var pKey = 'q'+p.n;
    var field = '<div class="field"><label>' + p.n + '. ' + p.pergunta + '</label>';
    if(p.tipo.indexOf('Escala') >= 0){{
      var ops = (p.opcoes || ['1','2','3','4','5']).map(function(x){{
        return '<button data-value="'+x+'" onclick="selStar(this,\\''+pKey+'\\')">'+x+'</button>';
      }}).join('');
      field += '<div class="stars">'+ops+'</div><input type="hidden" name="'+pKey+'" id="'+pKey+'" data-pergunta="' + p.pergunta.replace(/"/g,'&quot;') + '">';
    }} else if(p.tipo.indexOf('suspensa') >= 0 || p.tipo.indexOf('Lista') >= 0){{
      var ops = (p.opcoes || []).map(function(x){{
        return '<button data-value="'+x+'" onclick="selReco(this,\\''+pKey+'\\')">'+x+'</button>';
      }}).join('');
      field += '<div class="reco">'+ops+'</div><input type="hidden" name="'+pKey+'" id="'+pKey+'" data-pergunta="' + p.pergunta.replace(/"/g,'&quot;') + '">';
    }} else {{
      field += '<textarea rows="3" name="'+pKey+'" data-pergunta="' + p.pergunta.replace(/"/g,'&quot;') + '" placeholder="Sua resposta..."></textarea>';
    }}
    field += '</div>';
    html += field;
  }});
  html += '<input type="hidden" name="colaborador_id" value="' + l.id + '">';
  html += '<input type="hidden" name="colaborador_nome" value="' + l.nome + '">';
  html += '<input type="hidden" name="area" value="' + (l.departamento || l.area_json) + '">';
  html += '<input type="hidden" name="lider_email" value="' + LEADER_EMAIL + '">';
  html += '<input type="hidden" name="lider_id" value="' + LEADER_ID + '">';
  document.getElementById('perguntas-container').innerHTML = html;
  document.getElementById('perguntas-section').hidden = false;
  document.getElementById('status').textContent = '';
}}

function selStar(btn, id){{
  var g = btn.parentElement;
  g.querySelectorAll('button').forEach(function(b){{b.classList.remove('sel')}});
  btn.classList.add('sel');
  document.getElementById(id).value = btn.dataset.value;
}}

function selReco(btn, id){{
  var g = btn.parentElement;
  g.querySelectorAll('button').forEach(function(b){{b.classList.remove('sel')}});
  btn.classList.add('sel');
  document.getElementById(id).value = btn.dataset.value;
}}

function enviarForm(){{
  var s = document.getElementById('status');
  s.textContent = 'Salvando...';
  document.cookie = 'avaliacao_lider_respondida=1;max-age=864000;path=/';
  setTimeout(function(){{
    document.getElementById('perguntas-section').style.display = 'none';
    document.getElementById('dropdown-section').style.display = 'none';
    document.getElementById('thank-you').style.display = 'block';
  }}, 500);
}}
</script>
<div class="thank-you" id="thank-you">
<div class="emoji">🧡</div>
<h3>Agradecemos seu feedback!</h3>
<p>Sua avaliação de liderança foi registrada. Obrigado por dedicar este tempo ao desenvolvimento do seu time!</p>
</div>
</body>
</html>"""

# 5. Salvar e publicar
slug = f"avaliacao-lider-v2-{leader['full_name'].lower().replace(' ','-')[:50]}"
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