# 🧠 CodeManager — Automated Code Knowledge Base for AI and Developers  
### Version 2.0 — Hybrid Tracking + Windows/WSL Path Support

CodeManager V2 is a **Streamlit-based code knowledge management tool** that lets developers instantly convert an entire project (or selected files and folders) into two clean, machine-readable artifacts:

1. **CODEFILE.txt** — concatenated source code with headers  
2. **StructureLatest.md** — a Markdown tree of your project structure  

These two outputs together form a **live knowledge pack** for LLMs, RAG pipelines, documentation systems, and code reasoning workflows.

## 🔍 What’s New in V2

V2 is a major upgrade from V1. Instead of a single-folder watcher, V2 introduces a powerful **Hybrid Tracking System**.

### ✔ Hybrid Mode (Files + Folders Together)

- Add absolute paths to individual files  
- Add absolute paths to folder roots  
- Apply extension filters  
- Recursive or non-recursive folder scanning  
- Combine everything in a single manifest  
- Generate artifacts on demand  

---

## 🚀 Major Improvements in V2

### 1. Windows → WSL Path Normalization  
Paste Windows paths like `C:\Users\You\file.py`, and CodeManager automatically converts them into WSL paths internally.

### 2. No Watchdog Needed  
Click **Compile** whenever needed. No threads. No system hooks.

### 3. Migration-Friendly Manifest  
Auto-migrates old V1 manifests to V2 format.

### 4. Reliable Artifact Generation  
- Extension-filtered scanning  
- Multi-root structure  
- Large-file safety  
- Deduplication  

---

## 🧩 Components

- **app.py** – Streamlit UI  
- **file_ops.py** – Builds CODEFILE and StructureLatest  
- **code_watcher.py** – Legacy from V1  
- **manifest.json** – Hybrid tracking database  

---

## 📁 Outputs

### CODEFILE.txt  
All code merged into one file with labeled sections.

### StructureLatest.md  
Clean project tree view.

---

## 💡 AI Use Case

Use as a “knowledge pack” for:

- Local LLMs (Llama, Mistral, Gemma)  
- ChatGPT-based refactoring  
- RAG code understanding pipelines  
- Documentation engines  

---

## 🌐 Hosting via Apache2

Install:

```bash
sudo apt update
sudo apt install apache2 -y
```

Serve output folder:

```bash
sudo ln -s /path/to/output /var/www/html/codebase
```

Access:
```
http://localhost/codebase/CODEFILE.txt
http://localhost/codebase/StructureLatest.md
```

---

## ⚙️ Run Locally

```bash
git clone https://github.com/chinmay231/CodeManager.git
cd CodeManager
git checkout v2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

---

## 🧑‍💻 Author  
**Chinmay Kapoor**  
Data & AI Engineer | AI Systems Researcher
