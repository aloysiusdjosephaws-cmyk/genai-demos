import os
from databricks_openai import DatabricksOpenAI
from source_pkg.utils import get_config
import mlflow

def main():
    """
    Main function to demonstrate querying a Databricks OpenAI agent for headphone recommendations and warranty information.

    This function initializes MLflow auto-logging, retrieves configuration parameters,
    and then sequentially queries a deployed agent endpoint with a series of prompts 
    related to noise-canceling headphones.  A conversation ID is used to maintain
    context across prompts.

    Note: Requires Databricks workspace and an OpenAI endpoint to be deployed. 
    Configuration settings such as 'serving_endpoint_name' must be defined 
    in the environment or config file.
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
    
def query_agent_endpoint(SERVING_ENDPOINT_NAME: str, prompt: str, thread_id: str = "headphone-shopping-session-3"):
    """
    Queries a specified Databricks OpenAI agent endpoint with a given prompt, maintaining conversation context.

    Args:
        SERVING_ENDPOINT_NAME (str): The name of the deployed OpenAI serving endpoint on Databricks.
        prompt (str): The user's query or prompt to send to the agent.
        thread_id (str, optional): A unique identifier for the conversation thread. 
                                    Defaults to "headphone-shopping-session-3".  Used to maintain context.

    Returns:
        None. Prints the agent's response to the console.

    Raises:
        Exception: If any error occurs during the API call.  Handles potential SDK version differences
                   regarding 'conversation_id' parameter.
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
