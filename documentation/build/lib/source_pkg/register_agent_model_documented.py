import os
import mlflow
from mlflow import MlflowClient
from mlflow.models.resources import DatabricksServingEndpoint, DatabricksVectorSearchIndex
from mlflow.types.responses import RESPONSES_AGENT_INPUT_EXAMPLE
from databricks.sdk.runtime import dbutils
from source_pkg.utils import get_config


def main():
    """
    Logs a model to MLflow, registers it in Unity Catalog, and sets an alias for a specific version.

    This function automates the model logging and registration process, leveraging MLflow and Unity Catalog on Databricks.
    It assumes the existence of a `source_pkg.utils.get_config` function to retrieve configuration parameters.
    The script supports the model-as-code pattern and includes logging of resources like Databricks Serving Endpoints and Vector Search Indexes.
    It also includes specific pip requirements.
    """
    # auto log
    mlflow.langchain.autolog()

    config = get_config()

    VS_INDEX_NAME = config.vs_index_name
    MODEL_NAME = config.model_name
    METADATA_VOLUME = config.metadata_volume
    EXPERIMENT_PATH = config.experiment_path
    LLM_MODEL = config.llm_model
    ALIAS = config.alias

    dbutils.fs.mkdirs(f"{METADATA_VOLUME}/artifacts")

    mlflow.set_tracking_uri("databricks")
    mlflow.set_registry_uri("databricks-uc")  # Ensure UC is primary
    mlflow.set_experiment(EXPERIMENT_PATH)

    try:
        with mlflow.start_run() as run:
            print(f"SUCCESS: Run ID: {run.info.run_id}")

            resource_list = [
                DatabricksServingEndpoint(endpoint_name=LLM_MODEL),
                DatabricksVectorSearchIndex(index_name=VS_INDEX_NAME)
            ]

            # Log model-as-code pattern
            # Log with the ResponsesAgent-compatible pattern
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(BASE_DIR, "agent_model.py")
            print(f"Loading model from: {model_path}")
            logged_info = mlflow.pyfunc.log_model(
                python_model=model_path,
                name="agent",
                input_example=RESPONSES_AGENT_INPUT_EXAMPLE,
                model_config=vars(config),  # to dict
                resources=resource_list,
                pip_requirements=[
                    "mlflow>=3.9.0",
                    "databricks-agents>=1.9.0",
                    "databricks-langchain>=0.14.0",
                    "langgraph>=1.0.6",
                    "pydantic>=2.0.0"
                ]
            )

            # Unity Catalog Registration
            model_uc = mlflow.register_model(
                model_uri=logged_info.model_uri,
                name=MODEL_NAME
            )

            # Set Alias using model_version object
            client = MlflowClient()
            client.set_registered_model_alias(
                name=MODEL_NAME,
                alias=ALIAS,
                version=str(model_uc.version)
            )
            print(f"Alias {ALIAS} set to version {model_uc.version}")

    except Exception as ee:
        print(f"ERROR: An exception occurred inside the mlflow.start_run() block: {ee}")


# Standard boilerplate for direct execution/testing
if __name__ == "__main__":
    main()  # pylint: disable=E1102