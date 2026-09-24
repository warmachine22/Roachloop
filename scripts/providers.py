#!/usr/bin/env python3
"""Built-in deterministic Roach Loop evidence providers.
These are conservative baseline checks. Projects can replace/augment them in .roach/plugins.json.
"""
import argparse, re, subprocess, sys
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path.cwd()
IGNORE={".git",".roach","node_modules",".next","dist","build","vendor","__pycache__"}

def files(exts=None):
 for p in ROOT.rglob("*"):
  if not p.is_file() or any(x in IGNORE for x in p.parts):continue
  if exts and p.suffix.lower() not in exts:continue
  yield p

def security(_):
 secret=re.compile(r"(gh[pousr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")
 danger=[
  (re.compile(r"\beval\s*\("),"eval()"),
  (re.compile(r"subprocess\.[A-Za-z_]+\([^\n]*shell\s*=\s*True"),"subprocess shell=True"),
  (re.compile(r"pickle\.loads?\s*\("),"unsafe pickle load"),
 ]
 errors=[]
 for p in files({".py",".js",".ts",".tsx",".jsx",".json",".yml",".yaml",".env",".txt",".md"}):
  if p.resolve()==Path(__file__).resolve(): continue
  try:s=p.read_text(errors="ignore")
  except Exception:continue
  if secret.search(s):errors.append(f"{p}: possible committed secret")
  for rx,label in danger:
   if rx.search(s):errors.append(f"{p}: security-sensitive construct: {label}")
 for e in errors:print("SECURITY:",e)
 return 1 if errors else 0

class A11yParser(HTMLParser):
 def __init__(self,path):
  super().__init__();self.path=path;self.errors=[];self.has_lang=False
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=="html" and a.get("lang"):self.has_lang=True
  if tag=="img" and "alt" not in a:self.errors.append("img missing alt")
  if tag=="input" and a.get("type","text") not in ("hidden","submit","button") and not (a.get("aria-label") or a.get("aria-labelledby") or a.get("id")):self.errors.append("input lacks accessible naming hook")
  if tag=="button" and a.get("aria-hidden")=="true":self.errors.append("button hidden from accessibility tree")

def accessibility(_):
 errors=[]
 for p in files({".html"}):
  q=A11yParser(p)
  try:q.feed(p.read_text(errors="ignore"))
  except Exception as e:errors.append(f"{p}: parse error {e}");continue
  if not q.has_lang:errors.append(f"{p}: html element missing lang")
  errors += [f"{p}: {e}" for e in q.errors]
 for e in errors:print("ACCESSIBILITY:",e)
 return 1 if errors else 0

def performance(a):
 total=0;overs=[]
 for p in files({".html",".css",".js",".mjs",".json"}):
  n=p.stat().st_size;total+=n
  if n>a.max_file_bytes:overs.append(f"{p}={n}")
 print(f"PERFORMANCE: static bytes={total}, budget={a.max_total_bytes}")
 if overs:
  for x in overs:print("PERFORMANCE: oversized file",x)
 if total>a.max_total_bytes:print("PERFORMANCE: total static budget exceeded")
 return 1 if overs or total>a.max_total_bytes else 0

def migration(_):
 mig=ROOT/"migrations"
 if not mig.exists():
  print("MIGRATION: no migrations directory; not applicable baseline passes")
  return 0
 names=[p.name for p in mig.iterdir() if p.is_file()]
 if names!=sorted(names):
  print("MIGRATION: filenames are not lexically ordered");return 1
 hook=ROOT/"migration-test.sh"
 if hook.exists():
  r=subprocess.run(["bash",str(hook)],cwd=ROOT)
  return r.returncode
 print(f"MIGRATION: {len(names)} ordered migration files; add migration-test.sh for forward/rollback data-integrity proof")
 return 0

def main():
 p=argparse.ArgumentParser();sp=p.add_subparsers(dest="cmd",required=True)
 q=sp.add_parser("security");q.set_defaults(fn=security)
 q=sp.add_parser("accessibility");q.set_defaults(fn=accessibility)
 q=sp.add_parser("performance");q.add_argument("--max-total-bytes",type=int,default=2_000_000);q.add_argument("--max-file-bytes",type=int,default=500_000);q.set_defaults(fn=performance)
 q=sp.add_parser("migration");q.set_defaults(fn=migration)
 a=p.parse_args();raise SystemExit(a.fn(a))
if __name__=="__main__":main()
