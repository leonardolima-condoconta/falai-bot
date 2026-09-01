#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera formulario de avaliacao unificado para lideres.
Dropdown com liderados + perguntas dinamicas por liderado.
O access.verify e feito no NAVEGADOR (client-side) via /proxy, pois o container
nao alcanca a condopower-api. As perguntas vem do JSON embutido no HTML.
Uso: python3 gerar_form_lider.py <email_lider>
"""
import json, subprocess, sys

EMAIL = sys.argv[1] if len(sys.argv) > 1 else None
if not EMAIL:
    print("Uso: gerar_form_lider.py <email_lider>")
    sys.exit(1)

# 1. Carregar perguntas de avaliacao do lider (embutir no HTML)
with open("/opt/data/convenia/avaliacao_lider_perguntas.json") as f:
    lider_json = json.load(f)

# Montar mapa nome_normalizado -> perguntas (SEM a última pergunta de Recomendação)
def filtrar_perguntas(perguntas):
    # Remove a pergunta de "Recomendação" (última, tipo Lista suspensa)
    resultado = []
    for p in perguntas:
        texto = p.get("pergunta", "").lower()
        if "recomendação" in texto or "recomendacao" in texto:
            continue
        resultado.append({
            "n": p["n"], "pergunta": p["pergunta"], "tipo": p["tipo"],
            "opcoes": p.get("opcoes", [])
        })
    return resultado

perguntas_map = {}
for area in lider_json.get("areas", []):
    for col in area["colaboradores"]:
        nome = col["nome"]
        key = nome.lower()
        perguntas_map[key] = filtrar_perguntas(col["perguntas"])
        partes = nome.lower().split()
        if partes:
            perguntas_map[partes[0]] = perguntas_map[key]

# Tambem indexar por nome sem acentos (aproximacao)
import unicodedata
def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

for area in lider_json.get("areas", []):
    for col in area["colaboradores"]:
        nome = col["nome"]
        key = strip_accents(nome.lower())
        perguntas_map[key] = filtrar_perguntas(col["perguntas"])

perguntas_map_json = json.dumps(perguntas_map, ensure_ascii=False)

# Mapa de senioridade: nome → {senioridade, nivel_senioridade}
senioridade_map = {}
for area in lider_json.get("areas", []):
    for col in area["colaboradores"]:
        nome = col["nome"]
        sen = col.get("senioridade","") or col.get("nivel","")
        nv = col.get("nivel_senioridade","") or col.get("step","")
        if sen or nv:
            senioridade_map[nome.lower()] = {"senioridade": sen, "nivel_senioridade": nv}
            if nome.lower().split():
                senioridade_map[nome.lower().split()[0]] = {"senioridade": sen, "nivel_senioridade": nv}
            key = strip_accents(nome.lower())
            senioridade_map[key] = {"senioridade": sen, "nivel_senioridade": nv}
senioridade_map_json = json.dumps(senioridade_map, ensure_ascii=False)

# Mapa de step_atual: nome → descricao do step atual
step_atual_map = {}
for area in lider_json.get("areas", []):
    for col in area["colaboradores"]:
        nome = col["nome"]
        sat = col.get("step_atual","")
        if sat:
            step_atual_map[nome.lower()] = sat
            if nome.lower().split():
                step_atual_map[nome.lower().split()[0]] = sat
            key = strip_accents(nome.lower())
            step_atual_map[key] = sat
step_atual_json = json.dumps(step_atual_map, ensure_ascii=False)

# 2. Gerar HTML (sem access.verify no Python)
html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Avaliação de Liderados — CondoConta</title>
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
.sub{{color:#AFC1D6;margin-top:6px;font-size:13px}}
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
  <div class="sub" id="header-sub">Carregando...</div>
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
var LIDER_EMAIL = {json.dumps(EMAIL)};
var PERGUNTAS_MAP = {perguntas_map_json};
var SENIORIDADE_MAP = {senioridade_map_json};
var STEP_ATUAL_MAP = {step_atual_json};
var LIDERADOS = [];
var LEADER_ID = '';
var LEADER_NOME = '';
var LEADER_CARGO = '';

function matchSenioridade(nome){{
  var key = stripAccents(nome.toLowerCase());
  if(SENIORIDADE_MAP[key]) return SENIORIDADE_MAP[key];
  var partes = stripAccents(nome.toLowerCase()).split(' ');
  for(var i=0;i<partes.length;i++){{
    if(SENIORIDADE_MAP[partes[i]]) return SENIORIDADE_MAP[partes[i]];
  }}
  return {{}};
}}

function matchStepAtual(nome){{
  var key = stripAccents(nome.toLowerCase());
  if(STEP_ATUAL_MAP[key]) return STEP_ATUAL_MAP[key];
  var partes = stripAccents(nome.toLowerCase()).split(' ');
  for(var i=0;i<partes.length;i++){{
    if(STEP_ATUAL_MAP[partes[i]]) return STEP_ATUAL_MAP[partes[i]];
  }}
  return '';
}}

function stripAccents(s){{ return s.normalize('NFD').replace(/[\\u0300-\\u036f]/g,''); }}

function matchPerguntas(nome){{
  var key = stripAccents(nome.toLowerCase());
  if(PERGUNTAS_MAP[key]) return PERGUNTAS_MAP[key];
  // match por primeiro nome
  var partes = stripAccents(nome.toLowerCase()).split(' ');
  for(var i=0;i<partes.length;i++){{
    if(PERGUNTAS_MAP[partes[i]]) return PERGUNTAS_MAP[partes[i]];
  }}
  // match parcial: algum colaborador do mapa cujo nome contenha o nome do report
  for(var k in PERGUNTAS_MAP){{
    if(k.indexOf(partes[0]) >= 0) return PERGUNTAS_MAP[k];
  }}
  return [];
}}

function getFeitos(){{ try{{ var c=document.cookie.split('; ').find(function(r){{return r.startsWith('avaliacao_lider_feitos=')}}); return c?JSON.parse(decodeURIComponent(c.split('=')[1])):[]; }} catch(e){{ return []; }} }}
function setFeitos(list){{ document.cookie='avaliacao_lider_feitos='+encodeURIComponent(JSON.stringify(list))+';max-age=864000;path=/'; }}
function rebuildDropdown(){{
  var feitos=getFeitos(),sel=document.getElementById('select-liderado');
  sel.innerHTML='<option value="">Escolha um liderado...</option>';
  LIDERADOS.forEach(function(l,i){{
    if(feitos.indexOf(l.id)<0){{
      var srLabel = l.senioridade ? ' · ' + l.senioridade + (l.nivel_senioridade ? ' ' + l.nivel_senioridade : '') : '';
      var o=document.createElement('option'); o.value=i; o.textContent=l.nome + ' — ' + l.cargo + srLabel; sel.appendChild(o);
    }}
  }});
  if(sel.options.length===1){{
    document.getElementById('dropdown-section').style.display='none';
    document.getElementById('perguntas-section').hidden=true;
    document.getElementById('thank-you').style.display='block';
  }}
}}

// Init: access.verify client-side
(function(){{
  fetch('https://static-server.aiexpert-condoconta.info/proxy/condopower-rpc',{{
    method:'POST',
    headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{method:'access.verify',params:{{identifier:LIDER_EMAIL}}}})
  }}).then(function(r){{return r.json()}}).then(function(r){{
    if(r.ok && r.result && r.result.employee){{
      var emp = r.result.employee;
      LEADER_ID = emp.id;
      LEADER_NOME = emp.full_name;
      LEADER_CARGO = emp.job || '';
      var reports = r.result.reports || [];
      document.getElementById('header-sub').textContent = LEADER_NOME + ' · ' + LEADER_CARGO + ' · ' + reports.length + ' liderados';
      LIDERADOS = reports.map(function(rep){{
        var sr = matchSenioridade(rep.full_name);
        return {{
          id: rep.id,
          nome: rep.full_name,
          email: rep.email || '',
          cargo: rep.job || '',
          departamento: rep.department || '',
          senioridade: sr.senioridade || '',
          nivel_senioridade: sr.nivel_senioridade || '',
          perguntas: matchPerguntas(rep.full_name)
        }};
      }});
      rebuildDropdown();
    }} else {{
      document.getElementById('header-sub').textContent = 'Não foi possível identificar o líder.';
    }}
  }}).catch(function(e){{
    document.getElementById('header-sub').textContent = 'Erro de conexão ao identificar o líder.';
    console.error(e);
  }});
}})();

function carregarPerguntas(idx){{
  if(idx === '') {{
    document.getElementById('perguntas-section').hidden = true;
    return;
  }}
  var l = LIDERADOS[idx];
  var srInfo = l.senioridade ? ' · ' + l.senioridade + (l.nivel_senioridade ? ' ' + l.nivel_senioridade : '') : '';
  var stepInfo = matchStepAtual(l.nome);
  var html = '<div style="color:var(--muted);font-size:12px;margin-bottom:6px">Avaliando: <b>' + l.nome + '</b> · ' + l.cargo + srInfo + '</div>';
  if(stepInfo){{
    html += '<div style="background:var(--lider-bg);border:1px solid var(--lider-border);border-radius:6px;padding:10px 12px;margin-bottom:18px;font-size:11px;color:var(--navy);line-height:1.5"><span style="font-weight:700;font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)">Step Atual</span><br>' + stepInfo + '</div>';
  }}
  if(!l.perguntas || l.perguntas.length===0){{
    html += '<div style="color:#C62828;font-size:13px">⚠️ Nenhuma pergunta configurada para este liderado no ciclo atual.</div>';
  }} else {{
    l.perguntas.forEach(function(p){{
      var pKey = 'q'+p.n;
      var field = '<div class="field"><label>' + p.n + '. ' + p.pergunta + '</label>';
      if(p.tipo.indexOf('Escala') >= 0){{
        var ops = (p.opcoes || ['1','2','3','4','5']).map(function(x){{
          return '<button data-value="'+x+'" onclick="selStar(this,\\''+pKey+'\\')">'+x+'</button>';
        }}).join('');
        field += '<div class="stars">'+ops+'</div><input type="hidden" name="'+pKey+'" id="'+pKey+'" data-pergunta="' + p.pergunta.replace(/"/g,'&quot;') + '">';
      }} else if(p.tipo.indexOf('suspensa') >= 0 || p.tipo.indexOf('Lista') >= 0){{
        var ops2 = (p.opcoes || []).map(function(x){{
          return '<button data-value="'+x+'" onclick="selReco(this,\\''+pKey+'\\')">'+x+'</button>';
        }}).join('');
        field += '<div class="reco">'+ops2+'</div><input type="hidden" name="'+pKey+'" id="'+pKey+'" data-pergunta="' + p.pergunta.replace(/"/g,'&quot;') + '">';
      }} else {{
        field += '<textarea rows="3" name="'+pKey+'" data-pergunta="' + p.pergunta.replace(/"/g,'&quot;') + '" placeholder="Sua resposta..."></textarea>';
      }}
      field += '</div>';
      html += field;
    }});
  }}
  html += '<input type="hidden" name="colaborador_id" value="' + l.id + '">';
  html += '<input type="hidden" name="colaborador_nome" value="' + l.nome + '">';
  html += '<input type="hidden" name="area" value="' + (l.departamento || '') + '">';
  html += '<input type="hidden" name="lider_email" value="' + LIDER_EMAIL + '">';
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
  // validacao: todas as perguntas
  var vazios = [];
  document.querySelectorAll('#perguntas-container [data-pergunta]').forEach(function(f){{
    if(!f.value) vazios.push(f);
  }});
  if(vazios.length>0){{
    s.textContent='⚠️ Preencha todas as perguntas ('+vazios.length+' pendente'+(vazios.length>1?'s':'')+').';
    s.style.color='#C62828';
    vazios[0].scrollIntoView({{behavior:'smooth',block:'center'}});
    return;
  }}
  var perguntas = {{}};
  var fields = document.querySelectorAll('#perguntas-container [name]');
  var colaborador_id = '';
  var colaborador_nome = '';
  var area = '';
  var lider_email = '';
  var lider_id = '';
  fields.forEach(function(f){{
    var name = f.name;
    if(name === 'colaborador_id') colaborador_id = f.value;
    else if(name === 'colaborador_nome') colaborador_nome = f.value;
    else if(name === 'area') area = f.value;
    else if(name === 'lider_email') lider_email = f.value;
    else if(name === 'lider_id') lider_id = f.value;
    else if(f.value && f.dataset.pergunta) perguntas[f.dataset.pergunta] = f.value;
  }});
  s.textContent = 'Enviando...';
  fetch('https://static-server.aiexpert-condoconta.info/proxy/condopower-rpc',{{
    method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{method:'form.avaliacao_lider',params:{{
      lider_email: lider_email,
      lider_id: lider_id,
      colaborador_id: colaborador_id,
      colaborador_nome: colaborador_nome,
      area: area,
      perguntas: perguntas
    }}}})
  }}).then(function(r){{return r.json()}}).then(function(r){{
    if(r.ok){{
      var feitos=getFeitos();
      if(feitos.indexOf(colaborador_id)<0) feitos.push(colaborador_id);
      setFeitos(feitos);
      var sel=document.getElementById('select-liderado');
      document.getElementById('perguntas-section').hidden=true;
      sel.value='';
      rebuildDropdown();
      document.getElementById('status').textContent='✅ Avaliado com sucesso!';
      s.style.color='#2E7D32';
    }} else {{
      s.textContent='❌ Erro: '+(r.error&&r.error.message||'?');s.style.color='#C62828';
    }}
  }}).catch(function(e){{s.textContent='❌ Erro de conexão';s.style.color='#C62828';}});
}}
</script>
<div class="thank-you" id="thank-you">
<div class="emoji">🧡</div>
<h3>Agradecemos seu feedback!</h3>
<p>Sua avaliação de liderança foi registrada. Obrigado por dedicar este tempo ao desenvolvimento do seu time!</p>
</div>
</body>
</html>"""

# 3. Salvar e publicar
slug = "avaliacao-lider-" + EMAIL.lower().split("@")[0].replace(".", "-").replace(" ", "-")[:50]
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

code = r.stdout[-3:]
body = r.stdout[:-3]
if "200" in code:
    data = json.loads(body)
    print(data.get("url", "ERRO"))
else:
    print(f"ERRO: {code} - {body[:200]}")