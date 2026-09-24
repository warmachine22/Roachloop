import json, subprocess, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; ROACH=ROOT/"scripts"/"roach.py"
class RoachTests(unittest.TestCase):
 def repo(self):
  d=Path(tempfile.mkdtemp()); subprocess.run(["git","init","-q"],cwd=d,check=True)
  subprocess.run(["git","config","user.email","test@example.com"],cwd=d,check=True); subprocess.run(["git","config","user.name","Roach Test"],cwd=d,check=True)
  (d/"app.txt").write_text("hello\n"); subprocess.run(["git","add","."],cwd=d,check=True); subprocess.run(["git","commit","-qm","init"],cwd=d,check=True); return d
 def rr(self,d,*a):return subprocess.run(["python3",str(ROACH),*a],cwd=d,text=True,capture_output=True)
 def test_init_doctor(self):
  d=self.repo();r=self.rr(d,"init","--name","Test");self.assertEqual(r.returncode,0,r.stderr);q=self.rr(d,"doctor");self.assertEqual(q.returncode,0,q.stderr)
 def test_mandatory_gate_cannot_skip(self):
  d=self.repo();self.rr(d,"init","--name","Test");self.rr(d,"requirement","add","FR-001","Works");self.rr(d,"checkpoint","add","CP-001","Test","--verify","true","--requirements","FR-001")
  self.assertNotEqual(self.rr(d,"gate","CP-001","audit","skip","--reason","no").returncode,0)
 def test_tamper_detected(self):
  d=self.repo();self.rr(d,"init","--name","Test");p=d/".roach"/"ledger.jsonl";o=json.loads(p.read_text().splitlines()[0]);o["event"]="tampered";p.write_text(json.dumps(o)+"\n")
  self.assertNotEqual(self.rr(d,"verify-project").returncode,0)
 def test_receipt_stale_after_change(self):
  d=self.repo();self.rr(d,"init","--name","Test");self.rr(d,"requirement","add","FR-001","Works");self.rr(d,"checkpoint","add","CP-001","Test","--verify","true","--requirements","FR-001","--no-ui");self.rr(d,"start","CP-001")
  self.assertEqual(self.rr(d,"verify","CP-001").returncode,0);(d/"app.txt").write_text("changed\n");self.assertNotEqual(self.rr(d,"check","CP-001").returncode,0)
if __name__=="__main__":unittest.main()
