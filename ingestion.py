import os
import shutil
from git import Repo

from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_cpp as tscpp

import re

import chromadb
from chromadb.utils import embedding_functions

os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"


class WorkspaceManager:

    """ Handles file system preparation
        Clears existing ones
    """

    def __init__(self, workspace_path: str = "./repo_workspace"):
        self.workspace_path=workspace_path
        self.prepare_workspace()


    def prepare_workspace(self):

        """ wipes exisiting dirs if any and estb a clean workspace"""

        if os.path.exists(self.workspace_path):
            print(f"Found existing workspace at {self.workspace_path}. Cleaning directory...")


            # Helper function to clear Windows read-only flags dynamically
            def remove_readonly(func, path, excinfo):
                import stat
                os.chmod(path, stat.S_IWRITE)
                func(path)
                
            shutil.rmtree(self.workspace_path, onerror=remove_readonly)

        os.makedirs(self.workspace_path)
        print(f"Clean workspace initialized at {self.workspace_path}")

    
    def clone_repo(self, repo_url:str):

        """cloning remote git repo into local workspace"""

        print(f"Cloning repository {repo_url}...")

        try:
            Repo.clone_from(repo_url,self.workspace_path)
            print(f"Cloning complete! Repository data successfully downloaded locally")

        except Exception as e:
            print(f"Failed to clone repository. Technical error: {e}")
            raise



    
    def get_source_files(self, extensions: list = None) -> list:

        """ Recursively walks the workspace file system tree
            Filters out configs/asset noice and isolate target code paths
        """

        if extensions is None:
            extensions=[".py",".cpp",".h"]

        discovered_paths=[]
        print(f"Crawling workpspace for target extensions: {extensions}")

        # os.walk yields a 3-tuple: (current_folder, sub_directories, files_within_folder)

        for root,_,files in os.walk(self.workspace_path):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    full_path=os.path.join(root,file)
                    absolute_path=os.path.abspath(full_path)
                    discovered_paths.append(absolute_path)
        
        print(f"File discovery complete. Isolated {len(discovered_paths)} valid source files.")
        return discovered_paths
    


class ASTChunker:

    """
    Leverages tree_sitter to parse source files into AST(Abstarct Syntax Tree)
    Identifies and extracts complete structural code blocks (function/classes)

    """

    def __init__(self):

        self.py_lang=Language(tspython.language())
        self.cpp_lang=Language(tscpp.language())

        self.parser=Parser()

    def get_language_form_path(self, file_path:str):
        """ Determines the appropriate grammer based on the file extension"""

        if file_path.endswith(".py"):
            return self.py_lang
        elif file_path.endswith((".cpp",".h",".hpp",".cc")):
            return self.cpp_lang
        return None
    

    def parse_file_to_chunks(self,file_path:str)->list:

        """Reads a file, compile its AST and slices it at structural boundaries"""

        lang=self.get_language_form_path(file_path)

        if not lang:
            return []
        
        

        with(open(file_path, "r", encoding="utf-8", errors="ignore")) as f:
            source_code=f.read()

        if not source_code.strip():
            return []

        parser=Parser(lang)

        tree=parser.parse(bytes(source_code,"utf8"))
        root_node=tree.root_node

        chunks=[]

        target_types=["function_definition", "class_definition", "struct_specifier"]

        def traverse(node):
            if node.type in target_types:

                start_line=node.start_point[0]+1
                end_line=node.end_point[0]+1

                lines=source_code.splitlines()[node.start_point[0]:node.end_point[0]+1]
                raw_code_block="\n".join(lines)

                chunks.append({
                    "file_path":file_path,
                    "node_type":node.type,
                    "start_line":start_line,
                    "end_line":end_line,
                    "code":raw_code_block
                })
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return chunks


class CodeGraphMapper:
    """
    Analyzes extracted AST chunks to map architectural relationships.
    Discovers how functions call each other, how classes inherit, and file imports.
    """
    def __init__(self, chunks: list):
        self.chunks = chunks
        
        self.valid_targets = self._build_target_lookup()

    def _build_target_lookup(self) -> dict:
        """Maps out names to their full structural chunk data for quick matching."""
        lookup = {}
        for chunk in self.chunks:
            
            first_line = chunk["code"].splitlines()[0] if chunk["code"] else ""
            
            #capture the name after 'def' or 'class'
            match = re.search(r'(?:def|class)\s+([a-zA-Z_][a-zA-Z0-9_]*)', first_line)
            if match:
                name = match.group(1)
                chunk["name"] = name  
                lookup[name] = chunk
            else:
                chunk["name"] = "unknown"
        return lookup

    def extract_relationships(self) -> list:
        """Scans the internal text of every chunk to generate relational graph edges."""
        edges = []

        for source_chunk in self.chunks:
            source_name = source_chunk.get("name", "unknown")
            if source_name == "unknown":
                continue

           
            code_body = source_chunk["code"]

            
            for target_name, target_chunk in self.valid_targets.items():
                if source_name == target_name:
                    continue 
                
                
                if re.search(r'\b' + re.escape(target_name) + r'\b\(', code_body):
                    edges.append({
                        "source": source_name,
                        "relationship": "CALLS",
                        "target": target_name,
                        "meta": {
                            "source_file": os.path.basename(source_chunk["file_path"]),
                            "target_file": os.path.basename(target_chunk["file_path"])
                        }
                    })

            # 2. Search for INHERITS_FROM relationships (For Class Definitions)
            if source_chunk["node_type"] == "class_definition":
                first_line = code_body.splitlines()[0]
                
                inheritance_match = re.search(r'class\s+\w+\(([^)]+)\)', first_line)
                if inheritance_match:
                    parents = [p.strip() for p in inheritance_match.group(1).split(",")]
                    for parent in parents:
                        edges.append({
                            "source": source_name,
                            "relationship": "INHERITS_FROM",
                            "target": parent,
                            "meta": {"source_file": os.path.basename(source_chunk["file_path"])}
                        })

        print(f"Relational Mapping Complete. Extracted {len(edges)} architectural graph edges.")
        return edges


class VectorStorageEngine:
    """
    Manages local vector database deployment using ChromaDB.
    Handles semantic code embedding generation and persistent disk indexing.
    """
    def __init__(self, db_path: str = "./pnsv_vector_db"):
        self.db_path = db_path
        
       
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        
        self.embedding_model = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        
        self.collection = self.client.get_or_create_collection(
            name="codebase_structures",
            embedding_function=self.embedding_model
        )

    def store_chunks(self, chunks: list):
        """Generates embeddings and populates the vector store with metadata updates."""
        if not chunks:
            print("No chunks available to index in the vector warehouse.")
            return

        print(f"Generating vector embeddings for {len(chunks)} code items via local transformer...")

        ids = []
        documents = []
        metadatas = []

        for idx, chunk in enumerate(chunks):
            
            chunk_id = f"chunk_{os.path.basename(chunk['file_path'])}_{chunk['start_line']}_{idx}"
            
            ids.append(chunk_id)
            documents.append(chunk["code"]) # string  gets vectorized
            
            #  (strings, ints, floats) for database querying
            metadatas.append({
                "file_path": chunk["file_path"],
                "node_type": chunk["node_type"],
                "start_line": int(chunk["start_line"]),
                "end_line": int(chunk["end_line"]),
                "identity_name": chunk.get("name", "unknown")
            })

        
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        print(f"Vector store database synced completely at: {self.db_path}")

    def semantic_search(self, query: str, num_results: int = 3) -> dict:
        """Runs a real-time vector math query against the code database."""
        return self.collection.query(
            query_texts=[query],
            n_results=num_results
        )

    


if __name__ == "__main__":

    #TEST_REPO="https://github.com/pallets/click"
    #TEST_REPO="https://github.com/reloaddd/Agent-Kiro"

    TEST_REPO = "https://github.com/coleifer/peewee"

    manager=WorkspaceManager()
    chunker=ASTChunker()
    db_engine = VectorStorageEngine()

    manager.clone_repo(TEST_REPO)

    files=manager.get_source_files(extensions=[".py"])

    all_extracted_chunks=[]

    for file_path in files:
        file_chunks=chunker.parse_file_to_chunks(file_path)
        #  FLATTENING SAFETY LAYER: Ensure every single item added is a dictionary
        if file_chunks:
            if isinstance(file_chunks, list):
                for item in file_chunks:
                    if isinstance(item, list):
                        all_extracted_chunks.extend(item)  # Handle unexpected double nesting
                    elif isinstance(item, dict):
                        all_extracted_chunks.append(item)
            elif isinstance(file_chunks, dict):
                all_extracted_chunks.append(file_chunks)

    print(f"\n Total AST Structural Chunks Extracted: {len(all_extracted_chunks)}")

    if all_extracted_chunks:
        mapper = CodeGraphMapper(all_extracted_chunks)
        graph_edges = mapper.extract_relationships()

        db_engine.store_chunks(all_extracted_chunks)

        print("\n🔍 --- TESTING AGENT VECTOR RETRIEVAL ---")
        TEST_QUERY = "How does the engine handle terminal argument parsing or click command options?"
        results = db_engine.semantic_search(TEST_QUERY, num_results=2)

        print(f"Query: '{TEST_QUERY}'")
        print("\nTop Semantically Relevent Code Chunk Found:")
        if results['documents'] and results['documents'][0]:
            print(f"  → Source File: {results['metadatas'][0][0]['file_path']}")
            print(f"  → Lines: {results['metadatas'][0][0]['start_line']} to {results['metadatas'][0][0]['end_line']}")
            print(f"  → Code Snippet:\n\n{results['documents'][0][0][:400]}...\n")
        