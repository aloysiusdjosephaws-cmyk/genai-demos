import os
from openai import OpenAI
import requests
from source_pkg.utils import get_config
import mlflow
import sys

def main():
    """
    Main function to automate documentation generation for a Python project using OpenAI's GPT models.

    This script analyzes all Python files in a specified source directory, generates detailed
    summaries of each file's purpose and key components, and then uses a high-level GPT model
    to synthesize these summaries into a comprehensive README.md file that includes an architectural
    overview.  The script also stores a Databricks personal access token (PAT) as a secret.
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

    print(SOURCE_PATH)
    print(TARGET_PATH)
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


    def create_enhanced_readme(analysis_dict, project_name=f"{APP_NAME} Project"):
        """
        Takes all detailed file analyses and asks the AI to write a comprehensive README.md,
        including a section on how the files work together.

        Args:
            analysis_dict (dict): A dictionary where keys are filenames and values are detailed
                                    analyses of those files.
            project_name (str, optional): The name of the project. Defaults to f"{APP_NAME} Project".

        Returns:
            str: The raw Markdown content for the complete README.md file.
        """
        
        all_analyses_text = ""
        for filename, analysis in analysis_dict.items():
            all_analyses_text += f"## File: `{filename}`\n{analysis}\n\n---\n\n"
            
        final_prompt = f"""
        You are a principal software architect and technical writer. Your task is to create a comprehensive, high-level README.md for a project named '{project_name}'.
        You have been provided with a detailed analysis of each file in the project.

        Your generated README.md must contain the following sections in this exact order:
        
        # {project_name}
        
        ## 1. Project Overview
        A high-level summary of the project's overall purpose and goal, synthesized from the collective information.
        
        ## 2. Project Architecture and Workflow
        **This is the most important section.** Based on the file summaries, describe how the files likely interact to form a cohesive application.
        - Infer the data flow: Where does data seem to enter the system? How is it processed?
        - Infer the execution order: Is there a main script (e.g., `main.py`, `app.py`) that calls functions from other utility or module files?
        - Explain the role of each file