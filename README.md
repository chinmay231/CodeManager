
# 🧠 CodeManager — Automated Code Knowledge Base for AI and Developers V1.0

CodeManager is a **Streamlit-based project management tool** that automatically observes any source code directory, tracks all file changes, and compiles two living artifacts that together act as a **machine-readable knowledge base** for your code.

## 🔍 What It Does

Whenever you edit or save any file in your project, CodeManager instantly rebuilds:

1. **`CODEFILE.txt`**
   A single concatenated file containing all source files (Python, Kotlin, Java, XML, Markdown, etc.) with clear headers.
2. **`StructureLatest.md`**
   A clean Markdown tree of your project structure.

These two files represent your **project’s evolving knowledge state**. They can be used for local or cloud-based LLMs and RAG systems, continuous documentation, or codebase review.

## 🧩 System Components

### `app.py`
Streamlit UI for control and visualization of the directory watcher.

### `code_watcher.py`
Uses watchdog to monitor file changes and trigger rebuilds.

### `file_ops.py`
Compiles code into CODEFILE.txt and folder tree into StructureLatest.md.

### `.streamlit/config.toml`
Maintains UI and server settings.


## What it Uses??

The Code Manager Uses Streamlit, Regex and Watcher to ensure that you can interact with your edited code saved into one file as Knowledge and Structure of the folder which may also need tracking. This tracker is similar to github but made more customisable for the user. 


## 💡 Use Case: AI Knowledge Base

These generated files can serve as a **Knowledge Base** for:
- Local LLMs (Llama, Mistral, Gemma, etc.) via RAG
- ChatGPT or API-based tools for refactoring or reasoning
- Automated documentation systems
- Team knowledge sharing

Example flow:
1. Developer codes → CodeManager updates CODEFILE.txt.
2. Apache2 server hosts this file.
3. LLM fetches it from HTTP endpoint for retrieval-augmented reasoning.

## 🌐 Hosting via Apache2 Server

### Install Apache2
```bash
sudo apt update
sudo apt install apache2 -y
```

### Link the output folder
```bash
sudo ln -s /path/to/project /var/www/html/codebase
```

Access the files at:
```
http://localhost/codebase/CODEFILE.txt
http://localhost/codebase/StructureLatest.md
```

### Check and start Apache
```bash
sudo systemctl status apache2
sudo systemctl start apache2
```

Your AI or RAG pipeline can now access:
`http://localhost/codebase/CODEFILE.txt`

## 🧠 Integration Example (LangChain)

```python
from langchain.document_loaders import WebBaseLoader
loader = WebBaseLoader("http://localhost/codebase/CODEFILE.txt")
docs = loader.load()
```

Now your AI has access to a live, auto-updated version of your source codebase.

## ⚙️ Run Locally

```bash
git clone https://github.com/chinmay231/CodeManager.git
cd CodeManager
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501 to use the app.

## 🧠 Concept Summary

CodeManager bridges the gap between **software engineering** and **AI comprehension** by converting your live project into a structured, continuously refreshed knowledge base.

## 🧑‍💻 Author
**Chinmay Kapoor**  
Data & AI Engineer | AI Systems Researcher
