import os
from databricks_openai import DatabricksOpenAI
from source_pkg.utils import get_config
import mlflow

def main():
    #auto log
    mlflow.langchain.autolog() 
    config = get_config()
    SERVING_ENDPOINT_NAME = config.serving_endpoint_name
    conversation_id = "conversation-session-10" # Use a new ID for a clean test
    query_agent_endpoint(
        SERVING_ENDPOINT_NAME,
        "noise-canceling headphones?",
        thread_id=conversation_id
    )    
    query_agent_endpoint(
        SERVING_ENDPOINT_NAME,
        "What are the best noise-canceling headphones under $300?",
        thread_id=conversation_id
    )
    query_agent_endpoint(
        SERVING_ENDPOINT_NAME,
        "Do any of those have a multi-year warranty?",
        thread_id=conversation_id
    )
    
def query_agent_endpoint(SERVING_ENDPOINT_NAME, prompt, thread_id="headphone-shopping-session-3"):
    client = DatabricksOpenAI()

    print(f"--- Querying Agent {SERVING_ENDPOINT_NAME} ---")
    
    try:
        response = client.responses.create(
            model=SERVING_ENDPOINT_NAME,
            input=[{"role": "user", "content": prompt}],
            context={"conversation_id": thread_id} # Use the standard field name
        )

        print(f"\nAgent: {response.content}")

    except Exception as e:
        # If 'conversation_id' isn't supported by your specific SDK version,
        # we fall back to the most reliable method: extra_body
        if "unexpected keyword argument" in str(e):
            response = client.responses.create(
                model=SERVING_ENDPOINT_NAME,
                input=[{"role": "user", "content": prompt}],
                extra_body={"context": {"conversation_id": thread_id}}
            )
            print(f"\nAgent: {response}")
            print(f"\nAgent: {response.output[0].content[0].text}")
        else:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

