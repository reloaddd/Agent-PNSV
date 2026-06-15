# Agent-PNSV

**AST-Driven Agentic GraphRAG for Repository-Level Code Understanding**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Tree-sitter](https://img.shields.io/badge/AST-Tree--sitter-green.svg)](https://tree-sitter.github.io/tree-sitter/)
[![Vector DB](https://img.shields.io/badge/Vector_DB-Qdrant-red.svg)](https://qdrant.tech/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Traditional RAG treats source code like prose. Fixed-size chunking splits functions mid-logic, semantic similarity returns superficial matches, and complex multi-file inheritance or call hierarchies are completely invisible to standard vector search.

**Agent-PNSV parses code the way compilers do — by structure, not by character count.**

---

## Visual Pipeline Workflow

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
What Agent-PNSV Does: Target any GitHub Repository → Agent-PNSV clones it, maps it, and tracks it.Abstract Syntax Tree Parsing → Code is deterministically sliced at function and class boundaries.Graph-Relational Indexing → Build multi-hop execution edges (CALLS, INHERITS_FROM).Agentic Execution Loop → Autonomous query router explores semantic search and graph maps simultaneously.Core Capabilities🌿 AST-Aware ChunkingNo function is ever split mid-logic. Tree-sitter guarantees that every extracted code element remains a completely self-contained logical block carrying strict structural metadata headers.⛓️ GraphRAG ArchitectureMulti-hop reasoning across independent code files, structural dependencies, and deep inheritance chains is handled natively by mapping code blocks as nodes inside a connected relational execution graph.🧠 Local InferenceAll LLM inference runs locally via Ollama (Llama 3.3, DeepSeek-R1). Your underlying intellectual property and codebase data never leave your local workspace environment.Tech StackLayerTechnologyAgent OrchestrationLangGraph, CrewAIAST ParsingTree-sitter (Core Python & C++ Modules)Vector StorageQdrantGraph EngineNetworkX / Neo4jLocal InferenceOllamaWhy Structure MattersCapabilityTraditional RAGAgent-PNSVChunking StrategyFixed character limitAST structural boundariesRetrieval SignalSemantic similarity onlySemantic similarity + Graph traversalCross-File ReasoningNoneMulti-hop dependency chainsHallucination SurfaceHigh (missing local context)Low (verified relational context)StatusActive development phase. Contributions and architectural reviews welcome.
---