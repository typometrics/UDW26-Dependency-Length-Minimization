#!/usr/bin/env python3
"""
Save VS Code Copilot Chat sessions to Markdown files in chat_history/.

Usage:
    python3 save_chat.py           # save all unsaved sessions
    python3 save_chat.py --all     # re-save all sessions (overwrite)
"""

import json
import os
import sys
import re
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE_STORAGE = Path.home() / "Library/Application Support/Code/User/workspaceStorage"
WORKSPACE_HASH = "2bc71c00fac80d9e1ad2c6d26fea9318"
SESSIONS_DIR = WORKSPACE_STORAGE / WORKSPACE_HASH / "chatSessions"
OUTPUT_DIR = Path(__file__).parent / "chat_history"


def ms_to_dt(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).astimezone()


def extract_text_from_parts(parts) -> str:
    """Extract plain text from a message parts list."""
    if isinstance(parts, list):
        return "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in parts)
    return str(parts) if parts else ""


def extract_response_text(response_items) -> str:
    """Extract assistant response text from the response array.

    VS Code stores response content in items where:
    - items WITHOUT a 'kind' field (IMarkdownString): value.value = plain text
    - 'markdownContent': value.value = text
    - Other kinds (toolInvocationSerialized, thinking, undoStop, etc.) are skipped.
    """
    texts = []
    for item in response_items or []:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")

        # Items with no 'kind' are IMarkdownString text chunks (the main response text)
        if kind is None:
            val = item.get("value", "")
            if isinstance(val, dict):
                t = val.get("value", "")
                if isinstance(t, str) and t.strip():
                    texts.append(t)
            elif isinstance(val, str) and val.strip():
                texts.append(val)

        # markdownContent (older format)
        elif kind == "markdownContent":
            val = item.get("value", {})
            if isinstance(val, dict):
                t = val.get("value", "")
                if isinstance(t, str) and t.strip():
                    texts.append(t)

    return "\n".join(t for t in texts if t)


def rebuild_session(jsonl_path: Path) -> dict:
    """
    Parse a JSONL session file and return a dict with:
      title, creationDate, requests: [{user_text, response_text, timestamp}]
    """
    state = {}
    requests_map = {}  # index -> {user, response_parts}

    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            kind = entry.get("kind")

            # kind=0: initial snapshot
            if kind == 0:
                v = entry.get("v", {})
                state["title"] = v.get("customTitle", "")
                state["creationDate"] = v.get("creationDate", 0)
                state["sessionId"] = v.get("sessionId", "")
                for i, req in enumerate(v.get("requests", [])):
                    msg = req.get("message", {})
                    user_text = msg.get("text", "") or extract_text_from_parts(msg.get("parts", []))
                    resp_text = extract_response_text(req.get("response", []))
                    ts = req.get("timestamp", state["creationDate"])
                    requests_map[i] = {
                        "user": user_text,
                        "response": resp_text,
                        "timestamp": ts,
                    }

            # kind=2: incremental update
            elif kind == 2:
                k = entry.get("k", [])
                v = entry.get("v")

                # New top-level metadata
                if k == ["customTitle"] and isinstance(v, str):
                    state["title"] = v
                elif k == ["creationDate"] and isinstance(v, int):
                    state["creationDate"] = v

                # New request appended: k = ["requests", N] and v is a full request dict
                elif (len(k) == 2 and k[0] == "requests" and isinstance(k[1], int)
                      and isinstance(v, dict) and "message" in v):
                    i = k[1]
                    msg = v.get("message", {})
                    user_text = msg.get("text", "") or extract_text_from_parts(msg.get("parts", []))
                    ts = v.get("timestamp", state.get("creationDate", 0))
                    if i not in requests_map:
                        requests_map[i] = {"user": user_text, "response": "", "timestamp": ts}
                    else:
                        requests_map[i]["user"] = user_text

                # Response update: k = ["requests", N, "response"]
                elif (len(k) == 3 and k[0] == "requests" and k[2] == "response"
                      and isinstance(v, list)):
                    i = k[1]
                    resp_text = extract_response_text(v)
                    if i not in requests_map:
                        requests_map[i] = {"user": "", "response": resp_text, "timestamp": 0}
                    else:
                        # Append or replace
                        if resp_text:
                            requests_map[i]["response"] = resp_text

    state["requests"] = [requests_map[i] for i in sorted(requests_map.keys())]
    return state


def session_to_markdown(session: dict, jsonl_path: Path) -> str:
    title = session.get("title", "Untitled")
    creation_ms = session.get("creationDate", 0)
    creation_dt = ms_to_dt(creation_ms) if creation_ms else datetime.now().astimezone()
    requests = session.get("requests", [])

    file_size = jsonl_path.stat().st_size
    lines = [
        f"# Chat Session: {title}",
        f"# Created: {creation_dt.strftime('%Y-%m-%d %H:%M:%S')}",
        f"# Last modified: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S')}",
        f"# Original size: {file_size:,} bytes",
        f"# Exchanges: {len(requests)}",
        "=" * 80,
        "",
    ]

    for req in requests:
        lines.append("## USER")
        lines.append("")
        lines.append(req.get("user", "").strip())
        lines.append("")
        lines.append("-" * 80)
        lines.append("")
        lines.append("## ASSISTANT")
        lines.append("")
        resp = req.get("response", "").strip()
        lines.append(resp if resp else "[No response captured]")
        lines.append("")
        lines.append("-" * 80)
        lines.append("")

    return "\n".join(lines)


def output_filename(session: dict, session_id: str) -> str:
    creation_ms = session.get("creationDate", 0)
    if creation_ms:
        dt = ms_to_dt(creation_ms)
        date_str = dt.strftime("%Y%m%d_%H%M")
    else:
        date_str = datetime.now().strftime("%Y%m%d_%H%M")
    short_id = session_id[:8]
    return f"session_{date_str}_{short_id}.md"


def main():
    overwrite = "--all" in sys.argv
    OUTPUT_DIR.mkdir(exist_ok=True)

    existing = {f.name for f in OUTPUT_DIR.glob("*.md")}

    saved = 0
    skipped = 0
    for jsonl_file in sorted(SESSIONS_DIR.glob("*.jsonl")):
        session_id = jsonl_file.stem  # UUID without .jsonl

        try:
            session = rebuild_session(jsonl_file)
        except Exception as e:
            print(f"  ERROR parsing {jsonl_file.name}: {e}")
            continue

        if not session.get("requests"):
            skipped += 1
            continue

        fname = output_filename(session, session_id)

        if fname in existing and not overwrite:
            # Check if the file needs updating (size changed)
            out_path = OUTPUT_DIR / fname
            # Update if the source is newer or larger
            src_mtime = jsonl_file.stat().st_mtime
            dst_mtime = out_path.stat().st_mtime
            if src_mtime <= dst_mtime:
                skipped += 1
                continue

        out_path = OUTPUT_DIR / fname
        md = session_to_markdown(session, jsonl_file)
        out_path.write_text(md, encoding="utf-8")
        print(f"  Saved: {fname}  ({len(session['requests'])} exchanges)")
        saved += 1

    print(f"\nDone. {saved} session(s) saved, {skipped} skipped.")


if __name__ == "__main__":
    main()
