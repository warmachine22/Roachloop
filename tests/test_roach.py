import json, subprocess, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ROACH=ROOT/"scripts"/"roach.py"

class RoachTests(unittest.TestCase):
 def repo(self):
  d=Path(tempfile.mkdtemp())
  subprocess.run(["git","init","-q"],cwd=d,check=True)
  subprocess.run(["git","config","user.email","test@example.com"],cwd=d,check=True)
  subprocess.run(["git","config","user.name","Roach Test"],cwd=d,check=True)
  (d/"app.txt").write_text("hello\n")
  subprocess.run(["git","add","."],cwd=d,check=True)
  subprocess.run(["git","commit","-qm","init"],cwd=d,check=True)
  return d
 def rr(self,d,*a):
  return subprocess.run(["python3",str(ROACH),*a],cwd=d,text=True,capture_output=True)
 def ok(self,r):
  self.assertEqual(r.returncode,0,r.stderr+"\n"+r.stdout)
 def init(self,d,profile="standard"):
  self.ok(self.rr(d,"init","--name","Test","--profile",profile))
 def addcp(self,d,no_ui=False,risk=None,files="app.txt"):
  self.ok(self.rr(d,"requirement","add","FR-001","It works"))
  args=["checkpoint","add","CP-001","Feature","--verify","true","--requirements","FR-001","--files",files]
  if no_ui: args+=["--no-ui"]
  if risk: args+=["--risk",risk]
  self.ok(self.rr(d,*args))
 def commit(self,d,msg="change"):
  subprocess.run(["git","add","."],cwd=d,check=True)
  subprocess.run(["git","commit","-qm",msg],cwd=d,check=True)

 def test_init_doctor(self):
  d=self.repo();self.init(d);self.ok(self.rr(d,"doctor"))
 def test_capability_registry_has_70(self):
  d=self.repo();self.init(d);r=self.rr(d,"capabilities","--json");self.ok(r)
  o=json.loads(r.stdout);self.assertEqual(len(o["protocol_capabilities"]),70);self.assertTrue(o["all_implemented"])
  self.assertTrue(all(x["available"] for x in o["protocol_capabilities"] if x["id"] in ("RL-45","RL-46","RL-47","RL-48")))
 def test_non_ui_gate_cannot_skip_by_design(self):
  d=self.repo();self.init(d);self.addcp(d)
  r=self.rr(d,"review","CP-001","adversarial","pass","--reviewer","A")
  self.assertNotEqual(r.returncode,0)
 def test_tamper_detected(self):
  d=self.repo();self.init(d)
  p=d/".roach"/"ledger.jsonl";lines=p.read_text().splitlines();o=json.loads(lines[0]);o["event"]="tampered";lines[0]=json.dumps(o);p.write_text("\n".join(lines)+"\n")
  self.assertNotEqual(self.rr(d,"verify-project").returncode,0)
 def test_evidence_manifest_tamper_detected(self):
  d=self.repo();self.init(d);self.addcp(d,no_ui=True);self.ok(self.rr(d,"start","CP-001"));self.ok(self.rr(d,"verify","CP-001"))
  p=d/".roach"/"evidence"/"CP-001"/"behavior.json";p.write_text(p.read_text()+" ")
  self.assertNotEqual(self.rr(d,"check","CP-001").returncode,0)
 def test_receipt_stale_only_for_relevant_change(self):
  d=self.repo();(d/"other.txt").write_text("x\n");self.commit(d,"other")
  self.init(d);self.addcp(d,no_ui=True,files="app.txt");self.ok(self.rr(d,"start","CP-001"));self.ok(self.rr(d,"verify","CP-001"))
  (d/"other.txt").write_text("y\n")
  self.ok(self.rr(d,"check","CP-001"))
  (d/"app.txt").write_text("changed\n")
  self.assertNotEqual(self.rr(d,"check","CP-001").returncode,0)
 def test_risk_auto_escalates_auth(self):
  d=self.repo();self.init(d);self.ok(self.rr(d,"requirement","add","FR-001","Login"))
  r=self.rr(d,"checkpoint","add","CP-001","Authentication","--verify","true","--requirements","FR-001","--files","src/auth.py")
  self.ok(r);s=json.loads((d/".roach"/"state.json").read_text());self.assertEqual(s["checkpoints"][0]["risk"],"high");self.assertIn("security",s["checkpoints"][0]["extra_gates"])
 def test_cannot_silently_downgrade_risk(self):
  d=self.repo();self.init(d);self.ok(self.rr(d,"requirement","add","FR-001","Login"))
  r=self.rr(d,"checkpoint","add","CP-001","Authentication","--verify","true","--requirements","FR-001","--files","src/auth.py","--risk","low")
  self.assertNotEqual(r.returncode,0)
 def test_context_is_role_specific_and_budgeted(self):
  d=self.repo();self.init(d);self.addcp(d)
  w=json.loads(self.rr(d,"context","CP-001","--role","worker","--json").stdout)
  a=json.loads(self.rr(d,"context","CP-001","--role","auditor","--json").stdout)
  self.assertIn("verify",w);self.assertNotIn("receipts",w);self.assertIn("receipts",a);self.assertTrue(w["_within_budget"])
 def test_requirement_conflict_blocks_project(self):
  d=self.repo();self.init(d)
  self.ok(self.rr(d,"requirement","add","FR-001","A","--conflicts","FR-002"))
  self.ok(self.rr(d,"requirement","add","FR-002","B","--conflicts","FR-001"))
  self.assertNotEqual(self.rr(d,"verify-project").returncode,0)
 def test_uncovered_requirement_detected(self):
  d=self.repo();self.init(d);self.ok(self.rr(d,"requirement","add","FR-001","A"))
  self.assertNotEqual(self.rr(d,"verify-project").returncode,0)
 def test_architecture_drift_detected(self):
  d=self.repo();self.init(d)
  self.ok(self.rr(d,"architecture","add","--id","AR-1","--files","app.txt","--forbidden-regex","hello","--reason","forbidden"))
  self.assertNotEqual(self.rr(d,"architecture","check").returncode,0)
 def test_redirect_preserves_history(self):
  d=self.repo();self.init(d);self.addcp(d)
  self.ok(self.rr(d,"redirect","--reason","intent changed","--checkpoints","CP-001","--human","owner"))
  s=json.loads((d/".roach"/"state.json").read_text());self.assertEqual(s["checkpoints"][0]["status"],"superseded")
 def test_decision_lineage(self):
  d=self.repo();self.init(d)
  self.ok(self.rr(d,"decision","add","--id","D-001","--title","Auth","--chosen","OAuth","--alternatives","passwords","--reason","managed identity"))
  ds=json.loads((d/".roach"/"decisions.json").read_text());self.assertEqual(ds[0]["chosen"],"OAuth")
 def test_finding_lifecycle(self):
  d=self.repo();self.init(d);self.addcp(d)
  r=self.rr(d,"finding","add","--checkpoint","CP-001","--text","bug","--reporter","reviewer","--json");self.ok(r);fid=json.loads(r.stdout)["id"]
  self.ok(self.rr(d,"finding","close",fid,"--resolution","fixed"))
 def test_baseline_must_fail(self):
  d=self.repo();self.init(d);self.ok(self.rr(d,"requirement","add","FR-001","A"))
  self.ok(self.rr(d,"checkpoint","add","CP-001","A","--verify","true","--baseline-verify","true","--requirements","FR-001","--no-ui"))
  self.assertNotEqual(self.rr(d,"baseline","CP-001").returncode,0)
 def test_external_evidence_is_hashed(self):
  d=self.repo();self.init(d);p=d/"proof.txt";p.write_text("proof")
  r=self.rr(d,"external","add","--id","E-1","--path","proof.txt","--source","vendor","--json");self.ok(r);self.assertTrue(json.loads(r.stdout)["sha256"])
 def test_environment_capabilities_reported(self):
  d=self.repo();self.init(d);r=self.rr(d,"capabilities","--json");self.ok(r);self.assertIn("git",json.loads(r.stdout)["runtime"])
 def test_status_json(self):
  d=self.repo();self.init(d);self.addcp(d);r=self.rr(d,"status","--json");self.ok(r);self.assertEqual(json.loads(r.stdout)["project"],"Test")
 def test_report_generation(self):
  d=self.repo();self.init(d);self.addcp(d);self.ok(self.rr(d,"report"));self.assertTrue((d/".roach"/"reports"/"assurance.html").exists())
 def test_threat_model(self):
  d=self.repo();self.init(d);r=self.rr(d,"threat-model","--json");self.ok(r);self.assertIn("protected_against",json.loads(r.stdout))
 def test_benchmark_record(self):
  d=self.repo();self.init(d);self.ok(self.rr(d,"benchmark","record","--name","trial","--mode","roach","--tokens","100"));r=self.rr(d,"benchmark","summary","--json");self.ok(r);o=json.loads(r.stdout);self.assertEqual(o["runs"],1);self.assertEqual(o["by_mode"]["roach"]["averages"]["tokens"],100)
 def test_examples(self):
  d=self.repo();self.init(d);self.ok(self.rr(d,"examples"));self.assertTrue((d/"examples"/"web-app.md").exists())
 def test_environment_freeze_and_check(self):
  d=self.repo();self.init(d);self.ok(self.rr(d,"environment","freeze"));self.ok(self.rr(d,"environment","check"))
 def test_requirement_can_be_explicitly_unknown(self):
  d=self.repo();self.init(d);self.ok(self.rr(d,"requirement","add","FR-001","Unknown external behavior"));self.ok(self.rr(d,"requirement","status","FR-001","--status","unknown","--reason","awaiting vendor"))
  rs=json.loads((d/".roach"/"requirements.json").read_text());self.assertEqual(rs[0]["status"],"unknown")
 def test_dashboard_generation(self):
  d=self.repo();self.init(d);self.addcp(d);self.ok(self.rr(d,"dashboard"));self.assertTrue((d/".roach"/"reports"/"dashboard.html").exists())
 def test_reproduce_receipt(self):
  d=self.repo();self.init(d);self.addcp(d,no_ui=True);self.ok(self.rr(d,"start","CP-001"));self.ok(self.rr(d,"verify","CP-001"));self.ok(self.rr(d,"reproduce","CP-001"))
 def test_complete_mode_requires_sealed_requirement(self):
  d=self.repo();self.init(d);self.addcp(d,no_ui=True);self.assertNotEqual(self.rr(d,"verify-project","--complete").returncode,0)
 def test_scope_trace_rejects_unrelated_changed_file(self):
  d=self.repo();(d/"other.txt").write_text("x\n");self.commit(d,"add other");self.init(d);self.addcp(d,no_ui=True,files="app.txt");self.ok(self.rr(d,"start","CP-001"))
  (d/"app.txt").write_text("ok\n");(d/"other.txt").write_text("out of scope\n");self.commit(d,"feature plus drift");self.ok(self.rr(d,"verify","CP-001"))
  self.assertNotEqual(self.rr(d,"check","CP-001").returncode,0)
 def test_product_export_and_check(self):
  d=self.repo();self.init(d);self.ok(self.rr(d,"requirement","add","FR-001","A"));self.ok(self.rr(d,"product","export"));self.assertTrue((d/"PRODUCT.md").exists());self.ok(self.rr(d,"product","check"))
 def test_dependency_check_executes_verifier(self):
  d=self.repo();self.init(d);self.ok(self.rr(d,"dependency","add","--id","EXT-1","--source","vendor","--verification","true"));r=self.rr(d,"dependency","check","--id","EXT-1","--json");self.ok(r);self.assertEqual(json.loads(r.stdout)["status"],"verified")
 def test_provenance_hashes_prompt(self):
  d=self.repo();self.init(d);r=self.rr(d,"provenance","--agent","codex","--model","test","--prompt","secret prompt","--json");self.ok(r);o=json.loads(r.stdout);self.assertTrue(o["prompt_hash"]);self.assertNotIn("secret prompt",json.dumps(o))
 def test_human_artifact_must_exist_or_be_head(self):
  d=self.repo();self.init(d);self.addcp(d,no_ui=True)
  # Fast profile is tested separately; invalid arbitrary artifact is always rejected.
  r=self.rr(d,"approve","CP-001","--approver","owner","--artifact","does-not-exist")
  self.assertNotEqual(r.returncode,0)
 def test_report_includes_pdf(self):
  d=self.repo();self.init(d);self.addcp(d);self.ok(self.rr(d,"report"));self.assertTrue((d/".roach"/"reports"/"assurance.pdf").read_bytes().startswith(b"%PDF"))
 def test_builtin_providers(self):
  d=self.repo();self.init(d)
  # Provider executable itself should be callable and the simple site-less checks pass.
  for name in ("security","accessibility","performance","migration"):
   r=subprocess.run(["python3",str(ROOT/"scripts"/"providers.py"),name],cwd=d,text=True,capture_output=True)
   self.assertEqual(r.returncode,0,r.stderr+r.stdout)
 def test_fast_profile_full_lifecycle_seals(self):
  d=self.repo();self.init(d,"fast");self.addcp(d,no_ui=True);self.ok(self.rr(d,"start","CP-001"));self.ok(self.rr(d,"verify","CP-001"))
  self.ok(self.rr(d,"approve","CP-001","--approver","owner"));self.ok(self.rr(d,"audit","CP-001"));self.ok(self.rr(d,"seal","CP-001"));self.ok(self.rr(d,"verify-project"))
 def test_prepush_installer(self):
  d=self.repo();self.init(d);self.ok(self.rr(d,"prepush","install"));self.assertTrue((d/".git"/"hooks"/"pre-push").exists())

if __name__=="__main__":unittest.main()
