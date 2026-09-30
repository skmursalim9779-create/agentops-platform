DASHBOARD_HTML = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AgentOps Platform</title>
<style>
:root{--bg:#fff;--fg:#1a1a1a;--mut:#666;--card:#f4f5f7;--acc:#2563eb;--err:#dc2626}
@media(prefers-color-scheme:dark){:root{--bg:#111318;--fg:#e8e8e8;--mut:#9aa;--card:#1c1f27;--acc:#60a5fa;--err:#f87171}}
body{font:14px system-ui,sans-serif;background:var(--bg);color:var(--fg);margin:0;padding:16px;max-width:960px;margin:auto}
h1{font-size:20px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px}
.card{background:var(--card);border-radius:10px;padding:12px}.card b{display:block;font-size:20px;color:var(--acc)}
.card span{color:var(--mut);font-size:12px}table{width:100%;border-collapse:collapse;margin-top:8px}
td,th{padding:6px 8px;text-align:left;border-bottom:1px solid var(--card)}.wrap{overflow-x:auto}
tr.t{cursor:pointer}.err{color:var(--err)}pre{background:var(--card);padding:10px;border-radius:8px;overflow-x:auto;white-space:pre-wrap}
</style></head><body>
<h1>AgentOps Platform</h1><div class="grid" id="cards"></div>
<h2>By model</h2><div class="wrap"><table id="models"></table></div>
<h2>Traces</h2><div class="wrap"><table id="traces"></table></div><h2>Trace detail</h2><pre id="detail">Click a trace.</pre>
<script>
const f=(n,d=4)=>Number(n||0).toFixed(d), esc=s=>String(s??"").replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
async function load(){
 const s=await (await fetch("/api/stats")).json(), t=s.totals;
 document.getElementById("cards").innerHTML=[["Traces",t.traces],["Spans",t.spans],["Cost (USD)","$"+f(t.cost_usd)],
  ["Tokens in",t.tokens_in],["Tokens out",t.tokens_out],["Errors",t.errors]].map(([a,b])=>`<div class="card"><b>${b}</b><span>${a}</span></div>`).join("");
 document.getElementById("models").innerHTML="<tr><th>Model</th><th>Calls</th><th>Cost</th><th>Avg ms</th></tr>"+
  s.by_model.map(m=>`<tr><td>${esc(m.model)}</td><td>${m.calls}</td><td>$${f(m.cost_usd)}</td><td>${f(m.avg_latency_ms,1)}</td></tr>`).join("");
 const tr=await (await fetch("/api/traces")).json();
 document.getElementById("traces").innerHTML="<tr><th>Trace</th><th>Root</th><th>Spans</th><th>Cost</th><th>Err</th></tr>"+
  tr.map(x=>`<tr class="t" onclick="show('${x.trace_id}')"><td>${x.trace_id.slice(0,10)}</td><td>${esc(x.root||"-")}</td><td>${x.spans}</td><td>$${f(x.cost_usd)}</td><td class="${x.errors?"err":""}">${x.errors}</td></tr>`).join("");
}
async function show(id){const sp=await (await fetch("/api/traces/"+id)).json();
 document.getElementById("detail").textContent=sp.map(x=>`${x.kind.padEnd(9)} ${x.name}  ${((x.end_ts-x.start_ts)*1000).toFixed(1)}ms  $${f(x.cost_usd,6)}  ${x.status}\\n   in: ${(x.input||"").slice(0,120)}\\n  out: ${(x.output||"").slice(0,120)}`).join("\\n\\n");}
load();setInterval(load,5000);
</script></body></html>"""
