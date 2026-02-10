import streamlit as st
import os
import shutil
from pathlib import Path
# Import from the local file
from backend import CodeRAG

st.set_page_config(page_title="GitHub Code Assistant", page_icon="🤖", layout="wide")

st.title("🤖 GitHub Code Assistant")
st.markdown("Enter a GitHub URL to analyze the code and ask questions about it.")

# --- State Management ---
if "rag" not in st.session_state:
    st.session_state.rag = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "repo_ingested" not in st.session_state:
    st.session_state.repo_ingested = False
if "selected_file" not in st.session_state:
    st.session_state.selected_file = None
if "file_analysis" not in st.session_state:
    st.session_state.file_analysis = {}
if "analyzing_file" not in st.session_state:
    st.session_state.analyzing_file = False

def select_file(path):
    st.session_state.selected_file = path
    st.session_state.analyzing_file = True
    st.toast(f"📂 Analyzing: {os.path.basename(path)}")

def close_file():
    st.session_state.selected_file = None
    st.session_state.analyzing_file = False

# --- File Viewer (Document Format) ---
if st.session_state.selected_file and st.session_state.rag:
    with st.container():
        # Document Header
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            st.subheader(f"📄 {st.session_state.selected_file}")
        with col2:
            st.button("Close", on_click=close_file, type="primary", key="close_doc")
        
        # Robust path resolution with pathlib
        repo_root = Path(st.session_state.rag.repo_path)
        file_path = repo_root / st.session_state.selected_file
        
        if file_path.exists() and file_path.is_file():
            try:
                content = file_path.read_text(encoding='utf-8', errors='replace')
                
                # AI Analysis Section
                with st.expander("🤖 AI File Analysis", expanded=True):
                    file_key = str(file_path)
                    
                    # Generate analysis if not cached or if analyzing flag is set
                    if st.session_state.analyzing_file or file_key not in st.session_state.file_analysis:
                        with st.spinner("🔍 Analyzing file with AI..."):
                            # Create a simple, human-friendly prompt
                            analysis_prompt = f"""You are explaining code to someone who wants to understand what this file does in simple, everyday language. Avoid technical jargon and be conversational.

**File: {st.session_state.selected_file}**

Please analyze this file and provide the following 3 sections exactly:

## 📖 Human Readable Information
Provide a simple, non-technical explanation of what this file is and does. Imagine explaining it to a non-programmer. Focus on the "what" and "who" in plain English.

## ⚙️ Function of this File
Explain the specific technical role or function this file plays in the project. detailedly describe its responsibilities, main methods, or key logic.

## 🎯 Why This Code is Used
Explain the reasoning behind including this code in the project. What specific problem does it solve? Why is it necessary for the project to function correctly?

**Here's the code:**
{content[:3000]}{'...[more code below]' if len(content) > 3000 else ''}
```

**File size:** {len(content)} characters ({len(content.split())} words approximately)

Remember: Keep the headers exactly as requested. Be helpful and clear!"""
                            
                            # Get analysis from RAG system
                            try:
                                # ask_question returns a generator, so we need to collect all chunks
                                analysis_chunks = []
                                for chunk in st.session_state.rag.ask_question(analysis_prompt):
                                    analysis_chunks.append(chunk)
                                
                                analysis_text = ''.join(analysis_chunks)
                                
                                # Clean up any error messages
                                if not analysis_text or "Error:" in analysis_text:
                                    analysis_text = "Unable to generate analysis. Please try again."
                                
                                st.session_state.file_analysis[file_key] = analysis_text
                                st.session_state.analyzing_file = False
                            except Exception as e:
                                st.error(f"Analysis failed: {e}")
                                st.session_state.file_analysis[file_key] = f"Analysis unavailable: {str(e)}"
                                st.session_state.analyzing_file = False
                    
                    # Display cached analysis
                    if file_key in st.session_state.file_analysis:
                        st.markdown(st.session_state.file_analysis[file_key])
                    
                    # Refresh button
                    if st.button("🔄 Refresh Analysis", key="refresh_analysis"):
                        st.session_state.analyzing_file = True
                        st.rerun()
                
                # File Content Section
                with st.container(border=True):
                    st.markdown("### 📝 Full File Content")
                    
                    # File statistics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Lines", content.count('\n') + 1)
                    with col2:
                        st.metric("Characters", len(content))
                    with col3:
                        file_size_kb = len(content.encode('utf-8')) / 1024
                        st.metric("Size", f"{file_size_kb:.2f} KB")
                    
                    st.divider()
                    
                    # Highlight based on extension
                    suffix = file_path.suffix.lower()
                    if suffix == '.md':
                        st.markdown(content)
                    else:
                        st.code(content, language=suffix[1:] if suffix else None, line_numbers=True)
            except Exception as e:
                st.error(f"Could not read file at {file_path}: {e}")
        else:
            st.error(f"File not found: {file_path}")
    st.divider()

# --- Sidebar ---
with st.sidebar:
    st.header("Setup")
    if st.session_state.selected_file:
        st.info(f"📍 Active: `{os.path.basename(st.session_state.selected_file)}`")
    model_name = st.text_input("Ollama Model Name", value="qwen2.5:3b")
    
    st.divider()
    
    if st.session_state.repo_ingested and st.session_state.rag:
        st.divider()
        st.header("📥 Download")
        if st.button("Prepare Download (ZIP)", use_container_width=True):
            with st.spinner("Zipping repository..."):
                try:
                    zip_path = st.session_state.rag.prepare_zip()
                    with open(zip_path, "rb") as f:
                        st.download_button(
                            label="🔥 Download ZIP",
                            data=f,
                            file_name=f"{st.session_state.rag.repo_name}.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                    st.success("Download ready!")
                except Exception as e:
                    st.error(f"Zipping failed: {e}")
        st.divider()

        with st.expander("📁 Repository Map", expanded=True):
            structure = st.session_state.rag.get_repo_structure()
            for item in structure:
                indent = "  " * item["level"]
                if item["type"] == "folder":
                    st.markdown(f"{indent}📁 **{item['name']}**")
                else:
                    st.button(f"{indent}📄 {item['name']}", 
                              key=f"file_{item['path']}", 
                              use_container_width=True, 
                              on_click=select_file, 
                              args=(item['path'],))
    
    with st.expander("⚡ Speed Tips", expanded=False):
        st.write("1. **Use Small Models**: `qwen2.5:3b` is optimized.")
        st.write("2. **Persistence**: Analyzed repos and chats are cached.")


# --- Main Interaction ---
col1, col2 = st.columns([3, 1])

with col1:
    repo_url = st.text_input("GitHub Repository URL", placeholder="https://github.com/username/repo")

with col2:
    st.write("") # Spacer
    st.write("")
    if st.button("Analyze Repo", type="primary", use_container_width=True):
        if repo_url:
            with st.spinner("Processing..."):
                try:
                    rag = CodeRAG(repo_url, model_name=model_name)
                    st.session_state.rag = rag
                    rag.clone_repo()
                    chunks = rag.load_and_process_files()
                    rag.create_vector_store(chunks)
                    
                    # Phase 3: Load history
                    st.session_state.chat_history = rag.load_history()
                    st.session_state.repo_ingested = True
                    st.success(f"Ready!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

st.divider()

# Display history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
if prompt := st.chat_input("Ask about the codebase..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with st.chat_message("assistant"):
        if not st.session_state.repo_ingested:
            st.warning("Please analyze a repository first.")
        else:
            if st.session_state.rag:
                st.session_state.rag.model_name = model_name
                
                # Streaming with metrics
                full_response = st.write_stream(st.session_state.rag.ask_question(prompt))
                
                cache_entry = st.session_state.rag.cache.get(prompt, {})
                metrics = cache_entry.get("metrics", {})
                sources = cache_entry.get("source_documents", [])
                
                # Show metrics
                if metrics:
                    st.caption(f"⏱️ Search: {metrics.get('search_time')}s | AI: {metrics.get('llm_time')}s | Total: {metrics.get('total_time')}s")
                
                # Append to history and SAVE
                st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                st.session_state.rag.save_history(st.session_state.chat_history)
                
                if sources:
                    with st.expander("📚 Referenced Project Files"):
                        for doc in sources:
                            src_name = os.path.basename(doc.metadata.get('source', 'file'))
                            st.markdown(f"📍 `{src_name}`")
                            st.code(doc.page_content, language="python")
