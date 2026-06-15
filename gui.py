import streamlit as st
import os
from agent_interface import GraphRAGAgent

# 1. Page Configuration and Styling
st.set_page_config(page_title="Agent PNSV Dashboard", page_icon="🤖", layout="wide")
st.title("🤖 Agent PNSV - GraphRAG Workspace")
st.caption("Inspect abstract syntax trees, relational maps, and chat with your codebase locally.")

# 2. Initialize our core backend agent
@st.cache_resource
def load_agent():
    return GraphRAGAgent()

try:
    agent = load_agent()
except Exception as e:
    st.error(f"Could not connect to vector database. Did you run ingestion.py first? Error: {e}")
    st.stop()

# 3. Main Chat Interface Setup
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display ongoing chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Capture User Inputs
if user_query := st.chat_input("Ask a question about your cloned repository..."):
    # Display user question
    st.chat_message("user").write(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    # Extract Context and Search Vectors
    with st.spinner("Extracting deep structural context matrix..."):
        context, complete_llm_prompt = agent.generate_prompt(user_query)

    # 5. Render retrieved Context in a clean Sidebar panel
    with st.sidebar:
        st.header("📍 Retrieved AST Chunks")
        st.markdown("These exact structural code blocks were extracted to guide the AI's generation:")
        st.text_area(label="Context Window Payload", value=context, height=500, disabled=True)

    # 6. Route Payload to LLM Layer with Real-Time Streaming
    with st.chat_message("assistant"):
        try:
            import ollama
            response_placeholder = st.empty()
            full_ai_stream_text = ""
            
            # Request token streaming execution from local model core
            stream = ollama.generate(model='llama3', prompt=complete_llm_prompt, stream=True)
            
            for chunk in stream:
                full_ai_stream_text += chunk['response']
                # Render the current accumulated text alongside a blinking terminal block cursor
                response_placeholder.markdown(full_ai_stream_text + " █")
            
            # Clean render without cursor once stream completes
            response_placeholder.markdown(full_ai_stream_text)
            st.session_state.messages.append({"role": "assistant", "content": full_ai_stream_text})
            
        except Exception:
            # Fallback if Ollama service isn't turned on
            st.warning("⚠️ Local Ollama core service is offline.")
            st.markdown("Here is the compiled prompt data package ready for cloud execution:")
            st.code(complete_llm_prompt, language="markdown")