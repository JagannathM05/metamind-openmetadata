import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.metamind_agent import run_agent

st.set_page_config(page_title="MetaMind", page_icon="🧠", layout="wide")

st.markdown("""<style>
[data-testid="stSidebar"]{background:#1E3A5F}
[data-testid="stSidebar"] *{color:white!important}
[data-testid="stSidebar"] .stButton>button{background:#2563EB;color:white!important;border:none;border-radius:8px;width:100%;margin-bottom:4px;text-align:left;font-size:13px}
[data-testid="stSidebar"] .stButton>button:hover{background:#1D4ED8}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🧠 MetaMind")
    st.markdown("*AI Agent for OpenMetadata*")
    st.divider()
    st.markdown("### 🔍 Discovery")
    for ex in ["What tables exist?", "List the first 20 tables", "Search for process tables", "Find tables related to user data"]:
        if st.button(ex, key=ex): st.session_state.pending = ex
    st.markdown("### 📋 Schema")
    for ex in ["Get details of ACT_HI_PROCINST table", "Show columns of ACT_EVT_LOG table", "Get details of ACT_GE_PROPERTY table"]:
        if st.button(ex, key=ex): st.session_state.pending = ex
    st.markdown("### 🛡️ Governance")
    for ex in ["Detect PII in ACT_EVT_LOG table", "Auto classify PII across all tables", "Generate governance report for 10 tables", "Suggest data owners for unowned tables", "Apply PII.Sensitive tag to ACT_GE_BYTEARRAY"]:
        if st.button(ex, key=ex): st.session_state.pending = ex
    st.markdown("### 📊 Quality & Lineage")
    for ex in ["Check data quality of ACT_HI_PROCINST", "Show lineage of ACT_HI_PROCINST", "List all pipelines"]:
        if st.button(ex, key=ex): st.session_state.pending = ex
    st.divider()
    st.success("🟢 OpenMetadata v1.12.5\nlocalhost:8585")
    st.markdown("**168 tables** | **12 tools** | **MCP ready**")
    if st.button("🗑️ Clear Chat", key="clear"):
        st.session_state.messages = []
        st.rerun()

st.markdown("# 🧠 MetaMind")
st.markdown("**Conversational AI Agent for OpenMetadata** — powered by Groq + Llama 3.3")
st.markdown("*Discover data, trace lineage, detect PII, auto-classify, and govern your catalog through natural language*")
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": """👋 Hi! I'm **MetaMind**, your AI agent for OpenMetadata.

I can help you:
- 🔍 **Discover** 168 tables in your catalog
- 📋 **Explore** full schema and columns
- 🛡️ **Detect PII** and auto-classify tables
- 📊 **Check quality** and data health
- 🔗 **Trace lineage** upstream and downstream
- 🤖 **Semantic Search** — find tables by intent
- 📝 **Governance Report** — full compliance scan
- 👤 **Ownership** — suggest data owners
- 🏷️ **Auto-tag** — apply governance tags
- 📡 **MCP Server** — connect any MCP client

What would you like to explore?"""}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

query = st.session_state.pop("pending", None) or st.chat_input("Ask anything about your data catalog...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    with st.chat_message("assistant"):
        with st.spinner("🔍 MetaMind is thinking..."):
            response = run_agent(query, st.session_state.messages[:-1])
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})