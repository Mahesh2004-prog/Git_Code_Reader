import os
import sys
from unittest.mock import MagicMock

# Mocking modules that might not be fully installed or needed for basic logic test
sys.modules['langchain_community.embeddings'] = MagicMock()
sys.modules['langchain_community.vectorstores'] = MagicMock()
sys.modules['langchain_community.llms'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['git'] = MagicMock()

from backend import CodeRAG

def test_clean_code():
    rag = CodeRAG("https://github.com/test/repo")
    code = """
    # This is a comment
    def hello():
        # Another comment
        
        print("Hello")
        
    """
    cleaned = rag._clean_code(code)
    print("--- Original ---")
    print(code)
    print("--- Cleaned ---")
    print(cleaned)
    assert "#" not in cleaned
    assert "print" in cleaned
    print("✅ test_clean_code passed!")

def test_caching():
    rag = CodeRAG("https://github.com/test/repo")
    # Mocking retrieval and LLM call
    rag.load_vector_store = MagicMock()
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = "Mocked result"
    
    # We need to mock Ollama constructor or the LLM call inside ask_question
    # This is a bit complex for a simple script, so let's check the cache dict directly
    query = "test question"
    response = {"result": "Cached result", "source_documents": []}
    rag.cache[query] = response
    
    result = rag.ask_question(query)
    assert result == response
    print("✅ test_caching passed!")

if __name__ == "__main__":
    test_clean_code()
    test_caching()
