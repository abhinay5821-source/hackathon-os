"""Local, dependency-light review dashboard for RepairLab pair analyses."""
import argparse
import base64
import binascii
import json
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from repairlab.analyze import analyze_pair


MAX_REQUEST_BYTES = 6 * 1024 * 1024


HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>RepairLab review</title><style>
:root{color-scheme:dark;--bg:#0b1020;--card:#151c31;--ink:#f4f6fb;--muted:#aab4ce;--base:#55c2ff;--part:#ffba52}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:28px}h1{margin:0 0 6px}.muted{color:var(--muted)}.card{background:var(--card);padding:18px;border-radius:14px;margin:16px 0}form{display:grid;grid-template-columns:1fr 1fr;gap:12px}label{display:grid;gap:6px}input,button,select{font:inherit}input[type=file],input[type=number],select{background:#0e1528;color:var(--ink);padding:10px;border:1px solid #34405d;border-radius:8px}button{background:#e9efff;color:#11182b;border:0;border-radius:9px;padding:10px;font-weight:700;cursor:pointer}form>button{grid-column:1/-1}.play-region{white-space:nowrap;padding:6px 9px}button:disabled{opacity:.55}.audio-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.audio-grid audio{width:100%;margin-top:6px}canvas{width:100%;height:230px;background:#0e1528;border-radius:10px}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:9px;border-bottom:1px solid #303a54;vertical-align:top}.pill{display:inline-block;background:#522738;color:#ffd9df;border-radius:999px;padding:3px 8px}.error{color:#ff9bad;white-space:pre-wrap}@media(max-width:700px){form,.audio-grid{grid-template-columns:1fr}main{padding:16px}}
</style></head><body><main><h1>RepairLab review</h1><p class="muted">Transparent comparison, not a clinical or delivery-quality score.</p>
<section class="card"><form id="form"><label>Baseline WAV (16 kHz mono PCM)<input id="ba" type="file" accept="audio/wav" required></label><label>Participant WAV (16 kHz mono PCM)<input id="pa" type="file" accept="audio/wav" required></label><label>Baseline forced alignment JSON<input id="bj" type="file" accept="application/json" required></label><label>Participant forced alignment JSON<input id="pj" type="file" accept="application/json" required></label><label>Development threshold<input id="threshold" type="number" min="0.1" step="0.1" value="2.5" required></label><button id="run">Analyze pair</button></form><p id="message" class="muted"></p></section>
<section id="results" hidden><div class="card"><h2>Evidence playback</h2><div class="audio-grid"><label>Baseline<audio id="baseline-audio" controls preload="metadata"></audio></label><label>Participant<audio id="participant-audio" controls preload="metadata"></audio></label></div></div>
<div class="card"><h2>Acoustic overlay</h2><label>Feature<select id="feature"><option value="energy_db">Energy (dB)</option><option value="f0_hz">Pitch (Hz)</option><option value="spectral_centroid_hz">Spectral centroid (Hz)</option><option value="zero_crossing_rate">Zero-crossing rate</option></select></label><canvas id="chart" width="1000" height="230"></canvas><p class="muted">Baseline <span style="color:var(--base)">blue</span>; participant <span style="color:var(--part)">amber</span>; flagged participant intervals <span style="color:#ff7890">red</span>. Each recording retains its own timeline.</p></div>
<div class="card"><h2>Flagged regions</h2><div id="regions"></div></div><div class="card"><h2>Uncertainty</h2><ul id="uncertainty"></ul></div></section><p id="error" class="error"></p></main>
<script>
const $=id=>document.getElementById(id),state={result:null,urls:[],stopAt:null};
const b64=file=>new Promise((ok,no)=>{const r=new FileReader();r.onerror=no;r.onload=()=>ok(r.result.split(',')[1]);r.readAsDataURL(file)});
const labels={energy_db:'dB',f0_hz:'Hz',spectral_centroid_hz:'Hz',zero_crossing_rate:''};
function line(ctx,values,times,duration,color,min,max){ctx.strokeStyle=color;ctx.lineWidth=2;ctx.beginPath();let begun=false;values.forEach((v,i)=>{if(v===null)return;const x=35+930*times[i]/duration,y=205-(v-min)*180/(max-min||1);begun?ctx.lineTo(x,y):ctx.moveTo(x,y);begun=true});ctx.stroke()}
function chart(){const result=state.result,field=$('feature').value,c=$('chart'),x=c.getContext('2d'),a=result.baseline.frames[field],b=result.participant.frames[field],all=[...a,...b].filter(Number.isFinite);x.clearRect(0,0,c.width,c.height);if(!all.length){x.fillStyle='#aab4ce';x.fillText('No finite values for this feature.',35,30);return}const min=Math.min(...all),max=Math.max(...all),duration=Math.max(result.baseline.duration_seconds,result.participant.duration_seconds);x.fillStyle='rgba(255,100,124,.18)';result.comparison.regions.forEach(v=>x.fillRect(35+930*v.start_seconds/duration,15,930*(v.end_seconds-v.start_seconds)/duration,190));x.strokeStyle='#56627e';x.beginPath();x.moveTo(35,15);x.lineTo(35,205);x.lineTo(965,205);x.stroke();line(x,a,result.baseline.frames.frame_center_seconds,duration,'#55c2ff',min,max);line(x,b,result.participant.frames.frame_center_seconds,duration,'#ffba52',min,max);x.fillStyle='#aab4ce';x.fillText(max.toFixed(2)+' '+labels[field],2,20);x.fillText(min.toFixed(2)+' '+labels[field],2,205);x.fillText('0 s',35,225);x.fillText(duration.toFixed(2)+' s',915,225)}
function escapeHtml(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML}
function setAudio(){state.urls.forEach(URL.revokeObjectURL);state.urls=[$('ba').files[0],$('pa').files[0]].map(URL.createObjectURL);$('baseline-audio').src=state.urls[0];$('participant-audio').src=state.urls[1]}
function playRegion(start,end){const audio=$('participant-audio');state.stopAt=end;audio.currentTime=start;audio.play()}
function show(r){state.result=r;setAudio();chart();$('regions').innerHTML=r.comparison.regions.length?'<table><thead><tr><th>Time</th><th>Word</th><th>Evidence</th><th>Listen</th></tr></thead><tbody>'+r.comparison.regions.map(v=>`<tr><td><span class="pill">${v.start_seconds.toFixed(2)}–${v.end_seconds.toFixed(2)}s</span></td><td>${escapeHtml(v.word)}</td><td>${v.explanations.map(escapeHtml).join('<br>')}</td><td><button class="play-region" data-start="${v.start_seconds}" data-end="${v.end_seconds}">Play region</button></td></tr>`).join('')+'</tbody></table>':'<p>No regions crossed this uncalibrated threshold.</p>';$('uncertainty').innerHTML=r.uncertainty.map(v=>'<li>'+escapeHtml(v)+'</li>').join('');$('results').hidden=false}
$('feature').addEventListener('change',()=>state.result&&chart());$('regions').addEventListener('click',e=>{const b=e.target.closest('.play-region');if(b)playRegion(Number(b.dataset.start),Number(b.dataset.end))});$('participant-audio').addEventListener('timeupdate',e=>{if(state.stopAt!==null&&e.target.currentTime>=state.stopAt){e.target.pause();state.stopAt=null}});
$('form').addEventListener('submit',async e=>{e.preventDefault();$('error').textContent='';$('message').textContent='Analyzing locally…';$('run').disabled=true;try{const [ba,pa,bj,pj]=await Promise.all([b64($('ba').files[0]),b64($('pa').files[0]),$('bj').files[0].text().then(JSON.parse),$('pj').files[0].text().then(JSON.parse)]);const response=await fetch('/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({baseline_audio_base64:ba,participant_audio_base64:pa,baseline_alignment:bj,participant_alignment:pj,threshold:Number($('threshold').value)})});const data=await response.json();if(!response.ok)throw Error(data.error||'Analysis failed');show(data);$('message').textContent='Analysis complete.'}catch(err){$('error').textContent=String(err);$('message').textContent=''}finally{$('run').disabled=false}})
</script></body></html>"""


def _decode_audio(payload, field):
    encoded = payload.get(field)
    if not isinstance(encoded, str):
        raise ValueError(f"{field} must be base64 text")
    try:
        value = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"{field} is not valid base64") from exc
    if not value:
        raise ValueError(f"{field} is empty")
    return value


def analyze_request(payload):
    """Validate one dashboard request and return the pair-analysis contract."""
    if not isinstance(payload, dict):
        raise ValueError("Request JSON must be an object")
    threshold = payload.get("threshold", 2.5)
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise ValueError("threshold must be numeric")
    baseline = _decode_audio(payload, "baseline_audio_base64")
    participant = _decode_audio(payload, "participant_audio_base64")
    with tempfile.TemporaryDirectory(prefix="repairlab-") as directory:
        baseline_path = Path(directory) / "baseline.wav"
        participant_path = Path(directory) / "participant.wav"
        baseline_path.write_bytes(baseline)
        participant_path.write_bytes(participant)
        return analyze_pair(baseline_path, participant_path,
                            payload.get("baseline_alignment"),
                            payload.get("participant_alignment"), float(threshold))


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "RepairLab/1"

    def log_message(self, _format, *_args):
        return

    def _send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; media-src blob:; style-src 'unsafe-inline'; script-src 'unsafe-inline'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self._send(200, HTML.encode(), "text/html; charset=utf-8")
        elif self.path == "/health":
            self._send(200, b'{"status":"ok"}\n', "application/json")
        else:
            self._send(404, b'{"error":"not found"}\n', "application/json")

    def do_POST(self):
        if self.path != "/analyze":
            self._send(404, b'{"error":"not found"}\n', "application/json")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= MAX_REQUEST_BYTES:
                raise ValueError("Request is empty or exceeds 6 MiB")
            payload = json.loads(self.rfile.read(length))
            result = analyze_request(payload)
            self._send(200, (json.dumps(result, allow_nan=False) + "\n").encode(), "application/json")
        except (ValueError, json.JSONDecodeError) as exc:
            self._send(400, (json.dumps({"error": str(exc)}) + "\n").encode(), "application/json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"RepairLab dashboard: http://{args.host}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
