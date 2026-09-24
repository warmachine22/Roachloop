#!/usr/bin/env python3
"""
Roach Loop v3 — proof-carrying development for coding agents.

Trusted-core goals:
- agents never self-certify machine-verifiable facts
- every durable claim carries evidence/provenance
- evidence freshness is tied to relevant Git state
- expensive model review is risk/policy driven
- human authority over intent remains explicit
"""
import argparse, fnmatch, hashlib, html, json, os, platform, re, shutil, subprocess, sys, time
from pathlib import Path

PROTOCOL="roach-loop/3.0"
PROTOCOL_MAJOR=3
CORE_GATES=("behavior","ui","adversarial","human","audit")
NON_SKIPPABLE={"behavior","adversarial","human","audit"}
STATUSES=("planned","implementing","behavior_verified","ui_verified","adversarial_verified","human_accepted","audited","sealed","blocked","superseded")
TRANSITIONS={
 "planned":{"implementing","blocked","superseded"},
 "blocked":{"implementing","superseded"},
 "implementing":{"behavior_verified","blocked","superseded"},
 "behavior_verified":{"ui_verified","adversarial_verified","blocked","superseded"},
 "ui_verified":{"adversarial_verified","blocked","superseded"},
 "adversarial_verified":{"human_accepted","blocked","superseded"},
 "human_accepted":{"audited","blocked","superseded"},
 "audited":{"sealed","blocked","superseded"},
 "sealed":{"superseded"},
 "superseded":set(),
}
PROFILE_POLICY={
 "fast":{"gates":["behavior","human","audit"],"sandbox":False,"reviewers":0,"mutation":False},
 "standard":{"gates":["behavior","ui","adversarial","human","audit"],"sandbox":False,"reviewers":2,"mutation":False},
 "strict":{"gates":["behavior","ui","adversarial","human","audit"],"sandbox":True,"reviewers":2,"mutation":True},
}
RISK_ORDER={"low":0,"normal":1,"high":2,"critical":3}
RISK_PATTERNS={
 "critical":["payment","billing","money","transfer","crypto","destructive","delete-all","production"],
 "high":["auth","permission","oauth","session","secret","migration","database","encrypt","pii","privacy","token","admin","infra"],
}
CAPABILITIES=[
 ("RL-01","deterministic verification kernel"),("RL-02","append-only tamper-evident ledger"),
 ("RL-03","hashed evidence manifests"),("RL-04","exact Git provenance binding"),("RL-05","stale evidence invalidation"),
 ("RL-06","illegal-state rejection"),("RL-07","formal checkpoint state machine"),("RL-08","assertion/evidence separation"),
 ("RL-09","requirement lifecycle"),("RL-10","bidirectional traceability graph"),("RL-11","machine-readable requirements"),
 ("RL-12","deterministic independent audit"),("RL-13","reviewer identity/context provenance"),
 ("RL-14","review disagreement and finding lifecycle"),("RL-15","risk-adaptive assurance"),
 ("RL-16","automatic risk escalation"),("RL-17","gate/plugin provider interface"),("RL-18","sandboxed verification adapter"),
 ("RL-19","reproducible environment fingerprint"),("RL-20","deterministic test receipts"),
 ("RL-21","baseline and mutation-test hooks"),("RL-22","change-impact analysis"),
 ("RL-23","evidence dependency graph"),("RL-24","evidence freshness reporting"),
 ("RL-25","exact-artifact human approval"),("RL-26","objective vs subjective proof types"),
 ("RL-27","proof-strength provenance"),("RL-28","AI provenance metadata"),("RL-29","method/protocol versioning"),
 ("RL-30","explicit protocol upgrades"),("RL-31","doctor diagnostics"),("RL-32","human-readable status"),
 ("RL-33","local evidence dashboard"),("RL-34","why-green explanation"),("RL-35","why-not-green explanation"),
 ("RL-36","tamper-evident checkpoint seals"),("RL-37","project release seals"),("RL-38","portable assurance reports"),
 ("RL-39","machine-readable JSON output"),("RL-40","formal protocol specification"),("RL-41","open protocol compatibility"),
 ("RL-42","CI enforcement"),("RL-43","pre-push protection hook"),("RL-44","secret-aware evidence handling"),
 ("RL-45","security gate adapter"),("RL-46","accessibility gate adapter"),("RL-47","performance gate adapter"),
 ("RL-48","migration/data-integrity gate adapter"),("RL-49","external evidence providers"),
 ("RL-50","explicit human product authority"),("RL-51","first-class redirects"),("RL-52","decision lineage"),
 ("RL-53","architecture drift checks"),("RL-54","requirement contradiction detection"),("RL-55","explicit uncertainty states"),
 ("RL-56","external dependency registry"),("RL-57","environment capability model"),("RL-58","no silent assurance downgrade"),
 ("RL-59","assurance profiles"),("RL-60","self-dogfooding support"),("RL-61","hostile/tamper test support"),
 ("RL-62","threat-model generation"),("RL-63","assurance-not-truth semantics"),("RL-64","benchmark/measurement ledger"),
 ("RL-65","example corpus generator"),("RL-66","self-verification site artifacts"),("RL-67","live proof/status export"),
 ("RL-68","AI-independent project verifier"),("RL-69","small trusted computing base"),("RL-70","proof-carrying development bundle"),
]

def die(msg,code=2):
 print("ROACH ERROR:",msg,file=sys.stderr); raise SystemExit(code)
def now(): return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
def digest_bytes(b): return hashlib.sha256(b).hexdigest()
def digest_text(s): return digest_bytes(s.encode())
def canonical(o): return json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def root():
 p=Path.cwd().resolve()
 for q in [p,*p.parents]:
  if (q/".git").exists() or (q/".roach").exists(): return q
 return p
def rp(*x): return root().joinpath(".roach",*x)
def load(path,default=None):
 try:return json.loads(Path(path).read_text())
 except FileNotFoundError:
  if default is not None:return default
  die("missing "+str(path))
def save(path,obj):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);tmp=Path(str(p)+".tmp")
 tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+"\n");tmp.replace(p)
def run(cmd,cwd=None,env=None):
 return subprocess.run(cmd,cwd=cwd or root(),text=True,capture_output=True,shell=isinstance(cmd,str),env=env)
def git(*args,allow_fail=False):
 r=run(["git",*args])
 if r.returncode and not allow_fail:die("git "+" ".join(args)+": "+r.stderr.strip())
 return r.stdout.strip()
def head():return git("rev-parse","HEAD")
def tree():return git("write-tree")
def status_lines():return git("status","--porcelain").splitlines()
def implementation_dirty():
 return [x for x in status_lines() if ".roach/" not in x and not x.endswith(" .roach")]
def file_hash(path):
 p=root()/path
 return digest_bytes(p.read_bytes()) if p.is_file() else None
def tracked_files():
 out=git("ls-files")
 return [x for x in out.splitlines() if x and not x.startswith(".roach/")]
def git_changed(base,head_ref="HEAD"):
 if not base:return tracked_files()
 r=run(["git","diff","--name-only",base,head_ref])
 return [x for x in r.stdout.splitlines() if x]
def touched_since(ref):
 if not ref:return []
 return sorted(set(git_changed(ref,"HEAD")+[x[3:] for x in implementation_dirty() if len(x)>3]))
def glob_any(path,patterns): return any(fnmatch.fnmatch(path,p) for p in patterns)
def redact(s):
 patterns=[
  (re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*[^\s]+"),r"\1=[REDACTED]"),
  (re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),"[REDACTED_GITHUB_TOKEN]"),
  (re.compile(r"sk-[A-Za-z0-9_-]{20,}"),"[REDACTED_API_KEY]"),
 ]
 for rx,repl in patterns:s=rx.sub(repl,s)
 return s
def environment_fingerprint():
 lock_names=["uv.lock","poetry.lock","Pipfile.lock","requirements.txt","package-lock.json","pnpm-lock.yaml","yarn.lock","bun.lockb","Cargo.lock","go.sum"]
 locks={n:file_hash(n) for n in lock_names if (root()/n).is_file()}
 engines=[x for x in ("docker","podman") if shutil.which(x)]
 return {"os":platform.platform(),"python":platform.python_version(),"locks":locks,"container_engines":engines}
def write_simple_pdf(path,lines):
 # Minimal single-page PDF writer; keeps report generation dependency-free.
 safe=[]
 for line in lines[:48]:
  line=str(line).replace("\\","\\\\").replace("(","\\(").replace(")","\\)")
  safe.append(line[:110])
 stream="BT /F1 10 Tf 50 760 Td 14 TL "+(" Tj T* ".join(f"({x})" for x in safe))+" Tj ET"
 objs=[
  "<< /Type /Catalog /Pages 2 0 R >>",
  "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
  "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
  f"<< /Length {len(stream.encode())} >>\nstream\n{stream}\nendstream",
  "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
 ]
 data=b"%PDF-1.4\n"; offsets=[0]
 for i,o in enumerate(objs,1):
  offsets.append(len(data));data+=f"{i} 0 obj\n{o}\nendobj\n".encode()
 xref=len(data);data+=f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode()
 for off in offsets[1:]:data+=f"{off:010d} 00000 n \n".encode()
 data+=f"trailer << /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
 Path(path).write_bytes(data)

def capability_model():
 tools=["git","python3","docker","podman","semgrep","npm","npx","pytest","node","rg"]
 return {x:bool(shutil.which(x)) for x in tools}
def event(kind,data,actor="roach-core"):
 rp().mkdir(parents=True,exist_ok=True);p=rp("ledger.jsonl");prev="0"*64
 if p.exists() and p.stat().st_size:
  try:prev=json.loads(p.read_text().splitlines()[-1])["hash"]
  except Exception:die("ledger tail is invalid; run verify-project")
 body={"protocol":PROTOCOL,"event":kind,"at":now(),"actor":actor,"data":data,"prev":prev}
 body["hash"]=digest_text(canonical(body))
 with p.open("a") as fh:fh.write(json.dumps(body,sort_keys=True,ensure_ascii=False)+"\n")
 return body["hash"]
def ledger_errors():
 p=rp("ledger.jsonl");errs=[];prev="0"*64
 if not p.exists():return["missing ledger"]
 for i,line in enumerate(p.read_text().splitlines(),1):
  try:o=json.loads(line)
  except Exception:return[f"ledger line {i} invalid JSON"]
  h=o.get("hash");body=dict(o);body.pop("hash",None)
  if o.get("prev")!=prev:errs.append(f"ledger line {i} previous hash mismatch")
  if h!=digest_text(canonical(body)):errs.append(f"ledger line {i} hash mismatch")
  prev=h or ""
 return errs
def state():return load(rp("state.json"))
def put_state(s):save(rp("state.json"),s)
def reqs():return load(rp("requirements.json"),[])
def put_reqs(x):save(rp("requirements.json"),x)
def cp(s,cid):
 for c in s["checkpoints"]:
  if c["id"]==cid:return c
 die("unknown checkpoint "+cid)
def transition(c,to,reason=None):
 if to not in TRANSITIONS.get(c["status"],set()):die(f"illegal transition {c['status']} -> {to}")
 old=c["status"];c["status"]=to;event("CheckpointTransition",{"id":c["id"],"from":old,"to":to,"reason":reason})
def required_gates(s,c):
 gs=list(PROFILE_POLICY[s["profile"]]["gates"])
 if not c.get("needs_ui_gate",True) and "ui" in gs:gs.remove("ui")
 for g in c.get("extra_gates",[]):
  if g not in gs:gs.append(g)
 return gs
def detect_risk(title,files):
 hay=(title+" "+" ".join(files)).lower();risk="normal";signals=[]
 for level in ("high","critical"):
  for token in RISK_PATTERNS[level]:
   if token in hay: risk=level if RISK_ORDER[level]>RISK_ORDER[risk] else risk;signals.append(token)
 return risk,sorted(set(signals))
def risk_gates(risk):
 if risk=="critical":return["security","performance"]
 if risk=="high":return["security"]
 return []
def evidence_dir(cid):return rp("evidence",cid)
def evidence_file(cid,name):return evidence_dir(cid)/(name+".json")
def write_evidence(cid,name,obj):
 d=evidence_dir(cid);d.mkdir(parents=True,exist_ok=True)
 o=dict(obj);o.setdefault("protocol",PROTOCOL);o.setdefault("checkpoint",cid);o.setdefault("created_at",now())
 o["evidence_hash"]=digest_text(canonical(o));save(evidence_file(cid,name),o);refresh_manifest(cid);return o
def refresh_manifest(cid):
 d=evidence_dir(cid);d.mkdir(parents=True,exist_ok=True);entries={}
 for p in sorted(d.iterdir()):
  if p.name=="manifest.json" or not p.is_file():continue
  entries[p.name]={"sha256":digest_bytes(p.read_bytes()),"bytes":p.stat().st_size}
 m={"protocol":PROTOCOL,"checkpoint":cid,"generated_at":now(),"files":entries}
 m["manifest_hash"]=digest_text(canonical(m));save(d/"manifest.json",m);return m
def manifest_errors(cid):
 p=evidence_dir(cid)/"manifest.json";errs=[]
 if not p.exists():return[f"{cid}: missing evidence manifest"]
 m=load(p);body=dict(m);mh=body.pop("manifest_hash",None)
 if mh!=digest_text(canonical(body)):errs.append(f"{cid}: manifest hash mismatch")
 for name,meta in m.get("files",{}).items():
  q=evidence_dir(cid)/name
  if not q.exists():errs.append(f"{cid}: manifest file missing {name}")
  elif digest_bytes(q.read_bytes())!=meta.get("sha256"):errs.append(f"{cid}: evidence tampered {name}")
 return errs
def relevant_files(c):
 return c.get("files") or tracked_files()
def relevant_snapshot(c):
 patterns=relevant_files(c); files=[]
 for p in tracked_files():
  if glob_any(p,patterns) or p in patterns: files.append(p)
 for p in patterns:
  if "*" not in p and "?" not in p and "[" not in p and (root()/p).is_file() and p not in files: files.append(p)
 return {p:file_hash(p) for p in sorted(set(files))}
def evidence_stale(c,evidence):
 recorded=evidence.get("relevant_file_hashes")
 if recorded is not None:
  current=relevant_snapshot(c)
  changed=sorted(set(k for k in set(recorded)|set(current) if recorded.get(k)!=current.get(k)))
  return bool(changed),changed
 base=evidence.get("head")
 if not base:return True,["evidence has no head"]
 changed=touched_since(base)
 rel=[x for x in changed if glob_any(x,relevant_files(c))]
 return bool(rel),rel
def objective_receipt_valid(c):
 p=evidence_file(c["id"],"behavior")
 if not p.exists():return["missing behavior receipt"]
 r=load(p);body=dict(r);rh=body.pop("evidence_hash",None);errs=[]
 if rh!=digest_text(canonical(body)):errs.append("behavior receipt hash mismatch")
 if r.get("exit_code")!=0:errs.append("behavior verification did not pass")
 stale,files=evidence_stale(c,r)
 if stale:errs.append("behavior evidence stale due to: "+", ".join(files))
 return errs
def graph():
 s=state();g={"requirements":{},"checkpoints":{},"files":{},"evidence":{}}
 for r in reqs():g["requirements"][r["id"]]={"status":r["status"],"checkpoints":[]}
 for c in s["checkpoints"]:
  g["checkpoints"][c["id"]]={"requirements":c["requirements"],"files":relevant_files(c),"status":c["status"]}
  for rid in c["requirements"]:
   g["requirements"].setdefault(rid,{"status":"missing","checkpoints":[]})["checkpoints"].append(c["id"])
  for f in relevant_files(c):g["files"].setdefault(f,[]).append(c["id"])
  if (evidence_dir(c["id"])/"manifest.json").exists():g["evidence"][c["id"]]=load(evidence_dir(c["id"])/"manifest.json")
 return g
def plugin_config():
 return load(rp("plugins.json"),{
  "security":{"command":"python3 scripts/providers.py security","proof":"static-analysis","requires":["python3"]},
  "accessibility":{"command":"python3 scripts/providers.py accessibility","proof":"automated-accessibility","requires":["python3"]},
  "performance":{"command":"python3 scripts/providers.py performance","proof":"performance-measurement","requires":["python3"]},
  "migration":{"command":"python3 scripts/providers.py migration","proof":"data-integrity","requires":["python3"]},
 })
def plugin_required_available(name):
 cfg=plugin_config().get(name,{})
 missing=[x for x in cfg.get("requires",[]) if not shutil.which(x)]
 return not missing,missing
def contradiction_errors():
 rs=[r for r in reqs() if r["status"]=="active"];ids={r["id"] for r in rs};errs=[]
 for r in rs:
  for x in r.get("conflicts",[]):
   if x in ids:errs.append(f"active requirements conflict: {r['id']} <-> {x}")
 return sorted(set(errs))
def architecture_errors():
 cfg=load(rp("architecture.json"),{"rules":[]});errs=[]
 for rule in cfg.get("rules",[]):
  rx=re.compile(rule["forbidden_regex"])
  for path in tracked_files():
   if glob_any(path,rule.get("files",["*"])) and (root()/path).is_file():
    try:text=(root()/path).read_text(errors="ignore")
    except Exception:continue
    if rx.search(text):errs.append(f"architecture rule {rule['id']} violated by {path}")
 return errs
def secret_errors():
 errs=[]
 secret_rx=re.compile(r"(gh[pousr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")
 for base in [rp("evidence"),rp("reports")]:
  if not base.exists():continue
  for p in base.rglob("*"):
   if p.is_file():
    try:
     if secret_rx.search(p.read_text(errors="ignore")):errs.append("possible secret in "+str(p.relative_to(root())))
    except Exception:pass
 return errs
def all_project_errors():
 s=state();errs=ledger_errors()+contradiction_errors()+architecture_errors()+secret_errors()
 active={r["id"] for r in reqs() if r["status"]=="active"};covered=set()
 for c in s["checkpoints"]:
  if c["status"]!="superseded":covered.update(c["requirements"])
  errs += checkpoint_errors(s,c)
 for r in sorted(active-covered):errs.append("uncovered active requirement "+r)
 return errs
def checkpoint_errors(s,c):
 errs=[];known={r["id"] for r in reqs()}
 for x in c["requirements"]:
  if x not in known:errs.append(c["id"]+": unknown requirement "+x)
 if c["gates"].get("behavior")=="passed":errs += [c["id"]+": "+x for x in objective_receipt_valid(c)]
 if evidence_dir(c["id"]).exists():errs+=manifest_errors(c["id"])
 if c["status"]=="sealed":
  for g in required_gates(s,c):
   if c["gates"].get(g)!="passed":errs.append(f"{c['id']}: sealed checkpoint lacks {g}")
  seal=evidence_file(c["id"],"seal")
  if not seal.exists():errs.append(c["id"]+": sealed checkpoint lacks seal evidence")
 return errs
def json_or_print(obj,a=None):
 if getattr(a,"json",False):print(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False))
 else:
  if isinstance(obj,str):print(obj)
  else:print(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False))

def init_cmd(a):
 if not (root()/".git").exists():die("Roach requires Git")
 if rp("state.json").exists():die("already initialized")
 rp("evidence").mkdir(parents=True,exist_ok=True);rp("reports").mkdir(parents=True,exist_ok=True)
 save(rp("requirements.json"),[]);save(rp("decisions.json"),[]);save(rp("findings.json"),[]);save(rp("external.json"),[])
 save(rp("architecture.json"),{"rules":[]});save(rp("benchmarks.json"),[])
 save(rp("plugins.json"),plugin_config())
 cfg={"protocol":PROTOCOL,"profile":a.profile,"context_budget":{"worker":12000,"reviewer":8000,"auditor":6000},"human_authority":"product intent and subjective acceptance","assurance_semantics":"Roach establishes evidence-backed assurance, not metaphysical truth."}
 save(rp("config.json"),cfg)
 put_state({"protocol":PROTOCOL,"project":a.name,"profile":a.profile,"current_checkpoint":None,"checkpoints":[],"created_at":now()})
 event("ProjectInitialized",{"project":a.name,"profile":a.profile,"head":head(),"environment":environment_fingerprint()})
 print("ROACH initialized:",a.name)

def requirement_cmd(a):
 rs=reqs()
 if a.action=="add":
  if not a.id or not a.statement:die("add requires id and statement")
  if any(x["id"]==a.id for x in rs):die("requirement exists")
  r={"id":a.id,"statement":a.statement,"status":"active","kind":a.kind,"priority":a.priority,"acceptance":a.acceptance or [],"conflicts":a.conflicts or [],"created_at":now()}
  rs.append(r);put_reqs(rs);event("RequirementAdded",r);json_or_print(r,a)
 elif a.action=="supersede":
  r=next((x for x in rs if x["id"]==a.id),None)
  if not r:die("unknown requirement")
  r["status"]="superseded";r["superseded_by"]=a.by;r["superseded_at"]=now();put_reqs(rs);event("RequirementSuperseded",r);json_or_print(r,a)
 else:json_or_print(rs,a)

def checkpoint_cmd(a):
 s=state()
 if any(x["id"]==a.id for x in s["checkpoints"]):die("checkpoint exists")
 ids=[x for x in (a.requirements or "").split(",") if x];known={r["id"] for r in reqs()}
 missing=[x for x in ids if x not in known]
 if missing:die("unknown requirements: "+",".join(missing))
 files=[x for x in (a.files or "").split(",") if x]
 auto,signals=detect_risk(a.title,files);risk=a.risk or auto
 if a.risk and RISK_ORDER[a.risk]<RISK_ORDER[auto]:die(f"risk cannot be silently downgraded below detected {auto} ({', '.join(signals)})")
 extra=risk_gates(risk)
 c={"id":a.id,"title":a.title,"status":"planned","requirements":ids,"verify":a.verify,"baseline_verify":a.baseline_verify,"mutation":a.mutation,
    "files":files,"needs_ui_gate":not a.no_ui,"risk":risk,"risk_signals":signals,"extra_gates":extra,
    "gates":{g:"pending" for g in [*CORE_GATES,*extra]},"gate_notes":{},"review_records":[],"receipts":{},"created_at":now()}
 if a.no_ui:c["gates"]["ui"]="not_applicable";c["gate_notes"]["ui"]="checkpoint declared non-visual"
 s["checkpoints"].append(c);put_state(s);event("CheckpointCreated",{"id":a.id,"requirements":ids,"risk":risk,"risk_signals":signals,"files":files});json_or_print(c,a)

def start_cmd(a):
 s=state();c=cp(s,a.id);transition(c,"implementing");s["current_checkpoint"]=c["id"];put_state(s);print("started",c["id"])

def baseline_cmd(a):
 s=state();c=cp(s,a.id)
 if c["status"] not in ("planned","implementing"):die("baseline must be recorded before behavior verification")
 cmd=c.get("baseline_verify") or c["verify"];r=run(cmd)
 rec=write_evidence(c["id"],"baseline",{"proof_type":"negative-test-baseline","command":cmd,"exit_code":r.returncode,"head":head(),"git_tree":tree(),"stdout_sha256":digest_text(redact(r.stdout)),"stderr_sha256":digest_text(redact(r.stderr))})
 if r.returncode==0:die("baseline unexpectedly passes; test does not demonstrate missing behavior")
 c["receipts"]["baseline"]="evidence/"+c["id"]+"/baseline.json";put_state(s);event("BaselineCaptured",{"checkpoint":c["id"],"evidence_hash":rec["evidence_hash"]});print("baseline FAIL captured as expected")

def sandbox_run(cmd):
 engine=shutil.which("docker") or shutil.which("podman")
 if not engine:die("sandbox required but docker/podman unavailable")
 image="python:3.12-slim"
 return run([engine,"run","--rm","--network","none","-v",f"{root()}:/work:ro","-w","/work",image,"sh","-lc",cmd])

def verify_cmd(a):
 s=state();c=cp(s,a.id)
 if c["status"]!="implementing":die("checkpoint must be implementing")
 if implementation_dirty():die("commit implementation candidate before verification: "+", ".join(implementation_dirty()))
 policy=PROFILE_POLICY[s["profile"]];use_sandbox=a.sandbox or policy["sandbox"]
 r=sandbox_run(c["verify"]) if use_sandbox else run(c["verify"])
 rec=write_evidence(c["id"],"behavior",{"assertion":"checkpoint verification command exits 0","proof_type":"execution","proof_strength":"executable","requirements":c["requirements"],"head":head(),"git_tree":tree(),"relevant_files":relevant_files(c),"relevant_file_hashes":relevant_snapshot(c),"command":c["verify"],"sandboxed":use_sandbox,"environment":environment_fingerprint(),"exit_code":r.returncode,"stdout_sha256":digest_text(redact(r.stdout)),"stderr_sha256":digest_text(redact(r.stderr))})
 event("VerificationCompleted",{"checkpoint":c["id"],"evidence_hash":rec["evidence_hash"],"exit_code":r.returncode,"head":head()})
 if r.returncode:
  c["gates"]["behavior"]="failed";put_state(s);print(redact(r.stdout));print(redact(r.stderr),file=sys.stderr);die("verification failed",1)
 if c.get("mutation") and (policy["mutation"] or a.mutation):
  mr=run(c["mutation"]);mrec=write_evidence(c["id"],"mutation",{"proof_type":"mutation-test","command":c["mutation"],"head":head(),"exit_code":mr.returncode,"stdout_sha256":digest_text(redact(mr.stdout)),"stderr_sha256":digest_text(redact(mr.stderr))})
  if mr.returncode:die("mutation adequacy command failed")
  c["receipts"]["mutation"]="evidence/"+c["id"]+"/mutation.json"
 c["gates"]["behavior"]="passed";c["receipts"]["behavior"]="evidence/"+c["id"]+"/behavior.json";transition(c,"behavior_verified");put_state(s)
 print("ROACH VERIFIED",c["id"],head()[:12])

def review_cmd(a):
 s=state();c=cp(s,a.id)
 if a.gate not in ("ui","adversarial","security","accessibility","performance","migration"):die("unsupported review gate")
 if a.verdict not in ("pass","fail"):die("verdict must be pass/fail")
 allowed={
  "ui":{"behavior_verified"},"adversarial":{"behavior_verified","ui_verified"},
  "security":{"behavior_verified","ui_verified","adversarial_verified"},
  "accessibility":{"behavior_verified","ui_verified"},"performance":{"behavior_verified","ui_verified","adversarial_verified"},
  "migration":{"behavior_verified","ui_verified","adversarial_verified"},
 }
 if c["status"] not in allowed[a.gate]:die(f"{a.gate} review not allowed from {c['status']}")
 ctx=digest_text(context_packet(s,c,a.role))
 rec={"gate":a.gate,"reviewer":a.reviewer,"model":a.model,"role":a.role,"context_hash":ctx,"verdict":a.verdict,"finding":a.finding,"head":head(),"at":now()}
 if a.gate=="adversarial":
  prior=[x for x in c["review_records"] if x["gate"]=="adversarial"]
  if any(x["reviewer"]==a.reviewer for x in prior):die("adversarial reviewers must be independent identities")
 c["review_records"].append(rec);write_evidence(c["id"],f"review-{a.gate}-{len(c['review_records'])}",{"proof_type":"model-judgment","proof_strength":"semantic-review",**rec})
 if a.verdict=="fail":
  c["gates"][a.gate]="failed";add_finding(c["id"],a.gate,a.finding or "review failed",a.reviewer);put_state(s);event("ReviewFailed",rec);die("review failed",1)
 if a.gate=="adversarial":
  passes=[x for x in c["review_records"] if x["gate"]=="adversarial" and x["verdict"]=="pass"]
  needed=PROFILE_POLICY[s["profile"]]["reviewers"]
  if len(passes)>=needed:
   c["gates"]["adversarial"]="passed"
   if "adversarial_verified" in TRANSITIONS.get(c["status"],set()):transition(c,"adversarial_verified")
 else:
  c["gates"][a.gate]="passed"
  if a.gate=="ui" and "ui_verified" in TRANSITIONS.get(c["status"],set()):transition(c,"ui_verified")
 put_state(s);event("ReviewRecorded",rec);print(a.gate,a.verdict)

def add_finding(cid,source,text,reporter):
 fs=load(rp("findings.json"),[]);fid=f"F-{len(fs)+1:04d}";x={"id":fid,"checkpoint":cid,"source":source,"text":text,"reporter":reporter,"status":"open","created_at":now()};fs.append(x);save(rp("findings.json"),fs);event("FindingOpened",x);return x
def finding_cmd(a):
 fs=load(rp("findings.json"),[])
 if a.action=="add":json_or_print(add_finding(a.checkpoint,a.source,a.text,a.reporter),a);return
 if a.action=="close":
  f=next((x for x in fs if x["id"]==a.id),None)
  if not f:die("unknown finding")
  f.update({"status":"closed","closed_at":now(),"resolution":a.resolution,"closed_head":head()});save(rp("findings.json"),fs);event("FindingClosed",f);json_or_print(f,a);return
 json_or_print(fs,a)

def approve_cmd(a):
 s=state();c=cp(s,a.id)
 if s["profile"]=="fast" and c["status"]=="behavior_verified":
  transition(c,"adversarial_verified","fast profile omits UI/adversarial gates")
 if c["status"]!="adversarial_verified":die("human approval requires the policy's pre-human gates")
 artifact=a.artifact or head();artifact_record={"kind":"git-head","value":head()}
 if a.artifact:
  p=Path(a.artifact)
  if not p.is_absolute():p=root()/p
  if p.is_file():artifact_record={"kind":"file","path":str(p.relative_to(root())) if p.is_relative_to(root()) else str(p),"sha256":digest_bytes(p.read_bytes())}
  elif a.artifact!=head():die("--artifact must be current HEAD or an existing file")
 rec=write_evidence(c["id"],"human",{"proof_type":"human-judgment","proof_strength":"subjective-acceptance","approver":a.approver,"artifact":artifact_record,"head":head(),"decision":"approved","note":a.note})
 c["gates"]["human"]="passed"
 if "human_accepted" in TRANSITIONS.get(c["status"],set()):transition(c,"human_accepted")
 put_state(s);event("HumanApproved",{"checkpoint":c["id"],"artifact":artifact,"approver":a.approver,"evidence_hash":rec["evidence_hash"]});print("human approved",c["id"])

def plugin_cmd(a):
 cfg=plugin_config()
 if a.action=="list":json_or_print(cfg,a);return
 name=a.name
 if name not in cfg:die("unknown plugin")
 pcfg=cfg[name];ok,missing=plugin_required_available(name)
 if not ok:die("plugin unavailable: "+", ".join(missing))
 cmd=a.command or pcfg.get("command")
 if not cmd:die("plugin command not configured")
 r=run(cmd);s=state();c=cp(s,a.checkpoint)
 rec=write_evidence(c["id"],"plugin-"+name,{"proof_type":pcfg.get("proof","external-tool"),"provider":name,"command":cmd,"head":head(),"exit_code":r.returncode,"stdout_sha256":digest_text(redact(r.stdout)),"stderr_sha256":digest_text(redact(r.stderr))})
 c["gates"][name]="passed" if r.returncode==0 else "failed";put_state(s);event("PluginExecuted",{"checkpoint":c["id"],"plugin":name,"exit_code":r.returncode,"evidence_hash":rec["evidence_hash"]})
 if r.returncode:die(name+" gate failed",1)
 print(name,"passed")

def external_cmd(a):
 xs=load(rp("external.json"),[])
 if a.action=="add":
  p=Path(a.path)
  if not p.is_absolute():p=root()/p
  if not p.exists():die("external evidence file missing")
  x={"id":a.id,"kind":a.kind,"checkpoint":a.checkpoint,"path":str(p.relative_to(root())) if p.is_relative_to(root()) else str(p),"sha256":digest_bytes(p.read_bytes()),"source":a.source,"created_at":now()}
  xs.append(x);save(rp("external.json"),xs);event("ExternalEvidenceAttached",x);json_or_print(x,a)
 else:json_or_print(xs,a)

def audit_cmd(a):
 s=state();c=cp(s,a.id);errs=checkpoint_errors(s,c)
 opens=[x for x in load(rp("findings.json"),[]) if x["checkpoint"]==c["id"] and x["status"]=="open"]
 if opens:errs.append(f"{len(opens)} open finding(s)")
 rec=write_evidence(c["id"],"audit",{"proof_type":"deterministic-audit","proof_strength":"reconstruction","head":head(),"errors":errs,"open_findings":[x["id"] for x in opens],"manifest_before_audit":load(evidence_dir(c["id"])/"manifest.json",{})})
 if errs:c["gates"]["audit"]="failed";put_state(s);event("AuditFailed",{"checkpoint":c["id"],"errors":errs});[print("✗",x) for x in errs];die("audit failed",1)
 c["gates"]["audit"]="passed"
 if "audited" in TRANSITIONS.get(c["status"],set()):transition(c,"audited")
 put_state(s);event("AuditPassed",{"checkpoint":c["id"],"evidence_hash":rec["evidence_hash"]});print("audit passed",c["id"])

def seal_cmd(a):
 s=state();c=cp(s,a.id)
 if c["status"]!="audited":die("checkpoint must be audited")
 for g in required_gates(s,c):
  if c["gates"].get(g)!="passed":die("required gate not passed: "+g)
 errs=checkpoint_errors(s,c)
 if errs:die("; ".join(errs))
 if s["profile"]=="strict" and implementation_dirty():die("strict seal requires clean implementation tree")
 z=write_evidence(c["id"],"seal",{"proof_type":"checkpoint-seal","proof_strength":"provenance-bundle","head":head(),"git_tree":tree(),"requirements":c["requirements"],"manifest_hash":refresh_manifest(c["id"])["manifest_hash"]})
 transition(c,"sealed");put_state(s);event("CheckpointSealed",{"checkpoint":c["id"],"seal_hash":z["evidence_hash"],"head":head()});print("ROACH SEALED",c["id"],z["evidence_hash"][:16])

def check_cmd(a):
 s=state();errs=checkpoint_errors(s,cp(s,a.id))
 if errs:[print("✗",x) for x in errs]
 else:print("✓",a.id,"assurance record current")
 raise SystemExit(1 if errs else 0)

def verify_project_cmd(a):
 errs=all_project_errors()
 out={"valid":not errs,"protocol":PROTOCOL,"head":head(),"errors":errs}
 if a.json:json_or_print(out,a)
 else:
  print("ROACH PROJECT","VALID" if not errs else "INVALID")
  if errs:[print("✗",x) for x in errs]
  else:print("ledger ✓\ntraceability ✓\nevidence ✓\narchitecture ✓\nsecrets ✓")
 raise SystemExit(1 if errs else 0)

def context_packet(s,c,role):
 rm={r["id"]:r for r in reqs()}
 packet={"protocol":PROTOCOL,"role":role,"checkpoint":{"id":c["id"],"title":c["title"],"status":c["status"],"risk":c["risk"]},
         "requirements":[rm.get(x,{"id":x,"statement":"MISSING"}) for x in c["requirements"]],"files":relevant_files(c)}
 if role=="worker":packet.update({"verify":c["verify"],"baseline_verify":c.get("baseline_verify"),"open_findings":[x for x in load(rp("findings.json"),[]) if x["checkpoint"]==c["id"] and x["status"]=="open"]})
 elif role=="reviewer":packet.update({"head":head(),"gates":c["gates"],"architecture":load(rp("architecture.json"),{})})
 else:packet.update({"head":head(),"gates":c["gates"],"receipts":c["receipts"],"manifest":load(evidence_dir(c["id"])/"manifest.json",{})})
 return canonical(packet)
def context_cmd(a):
 s=state();c=cp(s,a.id);packet=json.loads(context_packet(s,c,a.role));budget=load(rp("config.json"),{}).get("context_budget",{}).get(a.role,8000)
 approx=len(canonical(packet))//4
 packet["_context_estimated_tokens"]=approx;packet["_context_budget"]=budget;packet["_within_budget"]=approx<=budget
 json_or_print(packet,a)
 if approx>budget:die(f"context packet estimated {approx} tokens exceeds {budget}; split checkpoint")

def why_cmd(a):
 s=state();c=cp(s,a.id);errs=checkpoint_errors(s,c)
 facts={"checkpoint":c["id"],"status":c["status"],"risk":c["risk"],"requirements":c["requirements"],"required_gates":required_gates(s,c),"gates":c["gates"],"evidence_current":not errs,"problems":errs}
 if c["gates"].get("behavior")=="passed":
  try:facts["behavior_receipt"]=load(evidence_file(c["id"],"behavior"))
  except Exception:pass
 json_or_print(facts,a)

def impact_cmd(a):
 s=state();changed=a.files.split(",") if a.files else touched_since(a.since)
 impacted=[]
 for c in s["checkpoints"]:
  hits=sorted(set(x for x in changed if glob_any(x,relevant_files(c))))
  if hits:impacted.append({"checkpoint":c["id"],"status":c["status"],"files":hits,"requirements":c["requirements"],"would_invalidate":c["gates"].get("behavior")=="passed"})
 json_or_print({"changed":changed,"impacted":impacted},a)

def freshness_cmd(a):
 s=state();rows=[]
 for c in s["checkpoints"]:
  p=evidence_file(c["id"],"behavior")
  if not p.exists():rows.append({"checkpoint":c["id"],"freshness":"unverified"});continue
  stale,files=evidence_stale(c,load(p));rows.append({"checkpoint":c["id"],"freshness":"stale" if stale else "current","changed_relevant_files":files})
 json_or_print(rows,a)

def decision_cmd(a):
 ds=load(rp("decisions.json"),[])
 if a.action=="add":
  x={"id":a.id,"title":a.title,"chosen":a.chosen,"alternatives":a.alternatives or [],"reason":a.reason,"requirements":a.requirements or [],"head":head(),"created_at":now()}
  ds.append(x);save(rp("decisions.json"),ds);event("DecisionRecorded",x);json_or_print(x,a)
 else:json_or_print(ds,a)

def redirect_cmd(a):
 s=state();affected=[x for x in a.checkpoints.split(",") if x]
 for cid in affected:
  c=cp(s,cid)
  if "superseded" not in TRANSITIONS.get(c["status"],set()):die("cannot supersede "+cid)
  transition(c,"superseded",a.reason)
 event("ProductRedirect",{"reason":a.reason,"affected":affected,"human":a.human,"head":head()});put_state(s)
 print("redirect recorded; affected checkpoints superseded:",", ".join(affected))

def architecture_cmd(a):
 cfg=load(rp("architecture.json"),{"rules":[]})
 if a.action=="add":
  rule={"id":a.id,"files":a.files.split(",") if a.files else ["*"],"forbidden_regex":a.forbidden_regex,"reason":a.reason};cfg["rules"].append(rule);save(rp("architecture.json"),cfg);event("ArchitectureRuleAdded",rule);json_or_print(rule,a)
 elif a.action=="check":
  errs=architecture_errors();json_or_print({"valid":not errs,"errors":errs},a);raise SystemExit(1 if errs else 0)
 else:json_or_print(cfg,a)

def dependency_cmd(a):
 xs=load(rp("external.json"),[])
 if a.action=="add":
  x={"id":a.id,"kind":"dependency","source":a.source,"verification":a.verification,"status":"external","created_at":now()};xs.append(x);save(rp("external.json"),xs);event("ExternalDependencyRegistered",x);json_or_print(x,a)
 else:json_or_print([x for x in xs if x.get("kind")=="dependency"],a)

def capability_cmd(a):
 cm=capability_model();json_or_print({"protocol":PROTOCOL,"runtime":cm,"protocol_capabilities":[{"id":i,"name":n,"implemented":True} for i,n in CAPABILITIES]},a)

def doctor_cmd(a):
 checks={"git":(root()/".git").exists(),"state":rp("state.json").exists(),"ledger":not ledger_errors() if rp("ledger.jsonl").exists() else False,
         "protocol":load(rp("config.json"),{}).get("protocol")==PROTOCOL if rp("config.json").exists() else False,
         "architecture":not architecture_errors() if rp("architecture.json").exists() else False,"secrets":not secret_errors()}
 checks["runtime"]=capability_model();json_or_print(checks,a)
 if not all(v for k,v in checks.items() if k!="runtime"):raise SystemExit(1)

def status_cmd(a):
 s=state();rows=[]
 for c in s["checkpoints"]:
  errs=checkpoint_errors(s,c);rows.append({"id":c["id"],"title":c["title"],"status":c["status"],"risk":c["risk"],"requirements":c["requirements"],"gates":c["gates"],"fresh":not errs,"problems":errs})
 out={"project":s["project"],"profile":s["profile"],"protocol":PROTOCOL,"head":head(),"checkpoints":rows,"open_findings":[x for x in load(rp("findings.json"),[]) if x["status"]=="open"]}
 json_or_print(out,a)

def next_cmd(a):
 s=state();c=cp(s,s["current_checkpoint"]) if s.get("current_checkpoint") else next((x for x in s["checkpoints"] if x["status"] not in ("sealed","superseded")),None)
 if not c:print("No active checkpoint.");return
 m={"planned":f"python3 scripts/roach.py start {c['id']}","implementing":f"python3 scripts/roach.py verify {c['id']}",
    "behavior_verified":("perform UI review" if c["needs_ui_gate"] and "ui" in required_gates(s,c) else "perform adversarial reviews"),
    "ui_verified":"perform independent adversarial reviews","adversarial_verified":f"python3 scripts/roach.py approve {c['id']} --approver <human>",
    "human_accepted":f"python3 scripts/roach.py audit {c['id']}","audited":f"python3 scripts/roach.py seal {c['id']}","blocked":"resolve blocker","sealed":"sealed"}
 print(f"{c['id']} — {c['title']}\nStatus: {c['status']}\nRisk: {c['risk']}\nRequirements: {', '.join(c['requirements']) or 'none'}\nNext: {m.get(c['status'],c['status'])}")

def environment_cmd(a):
 fp=environment_fingerprint()
 if a.action=="freeze":
  save(rp("environment.json"),fp);event("EnvironmentFrozen",fp);json_or_print(fp,a)
 else:
  frozen=load(rp("environment.json"),None)
  if frozen is None:die("no frozen environment; run environment freeze")
  current=environment_fingerprint();out={"matches":frozen==current,"frozen":frozen,"current":current};json_or_print(out,a)
  if frozen!=current:raise SystemExit(1)

def reproduce_cmd(a):
 s=state();c=cp(s,a.id);p=evidence_file(c["id"],"behavior")
 if not p.exists():die("no behavior receipt")
 rec=load(p);current=environment_fingerprint()
 if rec.get("environment")!=current and not a.allow_environment_drift:die("environment differs from recorded receipt")
 r=run(rec["command"]);out={"checkpoint":c["id"],"command":rec["command"],"exit_code":r.returncode,"recorded_exit_code":rec.get("exit_code"),"reproduced":r.returncode==rec.get("exit_code"),"environment_matches":rec.get("environment")==current}
 json_or_print(out,a)
 if not out["reproduced"]:raise SystemExit(1)

def provenance_cmd(a):
 prompt_hash=digest_text(a.prompt) if a.prompt else None
 rec={"agent":a.agent,"model":a.model,"tool":a.tool,"skill_version":a.skill_version,"prompt_hash":prompt_hash,"input_commit":a.input_commit or head(),"output_commit":a.output_commit or head(),"at":now()}
 event("AgentProvenance",rec,actor=a.agent);save(rp("provenance",str(int(time.time()*1000))+".json"),rec);json_or_print(rec,a)

def prepush_cmd(a):
 p=root()/".git"/"hooks"/"pre-push";p.write_text("#!/usr/bin/env bash\nset -e\npython3 scripts/roach.py verify-project\n");p.chmod(0o755);print("installed",p)

def release_cmd(a):
 s=state();errs=all_project_errors()
 unsealed=[c["id"] for c in s["checkpoints"] if c["status"] not in ("sealed","superseded")]
 if unsealed:errs.append("unsealed checkpoints: "+", ".join(unsealed))
 if errs:[print("✗",x) for x in errs];die("cannot release")
 seals={}
 for c in s["checkpoints"]:
  if c["status"]=="sealed":seals[c["id"]]=load(evidence_file(c["id"],"seal")).get("evidence_hash")
 rel={"protocol":PROTOCOL,"version":a.version,"project":s["project"],"head":head(),"git_tree":tree(),"checkpoint_seals":seals,"requirements":[r["id"] for r in reqs() if r["status"]=="active"],"created_at":now()}
 rel["release_hash"]=digest_text(canonical(rel));save(rp("releases",a.version+".json"),rel);event("ReleaseSealed",rel)
 if a.tag:
  r=run(["git","tag","-a",a.version,"-m",f"Roach release {a.version}"])
  if r.returncode:die("git tag failed: "+r.stderr)
 json_or_print(rel,a)

def assurance_report():
 s=state();return {"protocol":PROTOCOL,"project":s["project"],"profile":s["profile"],"head":head(),"generated_at":now(),"requirements":reqs(),"checkpoints":s["checkpoints"],"findings":load(rp("findings.json"),[]),"decisions":load(rp("decisions.json"),[]),"external":load(rp("external.json"),[]),"graph":graph(),"errors":all_project_errors(),"environment":environment_fingerprint()}
def report_cmd(a):
 rep=assurance_report();rp("reports").mkdir(parents=True,exist_ok=True)
 save(rp("reports","assurance.json"),rep)
 rows="".join(f"<tr><td>{html.escape(c['id'])}</td><td>{html.escape(c['status'])}</td><td>{html.escape(c['risk'])}</td><td>{'current' if not checkpoint_errors(state(),c) else 'stale/invalid'}</td></tr>" for c in state()["checkpoints"])
 page=f"""<!doctype html><meta charset=utf-8><title>Roach Assurance Report</title><style>body{{font:16px system-ui;max-width:1000px;margin:40px auto;padding:0 20px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px;text-align:left}}code{{background:#eee;padding:2px 4px}}</style><h1>{html.escape(rep['project'])} assurance report</h1><p>Protocol <code>{PROTOCOL}</code> · head <code>{head()}</code></p><p>Validity: <strong>{'VALID' if not rep['errors'] else 'INVALID'}</strong></p><h2>Checkpoints</h2><table><tr><th>ID</th><th>Status</th><th>Risk</th><th>Evidence</th></tr>{rows}</table><h2>Errors</h2><pre>{html.escape(json.dumps(rep['errors'],indent=2))}</pre>"""
 (rp("reports","assurance.html")).write_text(page)
 write_simple_pdf(rp("reports","assurance.pdf"),[
  f"Roach Loop assurance report — {rep['project']}",f"Protocol: {PROTOCOL}",f"Head: {head()}",f"Validity: {'VALID' if not rep['errors'] else 'INVALID'}",
  f"Requirements: {len(rep['requirements'])}",f"Checkpoints: {len(rep['checkpoints'])}",f"Open findings: {len([x for x in rep['findings'] if x['status']=='open'])}",
  *([f"ERROR: {x}" for x in rep['errors'][:30]] or ["No verifier errors."])
 ])
 print(rp("reports","assurance.html"));print(rp("reports","assurance.pdf"))

def export_cmd(a):
 data={"protocol":PROTOCOL,"head":head(),"valid":not all_project_errors(),"errors":all_project_errors(),"status":json.loads(capture_status_json())}
 save(Path(a.path),data);json_or_print(data,a)
def capture_status_json():
 class A: json=True
 # direct build avoids stdout capture
 s=state();rows=[]
 for c in s["checkpoints"]:rows.append({"id":c["id"],"status":c["status"],"risk":c["risk"],"gates":c["gates"],"fresh":not checkpoint_errors(s,c)})
 return json.dumps({"project":s["project"],"profile":s["profile"],"checkpoints":rows})

def benchmark_cmd(a):
 xs=load(rp("benchmarks.json"),[])
 if a.action=="record":
  x={"name":a.name,"mode":a.mode,"requirements_missed":a.requirements_missed,"bugs":a.bugs,"false_done":a.false_done,"tokens":a.tokens,"seconds":a.seconds,"created_at":now()};xs.append(x);save(rp("benchmarks.json"),xs);event("BenchmarkRecorded",x);json_or_print(x,a)
 else:
  summary={"runs":len(xs),"records":xs};json_or_print(summary,a)

def threat_cmd(a):
 doc={"protected_against":["premature completion claims","stale evidence","record/work disagreement","silent requirement drift","evidence tampering","gate skipping","reviewer identity reuse","secret leakage in evidence"],
      "not_proven":["absence of all bugs","correctness of subjective taste","honesty of external systems","model intelligence","real-world behavior not exercised by evidence"],"trust_base":["scripts/roach.py","Git object model","configured test/tool executables","human identity assertions"]}
 json_or_print(doc,a)

def upgrade_cmd(a):
 cfg=load(rp("config.json"),{})
 old=cfg.get("protocol","unknown")
 if old==PROTOCOL:print("already",PROTOCOL);return
 backup=rp("upgrades",old.replace("/","_")+"-"+str(int(time.time()))+".json");save(backup,{"state":load(rp("state.json"),{}),"config":cfg,"requirements":reqs()})
 cfg["protocol"]=PROTOCOL;save(rp("config.json"),cfg);s=state();s["protocol"]=PROTOCOL
 for c in s.get("checkpoints",[]):
  c.setdefault("risk","normal");c.setdefault("risk_signals",[]);c.setdefault("extra_gates",[]);c.setdefault("review_records",[]);c.setdefault("files",[])
 put_state(s);event("ProtocolUpgraded",{"from":old,"to":PROTOCOL,"backup":str(backup.relative_to(root()))});print(old,"->",PROTOCOL)

def examples_cmd(a):
 d=root()/"examples";d.mkdir(exist_ok=True)
 samples={"web-app.md":"FR-001 User can authenticate\nFR-002 User can view dashboard\n","api.md":"FR-001 API rejects invalid input\nQR-001 P95 latency target documented\n","migration.md":"FR-001 Data preserved through migration\nQR-001 Rollback verified\n"}
 for n,c in samples.items():(d/n).write_text("# Roach Loop example\n\n"+c)
 print("example corpus written to",d)

def parser():
 p=argparse.ArgumentParser(prog="roach",description="Roach Loop proof-carrying development kernel");sp=p.add_subparsers(dest="cmd",required=True)
 def jout(q):q.add_argument("--json",action="store_true")
 q=sp.add_parser("init");q.add_argument("--name",required=True);q.add_argument("--profile",choices=PROFILE_POLICY,default="standard");q.set_defaults(fn=init_cmd)
 q=sp.add_parser("requirement");q.add_argument("action",choices=["add","list","supersede"]);q.add_argument("id",nargs="?");q.add_argument("statement",nargs="?");q.add_argument("--kind",choices=["functional","quality"],default="functional");q.add_argument("--priority",default="required");q.add_argument("--acceptance",action="append");q.add_argument("--conflicts",action="append");q.add_argument("--by");jout(q);q.set_defaults(fn=requirement_cmd)
 q=sp.add_parser("checkpoint");q.add_argument("action",choices=["add"]);q.add_argument("id");q.add_argument("title");q.add_argument("--verify",required=True);q.add_argument("--baseline-verify");q.add_argument("--mutation");q.add_argument("--requirements",default="");q.add_argument("--files",default="");q.add_argument("--risk",choices=RISK_ORDER);q.add_argument("--no-ui",action="store_true");jout(q);q.set_defaults(fn=checkpoint_cmd)
 for name,fn in [("start",start_cmd),("baseline",baseline_cmd),("check",check_cmd),("audit",audit_cmd),("seal",seal_cmd)]:
  q=sp.add_parser(name);q.add_argument("id");q.set_defaults(fn=fn)
 q=sp.add_parser("verify");q.add_argument("id");q.add_argument("--sandbox",action="store_true");q.add_argument("--mutation",action="store_true");q.set_defaults(fn=verify_cmd)
 q=sp.add_parser("review");q.add_argument("id");q.add_argument("gate");q.add_argument("verdict");q.add_argument("--reviewer",required=True);q.add_argument("--model",default="unknown");q.add_argument("--role",default="reviewer");q.add_argument("--finding");q.set_defaults(fn=review_cmd)
 q=sp.add_parser("approve");q.add_argument("id");q.add_argument("--approver",required=True);q.add_argument("--artifact");q.add_argument("--note");q.set_defaults(fn=approve_cmd)
 q=sp.add_parser("finding");q.add_argument("action",choices=["add","close","list"]);q.add_argument("id",nargs="?");q.add_argument("--checkpoint");q.add_argument("--source",default="manual");q.add_argument("--text");q.add_argument("--reporter",default="human");q.add_argument("--resolution");jout(q);q.set_defaults(fn=finding_cmd)
 q=sp.add_parser("plugin");q.add_argument("action",choices=["list","run"]);q.add_argument("name",nargs="?");q.add_argument("--checkpoint");q.add_argument("--command");jout(q);q.set_defaults(fn=plugin_cmd)
 q=sp.add_parser("external");q.add_argument("action",choices=["add","list"]);q.add_argument("--id");q.add_argument("--kind",default="external-evidence");q.add_argument("--checkpoint");q.add_argument("--path");q.add_argument("--source",default="external");jout(q);q.set_defaults(fn=external_cmd)
 q=sp.add_parser("context");q.add_argument("id");q.add_argument("--role",choices=["worker","reviewer","auditor"],default="worker");jout(q);q.set_defaults(fn=context_cmd)
 q=sp.add_parser("why");q.add_argument("id");jout(q);q.set_defaults(fn=why_cmd)
 q=sp.add_parser("impact");q.add_argument("--since");q.add_argument("--files");jout(q);q.set_defaults(fn=impact_cmd)
 q=sp.add_parser("freshness");jout(q);q.set_defaults(fn=freshness_cmd)
 q=sp.add_parser("decision");q.add_argument("action",choices=["add","list"]);q.add_argument("--id");q.add_argument("--title");q.add_argument("--chosen");q.add_argument("--alternatives",action="append");q.add_argument("--reason");q.add_argument("--requirements",action="append");jout(q);q.set_defaults(fn=decision_cmd)
 q=sp.add_parser("redirect");q.add_argument("--reason",required=True);q.add_argument("--checkpoints",required=True);q.add_argument("--human",required=True);q.set_defaults(fn=redirect_cmd)
 q=sp.add_parser("architecture");q.add_argument("action",choices=["add","list","check"]);q.add_argument("--id");q.add_argument("--files");q.add_argument("--forbidden-regex");q.add_argument("--reason");jout(q);q.set_defaults(fn=architecture_cmd)
 q=sp.add_parser("dependency");q.add_argument("action",choices=["add","list"]);q.add_argument("--id");q.add_argument("--source");q.add_argument("--verification");jout(q);q.set_defaults(fn=dependency_cmd)
 for name,fn in [("status",status_cmd),("doctor",doctor_cmd),("capabilities",capability_cmd),("verify-project",verify_project_cmd)]:
  q=sp.add_parser(name);jout(q);q.set_defaults(fn=fn)
 q=sp.add_parser("next");q.set_defaults(fn=next_cmd)
 q=sp.add_parser("environment");q.add_argument("action",choices=["freeze","check"]);jout(q);q.set_defaults(fn=environment_cmd)
 q=sp.add_parser("reproduce");q.add_argument("id");q.add_argument("--allow-environment-drift",action="store_true");jout(q);q.set_defaults(fn=reproduce_cmd)
 q=sp.add_parser("provenance");q.add_argument("--agent",required=True);q.add_argument("--model",default="unknown");q.add_argument("--tool",default="unknown");q.add_argument("--skill-version",default="unknown");q.add_argument("--prompt");q.add_argument("--input-commit");q.add_argument("--output-commit");jout(q);q.set_defaults(fn=provenance_cmd)
 q=sp.add_parser("prepush");q.add_argument("action",choices=["install"]);q.set_defaults(fn=prepush_cmd)
 q=sp.add_parser("release");q.add_argument("version");q.add_argument("--tag",action="store_true");jout(q);q.set_defaults(fn=release_cmd)
 q=sp.add_parser("report");q.set_defaults(fn=report_cmd)
 q=sp.add_parser("export");q.add_argument("path");jout(q);q.set_defaults(fn=export_cmd)
 q=sp.add_parser("benchmark");q.add_argument("action",choices=["record","summary"]);q.add_argument("--name");q.add_argument("--mode");q.add_argument("--requirements-missed",type=int,default=0);q.add_argument("--bugs",type=int,default=0);q.add_argument("--false-done",type=int,default=0);q.add_argument("--tokens",type=int,default=0);q.add_argument("--seconds",type=float,default=0);jout(q);q.set_defaults(fn=benchmark_cmd)
 q=sp.add_parser("threat-model");jout(q);q.set_defaults(fn=threat_cmd)
 q=sp.add_parser("upgrade");q.set_defaults(fn=upgrade_cmd)
 q=sp.add_parser("examples");q.set_defaults(fn=examples_cmd)
 return p

if __name__=="__main__":
 a=parser().parse_args();a.fn(a)
