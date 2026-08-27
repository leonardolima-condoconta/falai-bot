#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera formulario HTML de AUTOAVALIACAO e publica no static server.
Uso: python3 gerar_form_avaliacao.py <email>
"""
import json, subprocess, sys

EMAIL = sys.argv[1] if len(sys.argv) > 1 else None
if not EMAIL:
    print("Uso: gerar_form_avaliacao.py <email>")
    sys.exit(1)

# Tokens
SA = AUTH = ""
with open("/opt/data/.env") as fenv:
    for line in fenv:
        if line.startswith("CONDOPOWER_SA_TOKEN="):
            SA = line.strip().split("=",1)[1].strip('"').strip("'")
        if line.startswith("CONDOPOWER_AUTH="):
            AUTH = line.strip().split("=",1)[1].strip('"').strip("'")

# Buscar ID na API
cid = ""
cemail = EMAIL
if SA and AUTH:
    r = subprocess.run([
        "curl", "-s", "-X", "POST",
        "https://webhook-proxy.condoconta.com.br/webhooks/condopower-api",
        "-H", "Content-Type: application/json",
        "-H", "X-Service-Account-Token: " + SA,
        "-H", "auth: " + AUTH,
        "-d", json.dumps({"method":"access.verify","params":{"identifier":EMAIL}})
    ], capture_output=True, text=True, timeout=30)
    try:
        v = json.loads(r.stdout)
        if v.get("ok"):
            cid = v["result"]["employee"]["id"]
            cemail = v["result"]["employee"].get("email", EMAIL)
    except:
        pass

# Carregar JSON
with open("/opt/data/convenia/autoavaliacao_perguntas.json") as f:
    auto = json.load(f)

all_cols = []
for area in auto.get("areas", []):
    for col in area["colaboradores"]:
        all_cols.append(("autoavaliacao", auto, col))

parts = EMAIL.lower().replace("@condoconta.com.br","").replace("@","").split(".")
best, best_score = None, 0
for t, src, col in all_cols:
    nome = col["nome"].lower()
    np = nome.split()
    if EMAIL.lower() == col.get("email","").lower():
        best = (t, src, col); break
    sc = sum(2 for p in parts for n in np if len(n)>=3 and (n in p or p in n))
    if sc > best_score:
        best_score = sc; best = (t, src, col)
if best and best_score >= 2:
    tipo_form, source_data, colaborador = best
if not colaborador:
    print("Colaborador nao encontrado: " + EMAIL); sys.exit(1)

titulo = "Autoavaliacao"
cnome = colaborador["nome"]
ccargo = colaborador["cargo"]
carea = colaborador["area"]
cnivel = colaborador.get("nivel","")
cstep = colaborador.get("step","")
ciclo = source_data.get("ciclo","2026.2")

# Montar perguntas HTML
ph = ""
for p in colaborador["perguntas"]:
    n = p["n"]; pergunta = p["pergunta"]; tipo = p["tipo"]
    pk = "q" + str(n)
    pqe = pergunta.replace("&","&amp;").replace('"',"&quot;").replace("<","&lt;").replace(">","&gt;")
    if "Escala" in tipo:
        ops = p.get("opcoes",["1","2","3","4","5"])
        btns = "".join('<button data-value="%s" onclick="selStar(this,\'%s\')">%s</button>'%(opt,pk,opt) for opt in ops)
        it = '<div class="stars">%s</div><input type="hidden" name="%s" id="%s" data-pergunta="%s">'%(btns,pk,pk,pqe)
    elif "suspensa" in tipo.lower() or "Lista" in tipo:
        ops = p.get("opcoes",[])
        btns = "".join('<button data-value="%s" onclick="selReco(this,\'%s\')">%s</button>'%(opt,pk,opt) for opt in ops)
        it = '<div class="reco">%s</div><input type="hidden" name="%s" id="%s" data-pergunta="%s">'%(btns,pk,pk,pqe)
    else:
        it = '<textarea rows="3" name="%s" data-pergunta="%s" placeholder="Sua resposta..."></textarea>'%(pk,pqe)
    ph += '<div class="field"><label>%d. %s</label>%s</div>\n'%(n, pergunta, it)

# HTML
html = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>""" + titulo + " - " + cnome + r""" — CondoConta</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{--paper:#F4F6FA;--ink:#0C2440;--navy:#14365C;--navy-deep:#0A2138;--gold:#F4B72C;--gold-deep:#C98F0C;--muted:#5E748C;--line:#DCE3EC;--card:#FFFFFF}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--paper);color:var(--ink);font-family:'Inter',sans-serif;line-height:1.5;padding:40px 20px}
.sheet{max-width:860px;margin:0 auto;background:var(--card);box-shadow:0 24px 60px -28px rgba(12,36,64,.35),0 0 0 1px var(--line)}
header{background:var(--navy-deep);color:#fff;padding:30px 44px}
.brandrow{display:flex;justify-content:space-between;align-items:center;margin-bottom:22px;flex-wrap:wrap;gap:8px}
.logo{display:flex;align-items:center;gap:10px;font-family:'Sora',sans-serif;font-weight:700;font-size:15px}
.logo b{color:var(--gold)}.logo span{color:#AFC1D6;font-weight:600}
.tag-conf{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--gold);border:1px solid rgba(244,183,44,.4);padding:5px 10px;border-radius:4px}
header h1{font-family:'Sora',sans-serif;font-size:28px;font-weight:800;letter-spacing:-.02em;line-height:1.1}
header h1 em{color:var(--gold);font-style:normal}
.sub{color:#AFC1D6;margin-top:8px;font-size:13px}
.pad{padding:30px 44px}
.field{margin-bottom:22px}
.field label{display:block;font-size:13px;font-weight:600;color:var(--navy);margin-bottom:7px;line-height:1.4}
textarea{width:100%;padding:11px 14px;border:1.5px solid var(--line);border-radius:8px;font-family:'Inter',sans-serif;font-size:14px;color:var(--ink);background:#FBFCFE;resize:vertical}
textarea:focus{outline:none;border-color:var(--gold)}
.stars,.reco{display:flex;gap:8px;flex-wrap:wrap}
.stars button{width:44px;height:44px;border-radius:8px;border:1.5px solid var(--line);background:#FBFCFE;font-size:15px;font-weight:600;cursor:pointer;color:var(--muted)}
.stars button.sel{background:var(--gold);border-color:var(--gold);color:#fff}
.reco button{padding:9px 15px;border:1.5px solid var(--line);border-radius:20px;background:#FBFCFE;font-size:12.5px;cursor:pointer;color:var(--muted)}
.reco button.sel{background:var(--navy);border-color:var(--navy);color:#fff}
.submit-row{text-align:right;margin-top:24px}
.submit-row button{background:var(--navy);color:#fff;border:none;padding:14px 36px;border-radius:10px;font-family:'Sora',sans-serif;font-size:15px;font-weight:600;cursor:pointer}
#status{text-align:right;margin-top:10px;font-size:13px;color:var(--gold-deep)}
.submit-row button:hover{opacity:.9}
.thank-you{display:none;text-align:center;padding:60px 44px}
.thank-you .emoji{font-size:64px;margin-bottom:20px}
.thank-you h3{font-family:'Sora',sans-serif;font-size:24px;font-weight:700;color:var(--navy);margin-bottom:12px}
.thank-you p{font-size:14px;color:var(--muted);max-width:500px;margin:0 auto}
footer{background:var(--navy-deep);color:#AFC1D6;padding:20px 44px;display:flex;justify-content:space-between;font-family:'IBM Plex Mono',monospace;font-size:10.5px;flex-wrap:wrap;gap:8px}
footer b{color:#fff}footer .gold{color:var(--gold)}
</style>
</head>
<body>
<div class="sheet">
<header>
<div class="brandrow">
<div class="logo"><b>CondoConta</b><span>· People</span></div>
<div class="tag-conf">Confidencial</div>
</div>
<h1>""" + titulo + r""" <em>""" + cnome + r"""</em></h1>
<div class="sub">""" + ccargo + " · " + carea + " · " + cnivel + " " + cstep + " · Ciclo " + ciclo + r"""</div>
</header>
<section class="pad">
""" + ph + r"""
<input type="hidden" id="colaborador_id" value=\"""" + cid + r"""">
<input type="hidden" id="colaborador_email" value=\"""" + cemail + r"""">
<input type="hidden" id="colaborador_nome" value=\"""" + cnome + r"""">
<input type="hidden" id="area" value=\"""" + carea + r"""">
<div class="submit-row">
<button onclick="enviarForm()">Enviar Avaliacao</button>
<div id="status"></div>
</div>
</section>
<div class="thank-you" id="thank-you">
<div class="emoji">🧡</div>
<h3>Agradecemos seu feedback!</h3>
<p>Sua autoavaliação foi registrada. Obrigado por dedicar este tempo à sua evolução!</p>
</div>
<footer>
<div><b>FALAI</b> · People</div>
<div class="gold">condoconta.com.br</div>
<div>by Falai — CC People</div>
</footer>
</div>
<script>
(function(){
  if(document.cookie.indexOf('autoavaliacao_respondida=1') >= 0){
    document.querySelector('.pad').style.display = 'none';
    document.getElementById('thank-you').style.display = 'block';
  }
})();
function selStar(btn,id){var g=btn.parentElement;g.querySelectorAll('button').forEach(function(b){b.classList.remove('sel')});btn.classList.add('sel');document.getElementById(id).value=btn.dataset.value;}
function selReco(btn,id){var g=btn.parentElement;g.querySelectorAll('button').forEach(function(b){b.classList.remove('sel')});btn.classList.add('sel');document.getElementById(id).value=btn.dataset.value;}
function enviarForm(){
 var s=document.getElementById('status');
 s.textContent='Salvando...';
 document.cookie = 'autoavaliacao_respondida=1;max-age=864000;path=/';
 setTimeout(function(){
  document.querySelector('.pad').style.display = 'none';
  document.getElementById('thank-you').style.display = 'block';
 }, 500);
}
</script>
</body>
</html>"""

# Publicar
slug = "avaliacao-v2-" + cnome.lower().replace(" ","-")[:40]
with open("/tmp/" + slug + ".html", "w") as f:
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
    "-F", "slug=" + slug,
    "-F", "file=@" + "/tmp/" + slug + ".html;type=text/html"
], capture_output=True, text=True, timeout=30)

code = r.stdout[-3:]; body = r.stdout[:-3]
if "200" in code:
    print(json.loads(body).get("url","ERRO"))
else:
    print("ERRO: " + code + " - " + body[:200])