import streamlit as st
import requests
import os
import json
import uuid

DATABRICKS_HOST = os.getenv("host")
DATABRICKS_TOKEN = os.getenv("token")
SERVING_ENDPOINT_NAME = os.getenv("serving_endpoint_name")

# Construct the URL for the model endpoint
ENDPOINT_URL = f"{DATABRICKS_HOST}/serving-endpoints/{SERVING_ENDPOINT_NAME}/invocations"
print(f"endpoint URL-{ENDPOINT_URL}")

st.set_page_config(page_title="Databricks Agent Demo", layout="wide")
st.title("DEMO - GenAI RAG system using Databricks")

# --- 2. Session Initialization ---
if "chats" not in st.session_state:
    st.session_state.chats = {}
    first_id = str(uuid.uuid4())
    st.session_state.chats[first_id] = {"name": " ", "messages": []}
    st.session_state.current_id = first_id

# --- 3. Sidebar Management ---
with st.sidebar:
    st.title("History")
    if st.button("➕ New Chat", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.chats[new_id] = {"name": "New Search", "messages": []}
        st.session_state.current_id = new_id
        st.rerun()
    
    st.divider()
    for cid, data in st.session_state.chats.items():
        if st.button(data["name"], key=cid, use_container_width=True, 
                     type="primary" if cid == st.session_state.current_id else "secondary"):
            st.session_state.current_id = cid
            st.rerun()

    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- 4. Chat UI ---
current_chat = st.session_state.chats[st.session_state.current_id]
st.title(current_chat["name"])

# This loop renders all previous messages in the current chat
for msg in current_chat["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Best headphones less than $300?"):
    # Update Chat Name on first message
    if not current_chat["messages"]:
        current_chat["name"] = prompt[:10] + "..."
    
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
                response = requests.post(ENDPOINT_URL, headers=headers, json=payload)

                if response.status_code == 200:
                    data = response.json()                    
                    try:
                        # Extract the text from the response
                        agent_text = data['output'][0]['content'][0]['text']                        
                        # DISPLAY the response
                        st.markdown(agent_text)                        
                        # SAVE the response to session state so it persists
                        current_chat["messages"].append({"role": "assistant", "content": agent_text})                        
                        # Rerun to ensure the UI is fully synced and the sidebar name updates
                        st.rerun()
                    except (KeyError, IndexError, TypeError) as e:
                        st.error(f"Could not parse the agent's response text. Error: {e}")
                else:
                    st.error(f"API Error {response.status_code}: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"A network error occurred: {e}")