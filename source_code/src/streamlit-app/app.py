import streamlit as st
import requests
import os
import json

st.set_page_config(page_title="Databricks Agent UI", layout="wide")
st.title("🤖 Chat with your Databricks Agent (Deployed App)")

DATABRICKS_HOST = os.getenv("workspace_host")
DATABRICKS_TOKEN = os.getenv("token")
SERVING_ENDPOINT_NAME = os.getenv("serving_endpoint_name")

# Construct the URL for the model endpoint
ENDPOINT_URL = f"{DATABRICKS_HOST}/serving-endpoints/{SERVING_ENDPOINT_NAME}/invocations"

# --- User Interface ---
prompt = st.text_input(
    "Enter your question for the agent:",
    value="What are the best noise-canceling headphones under $300?"
)

if st.button("💬 Send Query"):
    if not prompt:
        st.warning("Please enter a question.")
    else:
        with st.spinner(f"📡 Sending request to {SERVING_ENDPOINT_NAME}..."):
            # Define the payload and headers for the API request
            payload = {
                "input": [{"role": "user", "content": prompt}],
                "context": {"conversation_id": "databricks-app-session-001"}
            }
            headers = {"Authorization": f"Bearer {DATABRICKS_TOKEN}"}

            try:
                # Send the request to the model serving endpoint
                response = requests.post(ENDPOINT_URL, headers=headers, json=payload, timeout=120)

                # Check the HTTP response status code
                if response.status_code == 200:
                    st.success("Response received!")
                    data = response.json()
                    
                    # Safely parse the response to get the agent's text
                    try:
                        agent_text = data['output'][0]['content'][0]['text']
                        st.markdown("### Agent Response:")
                        st.markdown(agent_text)
                        st.markdown(data)
                    except (KeyError, IndexError, TypeError) as e:
                        st.error(f"Could not parse the agent's response text. Error: {e}")
                        st.json(data) # Display raw JSON for debugging
                else:
                    # Show an error if the API returned a non-200 status
                    st.error(f"API Error {response.status_code}: {response.text}")

            except requests.exceptions.RequestException as e:
                # Handle network-level errors (e.g., DNS failure, connection refused)
                st.error(f"A network error occurred: {e}")

