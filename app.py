import os
import re
import time
import threading
from pathlib import Path, PureWindowsPath
from queue import Queue, Empty

import streamlit as st

from code_watcher import DirectoryWatcher
from file_ops import compile_codefile, compile_structure_md

st.set_page_config(page_title="Codefile Manager", layout="wide")

if "watcher" not in st.session_state:
    st.session_state.watcher = None
if "running" not in st.session_state:
    st.session_state.running = False
if "last_update" not in st.session_state:
    st.session_state.last_update = None
if "events" not in st.session_state:
    st.session_state.events = []

st.title("Codefile Manager — directory watcher")

with st.sidebar:
    st.header("Settings")
    root_dir = st.text_input("Directory to watch (absolute path)", value=str(Path.home()))
    output_dir = st.text_input("Output directory (default: same as root, will be created if missing)", value="")
    include_ext = st.text_input("Include extensions (comma-separated)", value=".py,.kt,.java,.txt,.md,.gradle,.kts,.xml,.cpp,.c,.hpp,.h")
    exclude_dirs = st.text_input("Exclude directories (comma-separated)", value=".git,build,dist,.idea,.gradle,node_modules,__pycache__,.venv,.mypy_cache")
    exclude_files = st.text_input("Exclude file patterns (regex, comma-separated)", value=r".*\.class,.*\.o,.*\.so,.*\.dll,.*\.exe,.*~,.*\.png,.*\.jpg,.*\.bin")
    max_bytes = st.number_input("Max file size to include (bytes)", min_value=1_000, max_value=50_000_000, value=1_000_000, step=1000)
    order_mode = st.selectbox("Order files by", ["path", "mtime"])
    debounce_ms = st.number_input("Debounce interval (ms)", min_value=50, max_value=5000, value=400, step=50)
    show_previews = st.checkbox("Show previews of outputs", value=True)

    start_btn = st.button("▶ Start watching", disabled=st.session_state.running)
    stop_btn = st.button("⏹ Stop watching", disabled=not st.session_state.running)

# --- path normalization helpers ---
def _running_under_wsl() -> bool:
    try:
        with open("/proc/version","r") as f:
            s = f.read()
        return ("Microsoft" in s) or ("WSL" in s)
    except Exception:
        return False

def normalize_input_path(s: str) -> str:
    s = (s or "").strip()
    # Detect Windows absolute path like C:\...
    if len(s) >= 2 and s[1] == ":" and ("\\" in s or "/" in s):
        if _running_under_wsl():
            drive = s[0].lower()
            rest = s[2:].replace("\\", "/").lstrip("/")
            return f"/mnt/{drive}/{rest}"
        # not under WSL; leave as-is for native Windows run
        return s
    return s

# Normalize any user-entered paths for WSL
root_dir = normalize_input_path(root_dir)
if output_dir:
    output_dir = normalize_input_path(output_dir)

# Resolve paths
root_path = Path(root_dir).expanduser().resolve()
if output_dir.strip():
    out_path = Path(output_dir).expanduser().resolve()
else:
    out_path = root_path

codefile_path = out_path / "CODEFILE.txt"
struct_path = out_path / "StructureLatest.md"

# Prepare filter settings
exts = [e.strip().lower() for e in include_ext.split(",") if e.strip()]
exc_dirs = [d.strip() for d in exclude_dirs.split(",") if d.strip()]
import re as _re
file_regexes = [_re.compile(p.strip()) for p in exclude_files.split(",") if p.strip()]

def _start():
    out_path.mkdir(parents=True, exist_ok=True)
    watcher = DirectoryWatcher(
        root=root_path,
        exclude_dirs=exc_dirs,
        exclude_file_regexes=file_regexes,
        debounce_ms=int(debounce_ms),
        on_batch=lambda changed: handle_changes(changed),
    )
    watcher.start()
    st.session_state.watcher = watcher
    st.session_state.running = True

def _stop():
    w = st.session_state.watcher
    if w:
        w.stop()
    st.session_state.running = False
    st.session_state.watcher = None

def _initial_compile():
    # Run once to build fresh outputs
    try:
        compile_codefile(root_path, codefile_path, include_exts=exts, exclude_dirs=exc_dirs,
                         exclude_file_regexes=file_regexes, max_bytes=int(max_bytes), order_mode=order_mode)
        compile_structure_md(root_path, struct_path, exclude_dirs=exc_dirs)
        st.session_state.last_update = time.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as ex:
        st.error(f"Initial compile failed: {ex}")

def handle_changes(changed_paths):
    # Rebuild both outputs when any relevant file changes
    try:
        compile_codefile(root_path, codefile_path, include_exts=exts, exclude_dirs=exc_dirs,
                         exclude_file_regexes=file_regexes, max_bytes=int(max_bytes), order_mode=order_mode)
        compile_structure_md(root_path, struct_path, exclude_dirs=exc_dirs)
        st.session_state.last_update = time.strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.events.extend([f"{time.strftime('%H:%M:%S')} • {p}" for p in changed_paths])
        # Keep last 200 events
        st.session_state.events = st.session_state.events[-200:]
    except Exception as ex:
        st.error(f"Recompile failed: {ex}")

# Handle start/stop buttons
if start_btn:
    if not root_path.exists():
        st.error(f"Root path does not exist: {root_path}")
    else:
        _initial_compile()
        _start()

if stop_btn:
    _stop()

col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Status")
    st.write(f"Root: `{root_path}`")
    st.write(f"Output: `{out_path}`")
    st.write(f"CODEFILE → `{codefile_path}`")
    st.write(f"Structure → `{struct_path}`")
    st.write(f"Running: {st.session_state.running}")
    st.write(f"Last update: {st.session_state.last_update or '—'}")

    if st.session_state.running:
        st.info("Watching for changes… This continues until you press Stop.")
    else:
        st.warning("Not watching. Press Start to begin.")

with col2:
    st.subheader("Recent events")
    if st.session_state.events:
        st.code("\\n".join(st.session_state.events))
    else:
        st.write("—")

st.divider()

if show_previews:
    left, right = st.columns(2)
    with left:
        st.markdown("**CODEFILE preview**")
        try:
            if codefile_path.exists():
                with open(codefile_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                st.code(content[:10000] if len(content) > 10000 else content, language="text")
            else:
                st.write("CODEFILE.txt not yet generated.")
        except Exception as ex:
            st.error(f"Preview error: {ex}")

    with right:
        st.markdown("**StructureLatest.md preview**")
        try:
            if struct_path.exists():
                with open(struct_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                st.code(content, language="markdown")
            else:
                st.write("StructureLatest.md not yet generated.")
        except Exception as ex:
            st.error(f"Preview error: {ex}")

st.caption("Tip: Paste Windows paths too — when running under WSL, they auto-convert to /mnt/<drive>/...; on /mnt paths, the watcher uses polling for reliability.")
