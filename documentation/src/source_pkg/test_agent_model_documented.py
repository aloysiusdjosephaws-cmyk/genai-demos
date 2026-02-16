import os
from databricks_openai import DatabricksOpenAI
from source_pkg.utils import get_config
import mlflow

def main():
    """
    Main function to demonstrate querying a Databricks OpenAI endpoint for
    noise-canceling headphone recommendations in a conversational manner.

    This function utilizes Langchain's autologging for MLflow tracking and
    queries a specified Databricks OpenAI endpoint multiple times with
    successive prompts, maintaining a conversation thread.

    Args:
        None. Configuration is loaded from `source_pkg.utils.get_config`.
    """
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
    """
    Queries a specified Databricks OpenAI endpoint with a given prompt,
    maintaining a conversation thread. Handles potential SDK version
    incompatibilities regarding the `context` parameter.

    Args:
        SERVING_ENDPOINT_NAME (str): The name of the Databricks OpenAI model
            endpoint to query.
        prompt (str): The user's query or prompt for the agent.
        thread_id (str, optional):  A unique identifier for the conversation
            thread. Defaults to "headphone-shopping-session-3".

    Returns:
        None. Prints the agent's response to the console.

    Raises:
        Exception: If an error occurs during the API call. The error handling
            attempts to gracefully fall back to using `extra_body` if the
            `context` parameter is not supported by the Databricks-OpenAI SDK
            version.
    """
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
