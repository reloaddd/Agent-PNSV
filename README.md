# Agent-PNSV

**AST-Driven Agentic GraphRAG for Repository-Level Code Understanding**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Tree-sitter](https://img.shields.io/badge/AST-Tree--sitter-green.svg)](https://tree-sitter.github.io/tree-sitter/)
[![Vector DB](https://img.shields.io/badge/Vector_DB-Qdrant-red.svg)](https://qdrant.tech/)
[![Ollama](https://img.shields.io/badge/Ollama-Local_Inference-orange.svg)](https://ollama.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 The Core Problem

Traditional Retrieval-Augmented Generation (RAG) processes source code as if it were regular prose. This naive approach introduces severe architectural failures when applied to complex software engineering repositories:

1. **Logical Fragmentation:** Fixed-size chunking strategies (e.g., slicing text every 500 characters) blindside the LLM by cutting functions, loops, or try-catch blocks completely in half.
2. **Context Blindness:** Standard semantic search relies entirely on superficial text similarity. It struggles to distinguish between a core function implementation, its unit test file, or its interface declaration.
3. **Relational Invisibility:** Multi-file inheritance chains, object-oriented overrides, and explicit function call hierarchies are entirely invisible to vector embeddings. The system cannot perform multi-hop reasoning across independent modules.

**Agent-PNSV solves this by parsing code exactly how compilers do — by structural abstract syntax trees (AST), not by character count.**

---

## 🏗️ System Architecture & Workflow

Agent-PNSV works like an automated code-to-graph translation pipeline. Below is the full engineering workflow mapping how a target codebase is ingested, decomposed, and reassembled into an agent-navigable relational graph.

```mermaid
graph TD
    %% Styling Configuration
    classDef stageStyle fill:#1f2937,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef dataStyle fill:#111827,stroke:#10b981,stroke-width:1px,color:#10b981,stroke-dasharray: 5 5;
    classDef userStyle fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff;

    %% Workflow Nodes
    URL["🔗 Target GitHub Repository URL"]:::userStyle
    
    subgraph M1 ["📦 MODULE 1: THE INGESTION ENGINE"]
        A["🧹 Workspace Cleaner<br/>(Wipes old ./repo_workspace)"]:::stageStyle
        B["📥 Git Cloner<br/>(GitPython Streaming)"]:::stageStyle
        C["🔍 File Walker<br/>(Filters for .py / .cpp)"]:::stageStyle
    end

    subgraph M2 ["🔮 MODULE 2: AST STRUCTURAL PARSING"]
        D["⚙️ Tree-Sitter Core Engine<br/>(Loads Language Grammars)"]:::stageStyle
        E["🌿 Syntax Tree Traversal<br/>(Recursive Node Inspection)"]:::stageStyle
        F["✂️ AST-Bound Chunker<br/>(Extracts Class/Function Scopes)"]:::stageStyle
    end

    Packet[/"📦 Final Structural Data Packet<br/>(Raw Code + Strict Line Metadata)"/]:::dataStyle

    %% Workflow Connections
    URL --> A
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> Packet
🚀 Key Architectural Pillars1. AST-Aware Structural ChunkingInstead of arbitrary splitting, Agent-PNSV utilizes Tree-sitter to compile source files into real Concrete Syntax Trees. It targets specific syntax nodes such as function_definition, class_definition, and struct_specifier.Functions and classes are extracted in their entirety, preserving complete internal logic.Every chunk is tagged with its absolute line numbers (start_line to end_line), parent file path, and enclosing lexical scope.2. GraphRAG Relational MappingExtracted chunks are not just saved as isolated text strings; they are mapped as interconnected nodes in a relational execution graph. Agent-PNSV automatically extracts three primary code edges:CALLS: Connects a function node directly to any external functions it invokes.INHERITS_FROM: Maps object-oriented relationships and class hierarchies.DEPENDS_ON: Tracks cross-file imports and module infrastructure.3. Dual-Engine Retrieval (Semantic + Graph Traversal)When a user asks a technical question, an Agentic Router maps the query loop:Vector Search (Qdrant): Pinpoints the precise entry-point code block based on conceptual semantic meaning.Graph Traversal (NetworkX/Neo4j): Once the entry node is located, the autonomous agent walks the relational graph to retrieve its parent classes, dependencies, and execution chains.4. Zero-Data-Leak Local InferenceDesigned for high-security enterprise codebases, Agent-PNSV handles all computational inference locally using Ollama. Your source code, metadata graphs, and embedding maps never leave your physical hard drive.📊 Performance ComparisonCapabilityTraditional Vector RAGAgent-PNSV (GraphRAG)Chunking BoundsFixed character windows (e.g., 512 tokens)Deterministic AST node boundariesCode PreservationHigh risk of splitting functions mid-lineGuarantees complete, self-contained elementsCross-File InsightBlind to multi-file imports/dependenciesFollows explicit relational execution edgesRetrieval BlueprintStandard mathematical similarity scoresHybrid: Vector seed + Multi-hop graph crawlHallucination LevelHigh (due to disjointed, incomplete context)Low (anchored to compiler-verified graph path)🛠️ Technology StackLayerTechnologyAgent OrchestrationLangGraph, CrewAIAST Parsing CoreTree-sitter (Native bindings for tree-sitter-python & tree-sitter-cpp)Vector StorageQdrantGraph EngineNetworkX / Neo4jLocal InferenceOllama (Llama 3.3, DeepSeek-R1)Development ToolkitGitPython, Python 3.12, FastAPI🗺️ Roadmap & Current Status[x] Core Workspace Ingestion and Git Streaming Architecture[x] Multi-Language AST Grammar Extraction Configuration (Python & C++)[ ] [In Progress] AST Node Extraction Handler Engine[ ] Relational Graph Mapping Interface & Database Construction[ ] Agentic Retrieval Execution Loop IntegrationAgent-PNSV — Because source code has strict structural meaning. Your RAG platform should too.
---
