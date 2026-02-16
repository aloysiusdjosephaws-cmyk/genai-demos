import streamlit as st
import requests
import os
import json
import uuid

"""
# Databricks Agent Demo

An interactive demo showcasing a Databricks-deployed agent for answering questions about electronics products.
"""

DATABRICKS_HOST = os.getenv("host")
DATABRICKS_TOKEN = os.getenv("token")
SERVING_ENDPOINT_NAME = os.getenv("serving_endpoint_name")

# Construct the URL for the model endpoint
ENDPOINT_URL = f"{DATABRICKS_HOST}/serving-endpoints/{SERVING_ENDPOINT_NAME}/invocations"
print(f"endpoint URL-{ENDPOINT_URL}")

st.set_page_config(page_title="Databricks Agent Demo", layout="wide")
st.title("🤖 Get information about electronics products")

# --- 2. Session Initialization ---
"""
Initializes the session state to manage chat history and the current chat session.
"""
if "chats" not in st.session_state:
    st.session_state.chats = {}
    first_id = str(uuid.uuid4())
    st.session_state.chats[first_id] = {"name": ".", "messages": []}
    st.session_state.current_id = first_id

# --- 3. Sidebar Management ---
"""
Creates the sidebar UI for managing chat history, including creating new chats, 
selecting existing chats, and clearing all chats.
"""
with st.sidebar:
    st.title("History")
    if st.button("➕ New Chat", use_container_width=True):
        """Creates a new chat session."""
        new_id = str(uuid.uuid4())
        st.session_state.chats[new_id] = {"name": "New Search", "messages": []}
        st.session_state.current_id = new_id
        st.rerun()
    
    st.divider()
    """Displays the list of available chat sessions and allows users to select them."""
    for cid, data in st.session_state.chats.items():
        if st.button(data["name"], key=cid, use_container_width=True, 
                     type="primary" if cid == st.session_state.current_id else "secondary"):
            """Selects the chat session and reloads the page."""
            st.session_state.current_id = cid
            st.rerun()

    if st.button("🗑️ Clear All", use_container_width=True):
        """Clears all chat sessions and reloads the page."""
        st.session_state.clear()
        st.rerun()

# --- 4. Chat UI ---
"""
Displays the current chat session and renders previous messages.  Handles user input and 
sends requests to the Databricks endpoint to generate responses.
"""
current_chat = st.session_state.chats[st.session_state.current_id]
st.title(current_chat["name"])

# This loop renders all previous messages in the current chat
"""Renders the previous messages in the current chat session."""
for msg in current_chat["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask me anything..."):
    """Handles user input and sends it to the Databricks agent."""
    # Update Chat Name on first message
    if not current_chat["messages"]:
        """Updates the chat name with the user's first message."""
        current_chat["name"] = prompt[:20] + "..."
    
    # Add user message to state and display
    current_chat["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            headers = {"Authorization": f"Bearer {DATABRICKS_TOKEN}"}
            payload = {
                "input": current_chat["messages"],
                "context": {
                    "conversation_id": st.session_state.current_id 
                }
            }
            
            try:
                response = requests.post(ENDPOINT_URL, headers=headers, json=payload, timeout=120)

                if response.status_code == 200:
                    data = response.json()                    
                    try:
                        # Extract the text from the response
                        agent_