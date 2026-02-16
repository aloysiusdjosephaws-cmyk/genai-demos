import os
from openai import OpenAI
import requests
from source_pkg.utils import get_config
import mlflow
import sys

def main():
    """
    Main function to automate documentation generation for Python code using a Databricks LLM endpoint.

    This function first stores a Databricks Personal Access Token (PAT) as a secret,
    then initializes an OpenAI client to communicate with a Databricks serving endpoint
    for generating docstrings.  Finally, it walks through a specified source code directory,
    generates Google-style docstrings for each Python file, and saves the documented
    code to a target directory with a "_documented.py" suffix.  MLflow autologging is enabled.
    """
    #auto log
    mlflow.langchain.autolog() 
    config = get_config()
    # --- Configuration ---
    APP_NAME = config.app_name
    TARGET_MODEL = config.llm_model
    workspace_url = config.workspace_host
    databricks_token = config.token

    SOURCE_PATH = config.source_code_path
    TARGET_PATH = config.documentation_path

    # --- Configuration ---
    scope_name = "databricks-secrets" 
    key_name = "db_pat" 

    api_url = f"{workspace_url}/api/2.0/secrets/put"

    headers = {
        'Authorization': f'Bearer {databricks_token}',
        'Content-Type': 'application/json'
    }

    payload = {
        "scope": scope_name,
        "key": key_name,
        "string_value": databricks_token
    }

    # --- Make the API Call ---
    print(f"Attempting to store secret '{key_name}' in scope '{scope_name}'...")

    response = requests.post(api_url, headers=headers, json=payload)

    # --- Check the Result ---
    if response.status_code == 200:
        print("\nSUCCESS! Your secret was successfully stored.")
    else:
        print(f"\nERROR: Failed to store the secret.")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

    # Initialize the OpenAI client.
    # The `api_key` is now set to your Databricks token.
    client = OpenAI(
        api_key=databricks_token,
        base_url=f"{workspace_url}/serving-endpoints"
    )

    print("Client configured to call Databricks endpoint with authentication.")


    def generate_docstrings_with_databricks_endpoint(code_snippet):
        """Calls a Databricks-hosted serving endpoint to generate docstrings.

        Args:
            code_snippet (str): The Python code snippet for which to generate docstrings.

        Returns:
            str: The code snippet with generated docstrings, or None if the API call fails.
        """
        
        prompt = f"You are an expert Python programmer. Your task is to add professional Google-style docstrings to the following Python code. Return ONLY the fully documented Python code, without any explanation. Do not wrap it in a markdown code block.\n\nHere is the code:\n\n{code_snippet}"

        try:
            response = client.chat.completions.create(
            model=TARGET_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"ERROR: Failed to call the model endpoint '{TARGET_MODEL}'.")
            print("This could be due to permission issues or the endpoint not being fully active on the free tier.")
            print(f"Details: {e}")
            return None

    
    def docstring():
        """
        Processes files in the source directory, generates docstrings using the Databricks endpoint,
        and saves the updated files to the target directory.
        """
        print(f"Starting documentation process for: {SOURCE_PATH}")

        for root, _, files in os.walk(SOURCE_PATH):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    # Get path relative to SOURCE_PATH (e.g., 'subdir/script.py')