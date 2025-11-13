import os
import platform
import json
import re
import time
import hashlib
from pathlib import Path
from typing import List, Dict

import streamlit as st

from file_ops import (
    compile_codefile_from_paths,
    compile_structure_md,
)

st.set_page_config(page_title="CodeManager V2 — Hybrid", layout="wide")

# ---------- Helpers ----------
def _running_under_wsl() -> bool:
    """Robust WSL detection."""
    try:
        if os.environ.get("WSL_DISTRO_NAME"):
            return True
        if Path("/proc/sys/fs/binfmt_misc/WSLInterop").exists():
            return True
        rel = platform.uname().release.lower()
        ver = Path("/proc/version").read_text(errors="ignore").lower() if Path("/proc/version").exists() else ""
        return ("microsoft" in rel) or ("microsoft" in ver) or ("wsl" in rel) or ("wsl" in ver)
    except Exception:
        return False

_WIN_DRIVE_RE = re.compile(r'^\s*([A-Za-z]):[\\/](.*)$')

def normalize_input_path(s: str) -> str:
    """
    Accepts Windows or POSIX. Handles quotes, backslashes, and whitespace.
    On POSIX/WSL, converts Windows absolute 'C:\\...' to '/mnt/c/...'.
    """
    if not s:
        return ""
    s = s.strip().strip('"').strip("'")

    # Already POSIX absolute
    if s.startswith("/"):
        return s

    # Windows absolute (C:\... or C:/...)
    m = _WIN_DRIVE_RE.match(s)
    if m:
        drive = m.group(1).lower()
        rest = m.group(2).replace("\\", "/").lstrip("/")
        # If running on POSIX (WSL/Linux), prefer /mnt/<drive>/...
        if os.name == "posix":
            return f"/mnt/{drive}/{rest}"
        # Otherwise leave as Windows form
        return f"{drive.upper()}:\\{rest.replace('/', '\\')}"
    # Fallback (relative or other)
    return s

def _sha256_quick(p: Path, max_bytes=1_000_000) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        h.update(f.read(max_bytes))
    return h.hexdigest()

# ---------- Manifest I/O (migration-safe) ----------
MANIFEST = Path(".codemanager/manifest.json")

def _empty_manifest() -> Dict:
    return {
        "version": 2,
        "files": [],     # list of {"path": "..."}
        "folders": [],   # list of {"path": "...", "exts": [...], "recursive": true}
        "last_compiled": None,
    }

def _coerce_list(x):
    return x if isinstance(x, list) else []

def load_manifest() -> Dict:
    base = _empty_manifest()
    if not MANIFEST.exists():
        return base
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8")) or {}
    except Exception:
        return base

    # Migrate V1 shape: {"tracked": ["...","..."]}
    tracked = data.get("tracked")
    if isinstance(tracked, list) and tracked and not data.get("files"):
        data["files"] = [{"path": str(Path(p))} for p in tracked]

    out = _empty_manifest()
    out["files"] = _coerce_list(data.get("files")) or []
    out["files"] = [{"path": str(Path(f.get("path", "")))} for f in out["files"]
                    if isinstance(f, dict) and f.get("path")]

    raw_folders = _coerce_list(data.get("folders")) or []
    norm_folders = []
    for fd in raw_folders:
        if not isinstance(fd, dict):
            continue
        p = fd.get("path")
        if not p:
            continue
        exts = fd.get("exts") or []
        if isinstance(exts, str):
            exts = [e.strip().lower() for e in exts.split(",") if e.strip()]
        elif isinstance(exts, list):
            exts = [str(e).strip().lower() for e in exts if str(e).strip()]
        norm_folders.append({
            "path": str(Path(p)),
            "exts": exts,
            "recursive": bool(fd.get("recursive", True)),
        })
    out["folders"] = norm_folders

    if data.get("last_compiled"):
        out["last_compiled"] = str(data["last_compiled"])

    return out

def save_manifest(m: Dict):
    clean = _empty_manifest()
    clean["files"] = [{"path": str(Path(f["path"]))}
                      for f in _coerce_list(m.get("files"))
                      if isinstance(f, dict) and f.get("path")]
    norm_folders = []
    for fd in _coerce_list(m.get("folders")):
        if not isinstance(fd, dict) or not fd.get("path"):
            continue
        exts = fd.get("exts") or []
        if isinstance(exts, str):
            exts = [e.strip().lower() for e in exts.split(",") if e.strip()]
        norm_folders.append({
            "path": str(Path(fd["path"])),
            "exts": [str(e).strip().lower() for e in exts],
            "recursive": bool(fd.get("recursive", True)),
        })
    clean["folders"] = norm_folders
    clean["last_compiled"] = m.get("last_compiled")
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(clean, indent=2), encoding="utf-8")

# ---------- Scan logic ----------
def list_folder_files(folder: Path, exts: List[str], recursive: bool = True) -> List[Path]:
    exts = [e.lower().strip() for e in exts if e.strip()]
    paths = []
    if not folder.exists() or not folder.is_dir():
        return paths
    it = folder.rglob("*") if recursive else folder.glob("*")
    for p in it:
        if p.is_file():
            if not exts or p.suffix.lower() in exts:
                paths.append(p)
    return paths

def build_hybrid_set(manifest: Dict) -> List[Path]:
    files: List[Path] = []

    # explicit files
    for f in manifest.get("files", []):
        raw = f["path"]
        norm = normalize_input_path(raw)
        p = Path(norm).expanduser()
        if p.exists() and p.is_file():
            files.append(p)

    # folders with ext filters
    for fd in manifest.get("folders", []):
        raw = fd["path"]
        norm = normalize_input_path(raw)
        root = Path(norm).expanduser()
        exts = fd.get("exts", [])
        rec = bool(fd.get("recursive", True))
        files.extend(list_folder_files(root, exts, recursive=rec))

    # de-dup & stable order
    uniq = []
    seen = set()
    for p in sorted(files, key=lambda x: str(x).lower()):
        s = str(p.resolve())
        if s not in seen:
            seen.add(s)
            uniq.append(Path(s))
    return uniq

# ---------- UI ----------
st.title("🧠 CodeManager V2 — Hybrid Tracking")
st.caption("Add **files** and **folders** (with extension filter). Compile outputs from the union. No watcher required.")

with st.sidebar:
    st.header("Output Settings")
    output_dir = st.text_input("Output directory (absolute). Default: current working dir", value="")
    exts_default = ".py,.kt,.java,.kts,.gradle,.xml,.md,.txt,.c,.cpp,.h,.hpp"
    default_folder_exts = st.text_input("Default folder ext filter (comma-separated)", value=exts_default)
    recursive = st.checkbox("Recurse folders", value=True)
    max_bytes = st.number_input("Max file size to read", min_value=1000, max_value=50_000_000, value=1_000_000, step=1000)
    show_previews = st.checkbox("Show previews after compile", value=True)

out_path = Path(normalize_input_path(output_dir)).expanduser().resolve() if output_dir.strip() else Path.cwd()
codefile_path = out_path / "CODEFILE.txt"
struct_path = out_path / "StructureLatest.md"

m = load_manifest()

st.markdown("### Add items to Hybrid Tracker")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Add Files (comma-separated)")
    files_csv = st.text_area("Absolute paths", placeholder=r"C:\Users\You\proj\a.py, /mnt/c/Users/You/proj/b.kt")
    if st.button("Add Files"):
        added, skipped = 0, 0
        for raw in [x.strip() for x in files_csv.split(",") if x.strip()]:
            norm = normalize_input_path(raw)
            p = Path(norm).expanduser()
            st.caption(f"File add: raw='{raw}'  →  normalized='{norm}'")
            if p.exists() and p.is_file():
                if not any(x.get("path") == raw for x in m.get("files", [])):
                    m["files"].append({"path": raw})  # store as entered; normalize at use time
                    added += 1
                else:
                    skipped += 1
            else:
                st.warning(f"File not found (normalized check): {norm}")
        save_manifest(m)
        st.success(f"Files added: {added}. Skipped (already present): {skipped}.")

with col2:
    st.subheader("Add Folders (comma-separated)")
    folders_csv = st.text_area("Absolute folders", placeholder=r"C:\Users\You\proj\src, /mnt/c/Users\You\other")
    folder_exts = st.text_input("Extensions for these folders", value=default_folder_exts)
    if st.button("Add Folders"):
        exts = [e.strip().lower() for e in folder_exts.split(",") if e.strip()]
        added, skipped = 0, 0
        for raw in [x.strip() for x in folders_csv.split(",") if x.strip()]:
            norm = normalize_input_path(raw)
            root = Path(norm).expanduser()
            st.caption(f"Folder add: raw='{raw}'  →  normalized='{norm}'")
            if root.exists() and root.is_dir():
                if not any(x.get("path") == raw for x in m.get("folders", [])):
                    m["folders"].append({"path": raw, "exts": exts, "recursive": bool(recursive)})
                    added += 1
                else:
                    skipped += 1
            else:
                st.warning(f"Folder not found (normalized check): {norm}")
        save_manifest(m)
        st.success(f"Folders added: {added}. Skipped (already present): {skipped}.")

st.markdown("---")
st.subheader("Current Manifest")

if m.get("files") or m.get("folders"):
    st.write("**Files**")
    if m.get("files"):
        for f in m["files"]:
            st.code(f.get("path", ""))
    else:
        st.caption("No files.")

    st.write("**Folders**")
    if m.get("folders"):
        for fd in m["folders"]:
            st.code(f"{fd.get('path','')}  |  exts={','.join(fd.get('exts', [])) or '(all)'}  |  recursive={fd.get('recursive', True)}")
    else:
        st.caption("No folders.")
else:
    st.info("Manifest is empty. Add files/folders above.")

# Removal controls
with st.expander("Remove items"):
    rm_file = st.text_input("Remove file (exact path as listed)")
    if st.button("Remove File"):
        before = len(m.get("files", []))
        m["files"] = [x for x in m.get("files", []) if x.get("path") != rm_file.strip()]
        save_manifest(m)
        st.success(f"Removed: {before - len(m.get('files', []))}")

    rm_folder = st.text_input("Remove folder (exact path as listed)")
    if st.button("Remove Folder"):
        before = len(m.get("folders", []))
        m["folders"] = [x for x in m.get("folders", []) if x.get("path") != rm_folder.strip()]
        save_manifest(m)
        st.success(f"Removed: {before - len(m.get('folders', []))}")

st.markdown("---")
st.subheader("Compile")

if st.button("Compile Now"):
    paths = build_hybrid_set(m)
    if not paths:
        st.warning("Nothing to compile. Add files or folders first.")
    else:
        out_path.mkdir(parents=True, exist_ok=True)

        # CODEFILE: union set
        compile_codefile_from_paths(paths, codefile_path, max_bytes=int(max_bytes))

        # Structure: tracked folders (or parents of files if no folders)
        folder_roots = []
        for fd in m.get("folders", []):
            norm = normalize_input_path(fd.get("path", ""))
            p = Path(norm).expanduser()
            if p.exists():
                folder_roots.append(p)

        if not folder_roots and paths:
            folder_roots = sorted(set([p.parent for p in paths]))

        struct_text = []
        for root in folder_roots:
            tmp_struct = out_path / f"_STRUCT_{root.name}.md"
            try:
                compile_structure_md(
                    root,
                    tmp_struct,
                    exclude_dirs=[".git", "__pycache__", "node_modules", ".venv", "build", "dist", ".idea", ".gradle"],
                )
                struct_text.append(tmp_struct.read_text(encoding="utf-8"))
            finally:
                if tmp_struct.exists():
                    tmp_struct.unlink()
        if struct_text:
            struct_path.write_text("\n\n".join(struct_text), encoding="utf-8")

        m["last_compiled"] = time.strftime("%Y-%m-%d %H:%M:%S")
        save_manifest(m)
        st.success(f"Compiled. Outputs: {codefile_path}  |  {struct_path}")

        if show_previews:
            left, right = st.columns(2)
            with left:
                st.markdown("**CODEFILE preview**")
                try:
                    content = codefile_path.read_text(encoding="utf-8", errors="ignore")
                    st.code(content[:20000] if len(content) > 20000 else content, language="text")
                except Exception as ex:
                    st.error(f"Preview error: {ex}")
            with right:
                st.markdown("**StructureLatest.md preview**")
                try:
                    st.code(struct_path.read_text(encoding="utf-8", errors="ignore"), language="markdown")
                except Exception as ex:
                    st.error(f"Preview error: {ex}")
else:
    if m.get("last_compiled"):
        st.caption(f"Last compiled: {m.get('last_compiled')}")
