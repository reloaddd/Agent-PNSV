import streamlit as st
from agent_interface import GraphRAGAgent
import ollama
from memory import save_chat_turn, get_chat_history, get_current_repo_name, clear_repo_history

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Agent PNSV",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Minimal styling ─────────────────────────────────────────────────
st.markdown("""
<style>
    /* hide streamlit branding */
    #MainMenu, footer, header { visibility: hidden; }

    /* font */
    html, body, [class*="css"] {
        font-family: "JetBrains Mono", "Fira Code", "Courier New", monospace;
    }

    /* background */
    .stApp { background-color: #0d1117; }

    /* sidebar */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #21262d;
    }

    /* chat messages */
    .stChatMessage {
        background-color: #161b22 !important;
        border: 1px solid #21262d;
        border-radius: 6px;
        margin-bottom: 8px;
    }

    /* input */
    .stChatInputContainer {
        border-top: 1px solid #21262d;
        background-color: #0d1117;
    }

    textarea, .stTextArea textarea {
        background-color: #161b22 !important;
        color: #8b949e !important;
        border: 1px solid #21262d !important;
        font-family: "JetBrains Mono", monospace !important;
        font-size: 12px !important;
    }

    /* text colors */
    .stMarkdown, p, li { color: #c9d1d9; }
    h1, h2, h3 { color: #f0f6fc; font-weight: 500; }
    .stCaption { color: #8b949e; }

    /* code blocks */
    code {
        background-color: #161b22;
        color: #79c0ff;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 12px;
    }

    /* spinner */
    .stSpinner { color: #58a6ff; }

    /* scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #21262d; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ── Agent init ──────────────────────────────────────────────────────
@st.cache_resource
def load_agent():
    return GraphRAGAgent()

try:
    agent = load_agent()
except Exception as e:
    st.error(f"failed to connect to vector database — {e}")
    st.caption("run ingestion.py first to index a repository.")
    st.stop()


# ── DYNAMIC MEMORY SYNCHRONIZATION ───────────────────────────────
current_repo = get_current_repo_name()

# If the repository flipped or hasn't loaded yet, pull dedicated history files
if "active_repo_identity" not in st.session_state or st.session_state.active_repo_identity != current_repo:
    st.session_state.active_repo_identity = current_repo
    st.session_state.messages = []
    
    # Load persistent histories matching this repository track exclusively
    saved_logs = get_chat_history()
    for turn in saved_logs:
        st.session_state.messages.append({"role": "user", "content": turn["user"]})
        st.session_state.messages.append({"role": "assistant", "content": turn["assistant"]})


# ── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### agent-pnsv")
    st.caption("ast-driven graphrag · local inference")
    st.caption(f"📍 Active Repo: `{current_repo}`")
    st.divider()

    st.markdown("**model**")
    model = st.selectbox(
        "model",
        ["llama3", "llama3.2", "deepseek-r1", "codellama"],
        label_visibility="collapsed"
    )

    st.markdown("**context limit**")
    limit = st.slider("limit", min_value=1, max_value=10, value=5, label_visibility="collapsed")

    st.markdown("**verbose**")
    show_context = st.toggle("show retrieved chunks", value=True)

    st.divider()

    # context panel — shown after query
    if "last_context" in st.session_state and show_context:
        st.markdown("**retrieved context**")
        st.text_area(
            "context",
            value=st.session_state.last_context,
            height=400,
            disabled=True,
            label_visibility="collapsed"
        )

    st.divider()
    st.caption("db · ./pnsv_vector_db")
    st.caption("ollama · localhost:11434")

    if st.button("clear chat", use_container_width=True):
        clear_repo_history()
        st.session_state.messages = []
        if "last_context" in st.session_state:
            del st.session_state.last_context
        st.rerun()


# ── Main area ───────────────────────────────────────────────────────
col1, col2 = st.columns([6, 1])
with col1:
    st.markdown("## `agent-pnsv`")
    st.caption(f"querying: **{current_repo}** · structural code understanding · local inference")

st.divider()

# ── Chat history ────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown(f"""$ agent-pnsv --ready
                 vector database connected [{current_repo}]
                 awaiting query...
                """)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ── Chat input ──────────────────────────────────────────────────────
if user_query := st.chat_input("query codebase..."):

    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # retrieve context
    with st.spinner("traversing syntax trees..."):
        try:
            results, context = agent.retrieve_context(user_query, limit=limit)
            _, full_prompt   = agent.generate_prompt(user_query)
        except Exception as e:
            st.error(f"retrieval error — {e}")
            st.stop()

    if results is None:
        st.warning("no matching context found in indexed codebase.")
        st.stop()

    # store context for sidebar
    st.session_state.last_context = context

    # stream response
    with st.chat_message("assistant"):
        try:
            placeholder   = st.empty()
            response_text = ""

            stream = ollama.generate(
                model=model,
                prompt=full_prompt,
                stream=True
            )

            for chunk in stream:
                response_text += chunk['response']
                placeholder.markdown(response_text + "▌")

            placeholder.markdown(response_text)
            st.session_state.messages.append({
                "role":    "assistant",
                "content": response_text
            })
            
            # Log turn to isolated repo cache on drive
            save_chat_turn("GUI", user_query, response_text)

        except Exception as e:
            if "connect" in str(e).lower():
                st.error("ollama is not running — start with: `ollama serve`")
            else:
                st.error(f"inference error — {e}")