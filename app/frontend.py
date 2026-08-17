import streamlit as st
import requests
st.set_page_config(
    page_title = "NexusRAG",
    page_icon = "🤖",
    layout = "wide"
)
st.title("NexusRAG: Autonomus Enterprise Knowledge Pipeline")
st.caption("A self-correcting multi-agent architecture for powered by Groq & FastAPI")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Agent Telemetry")
    st.write("This panel tracks the autonomous decision-making process of the RAG pipeline.")
    st.divider()
    telemetry_placeholder = st.empty()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about 2026 tax codes, Hellobooks compliance, or general Python code..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Agent routing query & validating context..."):
            try:
                response = requests.post(
                    "http://localhost:8000/api/v1/chat",
                    json = {"query": prompt}
                )
                if response.status_code == 200:
                    data = response.json()
                    answer = data["final_response"]
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    with telemetry_placeholder.container():
                        st.subheader("Latest Execution Stats")
                        st.info(f"**Route taken:** '{data['route_taken']}'")
                        audit_color = "green" if data['audit_status'] == "PASS" else "red"
                        st.markdown(f"**Recovery Loops Triggered:** '{data['total_recovery_loops']}")
                        with st.expander("View Execution Logs", expanded = True):
                            for log in data['execution_telemetry_logs']:
                                st.caption(f"🔹{log}")
                else:
                    st.error(f"Backend API Error: {response.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend! Is your FastAPI (Uvicorn) server running on port 8000?") 
