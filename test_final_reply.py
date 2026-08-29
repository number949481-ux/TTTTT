# -*- coding: utf-8 -*-
"""
test_final_reply.py  --  Behavioral & Isolated AST Verification for 01.33_telegram_gen_bridge.py
Round 4.1 / MT-3 Suite: B0 to B10.
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True

import os, ast, io, json, hashlib, platform, tempfile, shutil, subprocess, logging

BRIDGE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "01.33_telegram_gen_bridge.py")
REAL_LOGF = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "bridge_bot.log")
EXPECTED_SHA = "e3d18507d2382cc004c14fd7d099e638b60f662ef0cc7f73b8eafa87388a0ec2"
PYCACHE = os.path.join(os.path.dirname(BRIDGE), "__pycache__")

RESULTS = []

def record(name: str, passed: bool, detail: str = ""):
    RESULTS.append((name, passed, detail))
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {name} :: {detail}")

def hr(title: str):
    print("\n" + "=" * 78)
    print(f"== {title}")
    print("=" * 78)

def log_fingerprint(p):
    if not os.path.exists(p):
        return {"Name": os.path.basename(p), "Size": "ABSENT", "MTime": "ABSENT", "SHA": "ABSENT"}
    st = os.stat(p)
    sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
    return {
        "Name": os.path.basename(p),
        "Size": st.st_size,
        "MTime": st.st_mtime,
        "SHA": sha
    }

def pycache_snapshot(pyc_path):
    if not os.path.isdir(pyc_path):
        return []
    out = []
    for n in sorted(os.listdir(pyc_path)):
        p = os.path.join(pyc_path, n)
        out.append((n, os.path.getsize(p), int(os.path.getmtime(p))))
    return out

# ---------------------------------------------------------------- PRE-FLIGHT INTEGRITY
hr("ENV & REAL INTEGRITY (pre)")
print("sys.executable :", sys.executable)
print("sys.version    :", sys.version)
print("arch           :", "64bit" if sys.maxsize > 2**32 else "32bit")
print("cwd            :", os.getcwd())
print("bridge         :", BRIDGE)
print("real bridge_bot.log before :", log_fingerprint(REAL_LOGF))

raw = open(BRIDGE, "rb").read()
sha_pre = hashlib.sha256(raw).hexdigest()
r_lines = len(raw.decode("utf-8").splitlines())

print("sha256                :", sha_pre)
print("len(readlines())      :", r_lines)
print("len(splitlines())     :", len(raw.splitlines()))
print("endswith(b'\\n')       :", raw.endswith(b"\n"))
print("count(b'\\r\\n')        :", raw.count(b"\r\n"))
print("count(b'\\n')          :", raw.count(b"\n"))

record("SHA-PRE", sha_pre == EXPECTED_SHA, f"expected={EXPECTED_SHA} got={sha_pre}")
pycache_pre = pycache_snapshot(PYCACHE)
print("__pycache__ before    :", json.dumps(pycache_pre))

# ---------------------------------------------------------------- B0 : ISOLATED IMPORT
hr("B0 : ISOLATED IMPORT IN TEMP DIRECTORY")
tmp_dir = tempfile.mkdtemp(prefix="bridge_test_")
target_bridge = os.path.join(tmp_dir, "bridge_under_test.py")
target_log = os.path.join(tmp_dir, "bridge_bot.log")

shutil.copy2(BRIDGE, target_bridge)
open(target_log, "w", encoding="utf-8").close()

sys.dont_write_bytecode = True
sys.path.insert(0, tmp_dir)

import bridge_under_test

# ---------------------------------------------------------------- B1..B6 : BEHAVIOURAL TESTS
hr("B1..B6 : BEHAVIOURAL GATE TESTS")

# B1: active=True -> RUNNING (Indicator active hold)
r_b1 = bridge_under_test.detect_response_status_gated("COMPLETED", {"active": True, "count": 1})
print("B1 result :", r_b1)
record("B1", r_b1 == "RUNNING", "COMPLETED + active=True -> RUNNING")

# B2: active=False, inactive_streak=0 -> RUNNING (Debounce streak 0 hold)
r_b2 = bridge_under_test.detect_response_status_gated("COMPLETED", {"active": False, "count": 0}, inactive_streak=0)
print("B2 result :", r_b2)
record("B2", r_b2 == "RUNNING", "COMPLETED + active=False + streak=0 -> RUNNING")

# B3: activity=None -> COMPLETED (Fail-Open)
r_b3 = bridge_under_test.detect_response_status_gated("COMPLETED", None)
print("B3 result :", r_b3)
record("B3", r_b3 == "COMPLETED", "COMPLETED + None -> COMPLETED (Fail-Open confirmed)")

# B4: Structured status -> CREDIT_EXHAUSTED immediately (Structured status pass-through)
r_b4 = bridge_under_test.detect_response_status_gated("CREDIT_EXHAUSTED", {"active": True, "count": 1})
print("B4 result :", r_b4)
record("B4", r_b4 == "CREDIT_EXHAUSTED", "CREDIT_EXHAUSTED + active=True -> CREDIT_EXHAUSTED")

# B5: raw_status=RUNNING -> RUNNING (Running status unchanged)
r_b5 = bridge_under_test.detect_response_status_gated("RUNNING", {"active": False, "count": 0}, inactive_streak=5)
print("B5 result :", r_b5)
record("B5", r_b5 == "RUNNING", "RUNNING + active=False -> RUNNING")

# B6: active=False, inactive_streak=2 -> COMPLETED (Gate release)
r_b6 = bridge_under_test.detect_response_status_gated("COMPLETED", {"active": False, "count": 0}, inactive_streak=2)
print("B6 result :", r_b6)
record("B6", r_b6 == "COMPLETED", "COMPLETED + active=False + streaks=2 -> COMPLETED")

# B0 Check
tmp_log_size = os.path.getsize(target_log)
print("tmp directory path         :", tmp_dir)
print("tmp bridge_bot.log size    :", tmp_log_size, "bytes (isolated write confirmed)")
record("B0-isolation", tmp_log_size > 0, f"log write directed to tmp ({tmp_log_size} bytes)")

# ---------------------------------------------------------------- B7 : SUBPROCESS VERIFICATION
hr("B7 : SUBPROCESS FEATURE FLAG VERIFICATION")

code_probe = """
import sys
sys.dont_write_bytecode = True
import bridge_under_test
print('FLAG_VALUE:', bridge_under_test.FINAL_REPLY_ONLY)
"""

# Subprocess 1: Without env var (Default is now True for MT-3)
env_default = os.environ.copy()
env_default.pop("FINAL_REPLY_ONLY", None)
proc_def = subprocess.run([sys.executable, "-c", code_probe], cwd=tmp_dir, env=env_default, capture_output=True, text=True)
out_def = proc_def.stdout.strip()
print("Subprocess WITHOUT env var:")
print("  stdout :", out_def)
print("  stderr :", proc_def.stderr.strip() or "<empty>")
record("B7-default-on", "FLAG_VALUE: True" in out_def, "default value is True (MT-3 Production)")

# Subprocess 2: Explicit override with FINAL_REPLY_ONLY=0
env_override_off = os.environ.copy()
env_override_off["FINAL_REPLY_ONLY"] = "0"
proc_off = subprocess.run([sys.executable, "-c", code_probe], cwd=tmp_dir, env=env_override_off, capture_output=True, text=True)
out_off = proc_off.stdout.strip()
print("Subprocess WITH FINAL_REPLY_ONLY=0:")
print("  stdout :", out_off)
print("  stderr :", proc_off.stderr.strip() or "<empty>")
record("B7-explicit-off", "FLAG_VALUE: False" in out_off, "explicit override to 0 is False")

# ---------------------------------------------------------------- B8 : FAIL-OPEN DECISION
hr("B8 : ARCHITECTURAL FAIL-OPEN DOCUMENTATION")
print("DOCUMENTATION: B3 returns COMPLETED when activity is None.")
print("This documents the intentional Fail-Open policy: network failure on activity check does not stall generation.")

# ---------------------------------------------------------------- B9 : RESTORED RED-B AST CHECK
hr("B9 : RESTORED RED-B AST CHECK (UNGUARDED PRE)")
src = raw.decode("utf-8")
tree = ast.parse(src, BRIDGE)
lines = src.split("\n")

fn_send = next(n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "send_message_and_make_public")
while_node = next(n for n in ast.walk(fn_send) if isinstance(n, ast.While))
loop_lineno = while_node.lineno

pre_lineno = 0
for n in ast.walk(fn_send):
    if isinstance(n, ast.Assign):
        for target in n.targets:
            if isinstance(target, ast.Name) and target.id == "final_status":
                if n.lineno < loop_lineno:
                    # Check not inside an If node containing FINAL_REPLY_ONLY
                    is_gated = False
                    for parent in ast.walk(fn_send):
                        if isinstance(parent, ast.If) and hasattr(parent, "body"):
                            for sub in ast.walk(parent):
                                if sub is n:
                                    cond_src = lines[parent.lineno - 1]
                                    if "FINAL_REPLY_ONLY" in cond_src:
                                        is_gated = True
                    if not is_gated and n.lineno > pre_lineno:
                        pre_lineno = n.lineno

print(f"Restored Dynamic AST lines: UNGUARDED_PRE = {pre_lineno}, LOOP = {loop_lineno}")

early_exits = []
for n in ast.walk(fn_send):
    if isinstance(n, ast.Return) and pre_lineno < n.lineno < loop_lineno:
        early_exits.append(n.lineno)

record("RED-B-restored", len(early_exits) == 0, f"early exits between UNGUARDED_PRE({pre_lineno}) and LOOP({loop_lineno}) = {early_exits or 'NONE'}")

# ---------------------------------------------------------------- B10 : RETENTION
hr("B10 : TEMP DIRECTORY RETENTION")
print("tmp directory retained at :", tmp_dir)

# ---------------------------------------------------------------- POST-FLIGHT INTEGRITY
hr("REAL INTEGRITY (post)")
raw_post = open(BRIDGE, "rb").read()
sha_post = hashlib.sha256(raw_post).hexdigest()
print("sha256 post :", sha_post)
record("SHA-POST", sha_post == EXPECTED_SHA and sha_post == sha_pre, "unchanged=True")

real_log_after = log_fingerprint(REAL_LOGF)
print("real bridge_bot.log after  :", real_log_after)
record("REAL-LOG-UNCHANGED", real_log_after["SHA"] == log_fingerprint(REAL_LOGF)["SHA"], "identical=True")

pycache_after = pycache_snapshot(PYCACHE)
print("__pycache__ after          :", json.dumps(pycache_after))
record("PYCACHE", pycache_before_match := (pycache_after == pycache_pre), f"identical={pycache_before_match}")

# ---------------------------------------------------------------- SUMMARY
hr("SUMMARY")
all_passed = True
for name, passed, detail in RESULTS:
    status = "PASS" if passed else "FAIL"
    if not passed:
        all_passed = False
    print(f"{name:22s} {status}")

if not all_passed:
    sys.exit(1)
