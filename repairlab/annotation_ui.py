"""Local browser UI for prediction-blind human word-boundary annotation."""
import argparse
import hashlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HTML = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>RepairLab blind annotation</title><style>
:root{color-scheme:dark;--bg:#0b1020;--card:#151c31;--ink:#f4f6fb;--muted:#aab4ce;--accent:#62d6a7}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px system-ui,sans-serif}main{max-width:960px;margin:auto;padding:24px}.card{background:var(--card);padding:18px;border-radius:14px;margin:14px 0}audio,canvas{width:100%}canvas{height:150px;background:#0e1528;border:1px solid #34405d;border-radius:8px;cursor:crosshair}input,button{font:inherit;padding:8px;border-radius:8px}input{background:#0e1528;color:var(--ink);border:1px solid #34405d}button{border:0;font-weight:700;cursor:pointer}.mark{background:#e9efff;color:#11182b}.save{background:var(--accent);color:#09251b}.muted{color:var(--muted)}table{width:100%;border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #303a54;text-align:left}.done{color:var(--accent)}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media(max-width:650px){.grid{grid-template-columns:1fr}}</style></head><body><main>
<h1>RepairLab blind annotation</h1><p class="muted">Model predictions are not included. Annotate only what you hear and see in the waveform of your audio player.</p>
<section class="card"><audio id="audio" controls src="/audio.wav" preload="metadata"></audio><p class="muted">Waveform overview — click to seek. Zoom your browser for finer placement and replay each boundary.</p><canvas id="wave" width="900" height="150" aria-label="Audio waveform; click to seek"></canvas><p>Current time: <strong id="time">0.000</strong>s</p><div class="grid"><label>Annotator ID<input id="annotator" placeholder="ann-a"></label><label>Tool/version<input id="method" placeholder="RepairLab browser waveform v1"></label></div></section>
<section class="card"><table><thead><tr><th>#</th><th>Word</th><th>Start</th><th>End</th><th>Status</th></tr></thead><tbody id="rows"></tbody></table></section>
<button class="save" id="download">Download completed JSON</button> <button class="mark" id="reset">Clear saved progress</button><p id="message" class="muted"></p>
<script>const manifest=__MANIFEST__;const audio=document.getElementById('audio'),wave=document.getElementById('wave'),storageKey='repairlab-annotation-'+manifest.audio_sha256,values=new Map();let peaks=[];const esc=s=>{const d=document.createElement('div');d.textContent=s;return d.innerHTML};
try{const saved=JSON.parse(localStorage.getItem(storageKey)||'[]');for(const [i,v] of saved)if(Number.isInteger(i)&&v&&(Number.isFinite(v.start_seconds)||Number.isFinite(v.end_seconds)))values.set(i,v)}catch(_){localStorage.removeItem(storageKey)}
const saveProgress=()=>localStorage.setItem(storageKey,JSON.stringify([...values]));
function draw(){document.getElementById('rows').innerHTML=manifest.selected_words.map(w=>{const v=values.get(w.word_index)||{};return `<tr><td>${w.word_index}</td><td>${esc(w.word)}</td><td><button class="mark" data-kind="start" data-index="${w.word_index}">${v.start_seconds?.toFixed(3)??'Set start'}</button></td><td><button class="mark" data-kind="end" data-index="${w.word_index}">${v.end_seconds?.toFixed(3)??'Set end'}</button></td><td class="${v.start_seconds!==undefined&&v.end_seconds!==undefined&&v.start_seconds<v.end_seconds?'done':''}">${v.start_seconds!==undefined&&v.end_seconds!==undefined&&v.start_seconds<v.end_seconds?'Ready':'Incomplete'}</td></tr>`}).join('')}
function drawWave(){const c=wave.getContext('2d'),w=wave.width,h=wave.height;c.clearRect(0,0,w,h);c.strokeStyle='#62d6a7';c.beginPath();for(let x=0;x<peaks.length;x++){const a=peaks[x]*h*.46;c.moveTo(x,h/2-a);c.lineTo(x,h/2+a)}c.stroke();if(audio.duration){const x=audio.currentTime/audio.duration*w;c.strokeStyle='#ffcc66';c.beginPath();c.moveTo(x,0);c.lineTo(x,h);c.stroke()}}
fetch('/audio.wav').then(r=>r.arrayBuffer()).then(b=>new AudioContext().decodeAudioData(b)).then(buf=>{const data=buf.getChannelData(0),step=Math.max(1,Math.floor(data.length/wave.width));peaks=Array.from({length:wave.width},(_,x)=>{let p=0;for(let i=x*step;i<Math.min(data.length,(x+1)*step);i++)p=Math.max(p,Math.abs(data[i]));return p});drawWave()}).catch(()=>{wave.setAttribute('aria-label','Waveform unavailable; use audio controls')});
wave.addEventListener('click',e=>{if(audio.duration){const r=wave.getBoundingClientRect();audio.currentTime=Math.max(0,Math.min(audio.duration,(e.clientX-r.left)/r.width*audio.duration));drawWave()}});audio.addEventListener('timeupdate',()=>{document.getElementById('time').textContent=audio.currentTime.toFixed(3);drawWave()});document.getElementById('rows').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;const i=Number(b.dataset.index),v=values.get(i)||{};v[b.dataset.kind+'_seconds']=Number(audio.currentTime.toFixed(3));values.set(i,v);saveProgress();draw()});
document.getElementById('reset').addEventListener('click',()=>{if(confirm('Clear all locally saved timings for this recording?')){values.clear();localStorage.removeItem(storageKey);draw();document.getElementById('message').textContent='Local progress cleared.'}});
document.getElementById('download').addEventListener('click',()=>{const id=document.getElementById('annotator').value.trim(),method=document.getElementById('method').value.trim(),words=manifest.selected_words.map(w=>({...w,...(values.get(w.word_index)||{})}));if(!id||!method||words.some(w=>!(Number.isFinite(w.start_seconds)&&Number.isFinite(w.end_seconds)&&w.start_seconds<w.end_seconds&&w.end_seconds<=manifest.duration_seconds))){document.getElementById('message').textContent='Complete annotator ID, tool/version and every valid in-clip start/end pair first.';return}const result={evidence_type:'human_manual',audio_sha256:manifest.audio_sha256,duration_seconds:manifest.duration_seconds,annotation_method:method+'; model timestamps hidden',annotated_at:new Date().toISOString(),annotator_id:id,prediction_hidden:true,words};const blob=new Blob([JSON.stringify(result,null,2)+'\n'],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=manifest.clip_id+'-'+id+'.json';a.click();URL.revokeObjectURL(a.href);document.getElementById('message').textContent='Downloaded. Do not inspect model output before the second annotation is complete.'});draw();</script></main></body></html>'''


def load_package(package):
    root = Path(package).resolve()
    manifest_path, audio_path = root / "manifest.json", root / "audio.wav"
    if not manifest_path.is_file() or not audio_path.is_file():
        raise ValueError("Package needs manifest.json and audio.wav")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("format") != "repairlab-blind-annotation-v1" or manifest.get("prediction_included") is not False:
        raise ValueError("Require a prediction-free RepairLab annotation package")
    words = manifest.get("selected_words")
    if not isinstance(words, list) or not words:
        raise ValueError("Package needs selected_words")
    audio = audio_path.read_bytes()
    declared_hash = manifest.get("audio_sha256")
    actual_hash = hashlib.sha256(audio).hexdigest()
    if not isinstance(declared_hash, str) or declared_hash.lower() != actual_hash:
        raise ValueError("audio.wav does not match manifest audio_sha256")
    safe = json.dumps(manifest, separators=(",", ":")).replace("</", "<\\/")
    return HTML.replace("__MANIFEST__", safe).encode(), audio


def handler_for(package):
    page, audio = load_package(package)

    class Handler(BaseHTTPRequestHandler):
        server_version = "RepairLabAnnotation/1"
        def log_message(self, _format, *_args):
            return
        def _send(self, status, body, content_type):
            self.send_response(status); self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body))); self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; media-src 'self'")
            self.end_headers(); self.wfile.write(body)
        def do_GET(self):
            if self.path == "/": self._send(200, page, "text/html; charset=utf-8")
            elif self.path == "/audio.wav": self._send(200, audio, "audio/wav")
            elif self.path == "/health": self._send(200, b'{"status":"ok"}\n', "application/json")
            else: self._send(404, b'{"error":"not found"}\n', "application/json")
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), handler_for(args.package))
    print(f"RepairLab blind annotation: http://{args.host}:{server.server_port}")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()


if __name__ == "__main__":
    main()
