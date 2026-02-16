import os
from openai import OpenAI
import requests
from source_pkg.utils import get_config
import mlflow

def main():
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


    def create_enhanced_readme(analysis_dict, project_name=f"{APP_NAME} Project"):
        """
        Takes all detailed file analyses and asks the AI to write a comprehensive README.md,
        including a section on how the files work together.
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
        - Explain the role of each file within the overall architecture (e.g., "`utils.py` provides helper functions used by `data_processor.py`").
        
        ## 3. Detailed File Breakdown
        List each file and its detailed analysis that I have provided below. Use the filename as a sub-heading (e.g., `### `filename.py``).

        Here are the detailed analyses for each file:
        ---
        {all_analyses_text}
        ---
        
        Return ONLY the raw Markdown content for the complete README.md file.
        """
        
        print("\n--- Step 2: Calling AI to synthesize analyses into a final, enhanced README.md ---")
        
        try:
            response = client.chat.completions.create(
            model=TARGET_MODEL,
            messages=[{"role": "user", "content": final_prompt}],
            max_tokens=3072 # Increased limit for a very detailed final document
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"   ERROR: Could not generate the final README. Error: {e}")
            return "# Error Generating README"

    def get_detailed_file_analysis(code_snippet):
        """
        Calls the AI model to generate a structured analysis of a script,
        including its purpose and key components (functions/classes).
        """
        
        prompt = f"""
        Analyze the following Python script in detail. Provide a summary in Markdown format that includes the following sections:
        
        ### Purpose
        A concise overview of this file's role in the project.
        
        ### Key Components
        A bulleted list of the most important functions and classes in this file. For each, provide a brief, one-sentence description of its responsibility.

        Here is the script content:
        ---
        {code_snippet}
        """
        
        try:
            response = client.chat.completions.create(
            model=TARGET_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512 # Increased token limit for more detail
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"   WARNING: Could not analyze code. Error: {e}")
            return "### Purpose\nError analyzing this file.\n### Key Components\n- N/A"


    def analysis():
        file_analysis_results = {}

        print(f"--- Step 1: Generating detailed analysis for each file in {SOURCE_PATH} ---")
        extensions_to_check = (".py", ".txt", ".yml", ".yaml")
        for root, _, files in os.walk(SOURCE_PATH):
            for file in files:
                if file.endswith(extensions_to_check):
                    file_path = os.path.join(root, file)
                    print(f"Analyzing: {file_path}")
                    
                    with open(file_path, "r") as f:
                        code = f.read()
                    
                    if code.strip():
                        analysis = get_detailed_file_analysis(code)
                        file_analysis_results[file] = analysis
                    else:
                        file_analysis_results[file] = "### Purpose\nThis file is empty."

        print("\n--- All file analyses generated successfully! ---")
        return file_analysis_results
    
    def readme(file_analysis_results):
        # --- Generate and Write the Final README ---
        README_FILENAME = "README.md" 
        final_readme_content = create_enhanced_readme(file_analysis_results, os.path.basename(SOURCE_PATH))
        readme_path = os.path.join(TARGET_PATH, README_FILENAME)

        with open(readme_path, "w") as f:
            f.write(final_readme_content)

        print(f"\nSUCCESS! Enhanced documentation with architectural overview created at: {readme_path}")

    readme(analysis())

if __name__ == "__main__":
    main()
