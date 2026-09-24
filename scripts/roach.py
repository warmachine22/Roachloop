#!/usr/bin/env python3
import argparse, hashlib, json, subprocess, sys, time
from pathlib import Path

PROTOCOL="roach-loop/2.0"
GATES=("behavior","ui","adversarial","human","audit")
NON_SKIPPABLE={"behavior","adversarial","human","audit"}
TRANSITIONS={
 "planned":{"implementing","blocked","superseded"},"blocked":{"implementing","superseded"},
 "implementing":{"behavior_verified","blocked","superseded"},
 "behavior_verified":{"ui_verified","adversarial_verified","blocked","superseded"},
 "ui_verified":{"adversarial_verified","blocked","superseded"},
 "adversarial_verified":{"human_accepted","blocked","superseded"},
 "human_accepted":{"audited","blocked","superseded"},"audited":{"sealed","blocked","superseded"},
 "sealed":{"superseded"},"superseded":set()}
PROFILE_GATES={"fast":["behavior","human","audit"],"standard":["behavior","ui","adversarial","human","audit"],"strict":["behavior","ui","adversarial","human","audit"]}

def root():
 p=Path.cwd()
 while p!=p.parent:
  if (p/".git").exists() or (p/".roach").exists(): return p
  p=p.parent
 return Path.cwd()
def rp(*x): return root().joinpath(".roach",*x)
def load(p,default=None):
 try:return json.loads(Path(p).read_text())
 except FileNotFoundError:
  if default is not None:return default
  die("missing "+str(p))
def save(p,obj):
 Path(p).parent.mkdir(parents=True,exist_ok=True); q=Path(str(p)+".tmp")
 q.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n"); q.replace(p)
def die(s,code=2): print("ROACH ERROR:",s,file=sys.stderr); raise SystemExit(code)
def run(cmd): return subprocess.run(cmd,cwd=root(),text=True,capture_output=True,shell=isinstance(cmd,str))
def git(*a):
 r=run(["git",*a])
 if r.returncode: die("git "+" ".join(a)+": "+r.stderr.strip())
 return r.stdout.strip()
def tree(): return git("write-tree")
def head(): return git("rev-parse","HEAD")
def code_dirty():
 return any(".roach/" not in line for line in git("status","--porcelain").splitlines())
def now(): return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
def digest(s): return hashlib.sha256(s.encode()).hexdigest()
def event(kind,data):
 rp().mkdir(exist_ok=True); p=rp("ledger.jsonl"); prev="0"*64
 if p.exists() and p.stat().st_size: prev=json.loads(p.read_text().splitlines()[-1])["hash"]
 body={"protocol":PROTOCOL,"event":kind,"at":now(),"data":data,"prev":prev}
 body["hash"]=digest(json.dumps(body,sort_keys=True,separators=(",",":")))
 with p.open("a") as f:f.write(json.dumps(body,sort_keys=True)+"\n")
 return body["hash"]
def state(): return load(rp("state.json"))
def put(s): save(rp("state.json"),s)
def cp(s,cid):
 for c in s["checkpoints"]:
  if c["id"]==cid:return c
 die("unknown checkpoint "+cid)
def required(s,c):
 gs=PROFILE_GATES[s["profile"]][:]
 if not c.get("needs_ui_gate",True) and "ui" in gs: gs.remove("ui")
 return gs
def transition(c,to):
 if to not in TRANSITIONS.get(c["status"],set()): die(f"illegal transition {c['status']} -> {to}")
 old=c["status"]; c["status"]=to; event("CheckpointTransition",{"id":c["id"],"from":old,"to":to})
def init(a):
 if not (root()/".git").exists(): die("Roach requires a Git repository")
 if rp("state.json").exists(): die("already initialized")
 rp("evidence").mkdir(parents=True,exist_ok=True)
 save(rp("requirements.json"),[]); save(rp("config.json"),{"protocol":PROTOCOL,"profile":a.profile})
 put({"protocol":PROTOCOL,"project":a.name,"profile":a.profile,"current_checkpoint":None,"checkpoints":[]})
 event("ProjectInitialized",{"project":a.name,"profile":a.profile,"head":head()}); print("ROACH initialized:",a.name)
def requirement(a):
 rs=load(rp("requirements.json"),[])
 if a.action=="add":
  if not a.id or not a.statement: die("add requires id and statement")
  if any(x["id"]==a.id for x in rs): die("requirement exists")
  r={"id":a.id,"statement":a.statement,"status":"active","created_at":now()}; rs.append(r); save(rp("requirements.json"),rs); event("RequirementAdded",r); print("added",a.id)
 else:
  for r in rs: print(r["id"],r["status"],"-",r["statement"])
def checkpoint(a):
 s=state(); reqids=[x for x in a.requirements.split(",") if x]; known={r["id"] for r in load(rp("requirements.json"),[])}
 missing=[x for x in reqids if x not in known]
 if missing: die("unknown requirements: "+",".join(missing))
 c={"id":a.id,"title":a.title,"status":"planned","requirements":reqids,"verify":a.verify,"needs_ui_gate":not a.no_ui,
    "gates":{g:"pending" for g in GATES},"gate_notes":{},"receipts":{}}
 if a.no_ui:c["gates"]["ui"]="not_applicable";c["gate_notes"]["ui"]="checkpoint declared non-visual"
 s["checkpoints"].append(c);put(s);event("CheckpointCreated",{"id":a.id,"requirements":reqids,"verify":a.verify});print("added",a.id)
def start(a):
 s=state();c=cp(s,a.id);transition(c,"implementing");s["current_checkpoint"]=c["id"];put(s);print("started",c["id"])
def receipt_path(cid):return rp("evidence",cid,"behavior.json")
def verify(a):
 s=state();c=cp(s,a.id)
 if c["status"]!="implementing":die("checkpoint must be implementing")
 before=tree();r=run(c["verify"])
 rec={"protocol":PROTOCOL,"checkpoint":c["id"],"requirements":c["requirements"],"git_tree":before,"head":head(),"command":c["verify"],
      "at":now(),"exit_code":r.returncode,"stdout_sha256":digest(r.stdout),"stderr_sha256":digest(r.stderr)}
 rec["receipt_hash"]=digest(json.dumps(rec,sort_keys=True,separators=(",",":")));save(receipt_path(c["id"]),rec)
 event("VerificationCompleted",{"checkpoint":c["id"],"receipt_hash":rec["receipt_hash"],"exit_code":r.returncode,"git_tree":before})
 if r.returncode:c["gates"]["behavior"]="failed";put(s);print(r.stdout);print(r.stderr,file=sys.stderr);die("verification failed",1)
 c["gates"]["behavior"]="passed";c["receipts"]["behavior"]=str(receipt_path(c["id"]).relative_to(root()));transition(c,"behavior_verified");put(s)
 print("ROACH VERIFIED",c["id"],"tree",before[:12])
def gate(a):
 s=state();c=cp(s,a.id);g=a.gate
 if g not in GATES:die("unknown gate")
 if a.action=="skip":
  if g in NON_SKIPPABLE:die(g+" gate cannot be skipped")
  if g=="ui" and c["needs_ui_gate"]:die("UI gate required")
  if not a.reason:die("skip requires --reason")
  c["gates"][g]="not_applicable"
 else:
  if g=="behavior":die("behavior is machine-owned; use verify")
  c["gates"][g]="passed" if a.action=="pass" else "failed"
  if a.action=="pass":
   target={"ui":"ui_verified","adversarial":"adversarial_verified","human":"human_accepted","audit":"audited"}.get(g)
   if target in TRANSITIONS.get(c["status"],set()):transition(c,target)
 if a.reason:c["gate_notes"][g]=a.reason
 put(s);event("GateRecorded",{"checkpoint":c["id"],"gate":g,"result":c["gates"][g],"note":a.reason});print(g,c["gates"][g])
def check_cp(s,c):
 errs=[];known={r["id"] for r in load(rp("requirements.json"),[])}
 for x in c["requirements"]:
  if x not in known:errs.append("unknown requirement "+x)
 if c["gates"]["behavior"]=="passed":
  p=receipt_path(c["id"])
  if not p.exists():errs.append("missing behavior receipt")
  else:
   rec=load(p)
   if code_dirty() or rec.get("git_tree")!=tree():errs.append("behavior evidence is stale: implementation files or Git tree changed")
   body=dict(rec);rh=body.pop("receipt_hash",None)
   if rh!=digest(json.dumps(body,sort_keys=True,separators=(",",":"))):errs.append("behavior receipt hash mismatch")
 if c["status"]=="sealed":
  for g in required(s,c):
   if c["gates"].get(g)!="passed":errs.append("sealed checkpoint lacks "+g)
 return errs
def check(a):
 s=state();errs=check_cp(s,cp(s,a.id))
 for e in errs:print("✗",e)
 if not errs:print("✓",a.id,"evidence current")
 raise SystemExit(1 if errs else 0)
def ledger_errors():
 p=rp("ledger.jsonl");prev="0"*64;errs=[]
 if not p.exists():return["missing ledger"]
 for i,line in enumerate(p.read_text().splitlines(),1):
  try:o=json.loads(line)
  except:return[f"ledger line {i} invalid JSON"]
  h=o.get("hash");body=dict(o);body.pop("hash",None)
  if o.get("prev")!=prev:errs.append(f"ledger line {i} previous hash mismatch")
  if h!=digest(json.dumps(body,sort_keys=True,separators=(",",":"))):errs.append(f"ledger line {i} hash mismatch")
  prev=h
 return errs
def verify_project(a):
 s=state();errs=ledger_errors();active={r["id"] for r in load(rp("requirements.json"),[]) if r["status"]=="active"};covered=set()
 for c in s["checkpoints"]:
  if c["status"]!="superseded":covered.update(c["requirements"])
  errs += [c["id"]+": "+x for x in check_cp(s,c)]
 for r in sorted(active-covered):errs.append("uncovered active requirement "+r)
 if errs:
  print("ROACH PROJECT INVALID")
  for e in errs:print("✗",e)
  raise SystemExit(1)
 print("ROACH PROJECT VALID\nledger ✓\nrequirements ✓\nevidence ✓")
def seal(a):
 s=state();c=cp(s,a.id)
 if c["status"]!="audited":die("checkpoint must be audited before sealing")
 for g in required(s,c):
  if c["gates"].get(g)!="passed":die("required gate not passed: "+g)
 errs=check_cp(s,c)
 if errs:die("; ".join(errs))
 if s["profile"]=="strict" and git("status","--porcelain"):die("strict profile requires clean worktree")
 transition(c,"sealed");z={"protocol":PROTOCOL,"checkpoint":c["id"],"git_tree":tree(),"head":head(),"requirements":c["requirements"],"at":now()}
 z["seal_hash"]=digest(json.dumps(z,sort_keys=True,separators=(",",":")));save(rp("evidence",c["id"],"seal.json"),z);event("CheckpointSealed",z);put(s);print("ROACH SEALED",c["id"],z["seal_hash"][:16])
def status(a):
 s=state();print(s["project"],"["+s["profile"]+"]")
 for c in s["checkpoints"]:print(c["id"],c["status"],"|",", ".join(f"{g}:{v}" for g,v in c["gates"].items()))
def next_cmd(a):
 s=state();c=cp(s,s["current_checkpoint"]) if s.get("current_checkpoint") else next((x for x in s["checkpoints"] if x["status"] not in ("sealed","superseded")),None)
 if not c:print("No active checkpoint.");return
 print(f"{c['id']} — {c['title']}\nStatus: {c['status']}\nRequirements: {', '.join(c['requirements']) or 'none'}")
 m={"planned":f"python3 scripts/roach.py start {c['id']}","implementing":f"python3 scripts/roach.py verify {c['id']}","behavior_verified":"Perform UI review or adversarial review as policy requires","ui_verified":"Perform isolated adversarial review","adversarial_verified":"Ask human to review exact build","human_accepted":"Perform fresh audit","audited":f"python3 scripts/roach.py seal {c['id']}","blocked":"Resolve blocker","sealed":"Checkpoint sealed"}
 print("Next:",m.get(c["status"],c["status"]))
def context(a):
 s=state();c=cp(s,a.id);rm={r["id"]:r for r in load(rp("requirements.json"),[])}
 print(f"ROACH CONTEXT / {a.role.upper()} / {c['id']}\nGoal: {c['title']}\nStatus: {c['status']}\nRequirements:")
 for rid in c["requirements"]:print("-",rid,rm.get(rid,{}).get("statement","?"))
 if a.role=="worker":print("Verify:",c["verify"])
 else:print("Git tree:",tree(),"\nGates:",json.dumps(c["gates"],sort_keys=True))
 if a.role=="auditor":print("Evidence:",json.dumps(c["receipts"],sort_keys=True))
def doctor(a):
 errs=[]
 if not (root()/".git").exists():errs.append("git missing")
 for f in ("state.json","requirements.json","config.json","ledger.jsonl"):
  if not rp(f).exists():errs.append(".roach/"+f+" missing")
 if rp("ledger.jsonl").exists():errs+=ledger_errors()
 print("Roach Loop doctor")
 for e in errs:print("✗",e)
 if not errs:print("✓ git\n✓ managed state\n✓ ledger")
 raise SystemExit(1 if errs else 0)
def parser():
 p=argparse.ArgumentParser(prog="roach");sp=p.add_subparsers(dest="cmd",required=True)
 q=sp.add_parser("init");q.add_argument("--name",required=True);q.add_argument("--profile",choices=PROFILE_GATES,default="standard");q.set_defaults(fn=init)
 q=sp.add_parser("requirement");q.add_argument("action",choices=["add","list"]);q.add_argument("id",nargs="?");q.add_argument("statement",nargs="?");q.set_defaults(fn=requirement)
 q=sp.add_parser("checkpoint");q.add_argument("action",choices=["add"]);q.add_argument("id");q.add_argument("title");q.add_argument("--verify",required=True);q.add_argument("--requirements",default="");q.add_argument("--no-ui",action="store_true");q.set_defaults(fn=checkpoint)
 for name,fn in [("start",start),("verify",verify),("check",check),("seal",seal)]:q=sp.add_parser(name);q.add_argument("id");q.set_defaults(fn=fn)
 q=sp.add_parser("gate");q.add_argument("id");q.add_argument("gate");q.add_argument("action",choices=["pass","fail","skip"]);q.add_argument("--reason");q.set_defaults(fn=gate)
 q=sp.add_parser("status");q.set_defaults(fn=status);q=sp.add_parser("next");q.set_defaults(fn=next_cmd)
 q=sp.add_parser("context");q.add_argument("id");q.add_argument("--role",choices=["worker","reviewer","auditor"],default="worker");q.set_defaults(fn=context)
 q=sp.add_parser("doctor");q.set_defaults(fn=doctor);q=sp.add_parser("verify-project");q.set_defaults(fn=verify_project);return p
if __name__=="__main__":
 a=parser().parse_args();a.fn(a)
