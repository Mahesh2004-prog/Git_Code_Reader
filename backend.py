import os
import shutil
from pathlib import Path
import git
from typing import List, Dict, Any, Generator
import time
import json
from langchain_community.document_loaders import DirectoryLoader, TextLoader
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from endee_client import EndeeDB
from langchain_community.llms import Ollama
# Removed brittle chain imports to increase compatibility
# from langchain.chains import RetrievalQA
# from langchain.prompts import PromptTemplate
from sentence_transformers import CrossEncoder  # 2️⃣ Add a Reranker ⚡
from rank_bm25 import BM25Okapi # 🚀 Phase 2: Hybrid Search
import re


class CodeRAG:
    """
    RAG System for Code Analysis
    """
    def __init__(self, repo_url: str, model_name: str = "mistral"):
        self.repo_url = repo_url
        self.repo_name = repo_url.split("/")[-1].replace(".git", "")
        # Use absolute paths for robust storage in the new workspace
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.repo_path = os.path.join(self.base_dir, "repo_data", self.repo_name)
        self.vector_store_path = os.path.join(self.base_dir, "vector_store", self.repo_name)
        
        self.embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        self.model_name = model_name
        self.cache = {}  # Added for speed optimization ⚡
        # Initialize reranker
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2') 
        # Phase 2 State
        self.bm25 = None
        self.all_chunks = []
        
        # Phase 3 State
        self.history_path = os.path.join(self.repo_path, ".chat_history.json")
        
    def _remove_readonly(self, func, path, excinfo):
        """Helper to remove read-only files on Windows."""
        import stat
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            # If still fails, we'll handle it in the retry loop in clone_repo
            pass

    def clone_repo(self) -> str:
        """Clones the repository if it doesn't exist."""
        if os.path.exists(self.repo_path) and os.path.exists(self.vector_store_path):
            return f"Repository and vector store already exist for {self.repo_name}."
            
        if os.path.exists(self.repo_path):
            # 🚀 Robust Cleanup for Windows (Fixes WinError 5)
            import gc
            gc.collect() # Force release of any lingering file handles
            
            max_retries = 3
            for i in range(max_retries):
                try:
                    shutil.rmtree(self.repo_path, onerror=self._remove_readonly)
                    break
                except Exception as e:
                    if i == max_retries - 1:
                        raise e
                    time.sleep(1) # Wait a second before retrying
        
        os.makedirs(self.repo_path, exist_ok=True)
        
        print(f"Cloning {self.repo_url} into {self.repo_path}...")
        git.Repo.clone_from(self.repo_url, self.repo_path)
        return f"Cloned {self.repo_name} successfully."

    def load_and_process_files(self) -> List[Any]:
        """Loads code files and splits them into chunks."""
        # Supported extensions
        extensions = ['py', 'js', 'java', 'ts', 'cpp', 'c', 'cs', 'go', 'rs', 'swift', 'kt', 'rb', 'php', 'html', 'css', 'md', 'json']
        documents = []
        
        print(f"Scanning {self.repo_path}...")
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip hidden dirs
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                ext = file.split('.')[-1]
                if ext in extensions:
                    file_path = os.path.join(root, file)
                    try:
                        loader = TextLoader(file_path, encoding='utf-8')
                        documents.extend(loader.load())
                    except Exception as e:
                        # Fallback for encoding issues
                        pass

        print(f"Loaded {len(documents)} documents.")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        print(f"Split into {len(chunks)} chunks.")
        
        # Initialize BM25 for Phase 2 Hybrid Search
        print("Initializing BM25 index...")
        tokenized_corpus = [re.sub(r'[^\w\s]', '', chunk.page_content.lower()).split() for chunk in chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self.all_chunks = chunks
        
        return chunks

    def create_vector_store(self, chunks):
        """Creates and indexes the Endee vector store."""
        if not chunks:
            print("No chunks to index.")
            return None
            
        print("Creating embeddings and indexing into Endee...")
        db = EndeeDB(collection_name=self.repo_name)
        
        for i, chunk in enumerate(chunks):
            # Using embedding model to generate vectors
            vector = self.embeddings.embed_query(chunk.page_content)
            db.insert(
                id=f"chunk_{i}",
                vector=vector,
                metadata={
                    "source": chunk.metadata.get("source", "unknown"),
                    "content": chunk.page_content
                }
            )
        print(f"Data ingested into Endee collection: {self.repo_name}")
        return db

    def load_vector_store(self):
        """Initializes the Endee database client."""
        # EndeeDB initialization handles collection checking
        db = EndeeDB(collection_name=self.repo_name)
        
        # Reload BM25 if chunks are available in repo_path
        if not self.bm25 and os.path.exists(self.repo_path):
            print("Reloading BM25 from repo files...")
            self.load_and_process_files()
            
        return db

    def generate_repo_map(self) -> str:
        """Generates a text-based file tree of the repository."""
        if not os.path.exists(self.repo_path):
            return "Repository not cloned yet."
            
        repo_map = []
        for root, dirs, files in os.walk(self.repo_path):
            # Skip hidden and ignored directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != "__pycache__" and d != "node_modules"]
            
            level = root.replace(self.repo_path, '').count(os.sep)
            indent = '  ' * level
            repo_map.append(f"{indent}📁 {os.path.basename(root)}/")
            
            sub_indent = '  ' * (level + 1)
            for f in files:
                if not f.startswith('.'):
                    repo_map.append(f"{sub_indent}📄 {f}")
                    
        return "\n".join(repo_map)

    def get_repo_structure(self) -> List[Dict[str, Any]]:
        """Returns a structured list of files and folders for interactive display."""
        if not os.path.exists(self.repo_path):
            return []
            
        structure = []
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != "__pycache__" and d != "node_modules"]
            
            rel_path = os.path.relpath(root, self.repo_path)
            if rel_path == ".":
                rel_path = ""
                
            level = 0 if not rel_path else rel_path.count(os.sep) + 1
            
            # Add directory
            structure.append({
                "type": "folder",
                "name": os.path.basename(root) or self.repo_name,
                "path": rel_path,
                "level": level
            })
            
            # Add files
            for f in sorted(files):
                if not f.startswith('.'):
                    f_path = Path(rel_path) / f
                    structure.append({
                        "type": "file",
                        "name": f,
                        "path": f_path.as_posix(), # Always use forward slashes
                        "level": level + 1
                    })
                    
        return structure

    def prepare_zip(self) -> str:
        """Archives the repository into a ZIP file and returns the path."""
        if not os.path.exists(self.repo_path):
            raise FileNotFoundError("Repository not found. Please analyze first.")
            
        timestamp = int(time.time())
        zip_base_name = os.path.join(self.base_dir, "repo_data", f"{self.repo_name}_download_{timestamp}")
        # shutil.make_archive adds the .zip extension automatically
        zip_path = shutil.make_archive(zip_base_name, 'zip', self.repo_path)
        return zip_path

    def save_history(self, history: List[Dict[str, str]]):
        """Saves chat history to a local JSON file."""
        try:
            os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"Failed to save history: {e}")

    def load_history(self) -> List[Dict[str, str]]:
        """Loads chat history from the local JSON file."""
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Failed to load history: {e}")
        return []

    def _hybrid_search(self, db, query_vector, query_text, top_k=5):
        """Combines Vector search (Endee) and Keyword search (BM25)."""
        # 1. Vector Search
        vector_results = db.search(vector=query_vector, top_k=top_k)
        
        # Convert Endee results to LangChain-like Document objects
        try:
            from langchain_core.documents import Document
        except ImportError:
            from langchain.schema import Document
            
        docs = []
        for res in vector_results.get("matches", []):
            docs.append(Document(
                page_content=res.get("metadata", {}).get("content", ""),
                metadata=res.get("metadata", {})
            ))
            
        # 2. BM25 Search (Keyword)
        if self.bm25:
            tokenized_query = re.sub(r'[^\w\s]', '', query_text.lower()).split()
            bm25_hits = self.bm25.get_top_n(tokenized_query, self.all_chunks, n=top_k)
            
            # Combine and deduplicate (by source and snippet)
            seen_content = {d.page_content for d in docs}
            for hit in bm25_hits:
                if hit.page_content not in seen_content:
                    docs.append(hit)
                    seen_content.add(hit.page_content)
                    
        # 3. README Boost: If not present, look for it explicitly
        if "readme" in query_text.lower() or len(docs) < 2:
            readme_docs = [c for c in self.all_chunks if "readme.md" in c.metadata.get("source", "").lower()]
            for r in readme_docs[:2]:
                if r.page_content not in {d.page_content for d in docs}:
                    docs.insert(0, r)
                    
        return docs[:top_k * 2] # Return more for the reranker

    def _clean_code(self, content: str) -> str:
        """Removes excessive whitespace and common comment patterns to save tokens."""
        # Remove common comment patterns (basic)
        content = re.sub(r'#.*', '', content)  # Python/JS single line
        content = re.sub(r'//.*', '', content) # C-style single line
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL) # C-style multi-line
        
        # Collapse multiple newlines and spaces
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        return "\n".join(lines)

    def ask_question(self, query: str) -> Generator[str, None, None]:
        """Queries the RAG system with streaming and metrics."""
        start_time = time.time()
        
        db = self.load_vector_store()
        if not db:
            yield "Error: Endee database not initialized. Please ingest the repo first."
            return

        # 1. Search Time
        search_start = time.time()
        query_vector = self.embeddings.embed_query(query)
        
        # 🚀 Phase 2: Hybrid Search
        docs = self._hybrid_search(db, query_vector, query)
        
        # 2️⃣ Add a Reranker (Improves Speed + Quality) ⚡
        if docs:
            pairs = [[query, doc.page_content] for doc in docs]
            scores = self.reranker.predict(pairs)
            scored_docs = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
            # Keep top 3 for better context
            docs = [doc for score, doc in scored_docs[:3]]

        search_time = round(time.time() - search_start, 2)
        
        try:
            llm = Ollama(model=self.model_name, base_url="http://127.0.0.1:11434")
            
            # Clean documents content to save tokens
            for doc in docs:
                doc.page_content = self._clean_code(doc.page_content)

            # Context construction
            context_text = "\n\n".join([f"Source: {os.path.basename(d.metadata.get('source', 'unknown'))}\nCode:\n{d.page_content}" for d in docs])
            
            prompt = f"""You are a professional coding assistant. Use the following code snippets to answer the user's question. 
            Detailed and accurate answers are prioritized. If you don't know, say so.
            
            Question: {query}
            
            Code Context:
            {context_text}
            
            Answer:"""
            
            # Streaming and total tokens
            llm_start = time.time()
            full_response = ""
            for chunk in llm.stream(prompt):
                full_response += chunk
                yield chunk
            
            llm_time = round(time.time() - llm_start, 2)
            total_time = round(time.time() - start_time, 2)
            
            # Metadata for metrics
            metrics = {
                "search_time": search_time,
                "llm_time": llm_time,
                "total_time": total_time,
                "source_documents": docs
            }
            
            # Save to cache with metrics
            self.cache[query] = {"result": full_response, "metrics": metrics, "source_documents": docs}
            
        except Exception as e:
            if "connection" in str(e).lower() or "refused" in str(e).lower():
                explanation = f"### 💡 Note: Ollama is not running\n\nI couldn't connect to the local AI model (Ollama). Here are the most relevant code snippets I found:\n\n"
                for i, doc in enumerate(docs or []):
                    source = doc.metadata.get('source', 'unknown')
                    rel_path = os.path.basename(source)
                    explanation += f"**{i+1}. {rel_path}**\n```\n{doc.page_content[:800]}...\n```\n\n"
                yield explanation
                return
            
            yield f"Error: {e}"
