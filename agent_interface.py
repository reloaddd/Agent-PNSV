import os
import chromadb
from chromadb.utils import embedding_functions

class GraphRAGAgent:
    def __init__(self, db_path: str = "./pnsv_vector_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_model = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_collection(
            name="codebase_structures",
            embedding_function=self.embedding_model
        )

    def retrieve_context(self, user_query: str, limit: int = 2) -> str:
        results = self.collection.query(query_texts=[user_query], n_results=limit)
        if not results['documents'] or not results['documents'][0]:
            return "No matching codebase context found."

        context_payload = "--- RELEVANT CODEBASE CONTEXT STRUCTURAL BLOCKS ---\n\n"
        for i in range(len(results['documents'][0])):
            doc = results['documents'][0][i]
            meta = results['metadatas'][0][i]
            context_payload += f"📍 File: {os.path.basename(meta['file_path'])} | Type: {meta['node_type']} | Identity: {meta['identity_name']}\n"
            context_payload += f"🔢 Structural Boundaries: Lines {meta['start_line']} to {meta['end_line']}\n"
            context_payload += f"```python\n{doc}\n```\n\n"
        return context_payload

    def generate_prompt(self, user_query: str) -> tuple:
        """Assembles context matrix and returns raw context alongside full prompt payload."""
        context = self.retrieve_context(user_query)
        prompt = f"""You are an Elite Agentic GraphRAG System inspecting a complex technical codebase repository.
Using only the strict, syntax-verified code context nodes provided below, answer the user's question directly.

{context}

Question: {user_query}
Answer:"""
        return context, prompt