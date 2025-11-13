
# 🧠 CodeManager V2 — AI-Ready Code Knowledge Engine  
**Hybrid Project Tracker | Unified CODEFILE Generator | Project Structure Mapping**

<img width="2440" height="1527" alt="image" src="https://github.com/chinmay231/CodeManager/blob/main/image.png" />
---

## 🚀 Overview

CodeManager V2 transforms any software project into a **machine-readable knowledge base**, optimized for AI models, RAG pipelines, debugging, documentation, and multi-file reasoning.

With a single compile click, the system produces:

1. **`CODEFILE.txt`** — a unified snapshot of all tracked source files.  
2. **`StructureLatest.md`** — a clean Markdown tree representing your folder structure.

---

## ✨ What’s New in V2

### ✔ Hybrid Tracking (Files + Folders)
Track individual files and entire folders with recursive scanning and extension filters.

### ✔ Automatic Path Normalization  
Works with Windows, WSL, and Linux paths.

### ✔ Improved Manifest Engine  
Stored in `.codemanager/manifest.json` with migration-safe handling.

### ✔ Updated Streamlit UI  
Dual-pane adders, previews, and better error handling.

---

## 🧩 How It Works

### 1. Add Paths  
You can add files and folders with custom extension filters.

### 2. Compile  
Generates `CODEFILE.txt` and `StructureLatest.md`.

---

## 🤖 AI / RAG Integration

Example with LangChain:

```python
from langchain.document_loaders import WebBaseLoader
loader = WebBaseLoader("http://localhost/codebase/CODEFILE.txt")
docs = loader.load()
```

---

## 🌐 Hosting via Apache2

```bash
sudo apt update
sudo apt install apache2 -y
sudo ln -s /path/to/outputs /var/www/html/codebase
```

Access:  
`http://localhost/codebase/CODEFILE.txt`

---

## ⚙️ Installation  // I would recommend downloading the source package for the Latest Release (That way no version glitch exists)

```bash
git clone https://github.com/chinmay231/CodeManager.git
cd CodeManager_V2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

---

## 👤 Author  
**Chinmay Kapoor**  
AI Systems Researcher | Data Engineer

