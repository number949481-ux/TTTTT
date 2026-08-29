# -*- coding: utf-8 -*-
"""
analyze_run.py  --  Log Analysis Tool for bridge_bot.log (Round 5.14 Dynamic AST Origin Audit)
Read-only analysis tool for manual experiment runs.

STATEMENT:
وسم origin لا يكشف التسريب؛ وظيفته الوحيدة استبعاد ضجيج كروت الواجهة وإشعارات الإقلاع.
الحكم الآلي متاح في ذراع Treatment فقط (عبر الترتيب الزمني حول FINAL_FETCH_OK)،
وذراع Control يبقى CONTROL_NO_AUTO_VERDICT بحكم التصميم لا بحكم العجز.
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import os, argparse, re, ast, hashlib
from datetime import datetime

DEFAULT_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bridge_bot.log")
DEFAULT_BRIDGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "01.33_telegram_gen_bridge.py")

def derive_final_path_lines(bridge_path=None):
    bpath = bridge_path or DEFAULT_BRIDGE_PATH
    if not os.path.exists(bpath):
        return None, None, f"FAIL: Bridge file not found at {bpath}"
    
    raw = open(bpath, "rb").read()
    b_sha = hashlib.sha256(raw).hexdigest()
    
    try:
        tree = ast.parse(raw.decode("utf-8"), str(bpath))
    except Exception as e:
        return None, b_sha, f"FAIL: AST parse error: {e}"

    candidates = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "process_user_task_async":
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    name = None
                    if isinstance(child.func, ast.Name):
                        name = child.func.id
                    elif isinstance(child.func, ast.Attribute):
                        name = child.func.attr
                    if name == "send_telegram_message":
                        # Match the completion delivery call
                        for arg in child.args:
                            if isinstance(arg, ast.Name) and arg.id == "res_msg":
                                candidates.append(child.lineno)
    
    if len(candidates) not in (1, 2):
        return None, b_sha, f"FAIL: FINAL_PATH_AMBIGUOUS (Found {len(candidates)} candidate lines: {candidates})"
    
    return set(candidates), b_sha, None

def parse_log_time(line):
    m = re.match(r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", line)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    return None

def parse_tg_send_details(line):
    m_chars = re.search(r"TG_SEND_OK\s+chars=(\d+)", line)
    m_chat = re.search(r"chat=([^\s]+)", line)
    m_caller = re.search(r"caller=([^\s]+)", line)
    m_origin = re.search(r"origin=([^\s]+)", line)

    chars = int(m_chars.group(1)) if m_chars else None
    chat = str(m_chat.group(1)) if m_chat else None
    caller = str(m_caller.group(1)) if m_caller else "UNAVAILABLE"
    origin = str(m_origin.group(1)) if m_origin else "UNAVAILABLE"

    return chars, chat, caller, origin

def parse_error_chat(line):
    m = re.search(r"chat=([^\s,]+)", line)
    if m:
        return str(m.group(1))
    return None

def analyze(since_str=None, until_str=None, log_path=None, bridge_path=None):
    target_log = log_path or DEFAULT_LOG_PATH
    if not os.path.exists(target_log):
        print(f"ERROR: Log file not found at {target_log}")
        return

    # Derive dynamic AST final path lines
    final_lines_set, bridge_sha, err = derive_final_path_lines(bridge_path)
    if err:
        print(err)
        return

    with open(target_log, "r", encoding="utf-8", errors="replace") as f:
        all_raw_lines = f.readlines()

    parsed_lines = []
    for l in all_raw_lines:
        t = parse_log_time(l)
        parsed_lines.append((t, l.strip()))

    since_dt = None
    until_dt = None
    startup_arm = "UNKNOWN"
    anchored_at = None

    if since_str:
        try:
            since_dt = datetime.strptime(since_str, "%Y-%m-%d %H:%M:%S")
            anchored_at = str(since_dt)
        except ValueError:
            print(f"WARNING: Invalid since format '{since_str}'. Expected 'YYYY-MM-DD HH:MM:SS'.")

    if until_str:
        try:
            until_dt = datetime.strptime(until_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print(f"WARNING: Invalid until format '{until_str}'. Expected 'YYYY-MM-DD HH:MM:SS'.")

    # Filter lines strictly within [since_dt, until_dt]
    lines = []
    for t, l in parsed_lines:
        if since_dt and t and t < since_dt:
            continue
        if until_dt and t and t > until_dt:
            continue
        lines.append((t, l))

    # Check for startup arm inside the filtered window first
    for _, l in lines:
        if "FINAL_REPLY_ONLY =" in l or "FINAL_REPLY_ONLY=" in l:
            if "True" in l:
                startup_arm = "True"
            elif "False" in l:
                startup_arm = "False"
            break

    # If not found inside window, search backwards before since_dt
    if startup_arm == "UNKNOWN":
        for idx in range(len(parsed_lines) - 1, -1, -1):
            t, l = parsed_lines[idx]
            if "FINAL_REPLY_ONLY =" in l or "FINAL_REPLY_ONLY=" in l:
                if not since_dt or (t and t <= since_dt):
                    if "True" in l:
                        startup_arm = "True"
                    elif "False" in l:
                        startup_arm = "False"
                    if not since_str:
                        since_dt = t
                        anchored_at = str(t) if t else f"Line {idx+1}"
                    break

    print("=" * 82)
    print(f"📊 ANALYZE RUN REPORT (Window line count: {len(lines)})")
    print(f"Log File:         {target_log}")
    print(f"FINAL_PATH_LINES: {final_lines_set} (derived from AST, bridge_sha={bridge_sha[:16]}...)")
    if anchored_at:
        print(f"ANCHORED_AT:      {anchored_at}   |   ARM = {startup_arm}")
    else:
        print(f"ANCHORED_AT:      NO_STARTUP_MARKER   |   ARM = {startup_arm}")
    if until_str:
        print(f"UNTIL:            {until_str}")
    print("Mode:             DYNAMIC AST ORIGIN AUDIT (origin=*:FINAL_PATH_LINES -> FINAL_PATH)")
    print("=" * 82)

    # 1. FINAL_REPLY_ONLY in filtered window
    flag_val = startup_arm if startup_arm != "UNKNOWN" else "NOT_LOGGED"
    for _, l in lines:
        if "FINAL_REPLY_ONLY =" in l or "FINAL_REPLY_ONLY=" in l:
            flag_val = l
            break
    print(f"• FINAL_REPLY_ONLY:            {flag_val}")

    # 2. Gate events counts & Multi-attempt detection
    hold_lines = [(t, l) for t, l in lines if "ACTIVITY_GATE_HOLD" in l]
    release_lines = [(t, l) for t, l in lines if "ACTIVITY_GATE_RELEASE" in l]
    fetch_ok_lines = [(t, l) for t, l in lines if "FINAL_FETCH_OK" in l]
    fetch_fallback_lines = [(t, l) for t, l in lines if "FINAL_FETCH_FALLBACK" in l]
    account_attempts = [(t, l) for t, l in lines if "تجربة حساب" in l or "تم اختيار حساب" in l]

    print(f"• ACTIVITY_GATE_HOLD count:    {len(hold_lines)}")
    for t, l in hold_lines:
        print(f"    - [{t}] {l}")
    print(f"• ACTIVITY_GATE_RELEASE count: {len(release_lines)}")
    for t, l in release_lines:
        print(f"    - [{t}] {l}")
    print(f"• FINAL_FETCH_OK count:        {len(fetch_ok_lines)}")
    for t, l in fetch_ok_lines:
        print(f"    - [{t}] {l}")
    print(f"• FINAL_FETCH_FALLBACK count:  {len(fetch_fallback_lines)}")
    for t, l in fetch_fallback_lines:
        print(f"    - [{t}] {l}")

    if len(account_attempts) > 1:
        print(f"⚠️ MULTI_ATTEMPT_WINDOW = {len(account_attempts)} attempts detected in this window!")

    # 3. Independent Raw Grep Check (O5)
    raw_sends_in_window = [l for t, l in lines if "TG_SEND_OK" in l]
    raw_grep_count = len(raw_sends_in_window)

    last_fetch_time = fetch_ok_lines[-1][0] if fetch_ok_lines else None
    anchor_mode = "FETCH_OK" if last_fetch_time is not None else ("NO_GATE" if raw_grep_count > 0 else "NONE")

    classified_sends = []
    final_path_sends = []
    non_final_sends = []
    legacy_unavailable_sends = []
    active_target_chats = set()

    for idx, (t, l) in enumerate([(t, l) for t, l in lines if "TG_SEND_OK" in l], 1):
        chars, chat, caller, origin = parse_tg_send_details(l)
        if chat:
            active_target_chats.add(chat)

        is_final_origin = False
        if origin != "UNAVAILABLE":
            for fl in final_lines_set:
                if origin.endswith(f":{fl}"):
                    is_final_origin = True
                    break

        if origin == "UNAVAILABLE" or caller == "UNAVAILABLE":
            cls = "LEGACY_UNAVAILABLE"
            legacy_unavailable_sends.append((t, chars, chat, caller, origin, l))
        elif caller == "send_telegram_message" and is_final_origin:
            cls = "FINAL_PATH_SEND"
            final_path_sends.append((t, chars, chat, caller, origin, l))
        else:
            cls = "NON_FINAL"
            non_final_sends.append((t, chars, chat, caller, origin, l))

        classified_sends.append((idx, t, chars, chat, caller, origin, cls, l))

    print(f"• ANCHOR:                      {anchor_mode}")
    print(f"• TG_SEND_OK total count:      {raw_grep_count}")
    print(f"    - FINAL_PATH sends:        {len(final_path_sends)} (caller=send_telegram_message origin=*:{final_lines_set})")
    print(f"    - NON_FINAL sends:         {len(non_final_sends)} (UI cards, status, admin, cooldown)")
    print(f"    - LEGACY_UNAVAILABLE:      {len(legacy_unavailable_sends)} (Old lines without caller/origin tags)")

    # Strict Independent Verification
    if raw_grep_count == len(classified_sends):
        print(f"• Independent Raw Grep Check:  PASS (Raw Grep={raw_grep_count} == Classified={len(classified_sends)})")
    else:
        print(f"• Independent Raw Grep Check:  FAIL (Raw Grep={raw_grep_count} != Classified={len(classified_sends)})")

    # Print all classified sends without truncation
    for idx, t, chars, chat, caller, origin, cls, l in classified_sends:
        print(f"    #{idx:02d} [{cls}] at {t} | caller={caller} | origin={origin} | chars={chars} | chat={chat}")

    # Process 403 / Send Errors narrowing
    send_error_raw = [(t, l) for t, l in lines if "فشل إرسال رسالة تليجرام" in l or "403" in l or "Forbidden" in l]
    fatal_target_403 = False
    if send_error_raw:
        print(f"• Send Errors / 403 total:     {len(send_error_raw)}")
        for t, l in send_error_raw:
            err_chat = parse_error_chat(l)
            if err_chat and active_target_chats and err_chat not in active_target_chats:
                print(f"    [UNRELATED_403] at {t} | chat={err_chat} | raw={l}")
            elif err_chat and active_target_chats and err_chat in active_target_chats:
                print(f"    [TARGET_CHAT_403] at {t} | chat={err_chat} | raw={l}")
                fatal_target_403 = True
            elif not err_chat:
                print(f"    [UNKNOWN_403_TARGET] at {t} | raw={l}")
            else:
                print(f"    - [{t}] {l}")

    # 4. Gate Duration
    if hold_lines and fetch_ok_lines:
        first_hold_time = hold_lines[0][0]
        if first_hold_time and last_fetch_time:
            delta = (last_fetch_time - first_hold_time).total_seconds()
            print(f"• Gate Duration (HOLD -> FINAL_FETCH_OK): {delta:.1f} seconds")
        else:
            print("• Gate Duration: Timestamps could not be computed.")
    else:
        print("• Gate Duration: N/A")

    # 5. Activity Signature Anomalies
    activity_anomalies = [(t, l) for t, l in lines if any(k in l for k in ["P18", "activity", "fetch_project_activity_signature"]) and any(w in l.lower() for w in ["none", "error", "fail", "exception"])]
    print(f"• Activity Signature Anomalies: {len(activity_anomalies)}")
    for t, l in activity_anomalies:
        print(f"    - [{t}] {l}")

    # 6. Automatic Judgment (O4)
    print("-" * 82)
    if fatal_target_403 or raw_grep_count == 0:
        judgment = "INVALID (Send failed on target chat with 403 or 0 messages reached Telegram)"
    elif len(legacy_unavailable_sends) == raw_grep_count and raw_grep_count > 0:
        judgment = "NEEDS_RERUN (Caller/origin tags unavailable in legacy log lines — rerun required to evaluate via caller/origin)"
    elif startup_arm == "False":
        judgment = f"CONTROL_NO_AUTO_VERDICT (Control arm: automated verdict disabled by design; {len(final_path_sends)} FINAL_PATH send(s) logged for manual inspection)"
    elif startup_arm == "True":
        if len(final_path_sends) == 1 and last_fetch_time and (not final_path_sends[0][0] or final_path_sends[0][0] >= last_fetch_time):
            judgment = "LEAK=NO (Clean single final path send post-release confirmed)"
        elif len(final_path_sends) >= 2:
            judgment = f"LEAK=YES ({len(final_path_sends)} multiple final path sends detected in single request)"
        elif len(final_path_sends) == 1 and last_fetch_time and final_path_sends[0][0] and final_path_sends[0][0] < last_fetch_time:
            judgment = f"LEAK=YES (Premature final path send at {final_path_sends[0][0]} before FINAL_FETCH_OK at {last_fetch_time})"
        elif len(final_path_sends) == 0:
            judgment = "INVALID (0 final path messages delivered to Telegram)"
        else:
            judgment = "INVALID (Ambiguous send distribution)"
    else:
        judgment = "INVALID (Unknown startup arm)"

    print(f"🏁 JUDGMENT: {judgment}")
    print("=" * 82)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze bridge_bot.log runs")
    parser.add_argument("--since", type=str, default=None, help="Filter logs since YYYY-MM-DD HH:MM:SS (default: auto-anchor to last startup)")
    parser.add_argument("--until", type=str, default=None, help="Filter logs until YYYY-MM-DD HH:MM:SS")
    parser.add_argument("--log-file", type=str, default=None, help="Custom log file path (for testing)")
    parser.add_argument("--bridge-file", type=str, default=None, help="Custom bridge file path (for testing)")
    args = parser.parse_args()
    analyze(args.since, args.until, args.log_file, args.bridge_file)
