import streamlit as st
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime

API_URL = "http://localhost:8000"

st.set_page_config(page_title="AI Learning Agents", page_icon="🧠", layout="wide")

def get_agents() -> List[Dict]:
    """Fetch available agents from the v1 API."""
    try:
        response = requests.get(f"{API_URL}/api/v1/agents")
        response.raise_for_status()
        
        data = response.json()
        
        # Handle new SuccessResponse format
        if data.get("success") and "data" in data:
            return data["data"].get("agents", [])
        else:
            st.error("Unexpected response format from backend.")
            return []
            
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend. Make sure FastAPI is running on port 8000.")
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching agents: {str(e)}")
        return []

def send_message_stream(agent_id: str, message: str):
    """
    Send a message to an agent and stream the response.
    
    Yields chunks of the response as they arrive.
    """
    try:
        response = requests.post(
            f"{API_URL}/api/v1/agents/{agent_id}/stream",
            json={"message": message},
            timeout=20,
            stream=True
        )
        
        response.raise_for_status()
        
        # Parse SSE stream
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = json.loads(line[6:])  # Remove 'data: ' prefix
                    yield data
                    
    except requests.exceptions.Timeout:
        yield {"error": "Request timed out. Please try again or simplify your question.", "code": 504}
    except requests.exceptions.ConnectionError:
        yield {"error": "Cannot connect to backend. Make sure FastAPI is running.", "code": 500}
    except Exception as e:
        yield {"error": f"Unexpected error: {str(e)}", "code": 500}

# Initialize session state
if "selected_agent" not in st.session_state:
    st.session_state.selected_agent = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Agent Selection Page
if st.session_state.selected_agent is None:
    st.title("🧠 AI Learning Agents")
    st.markdown("Select a subject agent to start learning")
    
    agents = get_agents()
    
    cols = st.columns(3)
    for idx, agent in enumerate(agents):
        with cols[idx % 3]:
            with st.container():
                st.subheader(agent["name"])
                st.write(agent["description"])
                if st.button("Start Chat", key=agent["id"]):
                    st.session_state.selected_agent = agent
                    st.session_state.chat_history = []
                    st.rerun()

# Chat Page
else:
    agent = st.session_state.selected_agent
    
    # Header
    col1, col2 = st.columns([6, 1])
    with col1:
        st.title(f"💬 {agent['name']}")
        st.caption(agent["description"])
    with col2:
        if st.button("← Back"):
            st.session_state.selected_agent = None
            st.rerun()
    
    st.divider()
    
    # Chat history
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(msg["content"])
                    
                    # Display metadata if available
                    if msg.get("metadata"):
                        metadata = msg["metadata"]
                        
                        # Create a compact metadata display
                        meta_parts = []
                        if metadata.get("timestamp"):
                            try:
                                # Parse and format timestamp
                                ts = datetime.fromisoformat(metadata["timestamp"].replace("Z", "+00:00"))
                                meta_parts.append(f"⏰ {ts.strftime('%H:%M:%S')}")
                            except:
                                pass
                        
                        if metadata.get("processing_time_ms"):
                            meta_parts.append(f"⚡ {metadata['processing_time_ms']}ms")
                        
                        if meta_parts:
                            st.caption(" • ".join(meta_parts))
    
    # Input
    user_input = st.chat_input("Ask a question...")
    
    if user_input:
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Show user message
        with chat_container:
            st.chat_message("user").write(user_input)
        
        # Stream AI response
        with chat_container:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                metadata = {}
                error_occurred = False
                
                # Stream chunks
                for chunk_data in send_message_stream(agent["id"], user_input):
                    if "chunk" in chunk_data:
                        # Append chunk to response
                        full_response += chunk_data["chunk"]
                        message_placeholder.markdown(full_response + "▌")
                    elif "done" in chunk_data:
                        # Streaming complete
                        metadata = chunk_data.get("metadata", {})
                        message_placeholder.markdown(full_response)
                    elif "error" in chunk_data:
                        # Error occurred
                        error_occurred = True
                        error_msg = chunk_data["error"]
                        message_placeholder.error(f"❌ **Error:** {error_msg}")
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": f"❌ **Error:** {error_msg}"
                        })
                        break
                
                # If successful, save to history and show metadata
                if not error_occurred and full_response:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": full_response,
                        "metadata": metadata
                    })
                    
                    # Display metadata
                    meta_parts = []
                    if metadata.get("processing_time_ms"):
                        meta_parts.append(f"⚡ {metadata['processing_time_ms']}ms")
                    
                    if meta_parts:
                        st.caption(" • ".join(meta_parts))
        
        st.rerun()
