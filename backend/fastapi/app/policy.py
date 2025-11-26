import json
from pathlib import Path
POLICY_FILE = Path(__file__).parent / "policy_master.json"
if not POLICY_FILE.exists():
    POLICY_FILE.write_text(json.dumps({"allowed_extensions":[".txt",".pdf"], "blocked_extensions":[".exe"], "sensitive_patterns":["CONFIDENTIAL"]}, indent=2))

def load_policy():
    return json.loads(POLICY_FILE.read_text())

def update_policy(new_policy: dict):
    POLICY_FILE.write_text(json.dumps(new_policy, indent=2))
    return True
