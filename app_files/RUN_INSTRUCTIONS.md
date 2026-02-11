# How to Run the GitAIReader Project

Follow these exact steps to run the application in VS Code on Windows.

## 1. Prerequisites (Install First)

Before you begin, ensure you have the following installed:

1.  **Python 3.10+**: Download from [python.org](https://www.python.org/downloads/).
    *   **CRITICAL**: During installation, check the box **"Add Python to PATH"**.
2.  **VS Code**: Download from [code.visualstudio.com](https://code.visualstudio.com/).
3.  **Git**: Download from [git-scm.com](https://git-scm.com/downloads).
4.  **Ollama (for AI Capabilities)**: Download from [ollama.com](https://ollama.com/).
    *   This is required for the AI to answer questions about the code.

---

## 2. Setup Ollama (One-Time Setup)

1.  Open a new terminal (Search "cmd" in Windows Start menu).
2.  Run the following command to download the AI model:
    ```bash
    ollama run qwen2.5:3b
    ```
    *   Wait for the download to complete. Once you see a prompt `>>>`, type `/bye` to exit.
3.  Keep the Ollama application running in the background (check your system tray).

---

## 3. Option A: Automatic Setup (Recommended)

1.  Open the project folder (`GitAicode_Reader`) in VS Code.
2.  **Open the Terminal**:
    *   **Option A (Shortcut)**: Press `Ctrl + Shift + ` (backtick) or just `Ctrl + `
    *   **Option B (Menu)**: Click **Terminal** in the top menu bar -> **New Terminal**.
    *   **Option C (Command Palette)**: Press `Ctrl + Shift + P`, type "Create New Terminal", and press Enter.
3.  Type the following command and press Enter:
    ```bash
    .\start.bat
    ```
4.  This script will automatically:
    *   Create a virtual environment.
    *   Install all necessary dependencies.
    *   Check for Ollama.
    *   Launch the application.

If the browser opens to `http://localhost:8501`, you are done! 🎉

---

## 4. Option B: Manual Setup (Step-by-Step)

If the automatic script fails, follow these manual steps in the VS Code terminal.

### Step 1: Create a Virtual Environment
```bash
python -m venv venv
```

### Step 2: Activate the Environment
```bash
.\venv\Scripts\activate
```
*   You should see `(venv)` appear at the start of your command prompt.

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
streamlit run app_files/app.py
```

---

## 5. Using the Application

1.  **Enter a GitHub URL**: Paste a URL like `https://github.com/pallets/flask` in the sidebar.
2.  **Click "Analyze Repo"**: Wait for the process to finish.
3.  **Ask Questions**: Type your question in the chat box below.

### Troubleshooting

*   **"Connection refused" for localhost:8080**:
    *   This is normal! The app is trying to connect to the Endee vector database server. Since you are running in "Local Fallback Mode", it will simply use your computer's memory instead. You can safely ignore this error.
*   **"Ollama not found"**:
    *   Ensure you installed Ollama and it is running.
    *   Run `ollama list` in the terminal to verify.
*   **"ModuleNotFoundError"**:
    *   Make sure you activated the virtual environment (`.\venv\Scripts\activate`) before running the app.
