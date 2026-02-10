import requests
import json
import msgpack
import os
import numpy as np

class EndeeDB:
    """
    A resilient Python client for the Endee Vector Database REST API.
    Includes a local fallback to ensure the application works even if the server is down.
    """
    def __init__(self, collection_name, base_url="http://localhost:8080", token=None):
        self.collection_name = collection_name
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {"Content-Type": "application/json"}
        if self.token:
            self.headers["Authorization"] = self.token
        
        # Local fallback storage
        self.local_mode = False
        self.local_data = [] # List of {"id": id, "vector": vector, "metadata": metadata}
        
        # Attempt to ensure the index exists, if it fails, switch to local mode
        self._ensure_index()

    def _ensure_index(self):
        """Checks if the index exists, creates it if it doesn't. Errors switch to local mode."""
        try:
            url = f"{self.base_url}/api/v1/index/create"
            data = {
                "index_name": self.collection_name,
                "dim": 384,  # Default for all-MiniLM-L6-v2
                "space_type": "l2"
            }
            # Set a short timeout for the initial connection check
            response = requests.post(url, json=data, headers=self.headers, timeout=2)
            if response.status_code not in [200, 400, 409]: # 400/409 often mean already exists
                print(f"Endee server returned {response.status_code}. Using local fallback mode.")
                self.local_mode = True
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            print("Endee server not found at localhost:8080. Using local fallback mode.")
            self.local_mode = True
        except Exception as e:
            print(f"Connection error: {e}. Using local fallback mode.")
            self.local_mode = True

    def insert(self, id, vector, metadata=None):
        """
        Inserts a single vector and its metadata.
        Uses local fallback if the server is down.
        """
        if self.local_mode:
            self.local_data.append({
                "id": str(id),
                "vector": vector,
                "metadata": metadata or {}
            })
            return True

        try:
            # 1. Insert vector
            url = f"{self.base_url}/api/v1/index/{self.collection_name}/vector/insert"
            payload = {
                "id": str(id),
                "vector": vector
            }
            response = requests.post(url, json=payload, headers=self.headers, timeout=5)
            if response.status_code != 200:
                print(f"Insert failed: {response.text}. Attempting local fallback.")
                self.local_mode = True
                return self.insert(id, vector, metadata)

            # 2. Update metadata
            if metadata:
                self.update_metadata(id, metadata)
            return True
        except Exception as e:
            print(f"Insert failed with error: {e}. Attempting local fallback.")
            self.local_mode = True
            return self.insert(id, vector, metadata)

    def update_metadata(self, id, metadata):
        """Updates metadata. Handles fallback."""
        if self.local_mode:
            for item in self.local_data:
                if item["id"] == str(id):
                    item["metadata"] = metadata
            return True

        try:
            url = f"{self.base_url}/api/v1/index/{self.collection_name}/filters/update"
            payload = {
                "updates": [{"id": str(id), "filter": metadata}]
            }
            requests.post(url, json=payload, headers=self.headers, timeout=5)
        except:
            pass # Non-critical if metadata update fails on server during ingestion
        return True

    def search(self, vector, top_k=3):
        """
        Performs similarity search. Uses local fallback if server is down.
        """
        if self.local_mode:
            return self._local_search(vector, top_k)

        try:
            url = f"{self.base_url}/api/v1/index/{self.collection_name}/search"
            payload = {"vector": vector, "k": top_k}
            
            response = requests.post(url, json=payload, headers=self.headers, timeout=5)
            if response.status_code != 200:
                print(f"Search failed: {response.text}. Using local fallback.")
                return self._local_search(vector, top_k)
                
            data = msgpack.unpackb(response.content, raw=False)
            matches = []
            results_list = []
            
            if isinstance(data, dict) and 'results' in data:
                results_list = data['results']
            elif isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], list): results_list = data[0]

            for item in results_list:
                if isinstance(item, list) and len(item) >= 4:
                    score, vid, filter_str = item[0], item[1], item[3]
                    try:
                        md = json.loads(filter_str) if filter_str else {}
                    except:
                        md = {}
                    matches.append({"id": vid, "score": score, "metadata": md})
            
            return {"matches": matches}
        except Exception as e:
            print(f"Search failed: {e}. Using local fallback.")
            return self._local_search(vector, top_k)

    def _local_search(self, query_vector, top_k):
        """Simple in-memory Cosine Similarity search using numpy."""
        if not self.local_data:
            return {"matches": []}
            
        q_vec = np.array(query_vector)
        q_norm = np.linalg.norm(q_vec)
        
        results = []
        for item in self.local_data:
            i_vec = np.array(item["vector"])
            i_norm = np.linalg.norm(i_vec)
            
            # Cosine similarity
            if q_norm > 0 and i_norm > 0:
                sim = np.dot(q_vec, i_vec) / (q_norm * i_norm)
            else:
                sim = 0
                
            results.append({
                "id": item["id"],
                "score": float(sim),
                "metadata": item["metadata"]
            })
            
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return {"matches": results[:top_k]}
