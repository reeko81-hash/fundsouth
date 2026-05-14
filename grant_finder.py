"""
Grant Finder - Google Custom Search + Claude API
Correr: python grant_finder.py
Abrir: http://localhost:5000
"""

from flask import Flask, render_template_string, request, jsonify, Response
import threading
import httpx
import json
import csv
import io
import itertools

app = Flask(__name__)

ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
GOOGLE_API = "https://www.googleapis.com/customsearch/v1"
MODEL = "claude-sonnet-4-20250514"

job = {"running": False, "logs": [], "results": [], "done": False, "total": 0, "current": 0}

HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Grant Finder</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0d0f12;--surf:#151820;--bord:#232730;--acc:#4ade80;--acc2:rgba(74,222,128,.12);--txt:#e8eaf0;--mut:#6b7280;--err:#f87171;--mono:'DM Mono',monospace;--sans:'DM Sans',sans-serif}
body{background:var(--bg);color:var(--txt);font-family:var(--sans);min-height:100vh;padding:40px 24px}
.wrap{max-width:980px;margin:0 auto}
h1{font-family:var(--mono);font-size:1rem;color:var(--acc);letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px}
.sub{color:var(--mut);font-size:.85rem;margin-bottom:32px}
.card{background:var(--surf);border:1px solid var(--bord);border-radius:8px;padding:24px;margin-bottom:16px}
.label{font-family:var(--mono);font-size:.65rem;text-transform:uppercase;letter-spacing:.1em;color:var(--mut);margin-bottom:14px}
input[type=text]{width:100%;background:var(--bg);border:1px solid var(--bord);color:var(--txt);font-family:var(--mono);font-size:.82rem;padding:9px 13px;border-radius:6px;outline:none}
input[type=text]:focus{border-color:var(--acc)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{display:inline-flex;align-items:center;gap:5px;padding:5px 12px;border:1px solid var(--bord);border-radius:20px;font-size:.76rem;cursor:pointer;transition:all .15s;color:var(--mut);user-select:none}
.chip:hover{border-color:var(--acc);color:var(--txt)}
.chip.on{background:var(--acc2);border-color:var(--acc);color:var(--acc)}
.chip input{display:none}
.prow{display:flex;align-items:center;gap:14px;margin-top:18px}
.prow span{font-family:var(--mono);font-size:.72rem;color:var(--mut)}
.dots{display:flex;gap:6px}
.dot{width:28px;height:28px;border-radius:50%;border:1px solid var(--bord);display:flex;align-items:center;justify-content:center;font-size:.72rem;font-family:var(--mono);cursor:pointer;color:var(--mut);transition:all .15s}
.dot:hover{border-color:var(--acc);color:var(--txt)}
.dot.on{background:var(--acc2);border-color:var(--acc);color:var(--acc)}
.btn{display:inline-flex;align-items:center;gap:7px;padding:11px 26px;border-radius:6px;font-family:var(--mono);font-size:.78rem;letter-spacing:.06em;cursor:pointer;border:none;text-transform:uppercase;transition:all .2s}
.btn-p{background:var(--acc);color:#0d0f12;font-weight:500}
.btn-p:hover{opacity:.85}
.btn-p:disabled{opacity:.3;cursor:not-allowed}
.btn-s{background:transparent;border:1px solid var(--bord);color:var(--mut)}
.btn-s:hover{border-color:var(--acc);color:var(--acc)}
.acts{display:flex;gap:10px;margin-top:6px}
#prog,#res{display:none;margin-top:16px}
.bar-wrap{background:var(--bg);border-radius:4px;height:4px;margin-bottom:14px;overflow:hidden}
.bar{height:100%;background:var(--acc);transition:width .4s;width:0}
.log{background:var(--bg);border:1px solid var(--bord);border-radius:6px;padding:12px;height:160px;overflow-y:auto;font-family:var(--mono);font-size:.73rem;line-height:1.7}
.ok{color:var(--acc)}.er{color:var(--err)}.inf{color:var(--mut)}.found{color:#facc15}
.rhead{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.cnt{font-family:var(--mono);font-size:.73rem;color:var(--acc)}
table{width:100%;border-collapse:collapse}
th{font-family:var(--mono);font-size:.62rem;text-transform:uppercase;letter-spacing:.1em;color:var(--mut);padding:9px 11px;text-align:left;border-bottom:1px solid var(--bord)}
td{padding:11px 11px;font-size:.81rem;border-bottom:1px solid rgba(35,39,48,.5);vertical-align:top;line-height:1.5}
tr:hover td{background:rgba(255,255,255,.02)}
.t-org{color:var(--acc);font-family:var(--mono);font-size:.72rem}
.t-dim{color:var(--mut);font-size:.76rem}
.t-lnk a{color:var(--acc);text-decoration:none;font-size:.73rem}
.t-lnk a:hover{text-decoration:underline}
.empty{text-align:center;padding:36px;color:var(--mut);font-size:.84rem}
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-thumb{background:var(--bord);border-radius:2px}
</style>
</head>
<body>
<div class="wrap">
  <h1>Grant Finder</h1>
  <p class="sub">Motor de búsqueda de convocatorias activas — powered by Google + Claude</p>

  <div class="card">
    <div class="label">Credenciales</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <div>
        <div style="font-size:.72rem;color:var(--mut);margin-bottom:6px">Google API Key</div>
        <input type="text" id="gkey" value="AIzaSyCw6unIBr_hDm4Ggli1HXekn0nIJEi_JGE">
      </div>
      <div>
        <div style="font-size:.72rem;color:var(--mut);margin-bottom:6px">Search Engine ID</div>
        <input type="text" id="gid" value="00cc63376c1fa4d7f">
      </div>
    </div>
  </div>

  <div class="card">
    <div class="label">Filtros de búsqueda</div>
    <div class="grid">
      <div>
        <div style="font-size:.72rem;color:var(--mut);margin-bottom:10px">Temáticas</div>
        <div class="chips" id="kw">
          <label class="chip on"><input type="checkbox" value="human rights" checked> Human Rights</label>
          <label class="chip on"><input type="checkbox" value="environment" checked> Environment</label>
          <label class="chip on"><input type="checkbox" value="WASH" checked> WASH</label>
          <label class="chip on"><input type="checkbox" value="sanitation" checked> Sanitation</label>
          <label class="chip on"><input type="checkbox" value="nutrition" checked> Nutrition</label>
          <label class="chip on"><input type="checkbox" value="refugees" checked> Refugees</label>
          <label class="chip on"><input type="checkbox" value="human rights defenders" checked> HR Defenders</label>
        </div>
      </div>
      <div>
        <div style="font-size:.72rem;color:var(--mut);margin-bottom:10px">Regiones</div>
        <div class="chips" id="reg">
          <label class="chip on"><input type="checkbox" value="Latin America" checked> Latin America</label>
          <label class="chip on"><input type="checkbox" value="Europe" checked> Europe</label>
          <label class="chip on"><input type="checkbox" value="Asia" checked> Asia</label>
          <label class="chip on"><input type="checkbox" value="Africa" checked> Africa</label>
          <label class="chip on"><input type="checkbox" value="Oceania" checked> Oceania</label>
          <label class="chip on"><input type="checkbox" value="North America" checked> North America</label>
        </div>
      </div>
    </div>
    <div class="prow">
      <span>Año:</span>
      <input type="text" id="yr" value="2025 2026" style="width:120px">
    </div>
  </div>

  <div class="acts">
    <button class="btn btn-p" id="runbtn" onclick="run()">▶ Buscar convocatorias</button>
    <button class="btn btn-s" id="stopbtn" style="display:none" onclick="stop()">■ Detener</button>
  </div>

  <div id="prog" class="card">
    <div class="label">Progreso — <span id="plabel">0 / 0</span></div>
    <div class="bar-wrap"><div class="bar" id="bar"></div></div>
    <div class="log" id="logbox"></div>
  </div>

  <div id="res" class="card">
    <div class="rhead">
      <div class="label" style="margin:0">Resultados</div>
      <div style="display:flex;gap:10px;align-items:center">
        <span class="cnt" id="cnt"></span>
        <button class="btn btn-s" onclick="dl()" style="padding:7px 14px">↓ CSV</button>
      </div>
    </div>
    <div id="rtable"></div>
  </div>
</div>

<script>
let poll;
document.querySelectorAll('.chip').forEach(c=>{
  c.addEventListener('click',()=>{c.classList.toggle('on');c.querySelector('input').checked=c.classList.contains('on')});
});

function checked(id){return[...document.querySelectorAll(`#${id} input:checked`)].map(i=>i.value)}

function log(msg,cls='inf'){
  const b=document.getElementById('logbox');
  const d=document.createElement('div');d.className=cls;d.textContent=msg;
  b.appendChild(d);b.scrollTop=b.scrollHeight;
}

async function run(){
  const gkey=document.getElementById('gkey').value.trim();
  const gid=document.getElementById('gid').value.trim();
  const kw=checked('kw');const reg=checked('reg');
  const yr=document.getElementById('yr').value.trim();
  if(!gkey||!gid){alert('Ingresá las credenciales de Google');return}
  if(!kw.length){alert('Seleccioná al menos una temática');return}
  document.getElementById('runbtn').disabled=true;
  document.getElementById('stopbtn').style.display='inline-flex';
  document.getElementById('prog').style.display='block';
  document.getElementById('res').style.display='none';
  document.getElementById('logbox').innerHTML='';
  document.getElementById('bar').style.width='0%';
  log('Generando queries de búsqueda...','inf');
  const r=await fetch('/start',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({gkey,gid,keywords:kw,regions:reg,year:yr})});
  const d=await r.json();
  if(d.error){log('Error: '+d.error,'er');reset();return}
  poll=setInterval(async()=>{
    const s=await(await fetch('/status')).json();
    document.getElementById('logbox').innerHTML='';
    s.logs.forEach(l=>{const d=document.createElement('div');d.className=l.c;d.textContent=l.m;document.getElementById('logbox').appendChild(d)});
    document.getElementById('logbox').scrollTop=document.getElementById('logbox').scrollHeight;
    if(s.total>0){const p=Math.round(s.current/s.total*100);document.getElementById('bar').style.width=p+'%';document.getElementById('plabel').textContent=s.current+' / '+s.total}
    if(s.done){clearInterval(poll);reset();showRes(s.results)}
  },1500);
}

function reset(){document.getElementById('runbtn').disabled=false;document.getElementById('stopbtn').style.display='none'}
async function stop(){await fetch('/stop',{method:'POST'});clearInterval(poll);reset()}

function showRes(r){
  document.getElementById('res').style.display='block';
  document.getElementById('cnt').textContent=r.length+' convocatorias';
  if(!r.length){document.getElementById('rtable').innerHTML='<div class="empty">No se encontraron convocatorias. Probá con otros filtros.</div>';return}
  let h='<table><thead><tr><th>Organización</th><th>Título</th><th>Temática</th><th>Región</th><th>Deadline</th><th>Link</th></tr></thead><tbody>';
  r.forEach(x=>{
    h+=`<tr><td class="t-org">${x.org||'—'}</td><td>${x.titulo||'—'}</td><td class="t-dim">${x.tematica||'—'}</td><td class="t-dim">${x.region||'—'}</td><td class="t-dim">${x.deadline||'—'}</td><td class="t-lnk">${x.link?`<a href="${x.link}" target="_blank">→ ver</a>`:'—'}</td></tr>`;
  });
  document.getElementById('rtable').innerHTML=h+'</tbody></table>';
}

function dl(){
  fetch('/export').then(r=>r.blob()).then(b=>{
    const u=URL.createObjectURL(b),a=document.createElement('a');
    a.href=u;a.download='grants_'+new Date().toISOString().slice(0,10)+'.csv';a.click();
  });
}
</script>
</body>
</html>"""

# ── Core logic ────────────────────────────────────────────────────────────────

def build_queries(keywords, regions, year):
    """Genera combinaciones de queries para Google."""
    queries = []
    for kw in keywords:
        for reg in regions:
            queries.append(f'"{kw}" "open call" OR "call for proposals" OR "grant" {reg} {year}')
    return queries


def google_search(query, api_key, cx, start=1):
    """Llama a Google Custom Search API."""
    params = {"key": api_key, "cx": cx, "q": query, "num": 10, "start": start}
    try:
        r = httpx.get(GOOGLE_API, params=params, timeout=15)
        if r.status_code != 200:
            return []
        items = r.json().get("items", [])
        return [{"title": i.get("title",""), "snippet": i.get("snippet",""), "link": i.get("link","")} for i in items]
    except Exception:
        return []


def parse_results(items, keywords, regions):
    """Usa Claude para identificar convocatorias reales en los resultados de Google."""
    if not items:
        return []
    text = "\n\n".join([f"TÍTULO: {i['title']}\nURL: {i['link']}\nDESCRIPCIÓN: {i['snippet']}" for i in items])
    prompt = f"""Analizá estos resultados de búsqueda de Google e identificá cuáles son convocatorias de grants o financiamiento ACTIVAS o próximas.

Temáticas buscadas: {', '.join(keywords)}
Regiones: {', '.join(regions)}

Respondé SOLO con un array JSON válido, sin texto ni markdown. Si no hay convocatorias reales, respondé [].
Cada objeto debe tener estas claves exactas:
- org: nombre de la organización convocante
- titulo: título de la convocatoria
- tematica: área temática
- region: foco geográfico
- deadline: fecha límite si está disponible, sino "No especificado"
- link: URL del resultado

Resultados de Google:
{text}"""
    try:
        r = httpx.post(ANTHROPIC_API,
            json={"model": MODEL, "max_tokens": 1500, "messages": [{"role": "user", "content": prompt}]},
            headers={"Content-Type": "application/json"}, timeout=30)
        if r.status_code != 200:
            return []
        raw = r.json()["content"][0]["text"].strip()
        raw = raw.replace("```json","").replace("```","").strip()
        result = json.loads(raw)
        return result if isinstance(result, list) else []
    except Exception:
        return []


def run_search(gkey, gid, keywords, regions, year):
    global job
    job["logs"] = []
    job["results"] = []
    job["done"] = False

    def log(m, c="inf"):
        job["logs"].append({"m": m, "c": c})

    queries = build_queries(keywords, regions, year)
    job["total"] = len(queries)
    log(f"{len(queries)} queries generadas")

    seen_links = set()

    for i, q in enumerate(queries, 1):
        if not job["running"]:
            break
        job["current"] = i
        log(f"[{i}/{len(queries)}] Buscando: {q[:60]}...")

        items = google_search(q, gkey, gid)
        if not items:
            log(f"  — Sin resultados", "inf")
            continue

        # Filtra duplicados
        new_items = [x for x in items if x["link"] not in seen_links]
        for x in new_items:
            seen_links.add(x["link"])

        if not new_items:
            log(f"  — Resultados ya procesados", "inf")
            continue

        results = parse_results(new_items, keywords, regions)
        if results:
            job["results"].extend(results)
            log(f"  ✓ {len(results)} convocatoria(s) encontrada(s)", "found")
        else:
            log(f"  — Sin convocatorias en estos resultados", "inf")

    log(f"Finalizado. {len(job['results'])} convocatorias encontradas.", "ok")
    job["done"] = True
    job["running"] = False


# ── Flask routes ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/start", methods=["POST"])
def start():
    global job
    if job["running"]:
        return jsonify({"error": "Ya hay una búsqueda en curso"})
    d = request.json
    job.update({"running": True, "current": 0, "total": 0, "logs": [], "results": [], "done": False})
    t = threading.Thread(target=run_search, args=(
        d["gkey"], d["gid"], d["keywords"], d["regions"], d.get("year","2025 2026")), daemon=True)
    t.start()
    return jsonify({"ok": True})

@app.route("/status")
def status():
    return jsonify(job)

@app.route("/stop", methods=["POST"])
def stop():
    job["running"] = False
    return jsonify({"ok": True})

@app.route("/export")
def export():
    out = io.StringIO()
    fields = ["org","titulo","tematica","region","deadline","link"]
    w = csv.DictWriter(out, fieldnames=fields)
    w.writeheader()
    for row in job["results"]:
        w.writerow({k: row.get(k,"") for k in fields})
    out.seek(0)
    return Response(out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition":"attachment; filename=grants.csv"})

if __name__ == "__main__":
    print("\n  Grant Finder en http://localhost:5000\n")
    app.run(debug=False, port=5000)
