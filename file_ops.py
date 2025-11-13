from __future__ import annotations
import os
from pathlib import Path
from typing import List
HEADER_TEMPLATE = "<<<<<<<<<<<<<<<<<<    {path}     >>>>>>>>>>>>>>>>>>>>"

def _is_textish(p: Path) -> bool:
    try:
        with open(p, "rb") as f:
            chunk = f.read(2048)
        if b"\x00" in chunk:
            return False
    except Exception:
        return False
    return True

def _should_skip_file(p: Path, max_bytes: int) -> bool:
    try:
        st = p.stat()
        if st.st_size > max_bytes:
            return True
        if not _is_textish(p):
            return True
    except Exception:
        return True
    return False

def _iter_files(root: Path, include_exts: List[str], exclude_dirs: List[str]) -> List[Path]:
    include_exts = [e.lower().strip() for e in include_exts]
    out: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for name in filenames:
            p = Path(dirpath) / name
            if include_exts and p.suffix.lower() not in include_exts:
                continue
            out.append(p)
    return out

def compile_codefile(root: Path, out_path: Path, include_exts: List[str], exclude_dirs: List[str],
                     exclude_file_regexes, max_bytes: int, order_mode: str = "path") -> None:
    root = Path(root)
    out_path = Path(out_path)
    files = _iter_files(root, include_exts, exclude_dirs)

    def _excluded(p: Path) -> bool:
        s = str(p)
        for rx in (exclude_file_regexes or []):
            if rx.search(s):
                return True
        return False

    if order_mode == "mtime":
        files.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0)
    else:
        files.sort(key=lambda p: str(p).lower())

    lines: List[str] = []
    for p in files:
        if _excluded(p) or _should_skip_file(p, max_bytes):
            continue
        header = HEADER_TEMPLATE.format(path=str(p))
        lines.append("")
        lines.append(header)
        lines.append("")
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                lines.append(f.read())
        except Exception as ex:
            lines.append(f"<<ERROR READING {p}: {ex}>>")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).lstrip())

def compile_codefile_from_paths(paths: List[Path], out_path: Path, max_bytes: int):
    files = []
    for p in paths:
        p = Path(p)
        if p.exists() and p.is_file():
            files.append(p)
    files.sort(key=lambda p: str(p).lower())
    lines: List[str] = []
    for p in files:
        if _should_skip_file(p, max_bytes):
            continue
        header = HEADER_TEMPLATE.format(path=str(p))
        lines += ["", header, ""]
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                lines.append(f.read())
        except Exception as ex:
            lines.append(f"<<ERROR READING {p}: {ex}>>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines).lstrip(), encoding="utf-8")


def compile_structure_md(root: Path, out_path: Path, exclude_dirs: List[str]) -> None:
    root = Path(root)
    out_path = Path(out_path)

    def tree(prefix: str, dir_path: Path, buf: List[str]):
        try:
            entries = sorted([e for e in dir_path.iterdir()], key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            return
        for i, entry in enumerate(entries):
            last = i == len(entries) - 1
            connector = "└── " if last else "├── "
            if entry.is_dir():
                if entry.name in exclude_dirs:
                    continue
                buf.append(f"{prefix}{connector}{entry.name}/")
                tree(prefix + ("    " if last else "│   "), entry, buf)
            else:
                buf.append(f"{prefix}{connector}{entry.name}")

    lines: List[str] = ["# Folder Structure", "", f"📁 {root.name}/", "│"]
    tree("", root, lines)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
