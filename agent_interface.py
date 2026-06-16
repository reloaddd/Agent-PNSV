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

        prompt = f"""You are an elite, production-grade AI Code Intelligence Assistant named Agent-PNSV.
Your objective is to help the user understand, debug, optimize, and reason about their software codebase.

CRITICAL INSTRUCTIONS:
1. CODEBASE REASONING: When the user asks about specific system logic, deeply analyze the provided structural code chunks below. Reference specific classes, functions, variable names, and file sources accurately.
2. GENERAL KNOWLEDGE OUTSIDE THE CONTEXT: If the user asks general programming questions (e.g., explaining an algorithm, asking for architectural advice, writing new unit tests, or explaining software concepts like ORMs), do NOT say "I cannot answer." Act exactly like a standard advanced LLM (GPT/Claude) and fulfill the request using your broad technical knowledge base.
3. HYBRID CAPABILITY: Always merge context clues with your general coding expertise. If code context is provided but incomplete for a request, utilize the provided structure as a blueprint and complete the implementation logically.

[STRUCTURED CODE CONTEXT BARS]
{context}
[END OF CONTEXT BARS]

User Chat History & Active Request:
{user_query}

Answer:"""

        return context, prompt