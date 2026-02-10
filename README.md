
# GitAIReader – AI-Powered GitHub Code Assistant using Endee

##  Project Overview
GitAIReader is an **AI-powered GitHub repository analysis tool** that enables users to ask **natural language questions about any public GitHub codebase**.  
The system uses **vector embeddings, hybrid search, and Retrieval Augmented Generation (RAG)** to understand source code and provide accurate, contextual answers.

At its core, the project uses **Endee as the vector database**, with a **robust local fallback mode** to ensure the application works even if the Endee server is unavailable.

---

##  Objectives
- Build a real-world **AI/ML project using vector search**
- Use **Endee** as the primary vector database
- Implement **Semantic Search + Hybrid Search + RAG**
- Analyze GitHub repositories programmatically
- Provide a clean, user-friendly interface using Streamlit
- Host the complete project on GitHub with proper documentation

---

##  Use Case Implemented
###  AI-Powered Code Understanding (Semantic Search & RAG)

**What this application does:**
- Accepts a GitHub repository URL
- Clones the repository locally
- Splits code into meaningful chunks
- Generates vector embeddings
- Stores embeddings in **Endee**
- Retrieves relevant code using:
  - Vector similarity search
  - BM25 keyword search (hybrid search)
  - Cross-encoder reranking
- Uses a local LLM (via Ollama) to generate accurate answers

**Example questions:**
- "What does this repository do?"
- "Explain this file in simple terms"
- "Where is authentication handled?"
- "Why is this code used?"

---

##  Endee Vector Database Integration
Endee is used as the **core vector storage layer** for this project.

- Stores embeddings for all code chunks
- Enables fast vector similarity search
- Automatically switches to **local in-memory fallback mode** if:
  - Endee server is not running
  - Connection to `localhost:8080` fails
- Ensures reliability during local development

Official Endee repository:  
 https://github.com/EndeeLabs/endee

---

##  Tech Stack
- **Language:** Python  
- **UI:** Streamlit  
- **Vector Database:** Endee (with local fallback)  
- **Embeddings:** Sentence Transformers (all-MiniLM-L6-v2)  
- **Search:** Vector Search + BM25 (Hybrid Search)  
- **Reranking:** Cross-Encoder (ms-marco-MiniLM)  
- **LLM Runtime:** Ollama (qwen2.5:3b recommended)  
- **Version Control:** Git & GitHub  

All dependencies are listed in `requirements.txt`.

---

##  System Architecture / Workflow
1. User enters a GitHub repository URL
2. Repository is cloned locally
3. Code files are scanned and filtered by extension
4. Files are split into overlapping chunks
5. Embeddings are generated
6. Embeddings are stored in Endee
7. User query is embedded
8. Hybrid search is performed:
   - Vector search (Endee)
   - Keyword search (BM25)
9. Results are reranked using a cross-encoder
10. Top results are passed to the LLM
11. Final response is streamed to the UI

---

##  Project Structure
```
GitAicode_Reader/
├── app_files/
│   ├── app.py              # Streamlit frontend
│   └── README.md           # This file
├── backend.py              # RAG, hybrid search, Endee logic
├── endee_client.py         # Endee DB client with fallback
├── requirements.txt        # Python dependencies
├── start.bat               # Automated setup script
└── RUN_INSTRUCTIONS.md     # Detailed setup guide

# Endee: High-Performance Open Source Vector Database

**Endee (nD)** is a specialized, high-performance vector database built for speed and efficiency. This guide covers supported platforms, dependency requirements, and detailed build instructions using both our automated installer and manual CMake configuration.

there are 3 ways to build and run endee:
1. quick installation and run using install.sh and run.sh scripts
2. manual build using cmake
3. using docker

also you can run endee using docker from docker hub without building it locally. refer to section 4 for more details.

---
##  Prerequisites

Before running the project, ensure you have:

1. **Python 3.10+** installed ([python.org](https://www.python.org/downloads/))
   -  **CRITICAL**: Check "Add Python to PATH" during installation
2. **VS Code** installed ([code.visualstudio.com](https://code.visualstudio.com/))
3. **Git** installed ([git-scm.com](https://git-scm.com/downloads))
4. **Ollama** installed for AI capabilities ([ollama.com](https://ollama.com/))

### One-Time Ollama Setup
1. Open a terminal (Windows: Search "cmd" or "PowerShell")
2. Download the AI model:
   ```bash
   ollama run qwen2.5:3b
   ```
3. Wait for download, then type `/bye` to exit
4. Keep Ollama running in the background

---

##  Running the Project in VS Code

###  Step 1: Open Project in VS Code
1. Open VS Code
2. Click **File** → **Open Folder**
3. Navigate to and select the `GitAicode_Reader` folder

###  Step 2: Open Terminal in VS Code
Choose any method:
- **Keyboard Shortcut**: Press `Ctrl + `` (backtick)
- **Menu**: Click **Terminal** → **New Terminal**
- **Command Palette**: Press `Ctrl + Shift + P`, type "Create New Terminal", press Enter

###  Step 3: Run the Application

####  Option A: Automatic Setup (Recommended)
In the VS Code terminal, run:
```bash
.\start.bat
```

This script will automatically:
- ✓ Create a virtual environment
- ✓ Install all dependencies
- ✓ Check for Ollama
- ✓ Launch the Streamlit app

**Wait for the message:** `Local URL: http://localhost:8501`

####  Option B: Manual Setup
If the automated script fails, run these commands one by one in the VS Code terminal:

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
.\venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
streamlit run app_files/app.py
```

*Note: You should see `(venv)` at the start of your terminal prompt after activation*

###  Step 4: Open in Browser
Once you see `Local URL: http://localhost:8501`, open that URL in your web browser.

---

##  How to Use the Application

1. **Enter GitHub URL**: Paste a repository URL (e.g., `https://github.com/pallets/flask`)
2. **Click "Analyze Repo"**: Wait for cloning and processing to complete
3. **Browse Files**: View repository files from the sidebar
4. **Ask Questions**: Type questions in natural language like:
   - "What does this repository do?"
   - "Explain this file in simple terms"
   - "Where is authentication handled?"
5. **View Results**: See AI-generated answers with referenced source files and metrics

---

##  Example Output

**User Question:**
> "Explain what this file does"

**AI Response:**
- Human-readable explanation
- Technical function of the file
- Reason why the code exists
- Referenced source files

---

## 🖼️ Application Screenshots

### 1. Main Interface
<img width="1911" height="883" alt="main_interface" src="https://github.com/user-attachments/assets/6c190d35-397b-46ee-b730-996bb7b5d59b" />

*Clean, user-friendly interface with GitHub URL input, Ollama model selection, and speed tips for optimal performance*

### 2. Repository Analysis & AI-Powered Code Explanation
<img width="1814" height="838" alt="File_analysis" src="https://github.com/user-attachments/assets/05b67123-7984-4b93-a79e-b7a58bd972ea" />
)
*AI-powered analysis showing detailed explanations of repository purpose, functionality, and workflow. Includes repository map, file browser, and download functionality*

### 3. File-Level AI Analysis
<img width="1873" height="882" alt="repo_analysis" src="https://github.com/user-attachments/assets/80f0bb29-b059-496e-8792-51d07e2975f7" />

*Detailed file analysis with human-readable information and technical function breakdown for individual files*


---

##  Troubleshooting in VS Code

###  "Connection refused" for localhost:8080
**This is normal and safe to ignore!**
- The app tries to connect to the Endee vector database server
- It automatically falls back to local in-memory storage
- Your application will work perfectly fine

###  "Ollama not found"
**Solution:**
1. Ensure Ollama is installed from [ollama.com](https://ollama.com/)
2. Verify it's running: `ollama list`
3. Download the model: `ollama run qwen2.5:3b`
4. Keep Ollama running in the background

###  "ModuleNotFoundError" or "streamlit is not recognized"
**Solution:**
1. Activate the virtual environment: `.\venv\Scripts\activate`
2. Look for `(venv)` at the start of your terminal prompt
3. Reinstall dependencies: `pip install -r requirements.txt`
4. Alternative: `python -m streamlit run app_files/app.py`

###  "Python is not recognized"
**Solution:**
1. Install Python from [python.org](https://www.python.org/downloads/)
2. Check **"Add Python to PATH"** during installation
3. Restart VS Code
4. Verify: `python --version`

###  Port 8501 already in use
**Solution:**
- Streamlit will use the next available port (8502, 8503, etc.)
- Check terminal output for the actual URL
- Or stop existing process: Press `Ctrl + C`

###  Slow AI responses
**Solution:**
- Use smaller models like `qwen2.5:3b` (recommended)
- Avoid large models like `llama2:70b`

###  Virtual environment activation issues
**Solution:**
- If `.\venv\Scripts\activate` doesn't work, try:
  - PowerShell: `.\venv\Scripts\Activate.ps1`
  - Command Prompt: `.\venv\Scripts\activate.bat`
- Or use the automated script: `.\start.bat`

---

##  Stopping the Application

To stop Streamlit in VS Code:
- Press `Ctrl + C` in the terminal
- Or close the terminal window
- Or click the trash icon in the terminal panel

---

##  Future Enhancements
- Web deployment
- Multi-repo comparison
- Agentic AI workflows
- Recommendation systems
- Docker support

---

##  License
This project is licensed under the MIT License.

---

##  Acknowledgements
- **Endee Labs** – Vector Database
- **Ollama** – Local LLM runtime
- **LangChain** community
- Open-source AI ecosystem

---

##  Author
**Mahesh**  
GitHub: https://github.com/Mahesh2004-prog
=======
=======


## Contribution

We welcome contributions from the community to help make vector search faster and more accessible for everyone. To contribute:

* **Submit Pull Requests**: Have a fix or a new feature? Fork the repo, create a branch, and send a PR.
* **Report Issues**: Found a bug or a performance bottleneck? Open an issue on GitHub with steps to reproduce it.
* **Suggest Improvements**: We are always looking to optimize performance; feel free to suggest new CPU target optimizations or architectural enhancements.
* **Feature Requests**: If there is a specific functionality you need, start a discussion in the issues section.

---

## License

Endee is open source software licensed under the
**Apache License 2.0**.

You are free to use, modify, and distribute this software for
personal, commercial, and production use.

See the LICENSE file for full license terms.

---

## Trademark and Branding

“Endee” and the Endee logo are trademarks of Endee Labs.

The Apache License 2.0 does **not** grant permission to use the Endee name,
logos, or branding in a way that suggests endorsement or affiliation.

If you offer a hosted or managed service based on this software, you must:
- Use your own branding
- Avoid implying it is an official Endee service

For trademark or branding permissions, contact: enterprise@endee.io

---

## Third-Party Software

This project includes or depends on third-party software components that are
licensed under their respective open source licenses.

Use of those components is governed by the terms and conditions of their
individual licenses, not by the Apache License 2.0 for this project.

