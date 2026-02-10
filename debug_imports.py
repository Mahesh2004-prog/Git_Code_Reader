import sys
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

try:
    import langchain
    print(f"LangChain path: {langchain.__file__}")
    print(f"LangChain version: {getattr(langchain, '__version__', 'unknown')}")
except ImportError:
    print("LangChain not found")

print("\n--- Attempting Imports ---")

try:
    from langchain.chains import RetrievalQA
    print("SUCCESS: from langchain.chains import RetrievalQA")
except ImportError as e:
    print(f"FAIL: from langchain.chains import RetrievalQA -> {e}")

try:
    from langchain.chains.retrieval_qa.base import RetrievalQA
    print("SUCCESS: from langchain.chains.retrieval_qa.base import RetrievalQA")
except ImportError as e:
    print(f"FAIL: from langchain.chains.retrieval_qa.base import RetrievalQA -> {e}")

try:
    from langchain_community.chains import RetrievalQA
    print("SUCCESS: from langchain_community.chains import RetrievalQA")
except ImportError as e:
    print(f"FAIL: from langchain_community.chains import RetrievalQA -> {e}")
