import os
import mlflow
import pandas as pd
import mlflow.genai
from mlflow.genai.scorers import RelevanceToQuery, RetrievalGroundedness
from source_pkg.utils import get_config

def main():
    #auto log
    mlflow.langchain.autolog() 

    config = get_config()

    MODEL_URI = f"models:/{config.model_name}@{config.alias}"
    EXPERIMENT_PATH = config.experiment_path
    SYSTEM_PROMPT = config.system_prompt,
    LLM_TEMPERATURE = config.llm_temperature
    MAX_TOKENS = config.max_tokens
    LLM_MODEL = config.llm_model
    EVAL_LLM_MODEL = config.eval_llm_model

    eval_df = pd.DataFrame({
        "inputs": [
            {"question": "What is a brand of Wireless soundbar with dedicated subwoofer?"},
            {"question": "Do you have portable charger with integrated solar panels?"}
        ],
        "expectations": [
            {"expected_response": "CinemaBar 5.1 Surround System"},
            {"expected_response": "Yes, the EcoCharge Solar Power Bank"}
        ]
    })

    print(f"Starting Evaluation for: {MODEL_URI}")
    mlflow.set_experiment(EXPERIMENT_PATH)

    def predict_fn(question):
        loaded_model = mlflow.pyfunc.load_model(MODEL_URI)
        payload = {
            "input": [
                {"role": "user", "content": question}
            ]
        }
        raw_response = loaded_model.predict(payload)      
        if isinstance(raw_response, dict):
            return raw_response["output"][0]["content"][0]["text"]

        return raw_response.output[0].content[0].text

    with mlflow.start_run(run_name="tool_agent_eval"):
        mlflow.log_params({
            "system_prompt": SYSTEM_PROMPT,
            "temperature": LLM_TEMPERATURE,
            "max_tokens": MAX_TOKENS,
            "underlying_llm": LLM_MODEL
        })
        results = mlflow.genai.evaluate(
                data=eval_df,
                predict_fn=predict_fn, 
                scorers=[
                    RelevanceToQuery(model=f"endpoints:/{EVAL_LLM_MODEL}"),
                    RetrievalGroundedness(model=f"endpoints:/{EVAL_LLM_MODEL}")
                ]
            )

    print(f"Relevance: {results.metrics.get('relevance_to_query/v1/mean')}")
    print(f"Faithfulness: {results.metrics.get('faithfulness/v1/mean')}")

# Standard boilerplate for direct execution/testing
if __name__ == "__main__":
    main()

