import os
import chromadb
from chromadb.utils import embedding_functions

os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"


class GraphRAGAgent:
    def __init__(self, db_path: str = "./pnsv_vector_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_model = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name="codebase_structures",
            embedding_function=self.embedding_model
        )

    def retrieve_context(self, user_query: str, limit: int = 5) -> tuple:
        results = self.collection.query(
            query_texts=[user_query],
            n_results=limit,
            include=["documents", "metadatas", "distances"]
        )

        if not results['documents'] or not results['documents'][0]:
            return None, "No matching codebase context found."

        context_payload = "--- RETRIEVED CODE BLOCKS ---\n\n"

        for i in range(len(results['documents'][0])):
            doc      = results['documents'][0][i]
            meta     = results['metadatas'][0][i]
            distance = results['distances'][0][i]
            relevance = round((1 - distance) * 100, 1)

            context_payload += (
                f"File: {os.path.basename(meta['file_path'])} "
                f"| Type: {meta['node_type']} "
                f"| Name: {meta['identity_name']} "
                f"| Lines: {meta['start_line']}-{meta['end_line']} "
                f"| Relevance: {relevance}%\n"
            )
            context_payload += f"```python\n{doc}\n```\n\n"

        return results, context_payload

    def generate_prompt(self, user_query: str) -> tuple:
        results, context = self.retrieve_context(user_query)

        if results is None:
            return None, context

        prompt = f"""You are a code analysis assistant.
Answer questions about the codebase using ONLY the provided code blocks.

Rules:
- Reference specific function and class names from the context
- Cite file names and line numbers when relevant
- If the answer requires code not shown, say so explicitly
- Never guess implementation details not in the context

{context}

Question: {user_query}
Answer:"""

        return context, prompt